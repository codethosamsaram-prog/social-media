"""Reel production pipeline: storyboard -> voice -> timing -> sound design -> Remotion -> Instagram.

  1. Storyboard   storyboard.build(): scenes with narration + visual data per category
                  (LeetCode 20-32 s with a traced algorithm animation; repos 20-32 s with
                  how-it-works + setup + use cases; tools/tips 7-12 s).
  2. Voice        edge-tts (settings.tts_voice) per scene, all scenes in parallel. If the
                  reel runs long, the speaking rate is raised (from +15%), then optional scenes drop.
  3. Timing       openai-whisper word timestamps on the assembled voice track drive karaoke
                  captions and cue on-screen events (cards land as the narrator says them).
  4. Sound        drumless music bed (or assets/music/*) side-chain ducked to 25 % under the voice,
                  entering only after the hook, so a reel opens on the voice alone. Whooshes on
                  every cut, bright snaps on stamps, typing clicks, ticks per algorithm step,
                  chimes on results and a riser into the CTA. Nothing has a sub-bass thump.
  5. Visuals      Remotion (video/) renders 1080x1920 motion graphics from props.json.
  6. Publish      tmpfiles.org public URL -> /{ig-user-id}/media (REELS) -> poll FINISHED -> media_publish.

CLI:
    python auto_pipeline.py                         # render + publish next queued item
    python auto_pipeline.py --id seed-03-bitxor --no-publish
    python auto_pipeline.py --all --no-publish
    python auto_pipeline.py --publish-only seed-03-bitxor
"""

from __future__ import annotations

import argparse
import datetime as dt
import asyncio
import difflib
import json
import math
import random
import re
import shutil
import subprocess
import sys
import time
import wave
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import httpx
import numpy as np

import storyboard as sb
import topic_fetcher as tq
from config import settings

Log = Callable[[str], None]

FPS, SR = 30, 44100
LEAD, PAD = 0.15, 0.35           # silence before / after each scene's narration
DUCK_GAIN = 0.25                 # music at 25 % (-75 %) under the voice
MUSIC_LEVEL = 0.36
MAX_RATE = 22                    # gentle delivery: never faster than +22 %
VOICE_LOWCUT_HZ = 170            # nothing below ~85 Hz, full level from 170 Hz
VOICE_BODY_HZ, VOICE_BODY_GAIN = 380, 0.55  # chest resonance (under 190 Hz) cut to 55 %
VOICE_AIR_HZ, VOICE_AIR_DROP = 3000, 0.72   # everything under 1.5 kHz drops against the highs, for clarity
MUSIC_BASS_HZ, MUSIC_BASS_GAIN = 220, 0.0   # no bass from any bed or custom track
MUSIC_FADE_IN = 0.6              # seconds, starting when the hook ends
VIDEO_DIR = settings.base_dir / "video"

# ---------------------------------------------------------------------------
# ffmpeg + audio I/O
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        exe = shutil.which("ffmpeg")
        if exe:
            return exe
    raise RuntimeError("ffmpeg not found: pip install imageio-ffmpeg or put ffmpeg on PATH")


def decode_audio(path: Path, sr: int = SR, channels: int = 2) -> np.ndarray:
    """Decode any audio file to float32 PCM shaped (samples, channels)."""
    cmd = [ffmpeg_exe(), "-nostdin", "-v", "error", "-i", str(path),
           "-f", "s16le", "-acodec", "pcm_s16le", "-ac", str(channels), "-ar", str(sr), "-"]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed for {path}: {proc.stderr.decode(errors='ignore')[-400:]}")
    pcm = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return pcm.reshape(-1, channels)


def low_shelf(audio: np.ndarray, cutoff: float, gain: float, sr: int = SR) -> np.ndarray:
    """Scale everything below `cutoff` Hz by `gain` (0 = high-pass), with a one-octave smooth slope."""
    n = len(audio)
    if n == 0:
        return audio
    spec = np.fft.rfft(audio, axis=0)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    ramp = np.clip(np.log2(np.maximum(freqs, 1e-3) / (cutoff / 2)), 0, 1)  # 0 at cutoff/2 -> 1 at cutoff
    curve = gain + (1 - gain) * ramp
    return np.fft.irfft(spec * curve[:, None], n=n, axis=0).astype(np.float32)


def write_wav(path: Path, audio: np.ndarray, sr: int = SR) -> None:
    data = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(audio.shape[1])
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())


# ---------------------------------------------------------------------------
# Voice
# ---------------------------------------------------------------------------

Word = tuple[float, float, str]


async def _tts_once(text: str, out: Path, rate: int) -> list[Word]:
    import edge_tts

    kwargs = {"rate": f"{rate:+d}%", "pitch": settings.tts_pitch}
    try:
        comm = edge_tts.Communicate(text, settings.tts_voice, boundary="WordBoundary", **kwargs)
    except TypeError:  # edge-tts < 7 always emits WordBoundary
        comm = edge_tts.Communicate(text, settings.tts_voice, **kwargs)
    words: list[Word] = []
    with open(out, "wb") as fh:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


TTS_ATTEMPTS = 5
TTS_TIMEOUT = 30.0  # a scene is a few seconds of speech; edge-tts can stall forever without turn.end


async def _tts_one(text: str, out: Path, rate: int, sem: asyncio.Semaphore) -> list[Word]:
    """edge-tts throttles bursts with empty streams (NoAudioReceived) and sometimes never closes
    the stream at all; time out, back off and retry."""
    import edge_tts.exceptions as tts_err

    for attempt in range(TTS_ATTEMPTS):
        try:
            async with sem:
                return await asyncio.wait_for(_tts_once(text, out, rate), TTS_TIMEOUT)
        except (tts_err.NoAudioReceived, tts_err.WebSocketError, tts_err.UnexpectedResponse,
                tts_err.UnknownResponse, asyncio.TimeoutError, OSError):
            if attempt == TTS_ATTEMPTS - 1:
                raise
            await asyncio.sleep(1.5 * 2 ** attempt + random.random())
    raise AssertionError("unreachable")


async def _tts_all(jobs: list[tuple[str, Path]], rate: int) -> list[list[Word]]:
    sem = asyncio.Semaphore(2)
    return await asyncio.gather(*(_tts_one(text, path, rate, sem) for text, path in jobs))


def base_rate() -> int:
    match = re.match(r"([+-]?\d+)", settings.tts_rate)
    return int(match.group(1)) if match else 15


_WHISPER_MODELS: dict[str, Any] = {}


def whisper_words(path: Path, log: Log) -> list[Word] | None:
    try:
        import whisper
    except ImportError:
        log("openai-whisper not installed, using edge-tts word boundaries")
        return None
    name = settings.whisper_model
    if name not in _WHISPER_MODELS:
        log(f"Whisper: loading '{name}' model")
        _WHISPER_MODELS[name] = whisper.load_model(name)
    audio = decode_audio(path, 16000, 1)[:, 0].copy()
    result = _WHISPER_MODELS[name].transcribe(audio, word_timestamps=True, language="en", fp16=False)
    words = [(float(w["start"]), float(w["end"]), w["word"].strip())
             for seg in result.get("segments", []) for w in seg.get("words", []) if w["word"].strip()]
    log(f"Whisper: {len(words)} word timestamps")
    return words or None


def align_to_script(script: str, heard: list[Word], start: float, end: float) -> list[Word]:
    """Whisper gives great timing but mishears jargon ("LeetCode" -> "Lead code"). We know the
    exact script, so keep the script's words and borrow Whisper's timings: matched words take the
    heard timestamps, unmatched runs are spread across the gap between their neighbours."""
    tokens = script.split()
    if not tokens:
        return []
    if not heard:
        step = (end - start) / len(tokens)
        return [(start + i * step, start + (i + 1) * step, t) for i, t in enumerate(tokens)]
    norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())  # noqa: E731
    matcher = difflib.SequenceMatcher(a=[norm(t) for t in tokens], b=[norm(w[2]) for w in heard], autojunk=False)
    times: list[tuple[float, float] | None] = [None] * len(tokens)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            times[block.a + k] = heard[block.b + k][:2]
    i = 0
    while i < len(tokens):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(tokens) and times[j] is None:
            j += 1
        left = times[i - 1][1] if i > 0 else heard[0][0]  # type: ignore[index]
        right = times[j][0] if j < len(tokens) else heard[-1][1]  # type: ignore[index]
        if right <= left:
            right = left + 0.22 * (j - i)
        step = (right - left) / (j - i)
        for k in range(i, j):
            times[k] = (left + step * (k - i), left + step * (k - i + 1))
        i = j
    return [(a, b, t) for (a, b), t in zip(times, tokens)]  # type: ignore[misc]


def trim_silence(clip: np.ndarray, threshold: float = 0.02) -> tuple[np.ndarray, float]:
    """edge-tts pads every clip with ~0.85 s of silence; cut it so cuts land on the words.
    Returns (trimmed clip, seconds removed from the front)."""
    loud = np.where(np.abs(clip).max(axis=1) > threshold)[0]
    if not len(loud):
        return clip[:0], 0.0
    start = max(0, loud[0] - int(0.03 * SR))
    end = min(len(clip), loud[-1] + int(0.08 * SR))
    return clip[start:end], start / SR


def voice_scenes(scenes: list[sb.Scene], window: tuple[float, float], workdir: Path,
                 log: Log) -> tuple[list[sb.Scene], list[np.ndarray], list[list[Word]]]:
    """Synthesize every scene; speed up / drop optional scenes until the reel fits the window."""
    lo, hi = window
    rate = base_rate()
    while True:
        jobs = [(s.narration, workdir / f"voice_{i:02d}.mp3") for i, s in enumerate(scenes)]
        bounds = asyncio.run(_tts_all(jobs, rate))
        clips: list[np.ndarray] = []
        for k, (s, (_, path)) in enumerate(zip(scenes, jobs)):
            clip, cut = trim_silence(decode_audio(path))
            clips.append(clip)
            bounds[k] = [(a - cut, b - cut, w) for a, b, w in bounds[k]]
            s.voice_len = len(clip) / SR
            s.duration = max(s.min_dur, LEAD + s.voice_len + PAD)
        total = sum(s.duration for s in scenes)
        log(f"Voice at {rate:+d}%: {total:.1f}s across {len(scenes)} scenes (target {lo:.0f}-{hi:.0f}s)")
        if total <= hi:
            break
        if rate < MAX_RATE:
            # Only voice-bound scenes shrink when speech speeds up; padding and min_dur don't.
            # Scale the rate by how much of the *speech* must go, not the whole reel.
            bound = [s for s in scenes if LEAD + s.voice_len + PAD >= s.min_dur]
            speech = sum(s.voice_len for s in bound)
            target = speech - (total - hi) - 0.05
            if speech <= 0 or target <= 0:
                rate = MAX_RATE
            else:
                rate = min(MAX_RATE, math.ceil((100 + rate) * speech / target - 100) + 1)
            continue
        optional = [s for s in scenes if s.optional]
        if not optional:
            log(f"Still {total:.1f}s at max rate; keeping it")
            break
        scenes = [s for s in scenes if s is not optional[0]]
        rate = base_rate()
        log(f"Dropping optional '{optional[0].type}' scene to fit")
    deficit = lo - sum(s.duration for s in scenes)
    stretch = [s for s in scenes if s.stretchable]
    if deficit > 0 and stretch:
        for s in stretch:
            s.duration += min(deficit, 6.0) / len(stretch)
    t = 0.0
    for s in scenes:
        s.start = t
        t += s.duration
    return scenes, clips, bounds


# ---------------------------------------------------------------------------
# Sound design
# ---------------------------------------------------------------------------


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def _stereo(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32)
    return np.stack([x, x], axis=1)


def _onepole(x: np.ndarray, alphas: np.ndarray) -> np.ndarray:
    out = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alphas[i] * (x[i] - acc)
        out[i] = acc
    return out


def synth_sfx(name: str) -> np.ndarray:
    rng = np.random.default_rng(7)
    if name == "whoosh":
        n = int(0.42 * SR)
        t = np.linspace(0, 1, n)
        env = np.sin(np.pi * t ** 0.7) ** 2
        out = _onepole(rng.standard_normal(n), 0.02 + 0.25 * env)
        out *= env / (np.abs(out).max() + 1e-6)
        return np.stack([out * (1 - 0.6 * t), out * (0.4 + 0.6 * t)], axis=1).astype(np.float32) * 0.9
    if name == "pop":
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        freq = 320 + 700 * np.exp(-t * 40)
        return _stereo(np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.002, 0.04))
    if name == "click":
        n = int(0.03 * SR)
        burst = np.diff(rng.standard_normal(n + 1)) * _env(n, 0.0005, 0.005)
        tone = np.sin(2 * np.pi * 3200 * np.arange(n) / SR) * _env(n, 0.0003, 0.004) * 0.6
        out = burst / (np.abs(burst).max() + 1e-6) + tone
        return _stereo(out / (np.abs(out).max() + 1e-6))
    if name == "tick":
        n = int(0.06 * SR)
        t = np.arange(n) / SR
        out = np.sin(2 * np.pi * 2100 * t) * _env(n, 0.0005, 0.018) + 0.4 * np.sin(2 * np.pi * 4200 * t) * _env(n, 0.0005, 0.008)
        return _stereo(out / (np.abs(out).max() + 1e-6))
    if name == "impact":
        # A bright snap: no low sine, so stamps and cuts never read as a bass "dum".
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        crack = np.diff(rng.standard_normal(n + 1)) * _env(n, 0.0005, 0.03)
        tone = np.sin(2 * np.pi * np.cumsum(1500 - 900 * np.exp(-t * 30)) / SR) * _env(n, 0.001, 0.05)
        out = crack / (np.abs(crack).max() + 1e-6) + 0.7 * tone
        return _stereo(out / (np.abs(out).max() + 1e-6))
    if name == "chime":
        n = int(0.7 * SR)
        t = np.arange(n) / SR
        out = np.zeros(n)
        for delay, f in ((0.0, 1318.5), (0.07, 1760.0)):
            k = int(delay * SR)
            tt = t[: n - k]
            out[k:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * _env(n - k, 0.002, 0.22)
        return _stereo(out / (np.abs(out).max() + 1e-6))
    if name == "riser":
        n = int(0.9 * SR)
        t = np.linspace(0, 1, n)
        noise = _onepole(rng.standard_normal(n), 0.01 + 0.45 * t ** 2)
        sweep = np.sin(2 * np.pi * np.cumsum(200 + 1400 * t ** 2) / SR)
        out = (noise / (np.abs(noise).max() + 1e-6) * 0.7 + sweep * 0.3) * t ** 1.6
        return _stereo(out / (np.abs(out).max() + 1e-6))
    raise ValueError(name)


@lru_cache(maxsize=None)
def sfx(name: str) -> np.ndarray:
    custom = settings.assets_dir / "sfx" / f"{name}.wav"
    if custom.exists():
        return decode_audio(custom)
    return synth_sfx(name)


# bed -> (bpm, instrument, 16th-note pattern as chord-tone indexes (None = rest), soft hats?)
BEDS: dict[str, tuple[int, str, list[int | None], bool]] = {
    "lofi": (78, "keys", [0, None, None, 1, None, None, 2, None, None, None, 1, None, 2, None, None, None], True),
    "keys": (92, "keys", [0, None, 1, None, 2, None, 1, None] * 2, False),
    "pad": (70, "pad", [0] + [None] * 15, False),
    "pluck": (118, "pluck", [0, None, 2, 1, None, 2, 0, None, 1, None, 2, None, 0, 2, None, 1], True),
    "bell": (100, "bell", [2, None, None, 1, None, None, 0, None, None, None, 2, None, 1, None, None, None], False),
    "arp": (124, "pluck", [0, 1, 2, 3, 2, 1] * 2 + [0, 1, 2, 3], False),
}
CHORDS = [[0, 3, 7, 12], [-4, 0, 3, 8], [3, 7, 10, 15], [-2, 2, 5, 10]]  # minor i-VI-III-VII, in semitones


def _note(instrument: str, freq: float, length: float) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    if instrument == "pad":
        tone = sum(np.sin(2 * np.pi * freq * d * t) for d in (0.997, 1.0, 1.003, 2.0)) / 4
        return tone * np.minimum(1.0, t / 0.5) * np.minimum(1.0, (length - t) / 0.5)
    if instrument == "pluck":
        return (np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 18)) * np.exp(-t * 9)
    if instrument == "bell":
        return (np.sin(2 * np.pi * freq * 2 * t) + 0.35 * np.sin(2 * np.pi * freq * 5.52 * t) * np.exp(-t * 7)) * np.exp(-t * 3.5)
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)) * np.exp(-t * 3.2)  # keys


def synth_bed(kind: str, n: int, rng: random.Random) -> np.ndarray:
    """Procedural music with no kick and no bass: every note sits above 150 Hz."""
    bpm, instrument, pattern, hats = BEDS.get(kind, BEDS["lofi"])
    step = 60 / bpm / 4
    root = 220.0 * 2 ** (rng.randint(-3, 3) / 12)
    out = np.zeros((n, 2), dtype=np.float32)
    nrng = np.random.default_rng(rng.randint(0, 1 << 30))

    def add(at: float, sig: np.ndarray, gain: float, pan: float = 0.0) -> None:
        i = int(at * SR)
        if i >= n:
            return
        sig = sig[: n - i] * gain
        out[i:i + len(sig), 0] += sig * (1 - max(0.0, pan))
        out[i:i + len(sig), 1] += sig * (1 + min(0.0, pan))

    hn = int(0.04 * SR)
    hat = np.diff(np.diff(nrng.standard_normal(hn + 2))) * _env(hn, 0.0003, 0.012)
    length = step * 16 if instrument == "pad" else 1.4
    for bar in range(int(n / SR / (step * 16)) + 1):
        t0 = bar * step * 16
        chord = CHORDS[bar % len(CHORDS)]
        for k, tone in enumerate(pattern):
            if tone is None:
                continue
            notes = chord if instrument == "pad" else [chord[tone % len(chord)]]
            for semi in notes:
                add(t0 + k * step, _note(instrument, root * 2 ** (semi / 12), length), 0.42, pan=(k % 4 - 1.5) * 0.12)
        if hats:
            for k in range(2, 16, 4):
                add(t0 + k * step, hat, 0.09, pan=0.3)
    return out


def music_bed(n: int, rng: random.Random, log: Log, kind: str = "lofi") -> np.ndarray:
    folder = settings.assets_dir / "music"
    exts = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    files = sorted(p for p in folder.glob("*") if p.suffix.lower() in exts) if folder.exists() else []
    if files:
        path = rng.choice(files)
        track = decode_audio(path)
        log(f"Music: {path.name}")
        if len(track) < n:
            track = np.tile(track, (math.ceil(n / len(track)), 1))
        start = rng.randint(0, max(0, len(track) - n))
        track = track[start:start + n]
    else:
        log(f"Music: procedural '{kind}' bed")
        track = synth_bed(kind, n, rng)
    return track / (np.abs(track).max() + 1e-6) * 0.9


def voice_eq(voice: np.ndarray) -> np.ndarray:
    """Takes the bass out of the voice: high-pass, chest cut, then a lift of the highs against the rest."""
    peak = np.abs(voice).max()
    if peak == 0:
        return voice
    out = low_shelf(voice, VOICE_LOWCUT_HZ, 0.0)
    out = low_shelf(out, VOICE_BODY_HZ, VOICE_BODY_GAIN)
    out = low_shelf(out, VOICE_AIR_HZ, VOICE_AIR_DROP)
    return out / (np.abs(out).max() + 1e-6) * peak


def duck_envelope(words: list[Word], n: int) -> np.ndarray:
    """Side-chain gain: 1.0 normally, DUCK_GAIN while the voice is active (40 ms attack, 250 ms release)."""
    rate = 1000
    m = n * rate // SR + 1
    target = np.ones(m, dtype=np.float32)
    spans: list[list[float]] = []
    for start, end, _ in words:
        s, e = start - 0.06, end + 0.12
        if spans and s - spans[-1][1] < 0.3:
            spans[-1][1] = max(spans[-1][1], e)
        else:
            spans.append([s, e])
    for s, e in spans:
        target[max(0, int(s * rate)):min(m, int(e * rate))] = DUCK_GAIN
    env = np.empty_like(target)
    attack, release = 1 - math.exp(-1 / (0.04 * rate)), 1 - math.exp(-1 / (0.25 * rate))
    level = 1.0
    for i, goal in enumerate(target):
        level += (attack if goal < level else release) * (goal - level)
        env[i] = level
    return np.interp(np.arange(n) / SR, np.arange(m) / rate, env).astype(np.float32)


def mix_audio(voice: np.ndarray, words: list[Word], events: list[tuple[float, str, float]],
              total: float, out: Path, rng: random.Random, log: Log, music_kind: str = "lofi",
              music_from: float = 0.0) -> None:
    n = int(round(total * SR))
    mix = np.zeros((n, 2), dtype=np.float32)
    mix[: min(n, len(voice))] += voice_eq(voice[:n])
    music = low_shelf(music_bed(n, rng, log, music_kind), MUSIC_BASS_HZ, MUSIC_BASS_GAIN)
    music = music * MUSIC_LEVEL * duck_envelope(words, n)[:, None]
    begin = min(n, int(music_from * SR))
    fade_in = min(n - begin, int(MUSIC_FADE_IN * SR))
    music[:begin] = 0                                   # the hook is voice only
    music[begin:begin + fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    fade = int(0.2 * SR)
    music[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix += music
    for at, name, gain in events:
        s = sfx(name)
        i = int(at * SR)
        if i < 0:
            s, i = s[-i:], 0
        if i >= n or not len(s):
            continue
        s = s[: n - i] * gain
        mix[i:i + len(s)] += s
    peak = np.abs(mix).max()
    if peak > 0.97:
        mix = np.tanh(mix / peak * 1.4) / math.tanh(1.4) * 0.97
    write_wav(out, mix)
    log(f"Audio: {len(events)} SFX cues, music ducked to {int(DUCK_GAIN * 100)}% under voice")


# ---------------------------------------------------------------------------
# Stock footage (hook background)
# ---------------------------------------------------------------------------


def fetch_pexels_clips(queries: list[str], count: int, log: Log) -> list[Path]:
    if not settings.pexels_api_key:
        log("Pexels: PEXELS_API_KEY not set, hook uses the animated background")
        return []
    folder = settings.assets_dir / "stock"
    folder.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    with httpx.Client(timeout=60, follow_redirects=True, headers={"Authorization": settings.pexels_api_key}) as client:
        for query in queries:
            if len(clips) >= count:
                break
            try:
                resp = client.get("https://api.pexels.com/videos/search",
                                  params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 15})
                resp.raise_for_status()
                videos = [v for v in resp.json().get("videos", []) if v.get("duration", 0) >= 3]
                random.shuffle(videos)
                for video in videos:
                    files = [f for f in video.get("video_files", [])
                             if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 1) and f.get("width", 0) >= 540]
                    if not files:
                        continue
                    best = min(files, key=lambda f: abs(f["width"] - 1080))
                    target = folder / f"pexels-{video['id']}-{best['width']}.mp4"
                    if not target.exists():
                        with client.stream("GET", best["link"]) as stream:
                            stream.raise_for_status()
                            with open(target, "wb") as fh:
                                for chunk in stream.iter_bytes(1 << 16):
                                    fh.write(chunk)
                    clips.append(target)
                    log(f"Pexels: '{query}' -> {target.name}")
                    break
            except Exception as exc:  # noqa: BLE001
                log(f"Pexels search '{query}' failed: {exc}")
    return clips


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def refresh_repo(item: dict[str, Any], log: Log) -> dict[str, Any]:
    """Pull the live star count / language so the narration never quotes stale numbers."""
    repo = item.get("repo")
    if item["category"] != "repo" or not repo or not repo.get("full_name"):
        return item
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    try:
        data = httpx.get(f"https://api.github.com/repos/{repo['full_name']}", headers=headers, timeout=15).json()
        if "stargazers_count" in data:
            repo = {**repo, "stars": data["stargazers_count"], "language": repo.get("language") or data.get("language")}
            log(f"GitHub: {repo['full_name']} has {repo['stars']:,} stars")
            return {**item, "repo": repo}
    except Exception as exc:  # noqa: BLE001
        log(f"GitHub stats refresh failed: {exc}")
    return item


def render_remotion(props_path: Path, out: Path, log: Log, attempt: int = 1) -> None:
    cli = VIDEO_DIR / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
    node = shutil.which("node")
    if not node or not cli.exists():
        raise RuntimeError("Remotion is not installed: run `npm ci` inside video/ (Node 18+ required)")
    cmd = [node, str(cli), "render", "src/index.ts", "Reel", str(out), f"--props={props_path}",
           "--codec=h264", "--crf=18", "--pixel-format=yuv420p", "--audio-codec=aac", "--audio-bitrate=192k", "--log=info"]
    log("Remotion: rendering motion graphics")
    proc = subprocess.Popen(cmd, cwd=VIDEO_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    tail: list[str] = []
    last_log = 0.0
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        tail = (tail + [line])[-25:]
        if re.search(r"Rendered|Encoded|Stitch", line) and time.time() - last_log > 8:
            log(f"Remotion: {line[:120]}")
            last_log = time.time()
    if proc.wait() != 0:
        if attempt < 2:
            # Remotion's temp audio-mixing dir occasionally vanishes mid-render on Windows; one retry clears it.
            log("Remotion: render failed, retrying once")
            return render_remotion(props_path, out, log, attempt + 1)
        raise RuntimeError("Remotion render failed:\n" + "\n".join(tail))


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def day_number() -> int:
    """Day N of the daily-posting streak (Day 1 = DAY_ONE in IST); DAY_NUMBER env overrides."""
    if settings.day_number_override:
        return settings.day_number_override
    today = dt.datetime.now(IST).date()
    return max(1, (today - settings.day_one).days + 1)


def fetch_logos(companies: list[dict[str, Any]], public: Path, rel: str, log: Log) -> None:
    """Company favicons (Google's favicon service) for the hiring cards; a letter avatar if it fails."""
    for c in companies:
        c["logo"] = None
        try:
            r = httpx.get(f"https://www.google.com/s2/favicons?domain={c['domain']}&sz=128", timeout=15, follow_redirects=True)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/") and len(r.content) > 300:
                name = f"logo-{re.sub(r'[^a-z0-9]', '', c['name'].lower())}.png"
                (public / name).write_bytes(r.content)
                c["logo"] = f"{rel}/{name}"
        except httpx.HTTPError as exc:
            log(f"Logo for {c['name']} failed ({exc}); using a letter avatar")


INSIGHT_METRICS = "views,reach,likes,comments,shares,saved"


def refresh_insights(log: Log) -> None:
    """Pull Insights for published reels into the queue so pick_style can learn what works."""
    if not settings.instagram_ready:
        return
    n = 0
    with httpx.Client(timeout=30) as client:
        for item in tq.load_queue():
            if not item.get("ig_media_id"):
                continue
            try:
                data = _graph(client, "GET", f"{item['ig_media_id']}/insights", metric=INSIGHT_METRICS)
            except Exception as exc:  # noqa: BLE001 - learning is best-effort
                log(f"Insights for {item['id']} failed: {exc}")
                continue
            metrics: dict[str, Any] = {}
            for m in data.get("data", []):
                if m.get("total_value"):
                    metrics[m["name"]] = m["total_value"].get("value", 0)
                elif m.get("values"):
                    metrics[m["name"]] = m["values"][0].get("value", 0)
            tq.update_item(item["id"], insights=metrics, insights_at=tq.now_iso())
            n += 1
    if n:
        log(f"Insights: refreshed {n} published reel(s) for style learning")


def render_topic(item: dict[str, Any], log: Log = print) -> Path:
    rng = random.Random(item["id"])
    workdir = settings.output_dir / item["id"]
    workdir.mkdir(parents=True, exist_ok=True)
    log(f"Rendering '{item['topic']}' ({item['category']})")

    item = refresh_repo(item, log)
    refresh_insights(log)
    style = sb.pick_style(item, tq.load_queue(), random.Random())
    day = day_number()
    item = {**item, "_style": style, "_day": day}
    log("Style: " + ", ".join(f"{axis}={style[axis]}" for axis in sb.AXES) + f" | Day {day}")

    public = VIDEO_DIR / "public" / "renders" / item["id"]
    if public.exists():
        shutil.rmtree(public)
    public.mkdir(parents=True)
    if item["category"] == "hiring":
        fetch_logos(item["hiring"]["companies"], public, f"renders/{item['id']}", log)

    scenes = sb.build(item, settings.account_handle)
    scenes, voice_clips, bounds = voice_scenes(scenes, sb.length_window(item), workdir, log)
    total = sum(s.duration for s in scenes)

    voice = np.zeros((int(round(total * SR)) + SR, 2), dtype=np.float32)
    edge_words: list[Word] = []
    for s, clip, bw in zip(scenes, voice_clips, bounds):
        clip = clip / (np.abs(clip).max() + 1e-6) * 0.92
        i = int((s.start + LEAD) * SR)
        voice[i:i + len(clip)] += clip[: len(voice) - i]
        edge_words += [(a + s.start + LEAD, b + s.start + LEAD, w) for a, b, w in bw]
    voice = voice[: int(round(total * SR))]
    voice_wav = workdir / "voice.wav"
    write_wav(voice_wav, voice)
    heard = whisper_words(voice_wav, log) or edge_words
    words: list[Word] = []
    for s in scenes:
        s.words = align_to_script(s.narration, [w for w in heard if s.start <= w[0] < s.start + s.duration],
                                  s.start + LEAD, s.start + LEAD + s.voice_len)
        words += s.words

    stock_rel = None
    clips = fetch_pexels_clips(item.get("stock_queries") or [], 1, log)
    if clips:
        shutil.copy(clips[0], public / "stock.mp4")
        stock_rel = f"renders/{item['id']}/stock.mp4"

    scene_props, events, impacts = [], [], []
    for s in scenes:
        props, sfx_cues, hits = sb.layout(s)
        if s.type == "hook":
            props["stock"] = stock_rel
        scene_props.append(props)
        events += sfx_cues
        impacts += hits
    log("Scenes: " + " | ".join(f"{p['type']} {p['duration']:.1f}s" for p in scene_props))

    mix_audio(voice, words, events, total, public / "mix.wav", rng, log, style["music"], scenes[0].duration)
    shutil.copy(public / "mix.wav", workdir / "mix.wav")

    props_doc = {
        "fps": FPS, "width": 1080, "height": 1920, "durationInFrames": int(math.ceil(total * FPS)),
        "audio": f"renders/{item['id']}/mix.wav", "handle": settings.account_handle, "keyword": item["keyword"],
        "accent": style["accent"],
        "style": {**{k: style[k] for k in sb.AXES}, "highlight": style["highlight"], "emoji": style["emoji"]},
        "day": day,
        "words": [{"start": round(a, 3), "end": round(b, 3), "text": w} for a, b, w in words],
        "scenes": scene_props, "impacts": sorted(round(t, 3) for t in impacts), "emphasis": sb.emphasis(scenes),
    }
    props_path = workdir / "props.json"
    props_path.write_text(json.dumps(props_doc, ensure_ascii=False), encoding="utf-8")

    out = workdir / "reel.mp4"
    try:
        render_remotion(props_path, out, log)
    finally:
        shutil.rmtree(public, ignore_errors=True)
    tq.update_item(item["id"], style_used={k: style[k] for k in sb.AXES}, day=day)
    log(f"Rendered {out} ({total:.1f}s, {out.stat().st_size / 1e6:.1f} MB)")
    return out


# ---------------------------------------------------------------------------
# Publishing: tmpfiles.org -> Meta Graph API
# ---------------------------------------------------------------------------


class GraphAPIError(RuntimeError):
    pass


def _graph(client: httpx.Client, method: str, path: str, **params: Any) -> dict[str, Any]:
    params["access_token"] = settings.instagram_access_token
    url = f"{settings.graph_base}/{path.lstrip('/')}"
    resp = client.request(method, url, params=params if method == "GET" else None,
                          data=params if method != "GET" else None)
    try:
        data = resp.json()
    except ValueError:
        data = {}
    if resp.status_code >= 400 or "error" in data:
        err = data.get("error", {})
        raise GraphAPIError(f"{method} {path} -> {resp.status_code}: {err.get('message') or resp.text[:300]}")
    return data


def upload_tmpfiles(path: Path, log: Log) -> str:
    with httpx.Client(timeout=600) as client, open(path, "rb") as fh:
        resp = client.post("https://tmpfiles.org/api/v1/upload", files={"file": (path.name, fh, "video/mp4")})
    resp.raise_for_status()
    page_url = resp.json()["data"]["url"]
    match = re.match(r"https?://tmpfiles\.org/(?:dl/)?(\d+)/(.+)", page_url)
    if not match:
        raise RuntimeError(f"Unexpected tmpfiles.org response: {page_url}")
    direct = f"https://tmpfiles.org/dl/{match.group(1)}/{match.group(2)}"
    log(f"Uploaded to {direct}")
    return direct


def build_caption(item: dict[str, Any]) -> str:
    day = item.get("day") or day_number()
    thing = "links" if item.get("links") else ("code" if item["category"] == "dsa" else "link")
    return (
        f"Day {day} 🗓️ | {item.get('caption') or item['topic']}\n\n"
        f"💬 Comment \"{item['keyword']}\" and I'll DM you the {thing} instantly.\n"
        f"❤️ Like + ➕ follow @{settings.account_handle} for a new dev hack every few hours.\n"
        f"📤 Send this to a dev friend who needs it.\n\n"
        + " ".join(item["hashtags"][:5])
    )


def publish_reel(video: Path, caption: str, log: Log = print) -> dict[str, Any]:
    settings.require("instagram_access_token", "instagram_user_id")
    video_url = upload_tmpfiles(video, log)
    uid = settings.instagram_user_id
    with httpx.Client(timeout=120) as client:
        container = _graph(client, "POST", f"{uid}/media", media_type="REELS", video_url=video_url,
                           caption=caption, share_to_feed="true")["id"]
        log(f"Container {container} created, waiting for Meta to process")
        deadline = time.time() + 15 * 60
        while True:
            status = _graph(client, "GET", container, fields="status_code,status")
            code = status.get("status_code")
            if code == "FINISHED":
                break
            if code in {"ERROR", "EXPIRED"}:
                raise GraphAPIError(f"Container {container} {code}: {status.get('status')}")
            if time.time() > deadline:
                raise GraphAPIError(f"Container {container} still {code} after 15 minutes")
            log(f"Container status: {code}")
            time.sleep(10)
        media_id = _graph(client, "POST", f"{uid}/media_publish", creation_id=container)["id"]
        permalink = _graph(client, "GET", media_id, fields="permalink").get("permalink")
    log(f"Published reel {media_id} {permalink or ''}")
    return {"ig_media_id": media_id, "permalink": permalink, "container_id": container}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


MAX_ATTEMPTS = 3


def next_for(category: str | None) -> dict[str, Any] | None:
    """Oldest queued item; `hiring` picks the hiring reel, anything else skips it."""
    queued = [i for i in tq.load_queue() if i.get("status", "queued") == "queued"]
    if category == "hiring":
        queued = [i for i in queued if i.get("category") == "hiring"]
    else:
        queued = [i for i in queued if i.get("category") != "hiring"]
    queued.sort(key=lambda i: i.get("created_at", ""))
    return queued[0] if queued else None


def process_topic(item_id: str | None = None, publish: bool = True, log: Log = print,
                  category: str | None = None) -> dict[str, Any] | None:
    item = tq.get_item(item_id) if item_id else next_for(category)
    if not item:
        log("Queue is empty" if not item_id else f"No queue item '{item_id}'")
        return None
    # Fail before touching the item: otherwise a missing token uses up the queue without posting.
    if publish:
        settings.require("instagram_access_token", "instagram_user_id")
    item = tq.validate_item(item)
    tq.update_item(item["id"], status="rendering", error=None)
    try:
        video = render_topic(item, log)
        rel = video.relative_to(settings.base_dir).as_posix() if video.is_relative_to(settings.base_dir) else str(video)
        item = tq.update_item(item["id"], status="rendered", video_path=rel, rendered_at=tq.now_iso())
        if publish:
            result = publish_reel(video, build_caption(item), log)
            item = tq.update_item(item["id"], status="published", published_at=tq.now_iso(), **result)
        return item
    except Exception as exc:
        # Unattended runs must survive a flaky TTS or upload: retry on a later run, then give up.
        attempts = int(item.get("attempts") or 0) + 1
        status = "queued" if attempts < MAX_ATTEMPTS else "failed"
        tq.update_item(item["id"], status=status, attempts=attempts, error=str(exc)[:500])
        log(f"FAILED (attempt {attempts}/{MAX_ATTEMPTS}): {exc}")
        raise


def publish_existing(item_id: str, log: Log = print) -> dict[str, Any]:
    item = tq.get_item(item_id)
    if not item or not item.get("video_path"):
        raise RuntimeError(f"'{item_id}' has no rendered video; render it first")
    video = Path(item["video_path"])
    video = video if video.is_absolute() else settings.base_dir / video
    result = publish_reel(video, build_caption(item), log)
    return tq.update_item(item_id, status="published", published_at=tq.now_iso(), **result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render and publish @code_tho_samsaram reels.")
    parser.add_argument("--id", help="queue item id (default: oldest queued)")
    parser.add_argument("--all", action="store_true", help="process every queued item")
    parser.add_argument("--no-publish", action="store_true", help="render only")
    parser.add_argument("--publish-only", metavar="ID", help="publish an already rendered item")
    parser.add_argument("--category", help="'hiring' = today's hiring reel; default = next non-hiring reel")
    args = parser.parse_args()
    try:
        if args.publish_only:
            publish_existing(args.publish_only)
            return 0
        if args.all:
            while tq.next_queued():
                process_topic(publish=not args.no_publish)
            return 0
        result = process_topic(args.id, publish=not args.no_publish, category=args.category)
        return 0 if result is not None or not args.id else 1
    except Exception as exc:  # noqa: BLE001
        print(f"Pipeline error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

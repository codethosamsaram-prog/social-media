import React, { useMemo } from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, fonts, textStroke } from "../theme";
import { CaptionStyle, Scene, Word } from "../types";

type Group = { start: number; end: number; words: Word[] };

/** Words that get an emoji pop above the caption when spoken (first match wins). */
const EMOJI: [RegExp, string][] = [
  [/^(fast|faster|speed|instant|seconds?|quick)/i, "⚡"], [/^(ai|gpt|llm|agent|model|claude)/i, "🤖"],
  [/^(free|open)/i, "🆓"], [/^(money|salary|paid|pay|cost)/i, "💰"], [/^(hiring|jobs?|roles?|apply|career)/i, "💼"],
  [/^(code|coding|python|react|function)/i, "💻"], [/^(bug|error|crash|broken)/i, "🐛"], [/^(secret|hidden|nobody)/i, "🤫"],
  [/^(fire|crazy|insane|exploded|viral)/i, "🔥"], [/^(stop|never|don'?t|wrong)/i, "🛑"], [/^(memory|space|o\(1\))/i, "🧠"],
  [/^(follow|like)/i, "❤️"], [/^(comment|dm|link|links)/i, "📩"], [/^(india|bengaluru|bangalore|hyderabad|pune|mumbai)/i, "🇮🇳"],
  [/^(win|wins|best|top|gold)/i, "🏆"], [/^(github|repo|stars?)/i, "⭐"], [/^(one|single)$/i, "☝️"],
];
const emojiFor = (w: string) => EMOJI.find(([re]) => re.test(w))?.[1];

/** Pops the emoji of the most recently spoken keyword above the caption block, then floats it away. */
const EmojiPop: React.FC<{ words: Word[]; top: number }> = ({ words, top }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const hit = [...words].reverse().find((w) => t >= w.start && t < w.start + 0.9 && emojiFor(w.text));
  if (!hit) return null;
  const p = spring({ frame: f - Math.round(hit.start * fps), fps, config: { stiffness: 300, damping: 10 } });
  const age = t - hit.start;
  const side = (hit.start * 7) % 2 > 1 ? 1 : -1;
  return (
    <div style={{ position: "absolute", top: top - 230 - age * 80, left: 540 + side * 300 - 70, fontSize: 140, transform: `scale(${p}) rotate(${side * 12 * p}deg)`, opacity: Math.min(1, (0.9 - age) * 4), filter: "drop-shadow(0 10px 20px rgba(0,0,0,.6))" }}>
      {emojiFor(hit.text)}
    </div>
  );
};

const strip = (w: string) => w.replace(/^[^\w$#@%(]+|[^\w%)!?]+$/g, "");
const clean = (w: string) => strip(w).toUpperCase();

/** Chunk words into punchy 1-3 word groups, breaking on punctuation and pauses. */
const groupWords = (words: Word[], maxWords = 3, maxChars = 16, upper = true): Group[] => {
  const groups: Group[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) groups.push({ start: cur[0].start, end: cur[cur.length - 1].end, words: cur });
    cur = [];
  };
  words.forEach((w, i) => {
    const text = upper ? clean(w.text) : strip(w.text);
    if (!text) return;
    const prev = cur[cur.length - 1];
    const chars = cur.reduce((n, x) => n + x.text.length, 0) + text.length;
    if (cur.length && (cur.length >= maxWords || chars > maxChars || (prev && w.start - prev.end > 0.28))) flush();
    cur.push({ ...w, text });
    if (/[.,!?;:]$/.test(words[i].text.trim())) flush();
  });
  flush();
  return groups;
};

/** Hormozi-style captions: active word in yellow, punched up, group springs in. */
export const Captions: React.FC<{ words: Word[]; scenes: Scene[]; accent: string; variant: CaptionStyle; highlight: string; emoji?: boolean }> = (props) => (
  <>
    <CaptionText {...props} />
    {props.emoji && <EmojiLayer {...props} />}
  </>
);

const EmojiLayer: React.FC<{ words: Word[]; scenes: Scene[] }> = ({ words, scenes }) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const scene = [...scenes].reverse().find((s) => t >= s.start);
  if (!scene || scene.captionY === null) return null;
  return <EmojiPop words={words} top={scene.captionY} />;
};

const CaptionText: React.FC<{ words: Word[]; scenes: Scene[]; accent: string; variant: CaptionStyle; highlight: string }> = ({
  words, scenes, accent, variant, highlight,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const groups = useMemo(
    () => (variant === "clean" ? groupWords(words, 5, 30, false) : variant === "type" ? groupWords(words, 4, 22, false) : variant === "underline" ? groupWords(words, 4, 24, false) : variant === "mega" ? groupWords(words, 1, 40) : variant === "neon" ? groupWords(words, 2, 12) : groupWords(words)),
    [words, variant],
  );

  const scene = [...scenes].reverse().find((s) => t >= s.start);
  if (!scene || scene.captionY === null) return null;

  const gi = groups.findIndex((g, i) => t >= g.start && t < (groups[i + 1]?.start ?? Infinity));
  if (gi < 0) return null;
  const g = groups[gi];
  if (t > g.end + 0.45) return null;

  const enter = spring({ frame: f - Math.round(g.start * fps), fps, config: { stiffness: 260, damping: 14, mass: 0.5 } });
  const activeIdx = g.words.findIndex((w, i) => t >= w.start && (i === g.words.length - 1 || t < g.words[i + 1].start));

  if (variant === "box") {
    // Highlight-box captions: active word sits on a solid colour block that slides between words.
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: scene.captionY - 70, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 6, opacity: Math.min(1, enter * 2), transform: `translateY(${(1 - enter) * 30}px)` }}>
        {g.words.map((w, i) => {
          const on = i === activeIdx;
          const punch = spring({ frame: f - Math.round(w.start * fps), fps, config: { stiffness: 420, damping: 15 } });
          return (
            <span key={`${gi}-${i}`} style={{
              fontFamily: fonts.heavy, fontWeight: 900, fontSize: 82, lineHeight: 1.1, padding: "2px 18px", borderRadius: 16,
              color: on ? "#0b0b0b" : t >= w.start ? "#fff" : "rgba(255,255,255,.5)",
              background: on ? highlight : "transparent", ...(on ? {} : textStroke(12)),
              boxShadow: on ? `0 10px 0 rgba(0,0,0,.35)` : undefined,
              transform: on ? `scale(${0.9 + 0.1 * punch}) rotate(${-1.5 * punch}deg)` : "none", display: "inline-block",
            }}>{w.text}</span>
          );
        })}
      </div>
    );
  }

  if (variant === "clean") {
    // Subtitle-bar captions: sentence case on a frosted pill, the spoken word tinted.
    return (
      <div style={{ position: "absolute", left: 70, right: 70, top: scene.captionY - 60, display: "flex", justifyContent: "center", opacity: Math.min(1, enter * 2) }}>
        <div style={{ padding: "18px 34px", borderRadius: 28, background: "rgba(10,10,18,.72)", border: "2px solid rgba(255,255,255,.12)", textAlign: "center", fontFamily: fonts.body, fontWeight: 700, fontSize: 60, lineHeight: 1.2, color: "#fff", boxShadow: "0 20px 50px rgba(0,0,0,.5)" }}>
          {g.words.map((w, i) => (
            <span key={`${gi}-${i}`} style={{ color: i === activeIdx ? highlight : t >= w.start ? "#fff" : "rgba(255,255,255,.45)" }}>
              {w.text}{i < g.words.length - 1 ? " " : ""}
            </span>
          ))}
        </div>
      </div>
    );
  }

  if (variant === "neon") {
    // Neon sign: outlined glowing letters, the spoken word fills in with flicker.
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: scene.captionY - 70, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 22, opacity: Math.min(1, enter * 2) }}>
        {g.words.map((w, i) => {
          const on = i === activeIdx;
          const flicker = on && Math.floor((t - w.start) * 30) % 7 === 1 ? 0.55 : 1;
          return (
            <span key={`${gi}-${i}`} style={{
              fontFamily: fonts.display, fontSize: 104, lineHeight: 1.05, letterSpacing: 2,
              color: on ? highlight : "transparent", WebkitTextStroke: `3px ${on ? highlight : t >= w.start ? "#fff" : "rgba(255,255,255,.4)"}`,
              textShadow: on ? `0 0 12px ${highlight}, 0 0 40px ${highlight}, 0 0 80px ${accent}` : `0 0 18px ${accent}66`, opacity: flicker,
            }}>{w.text}</span>
          );
        })}
      </div>
    );
  }

  if (variant === "bounce") {
    // Bouncy multi-colour words that drop in one by one, cartoon style.
    const palette = [highlight, "#ff7edb", "#36f9f6", "#9ece6a", "#ff9e64"];
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: scene.captionY - 80, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 14 }}>
        {g.words.map((w, i) => {
          const d = spring({ frame: f - Math.round(w.start * fps), fps, config: { stiffness: 380, damping: 9 } });
          if (t < w.start) return null;
          const on = i === activeIdx;
          return (
            <span key={`${gi}-${i}`} style={{
              fontFamily: fonts.heavy, fontWeight: 900, fontSize: on ? 100 : 86, lineHeight: 1.1, color: palette[(gi + i) % palette.length],
              ...textStroke(14), display: "inline-block", transform: `translateY(${(1 - d) * -160}px) rotate(${(i % 2 ? 4 : -4) * (on ? 1 : 0.4)}deg)`,
              textShadow: "0 10px 0 rgba(0,0,0,.45)",
            }}>{w.text}</span>
          );
        })}
      </div>
    );
  }

  if (variant === "gradient") {
    // Gradient-filled heavy type with a soft glow, the spoken word lifts.
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: scene.captionY - 80, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 22px", opacity: Math.min(1, enter * 2), transform: `translateY(${(1 - enter) * 34}px)` }}>
        {g.words.map((w, i) => {
          const on = i === activeIdx;
          return (
            <span key={`${gi}-${i}`} style={{ position: "relative", display: "inline-block", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 94, lineHeight: 1.08, transform: on ? "translateY(-8px) scale(1.08)" : "none", filter: `drop-shadow(0 8px 0 rgba(0,0,0,.6)) drop-shadow(0 0 ${on ? 26 : 0}px ${accent})` }}>
              <span style={{ backgroundImage: on ? `linear-gradient(90deg, ${highlight}, ${accent})` : "linear-gradient(180deg, #fff, #c9d2e8)", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>{w.text}</span>
            </span>
          );
        })}
      </div>
    );
  }

  if (variant === "tape") {
    // Label-maker strips: each word slapped on at its own tilt as it is spoken.
    return (
      <div style={{ position: "absolute", left: 30, right: 30, top: scene.captionY - 70, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 10 }}>
        {g.words.map((w, i) => {
          if (t < w.start) return null;
          const p = spring({ frame: f - Math.round(w.start * fps), fps, config: { stiffness: 480, damping: 18 } });
          return (
            <span key={`${gi}-${i}`} style={{ display: "inline-block", padding: "4px 20px", background: i === activeIdx ? highlight : "#f5f1e6", color: "#111", fontFamily: fonts.mono, fontWeight: 700, fontSize: 78, lineHeight: 1.1, boxShadow: "0 8px 18px rgba(0,0,0,.55)", transform: `rotate(${(i % 2 ? 2 : -2.5)}deg) scale(${1.5 - 0.5 * p})`, opacity: Math.min(1, p * 3) }}>{w.text}</span>
          );
        })}
      </div>
    );
  }

  if (variant === "mega") {
    // One word at a time, as large as it fits.
    const w = g.words[0];
    const p = spring({ frame: f - Math.round(w.start * fps), fps, config: { stiffness: 520, damping: 20 } });
    return (
      <div style={{ position: "absolute", left: 20, right: 20, top: scene.captionY - 100, textAlign: "center", fontFamily: fonts.display, fontSize: Math.min(170, Math.floor(1700 / Math.max(5, w.text.length))), lineHeight: 1.05, color: gi % 3 === 1 ? highlight : "#fff", ...textStroke(14), transform: `scale(${1.35 - 0.35 * p})`, opacity: Math.min(1, p * 3) }}>{w.text}</div>
    );
  }

  if (variant === "underline") {
    // Quiet white type; a highlight bar slides under whichever word is being spoken.
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: scene.captionY - 70, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 24px", opacity: Math.min(1, enter * 2) }}>
        {g.words.map((w, i) => {
          const on = i === activeIdx;
          const p = on ? spring({ frame: f - Math.round(w.start * fps), fps, config: { stiffness: 340, damping: 22 } }) : 0;
          return (
            <span key={`${gi}-${i}`} style={{ position: "relative", display: "inline-block", fontFamily: fonts.body, fontWeight: 700, fontSize: 84, lineHeight: 1.2, color: t >= w.start ? "#fff" : "rgba(255,255,255,.55)", ...textStroke(10) }}>
              {w.text}
              <span style={{ position: "absolute", left: 0, right: 0, bottom: 2, height: 12, borderRadius: 6, background: highlight, transform: `scaleX(${p})`, transformOrigin: "0 50%", boxShadow: `0 0 16px ${highlight}` }} />
            </span>
          );
        })}
      </div>
    );
  }

  if (variant === "karaoke") {
    // Colour wipes through each word in step with how long it is spoken.
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: scene.captionY - 80, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 22px", opacity: Math.min(1, enter * 2) }}>
        {g.words.map((w, i) => {
          const fill = Math.max(0, Math.min(1, (t - w.start) / Math.max(0.05, w.end - w.start))) * 100;
          return (
            <span key={`${gi}-${i}`} style={{ position: "relative", display: "inline-block", fontFamily: fonts.oswald, fontWeight: 700, fontSize: 104, lineHeight: 1.1, color: "#fff", ...textStroke(14) }}>
              {w.text}
              <span style={{ position: "absolute", left: 0, top: 0, color: highlight, clipPath: `inset(0 ${100 - fill}% 0 0)` }}>{w.text}</span>
            </span>
          );
        })}
      </div>
    );
  }

  if (variant === "type") {
    // Terminal captions: lowercase mono, typed out word by word behind a prompt.
    return (
      <div style={{ position: "absolute", left: 60, right: 60, top: scene.captionY - 50, display: "flex", justifyContent: "center" }}>
        <div style={{ fontFamily: fonts.mono, fontWeight: 700, fontSize: 62, color: "#e6edf3", background: "rgba(13,17,23,.85)", border: `2px solid ${accent}66`, borderRadius: 14, padding: "14px 26px", textShadow: `0 0 18px ${accent}55` }}>
          <span style={{ color: accent }}>&gt; </span>
          {g.words.filter((w) => t >= w.start).map((w, i) => (
            <span key={`${gi}-${i}`} style={{ color: i === activeIdx ? highlight : undefined }}>{w.text.toLowerCase()} </span>
          ))}
          <span style={{ opacity: Math.floor(t * 4) % 2 ? 0 : 1, color: accent }}>█</span>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        left: 40,
        right: 40,
        top: scene.captionY - 80,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        rowGap: 0,
        transform: `scale(${0.75 + 0.25 * enter}) translateY(${(1 - enter) * 40}px)`,
        opacity: Math.min(1, enter * 2),
      }}
    >
      {g.words.map((w, i) => {
        const active = t >= w.start && (i === g.words.length - 1 || t < g.words[i + 1].start);
        const spoken = t >= w.start;
        const punch = spring({ frame: f - Math.round(w.start * fps), fps, config: { stiffness: 400, damping: 12 } });
        return (
          <span
            key={`${gi}-${i}`}
            style={{
              fontFamily: fonts.heavy,
              fontWeight: 900,
              fontSize: 96,
              lineHeight: 1.05,
              letterSpacing: -1,
              color: active ? highlight : spoken ? "#ffffff" : "rgba(255,255,255,.55)",
              ...textStroke(16),
              textShadow: active ? `0 0 30px ${highlight}88, 0 10px 30px rgba(0,0,0,.7)` : "0 10px 30px rgba(0,0,0,.7)",
              transform: active ? `scale(${1 + 0.14 * punch}) rotate(${-2 * punch}deg)` : "none",
              display: "inline-block",
              padding: "0 0.24em",
              transformOrigin: "50% 60%",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};

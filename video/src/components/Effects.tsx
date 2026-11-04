import React from "react";
import { AbsoluteFill, interpolate, random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp } from "../theme";
import { BurstStyle, CameraStyle, Emphasis, GradeStyle, OverlayStyle, Scene } from "../types";

/** Animated film grain (seed changes every frame) + vignette + subtle scanlines. */
export const FilmLook: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="1080" height="1920" style={{ position: "absolute", opacity: 0.09, mixBlendMode: "overlay" }}>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={f % 12} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
      <AbsoluteFill
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,.18) 0px, rgba(0,0,0,.18) 1px, transparent 1px, transparent 4px)",
          opacity: 0.35,
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.65) 100%)" }} />
    </AbsoluteFill>
  );
};

/** Screen shake that decays after each impact time (seconds). Wrap content in it. */
export const Shake: React.FC<{ impacts: number[]; children: React.ReactNode }> = ({ impacts, children }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  let amp = 0;
  for (const t of impacts) {
    const d = f - t * fps;
    if (d >= 0 && d < 10) amp = Math.max(amp, (1 - d / 10) * 16);
  }
  const x = Math.sin(f * 12.9898) * amp;
  const y = Math.cos(f * 78.233) * amp;
  const r = Math.sin(f * 4.1) * amp * 0.04;
  return (
    <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px) rotate(${r}deg) scale(${1 + amp * 0.002})` }}>
      {children}
    </AbsoluteFill>
  );
};

const clampFn = (x: number) => Math.max(0, Math.min(1, x));
const FULL_WIDTH = new Set<string>(["problem", "visualize", "code", "demo", "browser", "hiring"]);

/** The edit's camera: reacts to stressed words. Scene content only, so captions stay rock-steady and readable. */
export const Camera: React.FC<{ kind: CameraStyle; emphasis: Emphasis[]; scenes: Scene[]; children: React.ReactNode }> = ({ kind, emphasis, scenes, children }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const scene = [...scenes].reverse().find((s) => t >= s.start);
  const start = scene?.start ?? 0;
  const local = t - start;
  const hits = emphasis.filter((e) => e.t >= start && e.t <= t);
  const last = hits[hits.length - 1];
  let scale = 1, x = 0, y = 0, rot = 0;
  if (kind === "punch" || kind === "snap") {
    // Stepped zoom levels, the classic jump-cut punch-in. 1.08 max keeps 60 px margins on screen.
    const levels = [1, 1.045, 1.08];
    const to = levels[hits.length % 3];
    const from = levels[(hits.length + 2) % 3];
    const p = kind === "snap" || !last ? 1 : spring({ frame: f - Math.round(last.t * fps), fps, config: { stiffness: 240, damping: 20 } });
    scale = hits.length === 0 ? 1 : from + (to - from) * p;
    x = (hits.length % 2 ? 1 : -1) * (scale - 1) * 120;
  } else if (kind === "drift") {
    const p = clampFn(local / Math.max(0.1, scene?.duration ?? 1));
    scale = 1 + 0.06 * p;
    x = Math.sin(start * 3) * 30 * p;
    y = Math.cos(start * 2) * 26 * p;
  } else if (kind === "handheld") {
    scale = 1.03;
    x = Math.sin(t * 1.3) * 9 + Math.sin(t * 3.7) * 4;
    y = Math.cos(t * 1.1) * 8 + Math.sin(t * 2.9) * 4;
    rot = Math.sin(t * 0.9) * 0.35;
  } else {
    const bump = last ? Math.max(0, 1 - (t - last.t) * 3.5) : 0;
    scale = 1.02 + Math.sin(t * 1.6) * 0.012 + bump * 0.03;
  }
  // These layouts run nearly edge to edge, so a full-strength move would crop them.
  const k = scene && FULL_WIDTH.has(scene.type) ? 0.35 : 1;
  return <AbsoluteFill style={{ transform: `translate(${x * k}px, ${y * k}px) rotate(${rot * k}deg) scale(${1 + (scale - 1) * k})`, transformOrigin: "50% 46%" }}>{children}</AbsoluteFill>;
};

/** A burst behind the caption on strong words. */
export const Bursts: React.FC<{ kind: BurstStyle; emphasis: Emphasis[]; scenes: Scene[]; color: string }> = ({ kind, emphasis, scenes, color }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const hit = [...emphasis].reverse().find((e) => e.strong && t >= e.t && t < e.t + 0.5);
  if (!hit) return null;
  const scene = [...scenes].reverse().find((s) => hit.t >= s.start);
  const cy = (scene?.captionY ?? 960) - 10;
  const p = clampFn((t - hit.t) / 0.5);
  const ease = 1 - (1 - p) ** 3;
  const seed = `b${hit.t}`;
  if (kind === "ring") {
    return <>{[0, 0.12].map((d) => {
      const q = clampFn((p - d) / (1 - d));
      const r = 90 + (1 - (1 - q) ** 3) * 430;
      return <div key={d} style={{ position: "absolute", left: 540 - r, top: cy - r, width: r * 2, height: r * 2, borderRadius: "50%", border: `${Math.max(1, 12 * (1 - q))}px solid ${color}`, opacity: 1 - q }} />;
    })}</>;
  }
  if (kind === "rays") {
    return (
      <svg width={1080} height={1920} style={{ position: "absolute", left: 0, top: 0, opacity: 1 - p }}>
        {new Array(14).fill(0).map((_, i) => {
          const a = (i / 14) * Math.PI * 2 + random(`${seed}-${i}`) * 0.2;
          const r1 = 170 + ease * 240, r2 = r1 + 90 * (1 - p) + 20;
          return <line key={i} x1={540 + Math.cos(a) * r1} y1={cy + Math.sin(a) * r1} x2={540 + Math.cos(a) * r2} y2={cy + Math.sin(a) * r2} stroke={color} strokeWidth={8} strokeLinecap="round" />;
        })}
      </svg>
    );
  }
  if (kind === "slash") {
    return <div style={{ position: "absolute", left: -200, right: -200, top: cy - 60, height: 120, background: `linear-gradient(90deg, transparent, ${color}cc, transparent)`, transform: `translateX(${(ease - 0.5) * 1500}px) skewX(-24deg)`, opacity: 1 - p }} />;
  }
  return <>{new Array(20).fill(0).map((_, i) => {
    const a = random(`${seed}a${i}`) * Math.PI * 2;
    const r = 120 + ease * (200 + random(`${seed}r${i}`) * 330);
    const s = 8 + random(`${seed}s${i}`) * 14;
    return <div key={i} style={{ position: "absolute", left: 540 + Math.cos(a) * r, top: cy + Math.sin(a) * r + p * p * 110, width: s, height: s, borderRadius: i % 2 ? "50%" : 3, background: i % 3 ? color : "#fff", opacity: 1 - p, transform: `rotate(${p * 360}deg)` }} />;
  })}</>;
};

/** Finishing layer over everything except the chrome. */
export const Overlay: React.FC<{ kind: OverlayStyle; accent: string }> = ({ kind, accent }) => {
  const f = useCurrentFrame();
  const t = f / useVideoConfig().fps;
  if (kind === "leaks") {
    return (
      <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none" }}>
        <div style={{ position: "absolute", left: -500 + Math.sin(t * 0.7) * 500, top: 100 + Math.cos(t * 0.5) * 400, width: 1000, height: 1300, borderRadius: "50%", background: "radial-gradient(circle, #ff8a3daa, transparent 65%)", opacity: 0.35 + 0.25 * Math.sin(t * 1.1) }} />
        <div style={{ position: "absolute", right: -520 + Math.cos(t * 0.6) * 460, bottom: Math.sin(t * 0.4) * 500, width: 900, height: 1200, borderRadius: "50%", background: `radial-gradient(circle, ${accent}99, transparent 65%)`, opacity: 0.3 + 0.2 * Math.cos(t * 0.9) }} />
      </AbsoluteFill>
    );
  }
  if (kind === "dust") {
    return <AbsoluteFill style={{ pointerEvents: "none" }}>{new Array(46).fill(0).map((_, i) => {
      const s = 2 + random(`d${i}`) * 5;
      return <div key={i} style={{ position: "absolute", left: (random(`dx${i}`) * 1200 + f * (0.3 + random(`dv${i}`))) % 1080, top: (random(`dy${i}`) * 1920 + Math.sin(t + i) * 30 - f * random(`du${i}`) * 0.7 + 1920) % 1920, width: s, height: s, borderRadius: "50%", background: "#fff", opacity: 0.1 + random(`do${i}`) * 0.28, filter: "blur(1px)" }} />;
    })}</AbsoluteFill>;
  }
  if (kind === "vhs") {
    const bar = ((f * 11) % 2300) - 200;
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: bar, height: 46, background: "linear-gradient(180deg, transparent, rgba(255,255,255,.14), transparent)" }} />
        <AbsoluteFill style={{ boxShadow: "inset 7px 0 0 rgba(255,0,90,.14), inset -7px 0 0 rgba(0,240,255,.14)" }} />
        <div style={{ position: "absolute", left: 70, top: 225, color: "#fff", opacity: 0.75, fontFamily: "monospace", fontWeight: 700, fontSize: 34 }}>{Math.floor(t * 2) % 2 ? "● " : "  "}REC</div>
      </AbsoluteFill>
    );
  }
  if (kind === "letterbox") {
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 96, background: "#000" }} />
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 96, background: "#000" }} />
      </AbsoluteFill>
    );
  }
  if (kind === "sparks") {
    return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>{new Array(26).fill(0).map((_, i) => {
      const v = 3 + random(`sv${i}`) * 7;
      const y = 1920 - ((f * v + random(`sy${i}`) * 1920) % 2000);
      const s = 3 + random(`ss${i}`) * 5;
      return <div key={i} style={{ position: "absolute", left: random(`sx${i}`) * 1080 + Math.sin(f / 14 + i) * 26, top: y, width: s, height: s, borderRadius: "50%", background: accent, boxShadow: `0 0 ${s * 3}px ${accent}`, opacity: Math.min(1, y / 1400) }} />;
    })}</AbsoluteFill>;
  }
  return null;
};

export const GRADES: Record<GradeStyle, string | undefined> = {
  none: undefined,
  teal_orange: "contrast(1.1) saturate(1.2) hue-rotate(-6deg)",
  warm: "sepia(.16) saturate(1.2) contrast(1.04)",
  cool: "saturate(1.05) hue-rotate(10deg) contrast(1.06)",
  vivid: "saturate(1.4) contrast(1.06)",
  faded: "contrast(.92) saturate(.88) brightness(1.06)",
  contrast: "contrast(1.2) saturate(1.1)",
};

/** White flash + chromatic edge on impacts and cuts. */
export const Flashes: React.FC<{ times: number[] }> = ({ times }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  let o = 0;
  for (const t of times) {
    const d = f - t * fps;
    if (d >= 0 && d < 6) o = Math.max(o, interpolate(d, [0, 6], [0.45, 0], clamp));
  }
  if (o <= 0) return null;
  return <AbsoluteFill style={{ background: "#fff", opacity: o, mixBlendMode: "screen", pointerEvents: "none" }} />;
};

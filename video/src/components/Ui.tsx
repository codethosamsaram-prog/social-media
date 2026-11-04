import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { C, clamp, fonts, glow, pop, textStroke } from "../theme";

/** Small label chip + big title with a wipe-in underline. Used at the top of most scenes. */
export const Heading: React.FC<{ kicker?: string; title: string; accent: string; top?: number; size?: number }> = ({
  kicker, title, accent, top = 250, size = 92,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = pop(f, fps, 0.05);
  const h = pop(f, fps, 0.15, 200, 14);
  const wipe = interpolate(f / fps, [0.3, 0.7], [0, 1], clamp);
  return (
    <div style={{ position: "absolute", top, left: 50, right: 50, display: "flex", flexDirection: "column", alignItems: "center" }}>
      {kicker && (
        <div
          style={{
            padding: "8px 26px", borderRadius: 999, background: `${accent}22`, border: `3px solid ${accent}`,
            color: accent, fontFamily: fonts.mono, fontWeight: 700, fontSize: 30, letterSpacing: 4,
            transform: `scale(${k})`, boxShadow: glow(accent, 10), marginBottom: 22,
          }}
        >
          {kicker}
        </div>
      )}
      <div
        style={{
          fontFamily: fonts.heavy, fontWeight: 900, fontSize: size, lineHeight: 1.02, textAlign: "center", color: "#fff",
          textTransform: "uppercase", letterSpacing: -1, ...textStroke(10), textShadow: "0 12px 30px rgba(0,0,0,.6)",
          transform: `translateY(${(1 - h) * 50}px) scale(${0.9 + 0.1 * h})`, opacity: h,
        }}
      >
        {title}
      </div>
      <div style={{ marginTop: 18, height: 10, width: 320 * wipe, borderRadius: 5, background: `linear-gradient(90deg, ${accent}, ${C.cyan})`, boxShadow: glow(accent, 12) }} />
    </div>
  );
};

/** Terminal window with a typed command and timed output lines. */
export const Terminal: React.FC<{ command: string; typing: [number, number]; output: { text: string; at: number }[]; width?: number }> = ({
  command, typing, output, width = 980,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const chars = Math.floor(interpolate(t, typing, [0, command.length], clamp));
  const cursorOn = t < typing[1] || Math.floor(t * 2.4) % 2 === 0;
  return (
    <div
      style={{
        width, borderRadius: 26, background: "#0b0b12", border: `2px solid ${C.border}`, overflow: "hidden",
        boxShadow: `0 40px 90px rgba(0,0,0,.65), 0 0 70px ${C.green}22`,
      }}
    >
      <div style={{ height: 62, background: "#14141c", display: "flex", alignItems: "center", padding: "0 26px", gap: 12 }}>
        {["#ff5f56", "#ffbd2e", "#27c93f"].map((c) => <div key={c} style={{ width: 20, height: 20, borderRadius: 10, background: c }} />)}
        <div style={{ marginLeft: 20, fontFamily: fonts.mono, fontSize: 24, color: C.dim }}>zsh — terminal</div>
      </div>
      <div style={{ padding: "26px 34px 30px", fontFamily: fonts.mono, fontSize: 36, lineHeight: 1.6 }}>
        <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          <span style={{ color: C.green }}>❯ </span>
          <span style={{ color: "#fff" }}>{command.slice(0, chars)}</span>
          {cursorOn && <span style={{ background: C.fg, color: C.fg }}>_</span>}
        </div>
        {output.map((o, i) => {
          const p = interpolate(t, [o.at, o.at + 0.15], [0, 1], clamp);
          if (p <= 0) return null;
          return (
            <div key={i} style={{ color: o.text.startsWith("✓") ? C.green : C.dim, opacity: p, whiteSpace: "pre-wrap" }}>
              {o.text}
            </div>
          );
        })}
      </div>
    </div>
  );
};

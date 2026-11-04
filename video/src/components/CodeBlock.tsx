import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { C, clamp, fonts, glow, pop, textStroke } from "../theme";
import { CodeData } from "../types";

export const WindowChrome: React.FC<{ title: string; width: number; children: React.ReactNode; dark?: boolean }> = ({
  title, width, children, dark,
}) => (
  <div
    style={{
      width,
      borderRadius: 28,
      background: dark ? "#0d0d14" : C.panel,
      border: `2px solid ${C.border}`,
      boxShadow: `0 40px 90px rgba(0,0,0,.65), 0 0 0 1px rgba(255,255,255,.04) inset, 0 0 80px ${C.purple}22`,
      overflow: "hidden",
    }}
  >
    <div style={{ height: 70, background: C.panel2, display: "flex", alignItems: "center", padding: "0 28px", position: "relative" }}>
      {["#ff5f56", "#ffbd2e", "#27c93f"].map((c) => (
        <div key={c} style={{ width: 22, height: 22, borderRadius: 11, background: c, marginRight: 14 }} />
      ))}
      <div style={{ position: "absolute", left: 0, right: 0, textAlign: "center", fontFamily: fonts.mono, fontSize: 26, color: C.dim }}>
        {title}
      </div>
    </div>
    {children}
  </div>
);

/** Syntax-highlighted code with typing, a blinking cursor, focus-line spotlight and complexity stamps. */
export const CodeBlock: React.FC<{ code: CodeData; width?: number }> = ({ code, width = 980 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;

  const lineLens = code.lines.map((l) => l.reduce((n, [s]) => n + s.length, 0));
  const total = lineLens.reduce((a, b) => a + b + 1, 0);
  const longest = Math.max(...lineLens, 10);
  const gutterChars = String(code.lines.length).length + 1;
  const fontSize = Math.min(52, Math.floor((width - 90) / ((longest + gutterChars + 1) * 0.6)));
  const lineH = Math.round(fontSize * 1.6);

  const shown = Math.floor(interpolate(t, code.typing, [0, total], clamp));
  const typingDone = t >= code.typing[1];
  const focusP = code.focusAt === null ? 0 : interpolate(t, [code.focusAt, code.focusAt + 0.35], [0, 1], clamp);

  // `budget` = characters the typing animation has reached at the start of each line.
  let budget = shown;
  let cursorLine = -1;
  let cursorCol = 0;
  const rendered = code.lines.map((line, li) => {
    const spans: React.ReactNode[] = [];
    let left = Math.max(0, budget);
    for (const [text, color] of line) {
      if (left <= 0) break;
      const part = text.slice(0, left);
      spans.push(<span key={spans.length} style={{ color }}>{part}</span>);
      left -= part.length;
    }
    const visible = budget >= 0;
    if (cursorLine < 0 && budget <= lineLens[li]) {
      cursorLine = li;
      cursorCol = Math.max(0, budget);
    }
    budget -= lineLens[li] + 1;
    const focused = code.focusLines.includes(li);
    const opacity = focused ? 1 : 1 - 0.62 * focusP;
    return { li, spans, visible, focused, opacity };
  });

  const cursorOn = !typingDone || Math.floor(t * 2.4) % 2 === 0;
  const charW = fontSize * 0.6;

  return (
    <div style={{ position: "relative" }}>
      <WindowChrome title={code.filename} width={width}>
        <div style={{ padding: "30px 0 36px", position: "relative" }}>
          {rendered.map(({ li, spans, visible, focused, opacity }) => (
            <div
              key={li}
              style={{
                height: lineH,
                display: "flex",
                alignItems: "center",
                fontFamily: fonts.mono,
                fontSize,
                whiteSpace: "pre",
                opacity,
                background: focused ? `rgba(122,162,247,${0.16 * focusP})` : "transparent",
                borderLeft: `6px solid ${focused ? `rgba(255,230,0,${focusP})` : "transparent"}`,
                transform: focused ? `scale(${1 + 0.035 * focusP})` : "none",
                transformOrigin: "30% 50%",
                textShadow: focused && focusP > 0 ? `0 0 18px rgba(122,162,247,${0.5 * focusP})` : "none",
              }}
            >
              <span style={{ width: gutterChars * charW + 40, textAlign: "right", paddingRight: 28, color: "#3b4261", flexShrink: 0 }}>
                {visible ? li + 1 : ""}
              </span>
              <span style={{ color: C.fg, position: "relative" }}>
                {spans}
                {cursorOn && li === cursorLine && (
                  <span
                    style={{
                      position: "absolute",
                      left: cursorCol * charW,
                      top: fontSize * 0.1,
                      width: charW * 0.55,
                      height: fontSize * 1.15,
                      background: C.fg,
                      boxShadow: glow(C.fg, 8),
                      display: "inline-block",
                    }}
                  />
                )}
              </span>
            </div>
          ))}
        </div>
      </WindowChrome>
      {code.stamps.map((s, i) => {
        const p = pop(f, fps, s.at, 320, 11);
        if (p <= 0.001) return null;
        return (
          <div
            key={s.text}
            style={{
              position: "absolute",
              right: i % 2 ? 40 : undefined,
              left: i % 2 ? undefined : 30,
              bottom: -70 - i * 10,
              padding: "10px 30px",
              border: `7px solid ${s.color}`,
              borderRadius: 18,
              color: s.color,
              background: "rgba(7,7,15,.88)",
              fontFamily: fonts.display,
              fontSize: 70,
              letterSpacing: 2,
              transform: `scale(${Math.max(0.94, 3 - 2 * p)}) rotate(${i % 2 ? 7 : -7}deg)`,
              opacity: Math.min(1, p * 1.5),
              boxShadow: glow(s.color, 18),
              ...textStroke(0),
            }}
          >
            {s.text}
          </div>
        );
      })}
    </div>
  );
};

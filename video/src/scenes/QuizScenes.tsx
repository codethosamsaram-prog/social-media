import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { WindowChrome } from "../components/CodeBlock";
import { CtaScene, QuizScene } from "../types";
import { C, clamp, fonts, glow, pop, textStroke } from "../theme";

const LETTERS = ["A", "B", "C", "D"];
const OPTION_COLORS = [C.cyan, C.pink, C.yellow, C.purple];

/** Question (+ optional code), four options, a spoken 3-2-1 countdown, then the right option lights up green. */
export const Quiz: React.FC<{ s: QuizScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const head = pop(f, fps, 0.02, 200, 14);
  const codeLines = s.code ? s.code.split("\n") : [];
  const codeFont = codeLines.length > 4 ? 34 : 42;
  const codeH = codeLines.length ? 70 + 36 + codeLines.length * codeFont * 1.35 : 0;
  const codeTop = 480;
  const optTop = codeLines.length ? codeTop + codeH + 40 : 540;
  const optH = 118;
  const revealed = t >= s.revealAt;
  const reveal = pop(f, fps, s.revealAt, 220, 12);

  // Which countdown number is showing (3, 2, 1), and how far through its beat we are.
  const idx = s.countdown.reduce((acc, at, i) => (t >= at ? i : acc), -1);
  const beatStart = idx >= 0 ? s.countdown[idx] : 0;
  const beat = idx >= 0 ? pop(f, fps, beatStart, 260, 11) : 0;
  const showCount = idx >= 0 && !revealed;

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 210, left: 60, right: 60, textAlign: "center", transform: `scale(${head})` }}>
        <div style={{ display: "inline-block", padding: "8px 26px", borderRadius: 14, background: `${accent}22`, border: `3px solid ${accent}`, color: accent, fontFamily: fonts.mono, fontWeight: 700, fontSize: 32, letterSpacing: 2 }}>
          {s.kicker ?? "QUICK QUIZ"}
        </div>
        <div style={{ marginTop: 22, fontFamily: fonts.heavy, fontWeight: 900, fontSize: 66, lineHeight: 1.08, color: "#fff", ...textStroke(8) }}>
          {s.question}
        </div>
      </div>

      {codeLines.length > 0 && (
        <div style={{ position: "absolute", top: codeTop, left: 70, opacity: Math.min(1, head * 1.5), transform: `translateY(${(1 - head) * 40}px)` }}>
          <WindowChrome title="quiz" width={940} dark>
            <div style={{ padding: "18px 34px", fontFamily: fonts.mono, fontSize: codeFont, lineHeight: 1.35, color: C.fg, whiteSpace: "pre" }}>
              {codeLines.map((line, i) => <div key={i}>{line || " "}</div>)}
            </div>
          </WindowChrome>
        </div>
      )}

      {s.options.map((opt, i) => {
        const p = pop(f, fps, s.optionTimes[i] ?? 0.5, 200, 14);
        const right = i === s.correct;
        const col = revealed ? (right ? C.green : C.red) : OPTION_COLORS[i];
        const dim = revealed && !right ? interpolate(reveal, [0, 1], [1, 0.38], clamp) : 1;
        const grow = revealed && right ? 1 + 0.06 * reveal : 1;
        return (
          <div
            key={i}
            style={{
              position: "absolute", top: optTop + i * (optH + 22), left: 70, width: 940, height: optH, boxSizing: "border-box",
              display: "flex", alignItems: "center", gap: 28, padding: "0 30px", borderRadius: 28,
              background: revealed && right ? "rgba(30,60,30,.95)" : "rgba(22,22,32,.92)", border: `4px solid ${col}`,
              boxShadow: revealed && right ? glow(C.green, 22) : `0 18px 40px rgba(0,0,0,.45)`,
              opacity: Math.min(1, p * 2) * dim, transform: `translateX(${(1 - p) * (i % 2 ? 900 : -900)}px) scale(${grow})`,
            }}
          >
            <div style={{ width: 76, height: 76, borderRadius: 38, flexShrink: 0, background: col, color: "#07070f", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: fonts.display, fontSize: 48 }}>
              {LETTERS[i]}
            </div>
            <div style={{ flex: 1, minWidth: 0, fontFamily: fonts.mono, fontWeight: 700, fontSize: opt.length > 14 ? 40 : 50, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {opt}
            </div>
            {revealed && (
              <div style={{ fontSize: 64, transform: `scale(${reveal})` }}>{right ? "✅" : "❌"}</div>
            )}
          </div>
        );
      })}

      {showCount && (
        <div style={{ position: "absolute", top: optTop + 2 * (optH + 22) - 86, right: 36, width: 150, height: 150, borderRadius: 75, background: "rgba(10,10,18,.9)", border: `6px solid ${C.yellow}`, boxShadow: glow(C.yellow, 18), display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${0.6 + 0.4 * beat})` }}>
          <span style={{ fontFamily: fonts.display, fontSize: 100, color: C.yellow }}>{3 - idx}</span>
        </div>
      )}
      {!revealed && idx < 0 && t > (s.optionTimes[s.optionTimes.length - 1] ?? 1) + 0.4 && (
        <div style={{ position: "absolute", top: optTop + 4 * (optH + 22) + 10, width: "100%", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 44, color: C.yellow, ...textStroke(6) }}>
          COMMENT YOUR ANSWER 👇
        </div>
      )}
    </AbsoluteFill>
  );
};

/** Quiz ending: no DM promise, just "comment your answer" and follow. */
export const QuizCta: React.FC<{ s: CtaScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bubble = pop(f, fps, s.bubbleAt, 200, 12);
  const follow = pop(f, fps, s.followAt, 200, 12);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 430, width: "100%", display: "flex", justifyContent: "center", gap: 26 }}>
        {LETTERS.map((l, i) => {
          const p = pop(f, fps, 0.1 + i * 0.12, 240, 11);
          return (
            <div key={l} style={{ width: 170, height: 170, borderRadius: 40, background: OPTION_COLORS[i], color: "#07070f", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: fonts.display, fontSize: 110, transform: `scale(${p}) rotate(${(1 - p) * 30}deg)`, boxShadow: glow(OPTION_COLORS[i], 14) }}>
              {l}
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", top: 700, left: 60, right: 60, textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 92, lineHeight: 1.05, color: "#fff", ...textStroke(10), transform: `scale(${bubble})` }}>
        DID YOU GET IT <span style={{ color: C.green }}>RIGHT?</span>
      </div>
      <div style={{ position: "absolute", top: 960, left: 60, right: 60, textAlign: "center", fontFamily: fonts.body, fontWeight: 700, fontSize: 52, color: C.fg, opacity: bubble }}>
        Comment your answer 💬
      </div>
      <div style={{ position: "absolute", top: 1110, width: "100%", display: "flex", justifyContent: "center", transform: `scale(${follow})` }}>
        <div style={{ padding: "26px 54px", borderRadius: 60, background: accent, color: "#07070f", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 46, lineHeight: 1.15, maxWidth: 860, textAlign: "center", boxShadow: glow(accent, 20) }}>
          FOLLOW @{s.handle.toUpperCase()} FOR DAILY QUIZZES
        </div>
      </div>
    </AbsoluteFill>
  );
};

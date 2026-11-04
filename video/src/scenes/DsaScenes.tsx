import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ArrayViz } from "../components/ArrayViz";
import { Heading } from "../components/Ui";
import { NaiveScene, ProblemScene, VisualizeScene } from "../types";
import { C, clamp, fonts, glow, pop, textStroke } from "../theme";

const DIFF_COLOR = { Easy: C.green, Medium: C.orange, Hard: C.red } as const;

export const Problem: React.FC<{ s: ProblemScene; accent: string }> = ({ s }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const chip = pop(f, fps, 0.02);
  const title = pop(f, fps, 0.15, 200, 14);
  const body = pop(f, fps, 0.45, 120, 16);
  const n = s.example.length;
  const cell = Math.min(160, Math.floor((980 - (n - 1) * 16) / Math.max(1, n)));
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 300, width: "100%", display: "flex", justifyContent: "center", gap: 18, transform: `scale(${chip})` }}>
        <div style={{ padding: "10px 28px", borderRadius: 14, background: "#ffa1161f", border: "3px solid #ffa116", color: "#ffa116", fontFamily: fonts.mono, fontWeight: 700, fontSize: 34 }}>
          {s.source}{s.number ? ` #${s.number}` : ""}
        </div>
        <div style={{ padding: "10px 28px", borderRadius: 14, background: `${DIFF_COLOR[s.difficulty]}22`, border: `3px solid ${DIFF_COLOR[s.difficulty]}`, color: DIFF_COLOR[s.difficulty], fontFamily: fonts.mono, fontWeight: 700, fontSize: 34 }}>
          {s.difficulty}
        </div>
      </div>
      <div style={{ position: "absolute", top: 420, left: 60, right: 60, textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 100, lineHeight: 1, color: "#fff", textTransform: "uppercase", ...textStroke(10), transform: `translateY(${(1 - title) * 60}px)`, opacity: title }}>
        {s.title}
      </div>
      <div style={{ position: "absolute", top: 680, left: 80, right: 80, textAlign: "center", fontFamily: fonts.body, fontWeight: 500, fontSize: 56, lineHeight: 1.3, color: C.fg, opacity: body, transform: `translateY(${(1 - body) * 30}px)` }}>
        {s.statement}
      </div>
      {n > 0 && (
        <div style={{ position: "absolute", top: 1010, width: "100%" }}>
          <div style={{ textAlign: "center", fontFamily: fonts.mono, fontSize: 32, color: C.dim, marginBottom: 20, opacity: pop(f, fps, s.exampleAt[0] ?? 0.8) }}>input</div>
          <div style={{ display: "flex", justifyContent: "center", gap: 14 }}>
            {s.example.map((v, i) => {
              const p = pop(f, fps, s.exampleAt[i] ?? 0.8, 320, 12);
              return (
                <div key={i} style={{ width: cell, height: cell, borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(160deg, #24283b, #16161e)", border: `4px solid ${C.border}`, fontFamily: fonts.mono, fontWeight: 700, fontSize: Math.min(60, cell * 0.48), color: "#fff", transform: `translateY(${(1 - p) * -120}px) scale(${p})`, opacity: Math.min(1, p * 2) }}>
                  {String(v)}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

export const Naive: React.FC<{ s: NaiveScene; accent: string }> = ({ s }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const stamp = pop(f, fps, s.stampAt, 340, 11);
  const box = pop(f, fps, 0.1, 160, 15);
  const landed = s.itemTimes.filter((at) => t >= at + 0.25).length;
  const fill = interpolate(landed, [0, Math.max(1, s.items.length)], [0.05, 1], clamp);
  return (
    <AbsoluteFill>
      <Heading kicker={s.kicker ?? "THE OBVIOUS WAY"} title={s.label} accent={C.red} top={250} size={84} />
      <div style={{ position: "absolute", top: 600, left: 140, width: 800, height: 400, borderRadius: 34, border: `5px dashed ${C.red}`, background: "rgba(247,118,142,.07)", transform: `scale(${box})`, opacity: box }}>
        <div style={{ position: "absolute", top: -26, left: 40, padding: "4px 18px", background: C.bg, fontFamily: fonts.mono, fontSize: 32, color: C.red }}>memory</div>
        <div style={{ position: "absolute", inset: 40, display: "flex", flexWrap: "wrap", alignContent: "flex-start", gap: 20 }}>
          {s.items.map((v, i) => {
            const p = pop(f, fps, s.itemTimes[i] ?? 0, 260, 14);
            return (
              <div key={i} style={{ width: 120, height: 120, borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", background: "#24283b", border: `3px solid ${C.border}`, fontFamily: fonts.mono, fontWeight: 700, fontSize: 52, color: "#fff", transform: `translateY(${(1 - p) * -500}px) rotate(${(1 - p) * (i % 2 ? 30 : -30)}deg)`, opacity: Math.min(1, p * 3) }}>
                {String(v)}
              </div>
            );
          })}
        </div>
      </div>
      <div style={{ position: "absolute", top: 1060, left: 140, width: 800 }}>
        <div style={{ fontFamily: fonts.mono, fontSize: 30, color: C.dim, marginBottom: 12 }}>extra space</div>
        <div style={{ height: 34, borderRadius: 17, background: "#16161e", border: `2px solid ${C.border}`, overflow: "hidden" }}>
          <div style={{ width: `${fill * 100}%`, height: "100%", background: `linear-gradient(90deg, ${C.orange}, ${C.red})`, boxShadow: glow(C.red, 10) }} />
        </div>
      </div>
      {stamp > 0.001 && (
        <div style={{ position: "absolute", top: 720, width: "100%", display: "flex", justifyContent: "center" }}>
          <div style={{ padding: "16px 46px", border: `9px solid ${C.red}`, borderRadius: 22, color: C.red, background: "rgba(7,7,15,.9)", fontFamily: fonts.display, fontSize: 130, letterSpacing: 3, transform: `scale(${Math.max(0.94, 3 - 2 * stamp)}) rotate(-9deg)`, opacity: Math.min(1, stamp * 1.5), boxShadow: glow(C.red, 26) }}>
            ✗ {s.cost}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

export const Visualize: React.FC<{ s: VisualizeScene; accent: string }> = ({ s, accent }) => (
  <AbsoluteFill>
    <Heading kicker={s.kicker ?? "THE TRICK"} title={s.title} accent={accent} top={240} size={78} />
    <div style={{ position: "absolute", top: 450, height: 960, left: 0, width: 1080, display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <ArrayViz steps={s.steps} mode={s.mode} result={s.result} />
    </div>
  </AbsoluteFill>
);

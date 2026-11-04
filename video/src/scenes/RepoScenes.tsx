import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { CodeBlock } from "../components/CodeBlock";
import { Heading, Terminal } from "../components/Ui";
import { DemoScene, HowScene, RepoIntroScene, UseCasesScene } from "../types";
import { C, clamp, fonts, glow, pop, ramp } from "../theme";

const LANG_COLORS: Record<string, string> = {
  Python: "#3572A5", TypeScript: "#3178c6", JavaScript: "#f1e05a", Rust: "#dea584", Go: "#00ADD8",
  "C++": "#f34b7d", Java: "#b07219", Swift: "#F05138", Kotlin: "#A97BFF", Shell: "#89e051",
};

const GithubMark: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="#fff">
    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
  </svg>
);

export const RepoIntro: React.FC<{ s: RepoIntroScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const card = pop(f, fps, 0.05, 140, 14);
  const stars = s.stars * ramp(t, 0.5, 1.9);
  const burst = ramp(t, 1.85, 2.6);
  const ring = (t * 40) % 360;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 420, left: 140, width: 800, height: 800, borderRadius: "50%", background: `conic-gradient(from ${ring}deg, ${accent}00, ${accent}66, ${C.cyan}55, ${accent}00)`, filter: "blur(60px)", opacity: card }} />
      <div style={{ position: "absolute", top: 280, width: "100%", display: "flex", justifyContent: "center", transform: `scale(${pop(f, fps, 0)})` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "12px 30px", borderRadius: 999, background: "#ffffff14", border: "2px solid #ffffff33", fontFamily: fonts.mono, fontWeight: 700, fontSize: 32, color: "#fff" }}>
          <GithubMark size={38} /> {s.badge}
        </div>
      </div>
      <div
        style={{
          position: "absolute", top: 520, left: 60, width: 960, padding: "50px 54px", boxSizing: "border-box", borderRadius: 34,
          background: "linear-gradient(160deg, #1d1f2e, #0f1018)", border: `2px solid ${C.border}`,
          boxShadow: `0 50px 110px rgba(0,0,0,.7), 0 0 80px ${accent}33`,
          transform: `perspective(1400px) rotateX(${(1 - card) * 45}deg) translateY(${(1 - card) * 160}px)`, opacity: card,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20, fontFamily: fonts.mono, fontSize: 44 }}>
          <div style={{ width: 84, height: 84, borderRadius: 20, background: `linear-gradient(135deg, ${accent}, ${C.purple})`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 48, color: "#fff", flexShrink: 0 }}>
            {s.owner.slice(0, 1).toUpperCase()}
          </div>
          <div style={{ minWidth: 0, overflow: "hidden" }}>
            <div style={{ color: C.dim, fontSize: 34 }}>{s.owner} /</div>
            <div style={{ color: C.blue, fontWeight: 700, fontSize: s.name.length > 18 ? 46 : 58, whiteSpace: "nowrap" }}>{s.name}</div>
          </div>
        </div>
        <div style={{ marginTop: 34, fontFamily: fonts.body, fontWeight: 500, fontSize: 44, lineHeight: 1.35, color: C.fg }}>{s.description}</div>
        <div style={{ marginTop: 40, display: "flex", alignItems: "center", gap: 40, fontFamily: fonts.mono, fontSize: 40, color: C.fg }}>
          {s.language && (
            <span style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ width: 28, height: 28, borderRadius: 14, background: LANG_COLORS[s.language] ?? C.purple }} />
              {s.language}
            </span>
          )}
          <span style={{ position: "relative", display: "flex", alignItems: "center", gap: 12, color: C.yellow, fontWeight: 700, fontSize: 52, textShadow: glow(C.yellow, 10) }}>
            ★ {Math.round(stars).toLocaleString("en-US")}
            {new Array(10).fill(0).map((_, i) => {
              const a = random(`a${i}`) * Math.PI * 2;
              const d = burst * (120 + random(`d${i}`) * 160);
              return <span key={i} style={{ position: "absolute", left: 20 + Math.cos(a) * d, top: Math.sin(a) * d, fontSize: 34, opacity: burst > 0 ? 1 - burst : 0 }}>★</span>;
            })}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const How: React.FC<{ s: HowScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const n = s.steps.length;
  const nodeH = n > 3 ? 150 : 170;
  const gap = n > 3 ? 62 : 80;
  const top = 520;
  let active = -1;
  s.steps.forEach((st, i) => { if (t >= st.at) active = i; });
  return (
    <AbsoluteFill>
      <Heading kicker={s.kicker ?? "UNDER THE HOOD"} title={s.title} accent={accent} top={240} size={88} />
      {s.steps.map((st, i) => {
        const p = pop(f, fps, st.at, 200, 14);
        const y = top + i * (nodeH + gap);
        const next = s.steps[i + 1];
        const line = next ? ramp(t, st.at + 0.25, next.at) : 0;
        const dot = next ? interpolate(t, [st.at + 0.25, next.at], [0, 1], clamp) : 0;
        const isActive = i === active;
        return (
          <React.Fragment key={i}>
            {next && (
              <div style={{ position: "absolute", left: 140 - 4, top: y + nodeH, width: 8, height: gap * line, background: `linear-gradient(${accent}, ${C.cyan})`, borderRadius: 4, boxShadow: glow(accent, 8) }}>
                {dot > 0 && dot < 1 && <div style={{ position: "absolute", left: -10, top: gap * dot - 14, width: 28, height: 28, borderRadius: 14, background: "#fff", boxShadow: glow(C.cyan, 16) }} />}
              </div>
            )}
            <div
              style={{
                position: "absolute", top: y, left: 70, width: 940, height: nodeH, boxSizing: "border-box",
                display: "flex", alignItems: "center", gap: 34, padding: "0 34px 0 0",
                transform: `translateX(${(1 - p) * -220}px) scale(${isActive ? 1.03 : 1})`, opacity: Math.min(1, p * 2),
              }}
            >
              <div style={{ width: 140, height: 140, borderRadius: 70, flexShrink: 0, background: isActive ? `${accent}33` : "#16161e", border: `5px solid ${isActive ? accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 68, boxShadow: isActive ? glow(accent, 20) : "none" }}>
                {st.icon}
              </div>
              <div style={{ flex: 1, padding: "22px 30px", borderRadius: 26, background: isActive ? "rgba(36,40,59,.95)" : "rgba(22,22,30,.85)", border: `2px solid ${isActive ? accent : C.border}` }}>
                <div style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 46, color: "#fff", lineHeight: 1.1 }}>{st.title}</div>
                <div style={{ fontFamily: fonts.mono, fontSize: 30, color: isActive ? C.cyan : C.dim, marginTop: 8 }}>{st.detail}</div>
              </div>
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

export const Demo: React.FC<{ s: DemoScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const term = pop(f, fps, 0.02, 160, 15);
  const code = s.code ? pop(f, fps, s.codeAt, 150, 15) : 0;
  const termH = 62 + 56 + 58 * (1 + s.output.length);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 230, width: "100%", display: "flex", justifyContent: "center" }}>
        <div style={{ padding: "8px 26px", borderRadius: 999, background: `${accent}22`, border: `3px solid ${accent}`, color: accent, fontFamily: fonts.mono, fontWeight: 700, fontSize: 30, letterSpacing: 4, boxShadow: glow(accent, 10), transform: `scale(${pop(f, fps, 0)})` }}>
          {s.kicker ?? "TRY IT"}
        </div>
      </div>
      <div style={{ position: "absolute", top: 330, left: 50, transform: `translateY(${(1 - term) * 100}px) scale(${s.code ? 1 - 0.06 * code : 1})`, transformOrigin: "50% 0", opacity: term }}>
        <Terminal command={s.install} typing={s.installTyping} output={s.output} />
      </div>
      {s.code && (
        <div style={{ position: "absolute", top: 330 + termH + 30 - code * 20, left: 50, transform: `perspective(1400px) rotateX(${(1 - code) * 35}deg) translateY(${(1 - code) * 140}px)`, opacity: code }}>
          <CodeBlock code={s.code} />
        </div>
      )}
    </AbsoluteFill>
  );
};

export const UseCases: React.FC<{ s: UseCasesScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const colors = [C.cyan, accent, C.yellow, C.green];
  return (
    <AbsoluteFill>
      <Heading kicker={s.kicker ?? "WHAT YOU CAN BUILD"} title={s.title} accent={accent} top={240} size={92} />
      {s.cards.map((c, i) => {
        const p = pop(f, fps, c.at, 190, 13);
        const from = i % 2 ? 1 : -1;
        const col = colors[i % colors.length];
        return (
          <div
            key={i}
            style={{
              position: "absolute", top: 530 + i * 245, left: 60, width: 960, height: 210, boxSizing: "border-box",
              display: "flex", alignItems: "center", gap: 34, padding: "0 40px", borderRadius: 32,
              background: "linear-gradient(135deg, rgba(36,40,59,.96), rgba(16,16,24,.96))", border: `3px solid ${col}`,
              boxShadow: `0 30px 70px rgba(0,0,0,.55), 0 0 40px ${col}33`,
              transform: `translateX(${(1 - p) * from * 1100}px) rotate(${(1 - p) * from * 8}deg)`,
            }}
          >
            <div style={{ fontFamily: fonts.display, fontSize: 64, color: col, opacity: 0.9, width: 80 }}>{String(i + 1).padStart(2, "0")}</div>
            <div style={{ fontSize: 90, width: 110, textAlign: "center" }}>{c.icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 50, color: "#fff", lineHeight: 1.08 }}>{c.title}</div>
              <div style={{ fontFamily: fonts.body, fontWeight: 500, fontSize: 32, color: C.fg, marginTop: 8 }}>{c.detail}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

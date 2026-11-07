import React from "react";
import { AbsoluteFill, Easing, interpolate, OffthreadVideo, random, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CodeBlock } from "../components/CodeBlock";
import { Heading } from "../components/Ui";
import { BrowserScene, CodeScene, CompareScene, CtaScene, HiringScene, HookScene, Style } from "../types";
import { Img } from "remotion";
import { C, clamp, fonts, glow, pop, ramp, textStroke } from "../theme";

const hookFont = (st: Style) =>
  st.hookFont === "bebas" ? fonts.bebas : st.hookFont === "archivo" ? fonts.archivo : st.hookFont === "oswald" ? fonts.oswald : fonts.display;

/** Average uppercase glyph advance in em, per hook font: Archivo Black is ~twice as wide as Anton. */
const GLYPH_EM = { anton: 0.47, bebas: 0.4, archivo: 0.82, oswald: 0.55 } as const;
/** Largest font size (px) at which `word` fits in `width` px, capped at `max`. */
const fit = (word: string, width: number, max: number, st: Style) =>
  Math.min(max, Math.floor(width / (GLYPH_EM[st.hookFont] * Math.max(3, word.length))));

const StockUnder: React.FC<{ s: HookScene }> = ({ s }) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  if (!s.stock) return null;
  return (
    <AbsoluteFill style={{ transform: `scale(${1.15 - 0.08 * Math.min(1, t / s.duration)})` }}>
      <OffthreadVideo src={staticFile(s.stock)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,15,.75), rgba(7,7,15,.45) 40%, rgba(7,7,15,.85))" }} />
    </AbsoluteFill>
  );
};

/** `$ hook` typed into a terminal, then the last word slams in huge. */
const TerminalHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const text = s.words.join(" ").toLowerCase();
  const n = Math.floor(interpolate(t, [0.1, 0.85], [0, text.length], clamp));
  const slam = pop(f, fps, 0.9, 320, 12);
  const last = s.words[s.words.length - 1];
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 520, left: 60, right: 60, borderRadius: 24, background: "rgba(13,17,23,.92)", border: `2px solid ${accent}55`, boxShadow: `0 40px 100px rgba(0,0,0,.6), 0 0 60px ${accent}33`, overflow: "hidden", transform: `scale(${0.9 + 0.1 * pop(f, fps, 0, 200, 16)})` }}>
        <div style={{ display: "flex", gap: 14, padding: "22px 28px", background: "rgba(255,255,255,.04)", alignItems: "center" }}>
          {["#ff5f57", "#febc2e", "#28c840"].map((c) => <div key={c} style={{ width: 22, height: 22, borderRadius: 11, background: c }} />)}
          <div style={{ marginLeft: 20, fontFamily: fonts.mono, fontSize: 28, color: "#8b949e" }}>{s.kicker ? s.kicker.toLowerCase().replace(/\s+/g, "-") : "zsh"}</div>
        </div>
        <div style={{ padding: "40px 40px 50px", fontFamily: fonts.mono, fontWeight: 700, fontSize: 76, lineHeight: 1.25, color: "#e6edf3" }}>
          <span style={{ color: accent }}>$ </span>{text.slice(0, n)}
          <span style={{ opacity: Math.floor(t * 4) % 2 ? 0 : 1, color: accent }}>█</span>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1060, width: "100%", textAlign: "center", fontFamily: hookFont(st), fontSize: fit(last, 940, 300, st), color: st.highlight, ...textStroke(14), textShadow: `0 0 60px ${st.highlight}99`, transform: `scale(${Math.max(1, 3 - 2 * slam)}) rotate(-3deg)`, opacity: Math.min(1, slam * 3) }}>
        {last}
      </div>
    </AbsoluteFill>
  );
};

/** Hazard-tape warning banner, red flash, words punch in from alternating sides. */
const AlertHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const flash = Math.max(0, 1 - t * 2.5);
  const tape = (top: number, dir: number) => (
    <div style={{ position: "absolute", top, left: -100, right: -100, height: 80, transform: "rotate(-4deg)", backgroundImage: "repeating-linear-gradient(45deg, #ffd400 0 40px, #111 40px 80px)", backgroundPosition: `${dir * f * 6}px 0`, boxShadow: "0 12px 30px rgba(0,0,0,.5)" }} />
  );
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <AbsoluteFill style={{ background: `radial-gradient(circle, transparent 40%, rgba(255,30,60,${0.25 + 0.5 * flash}) 100%)` }} />
      {tape(430, 1)}
      <div style={{ position: "absolute", top: 560, width: "100%", textAlign: "center", fontFamily: fonts.mono, fontWeight: 700, fontSize: 44, letterSpacing: 8, color: "#ff3b5c", textShadow: "0 0 20px #ff3b5c", opacity: Math.floor(t * 5) % 2 || t > 1 ? 1 : 0.3 }}>
        ⚠ {s.kicker ?? "WARNING"}
      </div>
      <div style={{ position: "absolute", top: 660, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
        {s.words.map((w, i) => {
          const p = pop(f, fps, s.wordTimes[i] ?? i * 0.25, 380, 14);
          return (
            <div key={i} style={{ fontFamily: hookFont(st), fontSize: fit(w, 960, 240, st), lineHeight: 1, color: i === 0 ? "#ff3b5c" : "#fff", ...textStroke(12), transform: `translateX(${(1 - p) * (i % 2 ? 600 : -600)}px) skewX(${(1 - p) * -20}deg)`, textShadow: "0 16px 40px rgba(0,0,0,.8)" }}>
              {w}
            </div>
          );
        })}
      </div>
      {tape(1420, -1)}
    </AbsoluteFill>
  );
};

/** White sticker card with black type, slapped on with a tilt (reads like a native text post). */
const StickerHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(f, fps, 0, 170, 12);
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 560, left: 90, right: 90, transform: `rotate(${-4 + (1 - p) * -25}deg) scale(${0.6 + 0.4 * p})`, opacity: Math.min(1, p * 2) }}>
        {s.kicker && (
          <div style={{ display: "inline-block", marginLeft: 30, marginBottom: -14, padding: "10px 24px", background: accent, color: "#0b0b0b", fontFamily: fonts.mono, fontWeight: 700, fontSize: 32, borderRadius: 12, transform: "rotate(3deg)", position: "relative", zIndex: 2 }}>
            {s.kicker}
          </div>
        )}
        <div style={{ background: "#fff", borderRadius: 36, padding: "56px 50px", boxShadow: `14px 14px 0 ${accent}, 0 40px 80px rgba(0,0,0,.5)` }}>
          {s.words.map((w, i) => {
            const q = pop(f, fps, s.wordTimes[i] ?? i * 0.2, 300, 14);
            return (
              <div key={i} style={{ fontFamily: hookFont(st), fontSize: fit(w, 760, 190, st), lineHeight: 1.08, color: i === 1 ? "#fff" : "#0b0b0b", background: i === 1 ? "#0b0b0b" : "transparent", display: "table", padding: i === 1 ? "0 18px" : 0, transform: `scale(${q})`, transformOrigin: "0 50%" }}>
                {w}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Kinetic type: one word fills the screen at a time on an accent flash, then all three lock up. */
const KineticHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const times = s.words.map((_, i) => s.wordTimes[i] ?? i * 0.3);
  const lock = Math.max(times[times.length - 1] + 0.35, 1.0);
  const cur = times.reduce((k, at, i) => (t >= at ? i : k), 0);
  if (t < lock) {
    const at = times[cur];
    const p = pop(f, fps, at, 400, 16);
    const w = s.words[cur];
    const flash = Math.max(0, 1 - (t - at) * 4);
    return (
      <AbsoluteFill>
        <StockUnder s={s} />
        <AbsoluteFill style={{ background: accent, opacity: cur % 2 ? 0 : 0.35 * flash }} />
        <div style={{ position: "absolute", top: 0, bottom: 0, width: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: hookFont(st), fontSize: fit(w, 940, 420, st), color: cur === 1 ? st.highlight : "#fff", ...textStroke(16), transform: `scale(${1.6 - 0.6 * p}) rotate(${(cur - 1) * 4}deg)`, letterSpacing: -4 }}>
          {w}
        </div>
      </AbsoluteFill>
    );
  }
  const p = pop(f, fps, lock, 260, 14);
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 640, left: 50, right: 50, textAlign: "center", fontFamily: hookFont(st), fontSize: fit(s.words.reduce((a, b) => (b.length > a.length ? b : a)), 960, 170, st), lineHeight: 1, ...textStroke(12), transform: `scale(${0.85 + 0.15 * p})` }}>
        {s.words.map((w, i) => <span key={i} style={{ color: i === 1 ? st.highlight : "#fff" }}>{w} </span>)}
      </div>
    </AbsoluteFill>
  );
};

/** Question card: hook rewritten as a question, a giant "?" spins in, answer teased underneath. */
const QuestionHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const q = pop(f, fps, 0, 160, 10);
  const w = pop(f, fps, 0.2, 260, 14);
  const under = ramp(f / fps, 0.6, 1.2);
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 260, width: "100%", textAlign: "center", fontFamily: hookFont(st), fontSize: 520, lineHeight: 1, color: accent, opacity: 0.9 * q, transform: `rotate(${(1 - q) * -180}deg) scale(${q})`, textShadow: glow(accent, 40) }}>?</div>
      <div style={{ position: "absolute", top: 860, left: 50, right: 50, textAlign: "center", fontFamily: hookFont(st), fontSize: fit(s.words.reduce((a, b) => (b.length > a.length ? b : a)), 960, 150, st), lineHeight: 1.05, color: "#fff", ...textStroke(12), transform: `translateY(${(1 - w) * 80}px)`, opacity: w }}>
        {s.words.map((x, i) => <span key={i} style={{ color: i === 1 ? st.highlight : "#fff" }}>{x} </span>)}
      </div>
      <div style={{ position: "absolute", top: 1250, left: 340, right: 340, height: 12, borderRadius: 6, background: st.highlight, transform: `scaleX(${under})`, boxShadow: glow(st.highlight, 14) }} />
      {s.kicker && <div style={{ position: "absolute", top: 1300, width: "100%", textAlign: "center", fontFamily: fonts.mono, fontWeight: 700, fontSize: 36, letterSpacing: 6, color: "rgba(255,255,255,.8)", opacity: under }}>{s.kicker}</div>}
    </AbsoluteFill>
  );
};

/** Glitch: RGB-split text that jitters on every word hit, then settles clean. */
const GlitchHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 600, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
        {s.words.map((w, i) => {
          const at = s.wordTimes[i] ?? i * 0.25;
          const since = t - at;
          if (since < 0) return <div key={i} style={{ height: fit(w, 960, 230, st) }} />;
          const hot = Math.max(0, 1 - since * 3.5);
          const jx = hot * (random(`gx${i}-${f}`) - 0.5) * 60;
          const size = fit(w, 960, 230, st);
          const base: React.CSSProperties = { fontFamily: hookFont(st), fontSize: size, lineHeight: 1, position: "absolute", left: 0, right: 0, textAlign: "center" };
          return (
            <div key={i} style={{ position: "relative", width: "100%", height: size }}>
              <div style={{ ...base, color: "#ff004c", transform: `translate(${jx - 10 * hot}px, ${hot * 6}px)`, opacity: 0.8 * hot, mixBlendMode: "screen" }}>{w}</div>
              <div style={{ ...base, color: "#00e5ff", transform: `translate(${-jx + 10 * hot}px, ${-hot * 6}px)`, opacity: 0.8 * hot, mixBlendMode: "screen" }}>{w}</div>
              <div style={{ ...base, color: i === 1 ? st.highlight : "#fff", ...textStroke(12), transform: `translateX(${jx * 0.3}px)`, clipPath: hot > 0.3 ? `inset(${random(`gc${i}-${f}`) * 40}% 0 ${random(`gd${i}-${f}`) * 40}% 0)` : undefined }}>{w}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Breaking-news lower third: red LIVE bug, headline slides up, ticker scrolls underneath. */
const NewsHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bar = pop(f, fps, 0, 220, 16);
  const text = pop(f, fps, 0.15, 220, 16);
  const line = s.words.join(" ");
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 300, left: 60, display: "flex", alignItems: "center", gap: 14, padding: "12px 26px", background: "#d6001c", color: "#fff", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 44, transform: `translateX(${(1 - bar) * -500}px)` }}>
        <span style={{ width: 22, height: 22, borderRadius: 11, background: "#fff", opacity: Math.floor(f / 10) % 2 ? 0.3 : 1 }} /> LIVE
      </div>
      <div style={{ position: "absolute", top: 620, left: 0, right: 0, transform: `translateX(${(1 - bar) * -1100}px)` }}>
        <div style={{ display: "inline-block", background: "#d6001c", color: "#fff", padding: "10px 34px", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 52 }}>{s.kicker ?? "BREAKING"}</div>
        <div style={{ background: "#fff", padding: "26px 40px", overflow: "hidden" }}>
          <div style={{ fontFamily: hookFont(st), fontSize: fit(line, 980, 170, st), lineHeight: 1.05, color: "#0b0b0b", transform: `translateY(${(1 - text) * 200}px)` }}>{line}</div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1000, left: 0, right: 0, height: 74, background: "#10131f", overflow: "hidden", display: "flex", alignItems: "center", opacity: bar }}>
        <div style={{ whiteSpace: "nowrap", fontFamily: fonts.mono, fontWeight: 700, fontSize: 36, color: st.highlight, transform: `translateX(${-(f * 9) % 900}px)` }}>{`${line}  ///  `.repeat(8)}</div>
      </div>
    </AbsoluteFill>
  );
};

/** Dark stage: a spotlight sweeps in and each word is lit as it lands. */
const SpotlightHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const x = interpolate(t, [0, 0.7], [90, 50], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 610, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
        {s.words.map((w, i) => {
          const p = pop(f, fps, s.wordTimes[i] ?? i * 0.24, 260, 16);
          return <div key={i} style={{ fontFamily: hookFont(st), fontSize: fit(w, 980, 230, st), lineHeight: 1, color: i === 1 ? st.highlight : "#fff", opacity: p, transform: `translateY(${(1 - p) * 26}px)`, textShadow: `0 0 34px ${accent}aa` }}>{w}</div>;
        })}
      </div>
      <AbsoluteFill style={{ background: `radial-gradient(circle 660px at ${x}% 46%, transparent 45%, rgba(0,0,0,.93) 100%)` }} />
    </AbsoluteFill>
  );
};

/** The hook arrives as a chat message: typing dots first, then the bubble pops in. */
const ChatHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const showAt = 0.45;
  const b = pop(f, fps, showAt, 280, 15);
  const dots = pop(f, fps, 0, 300, 16);
  const line = s.words.join(" ");
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <div style={{ position: "absolute", top: 520, left: 70, fontFamily: fonts.body, fontWeight: 700, fontSize: 38, color: "rgba(255,255,255,.75)" }}>{s.kicker ?? "New message"}</div>
      {t < showAt ? (
        <div style={{ position: "absolute", top: 590, left: 70, display: "flex", gap: 16, padding: "34px 40px", background: "#2a2c3a", borderRadius: 48, transform: `scale(${dots})`, transformOrigin: "0 100%" }}>
          {[0, 1, 2].map((k) => <div key={k} style={{ width: 28, height: 28, borderRadius: 14, background: "#fff", opacity: 0.4 + 0.6 * Math.abs(Math.sin(t * 9 + k)) }} />)}
        </div>
      ) : (
        <div style={{ position: "absolute", top: 590, left: 70, right: 70, padding: "46px 50px", borderRadius: 60, borderBottomLeftRadius: 12, background: `linear-gradient(135deg, ${accent}, ${st.highlight})`, boxShadow: `0 30px 80px rgba(0,0,0,.5)`, transform: `scale(${b})`, transformOrigin: "0 100%" }}>
          <div style={{ fontFamily: hookFont(st), fontSize: fit(s.words.reduce((a, c) => (c.length > a.length ? c : a)), 820, 180, st), lineHeight: 1.08, color: "#0b0b0b" }}>{line}</div>
        </div>
      )}
    </AbsoluteFill>
  );
};

/** Screen splits on a diagonal: the two halves slide in from opposite corners and clash in the middle. */
const SplitHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(f, fps, 0, 170, 16);
  const mid = Math.max(1, Math.ceil(s.words.length / 2));
  const top = s.words.slice(0, mid).join(" "), bottom = s.words.slice(mid).join(" ");
  return (
    <AbsoluteFill>
      <StockUnder s={s} />
      <AbsoluteFill style={{ clipPath: "polygon(0 0, 100% 0, 100% 42%, 0 58%)", background: `${accent}e6`, transform: `translate(${(1 - p) * -1100}px, ${(1 - p) * -400}px)` }} />
      <AbsoluteFill style={{ clipPath: "polygon(0 60%, 100% 44%, 100% 100%, 0 100%)", background: "rgba(8,8,16,.9)", transform: `translate(${(1 - p) * 1100}px, ${(1 - p) * 400}px)` }} />
      <div style={{ position: "absolute", top: 520, left: 40, right: 40, textAlign: "center", fontFamily: hookFont(st), fontSize: fit(top, 980, 240, st), lineHeight: 1, color: "#0b0b0b", transform: `translateX(${(1 - p) * -1100}px) rotate(-4deg)` }}>{top}</div>
      <div style={{ position: "absolute", top: 1040, left: 40, right: 40, textAlign: "center", fontFamily: hookFont(st), fontSize: fit(bottom || top, 980, 240, st), lineHeight: 1, color: st.highlight, transform: `translateX(${(1 - p) * 1100}px) rotate(-4deg)`, textShadow: `0 0 40px ${st.highlight}77` }}>{bottom}</div>
    </AbsoluteFill>
  );
};

export const Hook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  switch (st.hook) {
    case "news": return <NewsHook s={s} accent={accent} st={st} />;
    case "spotlight": return <SpotlightHook s={s} accent={accent} st={st} />;
    case "chat": return <ChatHook s={s} accent={accent} st={st} />;
    case "split": return <SplitHook s={s} accent={accent} st={st} />;
    case "question": return <QuestionHook s={s} accent={accent} st={st} />;
    case "glitch": return <GlitchHook s={s} accent={accent} st={st} />;
    case "terminal": return <TerminalHook s={s} accent={accent} st={st} />;
    case "alert": return <AlertHook s={s} accent={accent} st={st} />;
    case "sticker": return <StickerHook s={s} accent={accent} st={st} />;
    case "kinetic": return <KineticHook s={s} accent={accent} st={st} />;
    default: return <StackHook s={s} accent={accent} st={st} />;
  }
};

const StackHook: React.FC<{ s: HookScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  return (
    <AbsoluteFill>
      {s.stock && (
        <AbsoluteFill style={{ transform: `scale(${1.15 - 0.08 * Math.min(1, t / s.duration)})` }}>
          <OffthreadVideo src={staticFile(s.stock)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,15,.75), rgba(7,7,15,.45) 40%, rgba(7,7,15,.85))" }} />
        </AbsoluteFill>
      )}
      {s.kicker && (
        <div style={{ position: "absolute", top: 470, width: "100%", display: "flex", justifyContent: "center" }}>
          <div
            style={{
              padding: "10px 30px", borderRadius: 999, background: accent, color: "#07070f",
              fontFamily: fonts.mono, fontWeight: 700, fontSize: 34, letterSpacing: 5,
              transform: `scale(${pop(f, fps, 0)}) rotate(-2deg)`, boxShadow: glow(accent, 18),
            }}
          >
            {s.kicker}
          </div>
        </div>
      )}
      <div style={{ position: "absolute", top: 600, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
        {s.words.map((w, i) => {
          const p = pop(f, fps, s.wordTimes[i] ?? 0, 330, 13);
          const size = fit(w, 980, 230, st);
          const yellow = i === 1;
          return (
            <div
              key={i}
              style={{
                fontFamily: hookFont(st), fontSize: size, lineHeight: 0.98, color: yellow ? st.highlight : "#fff",
                ...textStroke(14), letterSpacing: 2,
                textShadow: yellow ? `0 0 40px ${st.highlight}aa, 0 16px 40px rgba(0,0,0,.8)` : "0 16px 40px rgba(0,0,0,.8)",
                transform: `scale(${Math.max(0.95, 3.2 - 2.2 * p)}) rotate(${(i - 1) * -3 * p}deg)`,
                opacity: Math.min(1, p * 2.5),
                filter: p < 0.9 ? `blur(${(1 - p) * 16}px)` : undefined,
              }}
            >
              {w}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Code: React.FC<{ s: CodeScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(f, fps, 0.05, 150, 15);
  return (
    <AbsoluteFill>
      <Heading kicker={s.kicker} title={s.title} accent={accent} top={230} size={80} />
      <div
        style={{
          position: "absolute", top: 450, height: 960, left: 50, display: "flex", flexDirection: "column", justifyContent: "center",
          transform: `perspective(1400px) rotateX(${(1 - p) * 30}deg) translateY(${(1 - p) * 120}px) scale(${0.92 + 0.08 * p})`,
          opacity: p,
        }}
      >
        <CodeBlock code={s.code} />
      </div>
    </AbsoluteFill>
  );
};

export const Compare: React.FC<{ s: CompareScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const trackW = 900;
  return (
    <AbsoluteFill>
      <Heading kicker={s.kicker} title={s.title} accent={accent} top={250} size={84} />
      <div style={{ position: "absolute", top: 600, left: 90, width: trackW }}>
        {s.rows.map((row, ri) => {
          const lanes = row.bars.length;
          const play = ramp(t, row.at, row.at + 1.5);
          const head = play * s.scale;
          const appear = pop(f, fps, row.at - 0.2);
          return (
            <div key={ri} style={{ marginBottom: 70, opacity: appear, transform: `translateX(${(1 - appear) * -80}px)` }}>
              <div style={{ fontFamily: fonts.mono, fontSize: 40, color: row.color, marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
                <span>{row.label}</span>
                <span style={{ fontFamily: fonts.display, fontSize: 58, color: "#fff", opacity: play >= 0.99 ? 1 : 0.15, textShadow: glow(row.color, 10) }}>{row.total}</span>
              </div>
              <div style={{ position: "relative", height: lanes * 62 + 20, background: "#11111a", borderRadius: 18, border: `2px solid ${C.border}` }}>
                {row.bars.map(([a, b], bi) => {
                  const fill = Math.max(0, Math.min(b, head) - a) / s.scale;
                  return (
                    <div
                      key={bi}
                      style={{
                        position: "absolute", top: 10 + bi * 62 + 6, left: 10 + (a / s.scale) * (trackW - 20), height: 50,
                        width: fill * (trackW - 20), borderRadius: 12, background: `linear-gradient(90deg, ${row.color}, ${row.color}aa)`,
                        boxShadow: glow(row.color, 10),
                        display: "flex", alignItems: "center", paddingLeft: 16,
                        fontFamily: fonts.mono, fontSize: 26, color: "#07070f", fontWeight: 700, overflow: "hidden", whiteSpace: "nowrap",
                      }}
                    >
                      {fill > 0.05 ? `req ${bi + 1}` : ""}
                    </div>
                  );
                })}
                <div style={{ position: "absolute", top: 0, bottom: 0, left: 10 + Math.min(1, head / s.scale) * (trackW - 20), width: 4, background: "#fff", opacity: play > 0 && play < 1 ? 0.9 : 0, boxShadow: glow("#fff", 8) }} />
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const CountUp: React.FC<{ to: number; at: number; prefix?: string; suffix?: string }> = ({ to, at, prefix = "", suffix = "" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const v = to * ramp(f / fps, at, at + 1.2);
  return <>{prefix}{to % 1 ? v.toFixed(1) : Math.round(v).toLocaleString("en-US")}{suffix}</>;
};

export const Browser: React.FC<{ s: BrowserScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const p = pop(f, fps, 0.02, 160, 15);
  const urlChars = Math.floor(interpolate(t, s.urlTyping, [0, s.url.length], clamp));
  const promptChars = s.prompt ? Math.floor(interpolate(t, s.promptTyping, [0, s.prompt.length], clamp)) : 0;
  // promptTyping is zero-length when the scene has neither prompt nor query, and interpolate throws on that.
  const queryChars = s.query ? Math.floor(interpolate(t, s.promptTyping, [0, s.query.length], clamp)) : 0;
  const built = ramp(t, s.mockAt, s.mockAt + 0.6);
  const blink = Math.floor(t * 2.4) % 2 === 0;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute", top: 300, left: 40, width: 1000, height: 1080, borderRadius: 30, overflow: "hidden",
          background: "#0f1017", border: `2px solid ${C.border}`, boxShadow: `0 50px 100px rgba(0,0,0,.7), 0 0 90px ${accent}33`,
          transform: `perspective(1600px) rotateY(${(1 - p) * -25}deg) scale(${0.9 + 0.1 * p})`, opacity: p,
        }}
      >
        <div style={{ height: 120, background: "#181924", padding: "18px 26px", boxSizing: "border-box" }}>
          <div style={{ display: "flex", gap: 12, marginBottom: 14 }}>
            {["#ff5f56", "#ffbd2e", "#27c93f"].map((c) => <div key={c} style={{ width: 18, height: 18, borderRadius: 9, background: c }} />)}
          </div>
          <div style={{ height: 52, borderRadius: 26, background: "#0b0c12", display: "flex", alignItems: "center", padding: "0 26px", fontFamily: fonts.mono, fontSize: 30, color: C.fg }}>
            <span style={{ color: C.green, marginRight: 14 }}>🔒</span>
            {s.url.slice(0, urlChars)}
            {t < s.urlTyping[1] + 0.2 && blink && <span style={{ color: accent }}>|</span>}
          </div>
        </div>

        <div style={{ position: "relative", height: 960, padding: 40, boxSizing: "border-box" }}>
          {s.mock === "dashboard" && (
            <>
              {s.prompt && (
                <div
                  style={{
                    position: "absolute", left: 40, right: 40, top: interpolate(built, [0, 1], [330, 30]),
                    padding: "26px 30px", borderRadius: 24, background: "#191a26", border: `3px solid ${accent}`,
                    fontFamily: fonts.body, fontSize: 36, color: "#fff", boxShadow: glow(accent, 12),
                    transform: `scale(${1 - 0.12 * built})`, transformOrigin: "50% 0",
                  }}
                >
                  <span style={{ color: accent }}>✦ </span>
                  {s.prompt.slice(0, promptChars)}
                  {promptChars < s.prompt.length && blink && <span style={{ color: accent }}>|</span>}
                </div>
              )}
              <div style={{ position: "absolute", top: 190, left: 40, right: 40, opacity: built }}>
                <div style={{ display: "flex", gap: 22 }}>
                  {[["Revenue", 48.2, "$", "k", C.cyan], ["Users", 12904, "", "", C.pink], ["Churn", 1.8, "", "%", C.yellow]].map(([label, val, pre, suf, col], i) => {
                    const cp = pop(f, fps, s.mockAt + 0.1 + i * 0.12);
                    return (
                      <div key={String(label)} style={{ flex: 1, padding: 24, borderRadius: 22, background: "#191a26", border: `2px solid ${C.border}`, transform: `translateY(${(1 - cp) * 60}px)`, opacity: cp }}>
                        <div style={{ fontFamily: fonts.body, fontSize: 26, color: C.dim }}>{label}</div>
                        <div style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 52, color: String(col) }}>
                          <CountUp to={Number(val)} at={s.mockAt + 0.2} prefix={String(pre)} suffix={String(suf)} />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div style={{ marginTop: 26, height: 420, borderRadius: 22, background: "#191a26", border: `2px solid ${C.border}`, display: "flex", alignItems: "flex-end", gap: 18, padding: 30, boxSizing: "border-box" }}>
                  {[0.35, 0.55, 0.42, 0.7, 0.62, 0.85, 0.74, 0.95].map((h, i) => {
                    const g = ramp(t, s.mockAt + 0.35 + i * 0.07, s.mockAt + 0.85 + i * 0.07);
                    return <div key={i} style={{ flex: 1, height: `${h * 100 * g}%`, borderRadius: 10, background: `linear-gradient(180deg, ${accent}, ${C.purple})`, boxShadow: glow(accent, 8) }} />;
                  })}
                </div>
                {[0, 1, 2].map((r) => {
                  const rp = pop(f, fps, s.mockAt + 0.8 + r * 0.1);
                  return <div key={r} style={{ marginTop: 18, height: 54, borderRadius: 14, background: "#191a26", opacity: rp, transform: `translateX(${(1 - rp) * 100}px)` }} />;
                })}
              </div>
            </>
          )}

          {s.mock === "docs" && (
            <>
              <div style={{ height: 80, borderRadius: 18, background: "#191a26", border: `3px solid ${accent}`, display: "flex", alignItems: "center", padding: "0 26px", fontFamily: fonts.mono, fontSize: 36, color: "#fff", boxShadow: glow(accent, 10) }}>
                <span style={{ color: C.dim, marginRight: 16 }}>⌕</span>
                {s.query.slice(0, queryChars)}
                {blink && <span style={{ color: accent }}>|</span>}
              </div>
              {s.bullets.map((b, i) => {
                const bp = pop(f, fps, b.at);
                return (
                  <div key={i} style={{ marginTop: 22, padding: "22px 28px", borderRadius: 18, background: i === 0 ? `${accent}22` : "#191a26", border: `2px solid ${i === 0 ? accent : C.border}`, fontFamily: fonts.mono, fontSize: 32, color: i === 0 ? "#fff" : C.fg, opacity: bp, transform: `translateY(${(1 - bp) * 40}px)` }}>
                    {b.text}
                  </div>
                );
              })}
            </>
          )}

          {s.mock === "landing" && (
            <>
              <div style={{ marginTop: 60, textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 68, color: "#fff", lineHeight: 1.08, opacity: built, transform: `translateY(${(1 - built) * 40}px)` }}>
                {s.headline}
              </div>
              {s.bullets.map((b, i) => {
                const bp = pop(f, fps, b.at);
                return (
                  <div key={i} style={{ margin: "34px 20px 0", display: "flex", gap: 22, alignItems: "center", fontFamily: fonts.body, fontWeight: 700, fontSize: 40, color: C.fg, opacity: bp, transform: `translateX(${(1 - bp) * 80}px)` }}>
                    <span style={{ width: 54, height: 54, borderRadius: 27, background: accent, color: "#07070f", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>✓</span>
                    {b.text}
                  </div>
                );
              })}
            </>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const SearchCta: React.FC<{ s: CtaScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const title = pop(f, fps, 0.02, 300, 12);
  const bubble = pop(f, fps, s.bubbleAt, 200, 14);
  const chars = Math.floor(interpolate(t, [s.bubbleAt + 0.2, s.bubbleAt + 0.2 + s.keyword.length * 0.06], [0, s.keyword.length], clamp));
  const sent = t > s.bubbleAt + 0.35 + s.keyword.length * 0.06;
  const follow = pop(f, fps, s.followAt, 220, 12);
  const pulse = 1 + 0.04 * Math.sin(t * 9);
  const arrow = ramp(t, s.followAt + 0.2, s.followAt + 0.7);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 400, width: "100%", textAlign: "center", fontFamily: fonts.display, fontSize: 180, color: "#fff", ...textStroke(14), textShadow: `0 0 50px ${accent}aa`, transform: `scale(${Math.max(0.96, 2.4 - 1.4 * title)})`, opacity: Math.min(1, title * 2) }}>
        COMMENT
      </div>
      <div style={{ position: "absolute", top: 680, left: 90, right: 90, transform: `scale(${bubble}) rotate(${(1 - bubble) * -8}deg)`, opacity: bubble }}>
        <div style={{ display: "flex", alignItems: "center", gap: 24, padding: "26px 30px", borderRadius: 60, background: "#fff", boxShadow: `0 30px 80px rgba(0,0,0,.6), 0 0 60px ${accent}66` }}>
          <div style={{ width: 92, height: 92, borderRadius: 46, background: `linear-gradient(135deg, ${C.yellow}, ${accent}, ${C.purple})`, flexShrink: 0 }} />
          <div style={{ flex: 1, fontFamily: fonts.heavy, fontWeight: 900, fontSize: 76, color: "#111", letterSpacing: 1 }}>
            {s.keyword.slice(0, chars)}
            {!sent && Math.floor(t * 3) % 2 === 0 && <span style={{ color: accent }}>|</span>}
          </div>
          <div style={{ width: 92, height: 92, borderRadius: 46, background: sent ? "#3897f0" : "#ddd", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 50, transform: sent ? `scale(${1 + 0.15 * Math.max(0, 1 - (t - s.bubbleAt - 0.6) * 4)})` : "none" }}>
            ➤
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 900, width: "100%", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 56, color: "#fff", ...textStroke(8), opacity: bubble }}>
        I&apos;LL DM YOU THE <span style={{ color: C.yellow }}>{s.thing.toUpperCase()}</span> ⚡
      </div>
      <div style={{ position: "absolute", top: 1060, width: "100%", display: "flex", justifyContent: "center" }}>
        <div
          style={{
            padding: "24px 52px", borderRadius: 999, background: `linear-gradient(90deg, ${accent}, ${C.purple})`, whiteSpace: "nowrap",
            fontFamily: fonts.heavy, fontWeight: 900, fontSize: 44, color: "#fff", boxShadow: glow(accent, 26),
            transform: `scale(${follow * pulse})`, opacity: follow,
          }}
        >
          + FOLLOW @{s.handle}
        </div>
      </div>
      <svg style={{ position: "absolute", left: 0, top: 0 }} width={1080} height={1920}>
        <path d="M 640 1200 C 830 1230, 935 1300, 975 1420" fill="none" stroke={C.yellow} strokeWidth={9} strokeLinecap="round" strokeDasharray="520" strokeDashoffset={520 * (1 - arrow)} style={{ filter: `drop-shadow(0 0 10px ${C.yellow})` }} />
        <polygon points="950,1400 1000,1440 978,1380" fill={C.yellow} opacity={arrow > 0.95 ? 1 : 0} />
      </svg>
    </AbsoluteFill>
  );
};

/** Typed keyword inside a pill: shared by the alternative endings. */
const useTyped = (s: CtaScene, at: number) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const n = Math.floor(interpolate(t, [at, at + s.keyword.length * 0.06], [0, s.keyword.length], clamp));
  return { text: s.keyword.slice(0, n), done: n >= s.keyword.length, t };
};

/** Native-looking Instagram comment thread: viewer comments the keyword, the account replies "sent". */
const CommentCta: React.FC<{ s: CtaScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const head = pop(f, fps, 0.02, 260, 13);
  const row = pop(f, fps, s.bubbleAt, 220, 15);
  const typed = useTyped(s, s.bubbleAt + 0.15);
  const replyAt = s.bubbleAt + 0.4 + s.keyword.length * 0.06;
  const reply = pop(f, fps, replyAt, 220, 15);
  const heart = pop(f, fps, replyAt + 0.25, 400, 10);
  const follow = pop(f, fps, s.followAt, 220, 12);
  const avatar = (bg: string, size = 96) => <div style={{ width: size, height: size, borderRadius: size / 2, background: bg, flexShrink: 0, border: "4px solid #fff" }} />;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 330, width: "100%", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 70, color: "#fff", ...textStroke(10), transform: `scale(${head})` }}>
        WANT THE {s.thing.toUpperCase()}?
      </div>
      <div style={{ position: "absolute", top: 520, left: 60, right: 60, borderRadius: 40, background: "#fff", padding: "40px 40px 46px", boxShadow: `0 40px 100px rgba(0,0,0,.55), 0 0 0 6px ${accent}`, transform: `translateY(${(1 - row) * 300}px)`, opacity: row }}>
        <div style={{ fontFamily: fonts.body, fontWeight: 700, fontSize: 34, color: "#111", textAlign: "center", marginBottom: 30 }}>Comments</div>
        <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
          {avatar(`linear-gradient(135deg, ${C.yellow}, ${accent})`)}
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: fonts.body, fontWeight: 700, fontSize: 32, color: "#111" }}>you <span style={{ color: "#8e8e8e", fontWeight: 500 }}>· now</span></div>
            <div style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 76, color: "#111", letterSpacing: 1 }}>
              {typed.text}
              {!typed.done && <span style={{ color: accent }}>|</span>}
            </div>
          </div>
          <div style={{ fontSize: 56, color: heart > 0.05 ? "#ff3040" : "#bbb", transform: `scale(${1 + 0.6 * heart * Math.max(0, 1 - (typed.t - replyAt - 0.25) * 2)})` }}>♥</div>
        </div>
        <div style={{ display: "flex", gap: 20, alignItems: "flex-start", marginLeft: 120, marginTop: 34, transform: `scale(${reply})`, transformOrigin: "0 0", opacity: reply }}>
          {avatar(`linear-gradient(135deg, ${accent}, ${C.purple})`, 72)}
          <div>
            <div style={{ fontFamily: fonts.body, fontWeight: 700, fontSize: 28, color: "#111" }}>{s.handle} <span style={{ color: "#3897f0" }}>✔</span> <span style={{ color: "#8e8e8e", fontWeight: 500 }}>· author</span></div>
            <div style={{ fontFamily: fonts.body, fontWeight: 500, fontSize: 40, color: "#111" }}>Sent! Check your DMs 📩</div>
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1240, width: "100%", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 56, color: st.highlight, ...textStroke(9), transform: `scale(${follow})`, opacity: follow }}>
        + FOLLOW FOR MORE
      </div>
    </AbsoluteFill>
  );
};

/** Series ending: "PART N" stamp + "follow for part N+1" (an open loop is the strongest follow reason). */
const SeriesCta: React.FC<{ s: CtaScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const label = s.series ?? "PART 1";
  const m = /PART\s+(\d+)/i.exec(label);
  const next = m ? `PART ${Number(m[1]) + 1}` : "PART 2";
  const stamp = pop(f, fps, 0.02, 300, 11);
  const box = pop(f, fps, s.bubbleAt, 220, 14);
  const typed = useTyped(s, s.bubbleAt + 0.15);
  const nextP = pop(f, fps, s.followAt, 240, 12);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 330, width: "100%", display: "flex", justifyContent: "center" }}>
        <div style={{ padding: "16px 40px", border: `6px solid ${st.highlight}`, borderRadius: 20, color: st.highlight, fontFamily: fonts.mono, fontWeight: 700, fontSize: 46, letterSpacing: 4, transform: `rotate(-5deg) scale(${Math.max(0.95, 2.5 - 1.5 * stamp)})`, opacity: Math.min(1, stamp * 2), background: "rgba(0,0,0,.45)" }}>
          {label}
        </div>
      </div>
      <div style={{ position: "absolute", top: 560, width: "100%", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 64, color: "#fff", ...textStroke(9), opacity: box }}>
        COMMENT FOR THE {s.thing.toUpperCase()}
      </div>
      <div style={{ position: "absolute", top: 680, left: 160, right: 160, transform: `scale(${box})`, borderRadius: 28, background: accent, padding: "26px 0", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 96, color: "#0b0b0b", boxShadow: `0 16px 0 rgba(0,0,0,.35), ${glow(accent, 30)}` }}>
        {typed.text || "\u00a0"}
      </div>
      <div style={{ position: "absolute", top: 1010, width: "100%", textAlign: "center", transform: `translateY(${(1 - nextP) * 200}px)`, opacity: nextP }}>
        <div style={{ fontFamily: fonts.body, fontWeight: 700, fontSize: 44, color: "rgba(255,255,255,.85)", ...textStroke(6) }}>FOLLOW @{s.handle.toUpperCase()} FOR</div>
        <div style={{ fontFamily: fonts.display, fontSize: 200, lineHeight: 1.05, color: "#fff", ...textStroke(14), textShadow: `0 0 50px ${st.highlight}88` }}>{next} →</div>
      </div>
    </AbsoluteFill>
  );
};

/** Share ending: paper plane flies the reel to a friend; keyword pill underneath. */
const ShareCta: React.FC<{ s: CtaScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const head = pop(f, fps, 0.02, 260, 13);
  const fly = ramp(t, 0.25, 1.1);
  const box = pop(f, fps, s.bubbleAt, 220, 14);
  const typed = useTyped(s, s.bubbleAt + 0.15);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 320, left: 60, right: 60, textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 84, lineHeight: 1.05, color: "#fff", ...textStroke(10), transform: `scale(${head})` }}>
        SEND THIS TO A DEV WHO <span style={{ color: st.highlight }}>NEEDS IT</span>
      </div>
      <div style={{ position: "absolute", left: 140 + fly * 760, top: 760 - Math.sin(fly * Math.PI) * 200 - fly * 120, fontSize: 150, transform: `rotate(${-20 + fly * 30}deg) scale(${1 - 0.5 * fly})`, opacity: 1 - Math.max(0, fly - 0.85) * 6, filter: `drop-shadow(0 0 30px ${accent})` }}>
        ✈️
      </div>
      <div style={{ position: "absolute", top: 1010, width: "100%", textAlign: "center", fontFamily: fonts.body, fontWeight: 700, fontSize: 46, color: "#fff", ...textStroke(6), opacity: box }}>
        and comment for the {s.thing} 👇
      </div>
      <div style={{ position: "absolute", top: 1100, left: 200, right: 200, transform: `scale(${box})`, borderRadius: 999, background: "#fff", padding: "22px 0", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 84, color: "#111", boxShadow: `0 0 0 6px ${accent}, 0 30px 70px rgba(0,0,0,.5)` }}>
        {typed.text || "\u00a0"}
      </div>
    </AbsoluteFill>
  );
};

/** Follow -> like -> comment: three big buttons light up in order, keyword typed into the comment box. */
const TripleCta: React.FC<{ s: CtaScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const steps = [
    { icon: "➕", label: "FOLLOW", color: accent, at: 0.05 },
    { icon: "❤️", label: "LIKE", color: "#ff3040", at: 0.45 },
    { icon: "💬", label: "COMMENT", color: st.highlight, at: 0.85 },
  ];
  const typed = useTyped(s, 1.15);
  const box = pop(f, fps, 1.05, 220, 14);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 300, width: "100%", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 66, color: "#fff", ...textStroke(9), opacity: pop(f, fps, 0, 260, 13) }}>
        GET THE {s.thing.toUpperCase()} IN 3 TAPS 👇
      </div>
      {steps.map((st2, i) => {
        const p = pop(f, fps, st2.at, 300, 12);
        const lit = t > st2.at + 0.15;
        return (
          <div key={i} style={{ position: "absolute", top: 450 + i * 190, left: 150, right: 150, height: 150, borderRadius: 75, display: "flex", alignItems: "center", gap: 30, padding: "0 40px", background: lit ? st2.color : "rgba(255,255,255,.08)", border: `4px solid ${st2.color}`, transform: `translateX(${(1 - p) * (i % 2 ? 700 : -700)}px) scale(${lit ? 1 + 0.05 * Math.max(0, 1 - (t - st2.at - 0.15) * 4) : 1})`, boxShadow: lit ? glow(st2.color, 20) : undefined }}>
            <div style={{ fontSize: 80 }}>{st2.icon}</div>
            <div style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 70, color: lit ? "#0b0b0b" : "#fff" }}>{st2.label}</div>
            <div style={{ marginLeft: "auto", fontFamily: fonts.mono, fontWeight: 700, fontSize: 50, color: lit ? "#0b0b0b" : "rgba(255,255,255,.4)" }}>{i + 1}</div>
          </div>
        );
      })}
      <div style={{ position: "absolute", top: 1060, left: 200, right: 200, transform: `scale(${box})`, borderRadius: 999, background: "#fff", padding: "22px 0", textAlign: "center", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 80, color: "#111", boxShadow: `0 0 0 6px ${st.highlight}, 0 30px 70px rgba(0,0,0,.5)` }}>
        {typed.text || "\u00a0"}
      </div>
      <div style={{ position: "absolute", top: 1210, width: "100%", textAlign: "center", fontFamily: fonts.body, fontWeight: 700, fontSize: 44, color: "#fff", ...textStroke(6), opacity: box }}>
        I&apos;ll DM you the {s.thing} 📩
      </div>
    </AbsoluteFill>
  );
};

export const Cta: React.FC<{ s: CtaScene; accent: string; st: Style }> = ({ s, accent, st }) => {
  switch (st.cta) {
    case "triple": return <TripleCta s={s} accent={accent} st={st} />;
    case "comment": return <CommentCta s={s} accent={accent} st={st} />;
    case "series": return <SeriesCta s={s} accent={accent} st={st} />;
    case "share": return <ShareCta s={s} accent={accent} st={st} />;
    default: return <SearchCta s={s} accent={accent} />;
  }
};

/** Three company cards slide in as the narrator names each one: logo, open roles, cities, a real role. */
export const Hiring: React.FC<{ s: HiringScene; accent: string }> = ({ s, accent }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  return (
    <AbsoluteFill>
      <Heading kicker={s.kicker} title={s.title} accent={accent} top={230} size={84} />
      {s.companies.map((c, i) => {
        const p = pop(f, fps, c.at, 200, 15);
        const count = Math.round(interpolate(t, [c.at + 0.1, c.at + 0.8], [0, c.roles], clamp));
        return (
          <div key={c.name} style={{ position: "absolute", top: 480 + i * 330, left: 60, right: 60, height: 290, borderRadius: 36, background: "rgba(16,18,28,.92)", border: `3px solid ${c.color}`, boxShadow: `0 24px 60px rgba(0,0,0,.5), 0 0 40px ${c.color}33`, display: "flex", alignItems: "center", gap: 36, padding: "0 40px", transform: `translateX(${(1 - p) * (i % 2 ? 1100 : -1100)}px) rotate(${(1 - p) * (i % 2 ? 6 : -6)}deg)` }}>
            <div style={{ width: 150, height: 150, borderRadius: 34, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, overflow: "hidden", boxShadow: `0 0 0 5px ${c.color}` }}>
              {c.logo ? <Img src={staticFile(c.logo)} style={{ width: 110, height: 110, objectFit: "contain" }} /> : <span style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 90, color: "#111" }}>{c.name[0]}</span>}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: fonts.heavy, fontWeight: 900, fontSize: 64, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.name}</div>
              <div style={{ fontFamily: fonts.body, fontWeight: 700, fontSize: 34, color: "rgba(255,255,255,.75)", marginTop: 4 }}>📍 {c.cities.join(" · ")}</div>
              <div style={{ fontFamily: fonts.mono, fontSize: 27, color: c.color, marginTop: 10, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.top_role}</div>
            </div>
            <div style={{ textAlign: "center", flexShrink: 0 }}>
              <div style={{ fontFamily: fonts.display, fontSize: 110, lineHeight: 1, color: "#fff", textShadow: glow(c.color, 18) }}>{count}</div>
              <div style={{ fontFamily: fonts.mono, fontWeight: 700, fontSize: 24, color: "rgba(255,255,255,.7)", letterSpacing: 2 }}>OPEN ROLES</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

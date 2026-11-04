import React from "react";
import { AbsoluteFill, random, useCurrentFrame } from "remotion";
import { C, fonts } from "../theme";
import { Look } from "../types";

/** Living backdrop: drifting neon blobs, a scrolling synthwave grid and rising particles. */
const Neon: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const blob = (x: number, y: number, size: number, color: string, speed: number, phase: number) => (
    <div
      style={{
        position: "absolute",
        left: x + Math.sin(f / speed + phase) * 120 - size / 2,
        top: y + Math.cos(f / (speed * 1.3) + phase) * 160 - size / 2,
        width: size,
        height: size,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${color}88 0%, ${color}00 70%)`,
      }}
    />
  );
  const gridOffset = (f * 3) % 90;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, #0b0718 0%, ${C.bg} 45%, #120a24 100%)` }}>
      {blob(200, 380, 1100, accent, 70, 0)}
      {blob(900, 1500, 1200, C.purple, 90, 2)}
      {blob(800, 200, 800, C.cyan, 110, 4)}
      <div
        style={{
          position: "absolute",
          left: -540,
          right: -540,
          bottom: -200,
          height: 900,
          transform: "perspective(600px) rotateX(62deg)",
          transformOrigin: "50% 100%",
          backgroundImage: `linear-gradient(${C.pink}55 2px, transparent 2px), linear-gradient(90deg, ${C.pink}44 2px, transparent 2px)`,
          backgroundSize: "90px 90px",
          backgroundPosition: `0 ${gridOffset}px`,
          maskImage: "linear-gradient(to top, black 10%, transparent 90%)",
          WebkitMaskImage: "linear-gradient(to top, black 10%, transparent 90%)",
          opacity: 0.55,
        }}
      />
      {new Array(36).fill(0).map((_, i) => {
        const x = random(`px${i}`) * 1080;
        const speed = 0.6 + random(`ps${i}`) * 1.8;
        const y = 1920 - ((f * speed * 3 + random(`py${i}`) * 1920) % 2100);
        const s = 3 + random(`pz${i}`) * 6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + Math.sin(f / 30 + i) * 20,
              top: y,
              width: s,
              height: s,
              borderRadius: "50%",
              background: i % 3 === 0 ? C.cyan : i % 3 === 1 ? accent : "#fff",
              opacity: 0.25 + random(`po${i}`) * 0.5,
              boxShadow: `0 0 ${s * 3}px ${i % 2 ? accent : C.cyan}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Dark IDE: flat GitHub-dark, fine grid, scanlines, a soft accent glow from the top. */
const Terminal: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#0d1117" }}>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 40% at 50% 0%, ${accent}33, transparent 70%)` }} />
      <AbsoluteFill
        style={{
          backgroundImage: "linear-gradient(#ffffff0a 1px, transparent 1px), linear-gradient(90deg, #ffffff0a 1px, transparent 1px)",
          backgroundSize: "54px 54px",
          backgroundPosition: `0 ${(f * 0.6) % 54}px`,
        }}
      />
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,.18) 0 2px, transparent 2px 5px)" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: ((f * 9) % 2300) - 300, height: 220, background: `linear-gradient(180deg, transparent, ${accent}12, transparent)` }} />
    </AbsoluteFill>
  );
};

/** Engineering blueprint: deep blue paper, white grid, slowly rotating construction rings. */
const Blueprint: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #12408a 0%, #0a2556 60%, #061636 100%)" }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(#ffffff14 2px, transparent 2px), linear-gradient(90deg, #ffffff14 2px, transparent 2px), linear-gradient(#ffffff08 1px, transparent 1px), linear-gradient(90deg, #ffffff08 1px, transparent 1px)",
          backgroundSize: "180px 180px, 180px 180px, 36px 36px, 36px 36px",
        }}
      />
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute", left: 540 - (500 + i * 260) / 2, top: 960 - (500 + i * 260) / 2,
            width: 500 + i * 260, height: 500 + i * 260, borderRadius: "50%",
            border: `2px dashed ${i === 1 ? accent : "#ffffff"}${i === 1 ? "55" : "22"}`,
            transform: `rotate(${(i % 2 ? -1 : 1) * f * (0.3 + i * 0.1)}deg)`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

/** Bold gradient: warm sunset sweep with big blurred shapes and film grain. */
const Sunset: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const shift = Math.sin(f / 60) * 8;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(${160 + shift}deg, #1b0b3a 0%, #4a1259 38%, #b3264f 72%, #f28a3c 100%)` }}>
      <div style={{ position: "absolute", left: -200 + Math.sin(f / 50) * 80, top: 200, width: 900, height: 900, borderRadius: "50%", background: `${accent}55`, filter: "blur(120px)" }} />
      <div style={{ position: "absolute", right: -260, bottom: 120 + Math.cos(f / 45) * 90, width: 1000, height: 1000, borderRadius: "50%", background: "#ffd16655", filter: "blur(140px)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.35), rgba(0,0,0,.05) 40%, rgba(0,0,0,.45))" }} />
    </AbsoluteFill>
  );
};

/** Minimal black: huge outlined keyword drifting behind everything. */
const Mono: React.FC<{ accent: string; keyword: string }> = ({ accent, keyword }) => {
  const f = useCurrentFrame();
  const row = (y: number, dir: number, i: number) => (
    <div
      key={i}
      style={{
        position: "absolute", top: y, left: 0, whiteSpace: "nowrap", fontFamily: fonts.display, fontSize: 300, lineHeight: 1,
        color: "transparent", WebkitTextStroke: `2px ${i === 1 ? accent + "66" : "#ffffff1c"}`,
        transform: `translateX(${dir * ((f * 2.2) % 1400) - 700}px)`,
      }}
    >
      {`${keyword} · `.repeat(8)}
    </div>
  );
  return (
    <AbsoluteFill style={{ background: "#050505" }}>
      {row(120, 1, 0)}
      {row(800, -1, 1)}
      {row(1480, 1, 2)}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(0,0,0,.8) 100%)" }} />
    </AbsoluteFill>
  );
};


/** Northern lights: slow green/violet ribbons over a deep night sky. */
const Aurora: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const ribbon = (y: number, color: string, speed: number, phase: number) => (
    <div style={{
      position: "absolute", left: -300, right: -300, top: y + Math.sin(f / speed + phase) * 90, height: 420,
      background: `linear-gradient(90deg, transparent, ${color}66, ${color}22, ${color}55, transparent)`,
      filter: "blur(60px)", transform: `skewY(${Math.sin(f / (speed * 1.4) + phase) * 8}deg)`,
    }} />
  );
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #020617 0%, #06142a 60%, #0b1020 100%)" }}>
      {ribbon(260, accent, 60, 0)}
      {ribbon(620, "#a78bfa", 75, 2)}
      {ribbon(1100, "#22d3ee", 90, 4)}
      {new Array(40).fill(0).map((_, i) => (
        <div key={i} style={{ position: "absolute", left: random(`ax${i}`) * 1080, top: random(`ay${i}`) * 1920, width: 3, height: 3, borderRadius: 2, background: "#fff", opacity: 0.2 + 0.6 * Math.abs(Math.sin(f / 20 + i)) }} />
      ))}
    </AbsoluteFill>
  );
};

/** Digital rain: columns of falling glyphs, dim except for the bright head of each column. */
const Matrix: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const glyphs = "01{}<>/=;:+*#$アイウエオカキクケコ";
  return (
    <AbsoluteFill style={{ background: "#020805" }}>
      {new Array(22).fill(0).map((_, col) => {
        const speed = 6 + random(`ms${col}`) * 10;
        const head = ((f * speed + random(`mo${col}`) * 2400) % 2600) - 300;
        return (
          <div key={col} style={{ position: "absolute", left: col * 50 + 4, top: 0, fontFamily: fonts.mono, fontSize: 34, lineHeight: "44px", width: 40, textAlign: "center" }}>
            {new Array(14).fill(0).map((__, k) => {
              const y = head - k * 44;
              const ch = glyphs[Math.floor(random(`mg${col}-${k}-${Math.floor(f / 6)}`) * glyphs.length)];
              return <div key={k} style={{ position: "absolute", top: y, color: k === 0 ? "#eafff4" : accent, opacity: k === 0 ? 0.9 : Math.max(0, 0.45 - k * 0.03), textShadow: k === 0 ? `0 0 12px ${accent}` : undefined }}>{ch}</div>;
            })}
          </div>
        );
      })}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(2,8,5,.25), rgba(2,8,5,.85) 75%)" }} />
    </AbsoluteFill>
  );
};

/** Frosted glass: soft pastel orbs behind a blurred pane, calm and premium. */
const Glass: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const orb = (x: number, y: number, size: number, color: string, sp: number) => (
    <div style={{ position: "absolute", left: x + Math.sin(f / sp) * 140, top: y + Math.cos(f / (sp * 1.2)) * 160, width: size, height: size, borderRadius: "50%", background: color }} />
  );
  return (
    <AbsoluteFill style={{ background: "#111827" }}>
      {orb(-100, 200, 700, accent, 70)}
      {orb(500, 900, 800, "#f472b6", 85)}
      {orb(100, 1400, 600, "#38bdf8", 95)}
      <AbsoluteFill style={{ backdropFilter: "blur(90px)", WebkitBackdropFilter: "blur(90px)", background: "rgba(17,24,39,.55)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(255,255,255,.05), transparent 30%, transparent 70%, rgba(0,0,0,.3))" }} />
    </AbsoluteFill>
  );
};

/** Forge glow from below, sparks climbing through smoke. */
const Ember: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #0a0605 0%, #1a0b06 55%, #3a1407 100%)" }}>
      <div style={{ position: "absolute", left: -200, right: -200, bottom: -420 + Math.sin(f / 30) * 40, height: 1000, background: `radial-gradient(ellipse at 50% 100%, ${accent}aa, transparent 65%)` }} />
      {new Array(44).fill(0).map((_, i) => {
        const v = 2 + random(`ev${i}`) * 6;
        const y = 1920 - ((f * v + random(`ey${i}`) * 1920) % 2000);
        const s = 3 + random(`es${i}`) * 6;
        return <div key={i} style={{ position: "absolute", left: random(`ex${i}`) * 1080 + Math.sin(f / 16 + i) * 40, top: y, width: s, height: s, borderRadius: "50%", background: i % 3 ? accent : "#ffe2a8", boxShadow: `0 0 ${s * 2}px ${accent}`, opacity: Math.max(0, y / 1900) }} />;
      })}
    </AbsoluteFill>
  );
};

/** Slow star field with two nebula clouds. */
const Galaxy: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#04030f" }}>
      <div style={{ position: "absolute", left: -300, top: 200 + Math.sin(f / 80) * 60, width: 1300, height: 900, borderRadius: "50%", background: `radial-gradient(circle, ${accent}66, transparent 65%)`, transform: `rotate(${f * 0.05}deg)` }} />
      <div style={{ position: "absolute", right: -360, bottom: 120, width: 1200, height: 1100, borderRadius: "50%", background: "radial-gradient(circle, #ec489955, transparent 65%)" }} />
      {new Array(110).fill(0).map((_, i) => {
        const z = 0.3 + random(`gz${i}`) * 1.7;
        return <div key={i} style={{ position: "absolute", left: (random(`gsx${i}`) * 1080 + f * z * 0.5) % 1080, top: random(`gsy${i}`) * 1920, width: z * 2.4, height: z * 2.4, borderRadius: "50%", background: "#fff", opacity: 0.25 + 0.6 * Math.abs(Math.sin(f / 22 + i)) }} />;
      })}
    </AbsoluteFill>
  );
};

/** Circuit board: right-angled traces with pulses travelling along them. */
const Circuit: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const traces = new Array(13).fill(0).map((_, i) => {
    const x = 40 + i * 82;
    const bend = 300 + random(`cb${i}`) * 1200;
    const dx = (random(`cd${i}`) > 0.5 ? 1 : -1) * 82;
    return `M ${x} -20 L ${x} ${bend} L ${x + dx} ${bend + 82} L ${x + dx} 1940`;
  });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #07202b, #030b11 75%)" }}>
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        {traces.map((d, i) => <path key={i} d={d} fill="none" stroke={`${accent}26`} strokeWidth={3} />)}
        {traces.map((d, i) => <path key={`p${i}`} d={d} fill="none" stroke={accent} strokeWidth={5} strokeLinecap="round" strokeDasharray="70 2100" strokeDashoffset={-((f * (9 + (i % 4) * 4) + i * 170) % 2170)} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />)}
      </svg>
    </AbsoluteFill>
  );
};

/** Striped retro sun over a dark horizon with a scrolling floor. */
const RetroSun: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #12062e 0%, #2a0a4a 50%, #070314 62%)" }}>
      <div style={{ position: "absolute", left: 140, top: 340, width: 800, height: 800, borderRadius: "50%", background: `linear-gradient(180deg, #ffe066, ${accent})`, boxShadow: `0 0 130px ${accent}88`, maskImage: "repeating-linear-gradient(180deg, #000 0 58px, transparent 58px 74px)", WebkitMaskImage: "repeating-linear-gradient(180deg, #000 0 58px, transparent 58px 74px)", opacity: 0.22 }} />
      <div style={{ position: "absolute", left: -540, right: -540, bottom: -160, height: 880, transform: "perspective(520px) rotateX(64deg)", transformOrigin: "50% 100%", backgroundImage: `linear-gradient(${accent}88 3px, transparent 3px), linear-gradient(90deg, ${accent}66 3px, transparent 3px)`, backgroundSize: "100px 100px", backgroundPosition: `0 ${(f * 4) % 100}px`, maskImage: "linear-gradient(to top, #000 15%, transparent 95%)", WebkitMaskImage: "linear-gradient(to top, #000 15%, transparent 95%)" }} />
    </AbsoluteFill>
  );
};

/** Deep water: layered swells and light rays from the surface. */
const Ocean: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const wave = (y: number, amp: number, color: string, speed: number) => {
    const pts = new Array(13).fill(0).map((_, i) => `${i * 100 - 50},${y + Math.sin(i * 0.8 + f / speed) * amp}`).join(" L ");
    return <path d={`M ${pts} L 1200,1920 L -50,1920 Z`} fill={color} />;
  };
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #032541 0%, #021a30 50%, #010d1c 100%)" }}>
      {[0, 1, 2, 3].map((i) => <div key={i} style={{ position: "absolute", top: -200, left: 60 + i * 250 + Math.sin(f / 50 + i) * 50, width: 130, height: 1500, background: `linear-gradient(180deg, ${accent}33, transparent)`, transform: `rotate(${8 - i * 5}deg)`, filter: "blur(20px)" }} />)}
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        {wave(1240, 44, "#0a3a5c88", 28)}
        {wave(1420, 34, "#072c4a99", 22)}
        {wave(1620, 26, "#041c32cc", 18)}
      </svg>
    </AbsoluteFill>
  );
};

/** Lecture chalkboard with faint formulas drifting past. */
const Chalk: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const notes = ["O(1)", "x ^= n", "a ^ a = 0", "log n", "f(x)", "n & (n-1)", "[ ]", "{ }", "=> ", "2ⁿ", "i++", "O(n)"];
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #24332c, #101a15 80%)" }}>
      {notes.map((n, i) => (
        <div key={i} style={{ position: "absolute", left: 40 + random(`nx${i}`) * 820, top: (random(`ny${i}`) * 2000 + f * 0.5) % 2000 - 60, fontFamily: fonts.mono, fontSize: 44 + random(`nz${i}`) * 50, color: i % 4 ? "#ffffff" : accent, opacity: 0.1, transform: `rotate(${(random(`nr${i}`) - 0.5) * 18}deg)` }}>{n}</div>
      ))}
    </AbsoluteFill>
  );
};

/** Hexagon lattice with cells lighting up in a wave. */
const HexGrid: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const r = 62, w = r * Math.sqrt(3), cells: React.ReactNode[] = [];
  for (let row = 0; row < 22; row++) {
    for (let col = 0; col < 11; col++) {
      const cx = col * w + (row % 2 ? w / 2 : 0) - 20, cy = row * r * 1.5 - 20;
      const glowAt = Math.max(0, Math.sin(f / 22 - (cy + cx * 0.6) / 260)) ** 6;
      const pts = [0, 1, 2, 3, 4, 5].map((k) => `${cx + r * Math.sin(k * Math.PI / 3)},${cy + r * Math.cos(k * Math.PI / 3)}`).join(" ");
      cells.push(<polygon key={`${row}-${col}`} points={pts} fill={accent} fillOpacity={glowAt * 0.3} stroke={accent} strokeOpacity={0.14 + glowAt * 0.5} strokeWidth={2} />);
    }
  }
  return <AbsoluteFill style={{ background: "#04100c" }}><svg width={1080} height={1920}>{cells}</svg></AbsoluteFill>;
};

/** Out-of-focus city lights. */
const Bokeh: React.FC<{ accent: string }> = ({ accent }) => {
  const f = useCurrentFrame();
  const palette = [accent, "#ffd166", "#38bdf8", "#f472b6"];
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #0b0a18, #15101f)" }}>
      {new Array(26).fill(0).map((_, i) => {
        const s = 90 + random(`bs${i}`) * 230;
        return <div key={i} style={{ position: "absolute", left: random(`bx${i}`) * 1200 - 100 + Math.sin(f / 60 + i) * 50, top: random(`by${i}`) * 2000 - 80 + Math.cos(f / 70 + i) * 50, width: s, height: s, borderRadius: "50%", background: palette[i % 4], opacity: 0.08 + 0.15 * Math.abs(Math.sin(f / 45 + i)), filter: "blur(5px)" }} />;
      })}
    </AbsoluteFill>
  );
};

export const Background: React.FC<{ accent: string; look: Look; keyword: string }> = ({ accent, look, keyword }) => {
  switch (look) {
    case "ember": return <Ember accent={accent} />;
    case "galaxy": return <Galaxy accent={accent} />;
    case "circuit": return <Circuit accent={accent} />;
    case "retrosun": return <RetroSun accent={accent} />;
    case "ocean": return <Ocean accent={accent} />;
    case "chalk": return <Chalk accent={accent} />;
    case "hexgrid": return <HexGrid accent={accent} />;
    case "bokeh": return <Bokeh accent={accent} />;
    case "terminal": return <Terminal accent={accent} />;
    case "blueprint": return <Blueprint accent={accent} />;
    case "sunset": return <Sunset accent={accent} />;
    case "mono": return <Mono accent={accent} keyword={keyword} />;
    case "aurora": return <Aurora accent={accent} />;
    case "matrix": return <Matrix accent={accent} />;
    case "glass": return <Glass accent={accent} />;
    default: return <Neon accent={accent} />;
  }
};

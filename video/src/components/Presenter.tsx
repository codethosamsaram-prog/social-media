import React from "react";
import { random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Emphasis, Presenter as Kind, Scene, Word } from "../types";

type Hair = "quiff" | "bun" | "curls" | "long" | "side" | "bob";
type Look = { skin: string; hair: string; iris: string; style: Hair; top: string; glasses?: boolean; beard?: boolean; earrings?: boolean; headphones?: boolean };

/** Original characters in a soft 3D look: gradients and highlights stand in for real lighting. */
const CAST: Record<Exclude<Kind, "none">, Look> = {
  aarav: { skin: "#c98a5e", hair: "#1d1512", iris: "#4a2c17", style: "quiff", top: "#3f6df0", glasses: true },
  meera: { skin: "#d39a6e", hair: "#20130e", iris: "#3e2412", style: "bun", top: "#e8528f", earrings: true },
  kabir: { skin: "#a96f48", hair: "#14100e", iris: "#2f1c0f", style: "curls", top: "#14b8a6", beard: true },
  zoya: { skin: "#e0ae85", hair: "#3a2116", iris: "#5a3a1c", style: "long", top: "#f59e0b" },
  rohan: { skin: "#b87a50", hair: "#191310", iris: "#3a2312", style: "side", top: "#8b5cf6", headphones: true, beard: true },
  anya: { skin: "#c48a60", hair: "#2a1710", iris: "#4d2f18", style: "bob", top: "#ef4444", glasses: true },
};

const shade = (hex: string, amt: number) => {
  const n = parseInt(hex.slice(1), 16);
  const ch = (v: number) => Math.max(0, Math.min(255, Math.round(v + amt * 255))).toString(16).padStart(2, "0");
  return `#${ch(n >> 16)}${ch((n >> 8) & 255)}${ch(n & 255)}`;
};

type Viseme = { open: number; wide: number };

/** Mouth shape for the letter under the playhead, from the real word timings. */
const visemeAt = (words: Word[], t: number): Viseme => {
  const w = words.find((x) => t >= x.start && t < x.end);
  if (!w) return { open: 0, wide: 0.5 };
  const letters = w.text.toLowerCase().replace(/[^a-z0-9]/g, "") || "a";
  const c = letters[Math.min(letters.length - 1, Math.floor(((t - w.start) / Math.max(0.01, w.end - w.start)) * letters.length))];
  if (c === "a") return { open: 0.95, wide: 0.6 };
  if ("ou".includes(c)) return { open: 0.65, wide: 0.1 };
  if ("eiy".includes(c)) return { open: 0.42, wide: 0.95 };
  if ("mbp".includes(c)) return { open: 0.02, wide: 0.5 };
  if ("fv".includes(c)) return { open: 0.14, wide: 0.6 };
  return { open: 0.28, wide: 0.5 };
};

/** Averaged over neighbouring frames: lips glide between shapes instead of snapping, which is what reads as robotic. */
const smoothViseme = (words: Word[], t: number): Viseme => {
  const samples = [-0.066, -0.033, 0, 0.033].map((d) => visemeAt(words, t + d));
  return { open: samples.reduce((a, s) => a + s.open, 0) / 4, wide: samples.reduce((a, s) => a + s.wide, 0) / 4 };
};

const Mouth: React.FC<{ id: string; v: Viseme; smile: number; lip: string }> = ({ id, v, smile, lip }) => {
  const x = 150, y = 212, w = 15 + v.wide * 13, h = v.open * 26, corner = -smile * 5;
  if (h < 2.5) {
    return <path d={`M ${x - w} ${y + corner} Q ${x} ${y + 6 + smile * 7} ${x + w} ${y + corner}`} fill="none" stroke={lip} strokeWidth={5} strokeLinecap="round" />;
  }
  const shape = `M ${x - w} ${y + corner} Q ${x} ${y - 3} ${x + w} ${y + corner} Q ${x + w * 0.8} ${y + h} ${x} ${y + h + 2} Q ${x - w * 0.8} ${y + h} ${x - w} ${y + corner} Z`;
  return (
    <g>
      <clipPath id={`${id}-m`}><path d={shape} /></clipPath>
      <path d={shape} fill="#3d1119" />
      <g clipPath={`url(#${id}-m)`}>
        <rect x={x - w} y={y - 6} width={w * 2} height={Math.min(11, 4 + h * 0.5)} rx={3} fill="#fbf7f2" />
        <ellipse cx={x} cy={y + h + 3} rx={w * 0.62} ry={Math.max(3, h * 0.42)} fill="#d9616f" />
      </g>
      <path d={shape} fill="none" stroke={lip} strokeWidth={4} strokeLinejoin="round" />
    </g>
  );
};

const HairBack: React.FC<{ a: Look; fill: string }> = ({ a, fill }) => {
  if (a.style === "bun") return <><circle cx="150" cy="40" r="32" fill={fill} /><path d="M 66 150 Q 62 60 150 54 Q 238 60 234 150 Z" fill={fill} /></>;
  if (a.style === "long") return <path d="M 62 160 Q 50 48 150 44 Q 250 48 238 160 Q 252 250 232 318 L 196 318 L 196 200 L 104 200 L 104 318 L 68 318 Q 48 250 62 160 Z" fill={fill} />;
  if (a.style === "bob") return <path d="M 60 150 Q 54 46 150 44 Q 246 46 240 150 Q 248 214 226 244 L 196 236 L 104 236 L 74 244 Q 52 214 60 150 Z" fill={fill} />;
  return null;
};

const HairFront: React.FC<{ a: Look; fill: string; shine: string }> = ({ a, fill, shine }) => {
  switch (a.style) {
    case "quiff":
      return <><path d="M 68 138 Q 58 62 118 48 Q 170 28 214 62 Q 244 92 232 138 Q 222 104 192 98 Q 146 110 104 96 Q 78 106 68 138 Z" fill={fill} /><path d="M 112 64 Q 150 44 192 66" fill="none" stroke={shine} strokeWidth={8} strokeLinecap="round" opacity={0.55} /></>;
    case "curls":
      return <g fill={fill}>{[[80, 110, 24], [92, 78, 27], [122, 58, 29], [156, 50, 30], [190, 60, 28], [214, 84, 26], [224, 114, 22], [108, 92, 20], [150, 82, 24], [192, 94, 20]].map(([x, y, r]) => <circle key={`${x}-${y}`} cx={x} cy={y} r={r} />)}<circle cx="128" cy="52" r="7" fill={shine} opacity={0.5} /><circle cx="184" cy="56" r="6" fill={shine} opacity={0.45} /></g>;
    case "side":
      return <><path d="M 68 142 Q 60 62 150 52 Q 240 58 232 142 Q 226 110 206 96 Q 150 112 96 84 Q 74 104 68 142 Z" fill={fill} /><path d="M 120 68 Q 168 60 204 80" fill="none" stroke={shine} strokeWidth={7} strokeLinecap="round" opacity={0.5} /></>;
    case "bun":
      return <><path d="M 70 142 Q 68 66 150 62 Q 232 66 230 142 Q 214 96 150 92 Q 86 96 70 142 Z" fill={fill} /><path d="M 112 76 Q 150 66 188 76" fill="none" stroke={shine} strokeWidth={6} strokeLinecap="round" opacity={0.45} /></>;
    case "long":
      return <><path d="M 70 158 Q 66 66 150 60 Q 234 66 230 158 Q 214 100 170 84 Q 124 116 70 158 Z" fill={fill} /><path d="M 114 74 Q 150 62 190 78" fill="none" stroke={shine} strokeWidth={7} strokeLinecap="round" opacity={0.45} /></>;
    default:
      return <><path d="M 68 150 Q 64 62 150 58 Q 236 62 232 150 Q 226 122 216 118 L 84 118 Q 74 122 68 150 Z" fill={fill} /><path d="M 104 78 Q 150 62 196 78" fill="none" stroke={shine} strokeWidth={7} strokeLinecap="round" opacity={0.5} /></>;
  }
};

const Eye: React.FC<{ id: string; x: number; y: number; open: number; look: [number, number]; a: Look; lid: string }> = ({ id, x, y, open, look, a, lid }) => {
  const ry = Math.max(0.6, 19 * open);
  return (
    <g>
      <clipPath id={id}><ellipse cx={x} cy={y} rx={20} ry={ry} /></clipPath>
      <ellipse cx={x} cy={y} rx={20} ry={ry} fill="#fdfbf8" />
      <g clipPath={`url(#${id})`}>
        <circle cx={x + look[0] * 6} cy={y + look[1] * 3} r={14} fill={`url(#${id.split("-")[0]}-iris)`} />
        <circle cx={x + look[0] * 6} cy={y + look[1] * 3} r={7} fill="#0d0806" />
        <circle cx={x + look[0] * 6 + 5} cy={y + look[1] * 3 - 6} r={4.2} fill="#fff" />
        <circle cx={x + look[0] * 6 - 4} cy={y + look[1] * 3 + 5} r={1.8} fill="#ffffffaa" />
        <ellipse cx={x} cy={y - ry - 2} rx={22} ry={7} fill="#00000022" />
      </g>
      <path d={`M ${x - 21} ${y} Q ${x} ${y - ry * 2 - 1} ${x + 21} ${y}`} fill="none" stroke={lid} strokeWidth={4.5} strokeLinecap="round" />
    </g>
  );
};

const Hand: React.FC<{ skin: string; angle: number; lift: number }> = ({ skin, angle, lift }) => (
  <g transform={`translate(262 ${262 + (1 - lift) * 110}) rotate(${angle})`}>
    <g fill={skin}>
      {[-20, -7, 7, 20].map((x, i) => <rect key={x} x={x - 6} y={-58 + Math.abs(i - 1.5) * 5} width={12} height={42} rx={6} />)}
      <rect x={-27} y={-24} width={54} height={46} rx={18} />
      <rect x={20} y={-16} width={13} height={34} rx={6.5} transform="rotate(38 26 0)" />
    </g>
    <ellipse cx={0} cy={-3} rx={15} ry={12} fill="#00000014" />
  </g>
);

const Bust: React.FC<{ kind: Exclude<Kind, "none">; v: Viseme; blink: number; look: [number, number]; smile: number; brow: number; tilt: number; nod: number; breathe: number; wave: number; t: number }> = ({ kind, v, blink, look, smile, brow, tilt, nod, breathe, wave, t }) => {
  const a = CAST[kind];
  const id = kind;
  const dark = shade(a.skin, -0.17), lid = shade(a.skin, -0.42), lip = shade(a.skin, -0.3);
  const hairLight = shade(a.hair, 0.3);
  const parallax = look[0] * 5;
  return (
    <svg viewBox="0 0 300 360" width="100%" height="100%" style={{ overflow: "visible" }}>
      <defs>
        <radialGradient id={`${id}-skin`} cx="42%" cy="34%" r="72%"><stop offset="0%" stopColor={shade(a.skin, 0.16)} /><stop offset="60%" stopColor={a.skin} /><stop offset="100%" stopColor={dark} /></radialGradient>
        <radialGradient id={`${id}-iris`} cx="50%" cy="65%" r="60%"><stop offset="0%" stopColor={shade(a.iris, 0.3)} /><stop offset="100%" stopColor={a.iris} /></radialGradient>
        <linearGradient id={`${id}-top`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={shade(a.top, 0.14)} /><stop offset="100%" stopColor={shade(a.top, -0.22)} /></linearGradient>
        <linearGradient id={`${id}-hair`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={hairLight} /><stop offset="55%" stopColor={a.hair} /></linearGradient>
        <radialGradient id={`${id}-blush`}><stop offset="0%" stopColor="#ef5a5a" stopOpacity="0.3" /><stop offset="100%" stopColor="#ef5a5a" stopOpacity="0" /></radialGradient>
      </defs>
      <g transform={`translate(0 ${breathe})`}>
        <path d="M 22 360 Q 28 284 92 268 L 208 268 Q 272 284 278 360 Z" fill={`url(#${id}-top)`} />
        <path d="M 96 268 Q 150 318 204 268 L 190 262 L 110 262 Z" fill={shade(a.top, -0.3)} />
        <path d="M 130 298 L 126 342 M 170 298 L 174 342" stroke="#fff" strokeOpacity={0.75} strokeWidth={4} strokeLinecap="round" />
        <rect x="122" y="226" width="56" height="58" rx="22" fill={dark} />
      </g>
      <g transform={`translate(${tilt * 0.8} ${nod}) rotate(${tilt} 150 240)`}>
        <HairBack a={a} fill={`url(#${id}-hair)`} />
        <ellipse cx="70" cy="165" rx="14" ry="20" fill={dark} /><ellipse cx="230" cy="165" rx="14" ry="20" fill={dark} />
        {a.earrings && <><circle cx="70" cy="192" r="8" fill="none" stroke="#f6c945" strokeWidth={3.5} /><circle cx="230" cy="192" r="8" fill="none" stroke="#f6c945" strokeWidth={3.5} /></>}
        <path d="M 70 150 Q 68 66 150 62 Q 232 66 230 150 Q 232 214 188 244 Q 150 262 112 244 Q 68 214 70 150 Z" fill={`url(#${id}-skin)`} />
        {a.beard && <path d="M 72 176 Q 84 224 112 244 Q 150 262 188 244 Q 216 224 228 176 Q 216 202 190 198 Q 150 188 110 198 Q 84 202 72 176 Z" fill={a.hair} opacity={0.72} />}
        <ellipse cx="100" cy="192" rx="24" ry="17" fill={`url(#${id}-blush)`} /><ellipse cx="200" cy="192" rx="24" ry="17" fill={`url(#${id}-blush)`} />
        <g transform={`translate(${parallax} 0)`}>
          <Eye id={`${id}-eyeL`} x={114} y={154} open={1 - blink} look={look} a={a} lid={lid} />
          <Eye id={`${id}-eyeR`} x={186} y={154} open={1 - blink} look={look} a={a} lid={lid} />
          <path d={`M 92 ${122 - brow * 8} Q 114 ${110 - brow * 10} 136 ${124 - brow * 6}`} fill="none" stroke={a.hair} strokeWidth={7.5} strokeLinecap="round" />
          <path d={`M 164 ${124 - brow * 6} Q 186 ${110 - brow * 10} 208 ${122 - brow * 8}`} fill="none" stroke={a.hair} strokeWidth={7.5} strokeLinecap="round" />
          <path d="M 150 170 Q 142 190 140 192 Q 150 200 160 192" fill="none" stroke={dark} strokeWidth={4} strokeLinecap="round" />
          <circle cx="148" cy="183" r="3.5" fill="#ffffff33" />
          <Mouth id={id} v={v} smile={smile} lip={lip} />
          {a.glasses && <g fill="#ffffff14" stroke="#14141c" strokeWidth={5}><circle cx="114" cy="154" r="30" /><circle cx="186" cy="154" r="30" /><path d="M 144 150 Q 150 145 156 150" fill="none" /></g>}
        </g>
        <HairFront a={a} fill={`url(#${id}-hair)`} shine={shade(a.hair, 0.5)} />
        {a.headphones && <g><path d="M 62 150 Q 56 40 150 38 Q 244 40 238 150" fill="none" stroke="#23252f" strokeWidth={11} /><rect x="46" y="134" width="30" height="58" rx="14" fill="#23252f" /><rect x="224" y="134" width="30" height="58" rx="14" fill="#23252f" /></g>}
      </g>
      {wave > 0.01 && <Hand skin={a.skin} angle={Math.sin(t * 11) * 15 + 8} lift={wave} />}
    </svg>
  );
};

/** On-screen host, rising from the bottom edge: lip-synced, with irregular blinks, held glances and nods on stressed words. */
export const Presenter: React.FC<{ kind: Kind; words: Word[]; scenes: Scene[]; emphasis: Emphasis[] }> = ({ kind, words, scenes, emphasis }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  if (kind === "none" || !(kind in CAST)) return null;
  const scene = [...scenes].reverse().find((s) => t >= s.start);
  if (!scene) return null;
  const big = scene.type === "hook" || scene.type === "cta";
  const width = big ? 470 : 340;
  const enter = spring({ frame: f - Math.round(scene.start * fps) - 3, fps, config: { stiffness: 120, damping: 15 } });
  const v = smoothViseme(words, t);

  const period = 2.7;
  const slot = Math.floor(t / period);
  const blinkAt = slot * period + 0.3 + random(`blink${slot}`) * 1.9;
  const blink = Math.max(0, 1 - Math.abs(t - blinkAt) / 0.075);

  // Eyes rest on the viewer and glance away now and then, holding each position.
  const hold = Math.floor(t / 1.15);
  const away = random(`away${hold}`) > 0.68;
  const look: [number, number] = away ? [(random(`lx${hold}`) - 0.5) * 1.5, (random(`ly${hold}`) - 0.5) * 0.8] : [0, 0];

  const hit = [...emphasis].reverse().find((e) => t >= e.t && t < e.t + 0.45);
  const beat = hit ? Math.sin(Math.min(1, (t - hit.t) / 0.45) * Math.PI) : 0;
  const nod = beat * 7 + v.open * 2 + Math.sin(t * 1.3) * 2;
  const tilt = Math.sin(t * 0.8) * 2.4 + Math.sin(t * 2.1 + 1) * 0.9 + beat * (Math.floor(t) % 2 ? 1.6 : -1.6);
  const brow = Math.max(0, beat * 0.9 + v.open * 0.18);
  const smile = scene.type === "cta" ? 1 : scene.type === "hook" ? 0.75 : 0.45;
  const local = t - scene.start;
  const wave = big ? Math.max(0, Math.min(1, local / 0.25)) * Math.max(0, Math.min(1, (1.9 - local) / 0.25)) : 0;

  return (
    <div style={{ position: "absolute", left: -6, top: 1920 - width * 1.2 + (1 - enter) * 280, width, height: width * 1.2, filter: "drop-shadow(0 18px 34px rgba(0,0,0,.55))" }}>
      <Bust kind={kind as Exclude<Kind, "none">} v={v} blink={blink} look={look} smile={smile} brow={brow} tilt={tilt} nod={nod} breathe={Math.sin(t * 1.5) * 2.5} wave={wave} t={t} />
    </div>
  );
};

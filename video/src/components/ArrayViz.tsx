import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, clamp, fonts, glow, textStroke } from "../theme";
import { VizStep } from "../types";

const POINTER_COLORS = [C.cyan, C.pink, C.yellow, C.green, C.orange, C.purple];
const pointerColor = (name: string, order: string[]) => POINTER_COLORS[Math.max(0, order.indexOf(name)) % POINTER_COLORS.length];

type Resolved = Required<Pick<VizStep, "array" | "pointers" | "vars" | "highlight" | "dim" | "links" | "bits">> & VizStep;

/** Carry arrays/links/bits forward so a step only needs to state what changed. */
const resolve = (steps: VizStep[]): Resolved[] => {
  let array: (number | string)[] = [];
  let links: string[] = [];
  let bits: VizStep["bits"] = [];
  return steps.map((s) => {
    array = s.array ?? array;
    links = s.links ?? links;
    bits = s.bits ?? bits;
    return { ...s, array, links, bits: bits ?? [], pointers: s.pointers ?? {}, vars: s.vars ?? {}, highlight: s.highlight ?? [], dim: s.dim ?? [] };
  });
};

export const ArrayViz: React.FC<{ steps: VizStep[]; mode: "array" | "list" | "bits"; result: string }> = ({ steps, mode, result }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const all = resolve(steps);
  let ci = 0;
  all.forEach((s, i) => { if (t >= s.at) ci = i; });
  const cur = all[ci];
  const prev = all[Math.max(0, ci - 1)];
  const sp = spring({ frame: f - Math.round(cur.at * fps), fps, config: { stiffness: 210, damping: 16, mass: 0.6 } });
  const appear = spring({ frame: f - Math.round(all[0].at * fps), fps, config: { stiffness: 140, damping: 15 } });
  const pointerOrder = Array.from(new Set(all.flatMap((s) => Object.keys(s.pointers))));

  const n = cur.array.length;
  const gap = mode === "list" ? 58 : 16;
  const cellW = n ? Math.min(mode === "list" ? 124 : 172, Math.floor((1010 - (n - 1) * gap) / n)) : 0;
  const rowW = n * cellW + (n - 1) * gap;
  const x0 = (1080 - rowW) / 2;
  const cx = (i: number) => x0 + i * (cellW + gap) + cellW / 2;

  const stacks: Record<number, number> = {};
  const maxStack = Math.max(1, ...Object.values(
    Object.values(cur.pointers).reduce<Record<number, number>>((acc, i) => ({ ...acc, [i]: (acc[i] ?? 0) + 1 }), {}),
  ));

  return (
    <div style={{ position: "relative", width: 1080, opacity: appear, transform: `translateY(${(1 - appear) * 60}px)` }}>
      {mode !== "bits" && n > 0 && (
        <div style={{ position: "relative", height: cellW + 60 }}>
          {cur.array.map((v, i) => {
            const changed = prev.array[i] !== v && ci > 0;
            const hi = cur.highlight.includes(i);
            const dim = cur.dim.includes(i);
            const flip = changed ? interpolate(sp, [0, 1], [90, 0], clamp) : 0;
            const lift = hi ? sp : 0;
            const neg = typeof v === "number" && v < 0;
            return (
              <React.Fragment key={i}>
                <div style={{ position: "absolute", left: cx(i) - 40, width: 80, top: 0, textAlign: "center", fontFamily: fonts.mono, fontSize: 24, color: C.dim }}>
                  {mode === "list" ? "" : i}
                </div>
                <div
                  style={{
                    position: "absolute",
                    left: cx(i) - cellW / 2,
                    top: 40 - lift * 12,
                    width: cellW,
                    height: cellW,
                    borderRadius: mode === "list" ? cellW / 2 : 22,
                    background: hi ? "linear-gradient(160deg, #3a2f00, #1a1b26)" : "linear-gradient(160deg, #24283b, #16161e)",
                    border: `4px solid ${hi ? C.yellow : neg ? C.red : C.border}`,
                    boxShadow: hi ? glow(C.yellow, 22) : "0 14px 30px rgba(0,0,0,.5)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontFamily: fonts.mono,
                    fontWeight: 700,
                    fontSize: Math.min(64, cellW * 0.5),
                    color: neg ? C.red : hi ? C.yellow : "#fff",
                    opacity: dim ? 0.28 : 1,
                    transform: `perspective(600px) rotateX(${flip}deg) scale(${1 + 0.08 * lift})`,
                  }}
                >
                  {String(v)}
                  {dim && (
                    <div style={{ position: "absolute", left: "8%", right: "8%", top: "50%", height: 6, background: C.red, transform: "rotate(-24deg)", borderRadius: 3 }} />
                  )}
                </div>
                {mode === "list" && i < n - 1 && (
                  <LinkArrow x={cx(i) + cellW / 2 + 4} y={40 + cellW / 2} w={gap - 8} dir={cur.links[i] ?? "→"} prevDir={prev.links[i] ?? "→"} p={sp} />
                )}
              </React.Fragment>
            );
          })}
          {mode === "list" && (
            <>
              <NullTag x={x0 - 120} y={40 + cellW / 2} />
              <NullTag x={x0 + rowW + 30} y={40 + cellW / 2} />
            </>
          )}
          {cur.swap && <SwapArc a={cx(cur.swap[0])} b={cx(cur.swap[1])} p={sp} />}
        </div>
      )}

      {mode !== "bits" && Object.keys(cur.pointers).length > 0 && (
        <div style={{ position: "relative", height: 86 * maxStack + 10 }}>
          {Object.entries(cur.pointers).map(([name, idx]) => {
            const from = prev.pointers[name];
            const pos = from === undefined || ci === 0 ? cx(idx) : interpolate(sp, [0, 1], [cx(from), cx(idx)]);
            const level = (stacks[idx] = (stacks[idx] ?? -1) + 1);
            const color = pointerColor(name, pointerOrder);
            const outside = idx < 0 || idx >= n;
            return (
              <div key={name} style={{ position: "absolute", left: pos - 90, width: 180, top: level * 86, textAlign: "center", opacity: outside ? 0.5 : 1 }}>
                <div style={{ color, fontSize: 34, lineHeight: "34px", textShadow: glow(color, 10) }}>▲</div>
                <span style={{ display: "inline-block", marginTop: 2, padding: "4px 18px", borderRadius: 999, background: color, color: "#0a0a14", fontFamily: fonts.mono, fontWeight: 700, fontSize: 30 }}>
                  {name}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {cur.bits.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, marginTop: 10 }}>
          {cur.bits.map((row, ri) => {
            const before = prev.bits.find((b) => b.label === row.label);
            return (
              <div key={row.label + ri} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 250, textAlign: "right", fontFamily: fonts.mono, fontSize: 42, color: row.color ?? C.fg, paddingRight: 14 }}>{row.label}</div>
                {row.bits.split("").map((b, bi) => {
                  const changed = before && before.bits[bi] !== b && ci > 0;
                  const on = b === "1";
                  return (
                    <div
                      key={bi}
                      style={{
                        width: 96, height: 96, borderRadius: 16,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontFamily: fonts.mono, fontWeight: 700, fontSize: 56,
                        background: on ? `${row.color ?? C.cyan}33` : "#16161e",
                        border: `3px solid ${on ? row.color ?? C.cyan : C.border}`,
                        color: on ? row.color ?? C.cyan : C.dim,
                        boxShadow: on ? glow(row.color ?? C.cyan, 10) : "none",
                        transform: changed ? `scale(${1.25 - 0.25 * sp})` : "none",
                      }}
                    >
                      {b}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}

      {Object.keys(cur.vars).length > 0 && (
        <div style={{ display: "flex", justifyContent: "center", flexWrap: "wrap", gap: 22, marginTop: 30 }}>
          {Object.entries(cur.vars).map(([k, v]) => {
            const changed = ci > 0 && prev.vars[k] !== v;
            const s = changed ? 1 + 0.22 * (1 - sp) : 1;
            return (
              <div
                key={k}
                style={{
                  padding: "14px 30px", borderRadius: 20, background: "rgba(22,22,30,.92)",
                  border: `3px solid ${changed ? C.yellow : C.border}`,
                  fontFamily: fonts.mono, fontSize: 54, color: C.fg,
                  transform: `scale(${s})`, boxShadow: changed ? glow(C.yellow, 12) : "none",
                }}
              >
                <span style={{ color: C.purple }}>{k}</span>
                <span style={{ color: C.dim }}> = </span>
                <span style={{ color: changed ? C.yellow : C.orange, fontWeight: 700 }}>{String(v)}</span>
              </div>
            );
          })}
        </div>
      )}

      {cur.note && (
        <div
          key={`note-${ci}`}
          style={{
            marginTop: 34, padding: "0 70px", textAlign: "center", fontFamily: fonts.mono, fontSize: cur.note.length > 26 ? 40 : 50, color: C.cyan,
            textShadow: glow(C.cyan, 8), opacity: sp, transform: `translateY(${(1 - sp) * 20}px)`,
          }}
        >
          {cur.note}
        </div>
      )}

      {cur.done && (
        <div style={{ display: "flex", justifyContent: "center", marginTop: 34 }}>
          <div
            style={{
              padding: "14px 44px", borderRadius: 22, background: C.green, color: "#07070f",
              fontFamily: fonts.display, fontSize: 82, letterSpacing: 2,
              transform: `scale(${2.2 - 1.2 * sp}) rotate(${-4 * sp}deg)`, opacity: Math.min(1, sp * 1.6),
              boxShadow: glow(C.green, 26), ...textStroke(0),
            }}
          >
            {result}
          </div>
        </div>
      )}
    </div>
  );
};

const LinkArrow: React.FC<{ x: number; y: number; w: number; dir: string; prevDir: string; p: number }> = ({ x, y, w, dir, prevDir, p }) => {
  if (!dir) return null;
  const changed = dir !== prevDir;
  const rot = dir === "←" ? 180 : 0;
  const from = prevDir === "←" ? 180 : 0;
  const angle = changed ? interpolate(p, [0, 1], [from, rot]) : rot;
  const color = dir === "←" ? C.green : C.dim;
  return (
    <svg style={{ position: "absolute", left: x, top: y - 20, overflow: "visible" }} width={w} height={40}>
      <g transform={`rotate(${angle} ${w / 2} 20)`}>
        <line x1={4} y1={20} x2={w - 14} y2={20} stroke={color} strokeWidth={7} strokeLinecap="round" />
        <polygon points={`${w - 16},6 ${w},20 ${w - 16},34`} fill={color} />
      </g>
    </svg>
  );
};

const NullTag: React.FC<{ x: number; y: number }> = ({ x, y }) => (
  <div style={{ position: "absolute", left: x, top: y - 24, width: 90, textAlign: "center", fontFamily: fonts.mono, fontSize: 30, color: C.dim }}>null</div>
);

const SwapArc: React.FC<{ a: number; b: number; p: number }> = ({ a, b, p }) => {
  const left = Math.min(a, b);
  const w = Math.abs(b - a);
  if (w < 1) return null;
  return (
    <svg style={{ position: "absolute", left, top: -50, overflow: "visible", opacity: 1 - p * 0.7 }} width={w} height={90}>
      <path d={`M 0 80 Q ${w / 2} ${-30} ${w} 80`} fill="none" stroke={C.pink} strokeWidth={6} strokeDasharray={`${w * 1.4}`} strokeDashoffset={w * 1.4 * (1 - p)} />
      <polygon points={`${w - 14},62 ${w + 4},86 ${w - 22},84`} fill={C.pink} opacity={p} />
    </svg>
  );
};

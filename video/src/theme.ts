import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadArchivo } from "@remotion/google-fonts/ArchivoBlack";
import { loadFont as loadBebas } from "@remotion/google-fonts/BebasNeue";
import { loadFont as loadOswald } from "@remotion/google-fonts/Oswald";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";
import { Easing, interpolate, spring } from "remotion";

export const fonts = {
  display: loadAnton("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
  heavy: loadMontserrat("normal", { weights: ["800", "900"], subsets: ["latin"] }).fontFamily,
  body: loadInter("normal", { weights: ["500", "700"], subsets: ["latin"] }).fontFamily,
  bebas: loadBebas("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
  oswald: loadOswald("normal", { weights: ["700"], subsets: ["latin"] }).fontFamily,
  archivo: loadArchivo("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
  mono: loadMono("normal", { weights: ["400", "700"], subsets: ["latin"] }).fontFamily,
};

export const C = {
  bg: "#07070f",
  panel: "#1a1b26",
  panel2: "#16161e",
  border: "#2f334d",
  fg: "#c0caf5",
  dim: "#565f89",
  pink: "#ff7edb",
  cyan: "#36f9f6",
  yellow: "#ffe600",
  purple: "#bb9af7",
  green: "#9ece6a",
  red: "#f7768e",
  orange: "#ff9e64",
  blue: "#7aa2f7",
};

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Spring that starts at `at` seconds (local time). 0 before, ~1 after. */
export const pop = (frame: number, fps: number, at: number, stiff = 180, damping = 13) =>
  spring({ frame: frame - Math.round(at * fps), fps, config: { stiffness: stiff, damping, mass: 0.6 } });

/** Smooth 0→1 ramp between two times (seconds), ease-out cubic. */
export const ramp = (t: number, from: number, to: number) =>
  interpolate(t, [from, Math.max(from + 0.001, to)], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });

export const textStroke = (px: number, color = "#000") => ({
  WebkitTextStroke: `${px}px ${color}`,
  paintOrder: "stroke fill" as const,
});

export const glow = (color: string, size = 24) => `0 0 ${size}px ${color}, 0 0 ${size * 2}px ${color}55`;

export const fmtCompact = (n: number) =>
  n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : `${Math.round(n)}`;

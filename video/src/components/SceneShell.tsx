import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Transition } from "../types";
import { clamp } from "../theme";

export const TRANSITION_FRAMES = 9;

/**
 * Animates a scene in with its own transition and out with the NEXT scene's transition,
 * so both halves of every cut move together (whip pans, zoom punches, glitch hits).
 */
export const SceneShell: React.FC<{
  id: string;
  enter: Transition;
  exit: Transition;
  durationFrames: number;
  children: React.ReactNode;
}> = ({ id, enter, exit, durationFrames, children }) => {
  const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const T = TRANSITION_FRAMES;
  const ease = Easing.bezier(0.7, 0, 0.2, 1);

  let tx = 0, ty = 0, scale = 1, opacity = 1, blurX = 0, blurY = 0, blur = 0, rgb = 0, rot = 0;
  let clip: string | undefined;

  if (f < T && enter !== "none") {
    const p = interpolate(f, [0, T], [0, 1], { ...clamp, easing: ease });
    const v = 1 - p;
    if (enter === "whip") { tx = v * width; blurX = Math.sin(p * Math.PI) * 60 + v * 20; rot = v * -6; }
    if (enter === "slide-up") { ty = v * height; blurY = Math.sin(p * Math.PI) * 60 + v * 20; }
    if (enter === "zoom") { scale = 1 + v * 0.9; opacity = p; blur = v * 24; }
    if (enter === "glitch") { tx = (f % 2 ? 1 : -1) * v * 60; rgb = v * 18; opacity = f % 3 === 1 ? 0.6 : 1; }
    if (enter === "spin") { rot = v * -70; scale = 1 + v * 0.7; opacity = p; blur = v * 16; }
    if (enter === "blur") { opacity = p; blur = v * 36; scale = 1 + v * 0.06; }
    if (enter === "flash") { scale = 1 + v * 0.14; opacity = Math.min(1, p * 2.5); }
    if (enter === "drop") { ty = -v * height; blurY = Math.sin(p * Math.PI) * 40; }
    // Wipes reveal the incoming scene over the outgoing one, which holds still underneath.
    if (enter === "shutter") { clip = `inset(${v * 50}% 0 ${v * 50}% 0)`; }
    if (enter === "iris") { clip = `circle(${p * 120}% at 50% 46%)`; }
  }
  const out = durationFrames - f;
  if (out < T && exit !== "none") {
    const p = interpolate(out, [0, T], [1, 0], { ...clamp, easing: ease });
    if (exit === "whip") { tx = -p * width; blurX = Math.sin(p * Math.PI) * 60 + p * 20; rot = p * 6; }
    if (exit === "slide-up") { ty = -p * height; blurY = Math.sin(p * Math.PI) * 60 + p * 20; }
    if (exit === "zoom") { scale = 1 - p * 0.35; opacity = 1 - p; blur = p * 18; }
    if (exit === "glitch") { tx = (f % 2 ? -1 : 1) * p * 50; rgb = p * 18; opacity = 1 - p; }
    if (exit === "spin") { rot = p * 70; scale = 1 - p * 0.3; opacity = 1 - p; blur = p * 16; }
    if (exit === "blur") { opacity = 1 - p; blur = p * 36; }
    if (exit === "flash") { opacity = 1 - p; scale = 1 + p * 0.06; }
    if (exit === "drop") { ty = p * height * 0.4; opacity = 1 - p; }
  }

  const filterId = `mb-${id}`;
  const filters: string[] = [];
  if (blurX > 0.5 || blurY > 0.5) filters.push(`url(#${filterId})`);
  if (blur > 0.5) filters.push(`blur(${blur}px)`);
  if (rgb > 0.5) filters.push(`drop-shadow(${rgb}px 0 0 rgba(255,0,90,.85)) drop-shadow(${-rgb}px 0 0 rgba(0,240,255,.85))`);

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${tx}px, ${ty}px) scale(${scale}) rotate(${rot}deg)`,
        opacity,
        filter: filters.join(" ") || undefined,
        clipPath: clip,
      }}
    >
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <filter id={filterId} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation={`${blurX} ${blurY}`} />
          </filter>
        </defs>
      </svg>
      {children}
    </AbsoluteFill>
  );
};

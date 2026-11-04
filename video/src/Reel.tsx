import React from "react";
import { AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "./components/Background";
import { Captions } from "./components/Captions";
import { Bursts, Camera, Flashes, FilmLook, GRADES, Overlay, Shake } from "./components/Effects";
import { SceneShell, TRANSITION_FRAMES } from "./components/SceneShell";
import { Browser, Code, Compare, Cta, Hiring, Hook } from "./scenes/CommonScenes";
import { Presenter } from "./components/Presenter";
import { Naive, Problem, Visualize } from "./scenes/DsaScenes";
import { Demo, How, RepoIntro, UseCases } from "./scenes/RepoScenes";
import { C, fonts } from "./theme";
import { DEFAULT_STYLE, ReelProps, Scene, Style } from "./types";

const renderScene = (s: Scene, accent: string, st: Style) => {
  switch (s.type) {
    case "hook": return <Hook s={s} accent={accent} st={st} />;
    case "problem": return <Problem s={s} accent={accent} />;
    case "naive": return <Naive s={s} accent={accent} />;
    case "visualize": return <Visualize s={s} accent={accent} />;
    case "code": return <Code s={s} accent={accent} />;
    case "compare": return <Compare s={s} accent={accent} />;
    case "repo_intro": return <RepoIntro s={s} accent={accent} />;
    case "how": return <How s={s} accent={accent} />;
    case "demo": return <Demo s={s} accent={accent} />;
    case "use_cases": return <UseCases s={s} accent={accent} />;
    case "browser": return <Browser s={s} accent={accent} />;
    case "cta": return <Cta s={s} accent={accent} st={st} />;
    case "hiring": return <Hiring s={s} accent={accent} />;
  }
};

/** Top chrome: handle + "DAY N" streak badge. (No progress bar: it signals "this will take a while".) */
const Chrome: React.FC<{ handle: string; accent: string; day?: number }> = ({ handle, accent, day }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const badge = spring({ frame: f - 4, fps, config: { stiffness: 220, damping: 12 } });
  return (
    <div style={{ position: "absolute", top: 140, width: "100%", display: "flex", justifyContent: "center", alignItems: "center", gap: 18 }}>
      <div style={{ fontFamily: fonts.mono, fontWeight: 700, fontSize: 30, color: "rgba(255,255,255,.78)", letterSpacing: 1 }}>@{handle}</div>
      {day ? (
        <div style={{ padding: "6px 18px", borderRadius: 999, background: accent, color: "#0b0b0b", fontFamily: fonts.heavy, fontWeight: 900, fontSize: 30, letterSpacing: 1, transform: `scale(${badge})`, boxShadow: `0 0 18px ${accent}88` }}>
          DAY {day}
        </div>
      ) : null}
    </div>
  );
};

export const Reel: React.FC<ReelProps> = (props) => {
  const { fps } = useVideoConfig();
  const { scenes, accent } = props;
  const st = props.style ?? DEFAULT_STYLE;
  const cuts = scenes.slice(1).filter((s) => s.transition === "zoom" || s.transition === "glitch" || s.transition === "flash").map((s) => s.start);
  const emphasis = props.emphasis ?? [];
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <AbsoluteFill style={{ filter: GRADES[st.grade ?? "none"] }}>
        <Background accent={accent} look={st.look} keyword={props.keyword} />
        <Shake impacts={props.impacts}>
          <Camera kind={st.camera ?? "punch"} emphasis={emphasis} scenes={scenes}>
            {scenes.map((s, i) => {
              const from = Math.round(s.start * fps);
              const next = scenes[i + 1];
              const dur = Math.round(s.duration * fps) + (next ? TRANSITION_FRAMES : 0);
              return (
                <Sequence key={s.id} from={from} durationInFrames={dur} name={`${i}-${s.type}`}>
                  <SceneShell id={s.id} enter={i === 0 ? "none" : s.transition} exit={next ? next.transition : "none"} durationFrames={dur}>
                    {renderScene(s, accent, st)}
                  </SceneShell>
                </Sequence>
              );
            })}
          </Camera>
          {st.presenter && st.presenter !== "none" && <Presenter kind={st.presenter} words={props.words} scenes={scenes} emphasis={emphasis} />}
          <Bursts kind={st.burst ?? "ring"} emphasis={emphasis} scenes={scenes} color={st.highlight} />
          <Captions words={props.words} scenes={scenes} accent={accent} variant={st.captions} highlight={st.highlight} emoji={st.emoji ?? true} />
        </Shake>
        <Flashes times={[...props.impacts, ...cuts]} />
        <Overlay kind={st.overlay ?? "none"} accent={accent} />
      </AbsoluteFill>
      <Chrome handle={props.handle} accent={accent} day={props.day} />
      <FilmLook />
      {props.audio && <Audio src={staticFile(props.audio)} />}
    </AbsoluteFill>
  );
};

import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { Reel } from "./Reel";
import sample from "./sample-props.json";
import { ReelProps } from "./types";

const calculateMetadata: CalculateMetadataFunction<ReelProps> = ({ props }) => ({
  durationInFrames: props.durationInFrames,
  fps: props.fps,
  width: props.width,
  height: props.height,
});

export const Root: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={(sample as ReelProps).durationInFrames}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={sample as ReelProps}
    calculateMetadata={calculateMetadata}
  />
);

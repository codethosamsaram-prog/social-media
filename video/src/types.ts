// Props contract between auto_pipeline.py (which writes props.json) and the Remotion reel.
// All times are in SECONDS. Scene-level `at` times are relative to the scene start.

export type Word = { start: number; end: number; text: string };

/** [text, hex colour] — tokens are pre-highlighted in Python with Pygments (Tokyo Night). */
export type Token = [string, string];

export type Stamp = { text: string; at: number; color: string };

export type CodeData = {
  filename: string;
  lines: Token[][];
  typing: [number, number];
  focusLines: number[];
  focusAt: number | null;
  stamps: Stamp[];
};

export type Transition = "whip" | "zoom" | "glitch" | "slide-up" | "spin" | "shutter" | "blur" | "flash" | "iris" | "drop" | "none";

type Base = {
  id: string;
  start: number;
  duration: number;
  transition: Transition;
  /** Caption centre Y in px, or null to hide captions during this scene. */
  captionY: number | null;
  kicker?: string;
};

export type HookScene = Base & { type: "hook"; words: string[]; wordTimes: number[]; stock: string | null };

export type ProblemScene = Base & {
  type: "problem";
  source: string;
  number: number | null;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  statement: string;
  example: (number | string)[];
  exampleAt: number[];
};

export type NaiveScene = Base & {
  type: "naive";
  label: string;
  items: (number | string)[];
  itemTimes: number[];
  cost: string;
  stampAt: number;
};

export type VizStep = {
  at: number;
  array?: (number | string)[];
  pointers?: Record<string, number>;
  vars?: Record<string, string | number>;
  highlight?: number[];
  dim?: number[];
  swap?: [number, number] | null;
  links?: string[];
  bits?: { label: string; bits: string; color?: string }[];
  note?: string;
  done?: boolean;
};

export type VisualizeScene = Base & {
  type: "visualize";
  title: string;
  mode: "array" | "list" | "bits";
  steps: VizStep[];
  result: string;
};

export type CodeScene = Base & { type: "code"; title: string; code: CodeData };

export type CompareScene = Base & {
  type: "compare";
  title: string;
  rows: { label: string; color: string; bars: [number, number][]; total: string; at: number }[];
  scale: number;
};

export type RepoIntroScene = Base & {
  type: "repo_intro";
  owner: string;
  name: string;
  description: string;
  stars: number;
  language: string | null;
  badge: string;
};

export type FlowStep = { icon: string; title: string; detail: string; at: number };

export type HowScene = Base & { type: "how"; title: string; steps: FlowStep[] };

export type DemoScene = Base & {
  type: "demo";
  install: string;
  installTyping: [number, number];
  output: { text: string; at: number }[];
  code: CodeData | null;
  codeAt: number;
};

export type UseCasesScene = Base & { type: "use_cases"; title: string; cards: FlowStep[] };

export type BrowserScene = Base & {
  type: "browser";
  url: string;
  urlTyping: [number, number];
  prompt: string | null;
  promptTyping: [number, number];
  mock: "dashboard" | "docs" | "landing";
  mockAt: number;
  headline: string;
  bullets: { text: string; at: number }[];
  query: string;
};

export type CtaScene = Base & {
  type: "cta";
  keyword: string;
  thing: string;
  handle: string;
  bubbleAt: number;
  followAt: number;
  /** "Part N" label for the series ending, e.g. "O(1) TRICKS · PART 3". */
  series?: string | null;
};

export type Company = {
  name: string;
  domain: string;
  color: string;
  roles: number;
  fresh: number;
  top_role: string;
  cities: string[];
  logo: string | null;
  at: number;
};

export type HiringScene = Base & { type: "hiring"; title: string; companies: Company[] };

export type Scene =
  | HiringScene
  | HookScene
  | ProblemScene
  | NaiveScene
  | VisualizeScene
  | CodeScene
  | CompareScene
  | RepoIntroScene
  | HowScene
  | DemoScene
  | UseCasesScene
  | BrowserScene
  | CtaScene;

/** Per-reel visual identity. Picked in Python so consecutive reels never share a look. */
export type Look = "neon" | "terminal" | "blueprint" | "sunset" | "mono" | "aurora" | "matrix" | "glass" | "ember" | "galaxy" | "circuit" | "retrosun" | "ocean" | "chalk" | "hexgrid" | "bokeh";
export type HookStyle = "stack" | "terminal" | "alert" | "sticker" | "kinetic" | "question" | "glitch" | "news" | "spotlight" | "chat" | "split";
export type CaptionStyle = "pop" | "box" | "clean" | "type" | "neon" | "bounce" | "gradient" | "tape" | "mega" | "underline" | "karaoke";
export type CameraStyle = "punch" | "snap" | "drift" | "handheld" | "breathe";
export type GradeStyle = "none" | "teal_orange" | "warm" | "cool" | "vivid" | "faded" | "contrast";
export type OverlayStyle = "none" | "leaks" | "dust" | "vhs" | "letterbox" | "sparks";
export type BurstStyle = "ring" | "rays" | "sparks" | "slash";
/** A moment the edit reacts to (seconds, absolute). `strong` also fires a burst. */
export type Emphasis = { t: number; strong: boolean };
export type CtaStyle = "search" | "comment" | "series" | "share" | "triple";
export type Presenter = "none" | "aarav" | "kabir" | "rohan";

export type Style = {
  look: Look;
  hook: HookStyle;
  captions: CaptionStyle;
  cta: CtaStyle;
  /** Hook / caption highlight colour. */
  highlight: string;
  /** Hook display font. */
  hookFont: "anton" | "bebas" | "archivo" | "oswald";
  /** Corner avatar that reacts while the voice speaks. */
  presenter?: Presenter;
  /** Emoji pops above caption keywords. */
  emoji?: boolean;
  camera?: CameraStyle;
  grade?: GradeStyle;
  overlay?: OverlayStyle;
  burst?: BurstStyle;
};

export const DEFAULT_STYLE: Style = { look: "neon", hook: "stack", captions: "pop", cta: "search", highlight: "#ffe600", hookFont: "anton", presenter: "none", emoji: true };

export type ReelProps = {
  style?: Style;
  /** Day N of the daily-posting streak. */
  day?: number;
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  audio: string | null;
  handle: string;
  keyword: string;
  accent: string;
  words: Word[];
  scenes: Scene[];
  impacts: number[];
  emphasis?: Emphasis[];
};

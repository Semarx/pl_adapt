/** Written by 09 PL_Platform/record_fp.py. Cells are flat ids: row * grid + col. */
export type Bounds = { rMin: number; rMax: number; cMin: number; cMax: number };
export type Frame = { t: number; a: number; n: number[]; f: number[] };
export type Check = { t: number; rate: number; ratio: number | null;
  route: number[]; arrived: boolean; target: number };
export type Change = { kind: "goal" | "shift" | "grow"; t: number;
  wallsAfter: number[]; targetBefore: number; targetAfter: number;
  flipped?: number[]; added?: number[] };
export type Run = {
  schemaVersion: string;
  run: { agent: string; condition: string; seed: number };
  world: { grid: number; bounds: Bounds; wallsBefore: number[]; target: number;
           change?: Change };
  frames: Frame[];
  checks: Check[];
  summary: { learnSteps: number; recoverSteps: number | null;
             finalArrival: number; finalRoute: number | null; steps: number };
};

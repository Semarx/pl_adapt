/** Recordings are imported, not fetched, so the page works opened from disk. */
import type { Run } from "./types";

const mods = import.meta.glob("../public/recordings_fp/*.json",
  { eager: true, import: "default" }) as Record<string, Run>;

export const RUNS: Record<string, Run[]> = {};
for (const r of Object.values(mods)) {
  (RUNS[r.run.condition] ??= []).push(r);
}
for (const k of Object.keys(RUNS)) RUNS[k].sort((a, b) => a.run.seed - b.run.seed);

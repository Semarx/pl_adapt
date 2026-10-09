import { useState } from "react";
import Stage from "./Stage";
import { RUNS } from "./data";

type Tab = "base" | "goal" | "shift" | "grow" | "slip";

const TABS: Array<{ id: Tab; label: string; h: string; p: string }> = [
  { id: "base", label: "1 · learning",
    h: "Learning a building from nothing",
    p: "A 100 × 100 building with 15% walls, about 8,500 open squares. The robot is told nothing — not the layout, not the size. It walks, records which square leads to which, and plans every route from that record." },
  { id: "goal", label: "2 · the job changes",
    h: "The job changes",
    p: "The building is learned once. Then the target moves. Nothing about the building changed — only what the robot is asked to do." },
  { id: "shift", label: "3 · the walls move",
    h: "The walls move",
    p: "One fifth of the inner walls are moved: corridors close and solid ground opens. The robot is not told. Part of what it knew is now wrong, and the only way to find out where is to walk." },
  { id: "grow", label: "4 · the building grows",
    h: "The building grows",
    p: "New ground is added on all four sides, 39% more floor, and the next target is in the new part. Nothing the robot knew became false; there is simply more of it. It is not told." },
  { id: "slip", label: "5 · one move in ten goes wrong",
    h: "One move in ten goes wrong",
    p: "Not a change but a noisy world: one move in ten lands on a random neighbouring square, and the robot is not told which. A check of robustness, not of adaptation." },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("base");
  const [sel, setSel] = useState(0);
  const t = TABS.find(x => x.id === tab)!;
  const runs = RUNS[tab] ?? [];

  return (
    <div className="app">
      <div className="tabs">
        {TABS.map(x => (
          <button key={x.id} className={tab === x.id ? "on" : ""}
                  onClick={() => { setTab(x.id); setSel(0); }}>{x.label}</button>
        ))}
      </div>
      <header>
        <div>
          <h1>{t.h}</h1>
          <p>{t.p}</p>
        </div>
        <div className="seeds">
          {runs.map((_, n) => (
            <button key={n} className={n === sel ? "on" : ""} onClick={() => setSel(n)}>
              run {n + 1}
            </button>
          ))}
        </div>
      </header>
      {runs.length > 0 && <Stage key={`${tab}-${sel}`} runs={runs} sel={sel} />}
      <p className="note" style={{ marginTop: 18 }}>
        Each run is a different building and a different walk. Ready means 95 of 100
        test trips from random starting squares reach the target, on three checks in a
        row; a check happens every 20,000 steps. Test trips follow a plan built from
        the robot's own map and nothing else. Agent: <code>agent_pl_frontier_fp.py</code>,
        one build, 5 runs per test.
      </p>
    </div>
  );
}

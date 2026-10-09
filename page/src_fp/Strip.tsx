import { C } from "../src/lib/palette";
import type { Run } from "./types";

/** Arrival over time for every run of this test, the chosen one highlighted.
 *  The animation shows HOW it adapts; these lines show that it always does. */
export default function Strip({ runs, sel, t }: { runs: Run[]; sel: number; t: number }) {
  const W = 560, H = 230, L = 50, R = 10, T = 14, B = 30;
  const xMax = Math.max(...runs.map(r => r.summary.steps));
  const x = (s: number) => L + (s / xMax) * (W - L - R);
  const y = (v: number) => T + (1 - v) * (H - T - B);
  const step = xMax > 500_000 ? 200_000 : 100_000;
  const ticks: number[] = [];
  for (let s = 0; s <= xMax; s += step) ticks.push(s);
  const pts = (r: Run) => [`${x(0)},${y(0)}`,
    ...r.checks.map(c => `${x(c.t)},${y(c.rate)}`)].join(" ");
  const me = runs[sel];
  const ch = me.world.change;

  return (
    <div className="strip">
      <h3>Arrival at each check · all {runs.length} runs · this run highlighted</h3>
      <svg viewBox={`0 0 ${W} ${H}`}>
        {[0, 0.5, 1].map(v => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke={C.line} />
            <text x={L - 8} y={y(v) + 4} textAnchor="end" fontSize="13" fill={C.dim}>
              {Math.round(v * 100)}%</text>
          </g>
        ))}
        <line x1={L} x2={W - R} y1={y(0.95)} y2={y(0.95)} stroke={C.target}
              strokeDasharray="4 5" opacity="0.55" />
        <text x={W - R} y={y(0.95) - 5} textAnchor="end" fontSize="12" fill={C.target}
              opacity="0.8">ready: 95 of 100 trips</text>
        {ticks.map(s => (
          <text key={s} x={x(s)} y={H - 10} textAnchor="middle" fontSize="13" fill={C.dim}>
            {s === 0 ? "0" : `${s / 1000}k`}</text>
        ))}
        <text x={L} y={H - 10} textAnchor="end" fontSize="12" fill={C.dim} dx="-8">steps</text>
        {ch && <>
          <line x1={x(ch.t)} x2={x(ch.t)} y1={T} y2={H - B} stroke="#d65a4a"
                strokeDasharray="3 4" opacity="0.8" />
          <text x={x(ch.t) + 5} y={T + 12} fontSize="12" fill="#d65a4a">the change</text>
        </>}
        {runs.map((r, k) => k === sel ? null : (
          <polyline key={k} points={pts(r)} fill="none" stroke="#4b5d73" strokeWidth="1.6" />
        ))}
        <polyline points={pts(me)} fill="none" stroke={C.pl} strokeWidth="3" />
        <line x1={x(Math.min(t, xMax))} x2={x(Math.min(t, xMax))} y1={T} y2={H - B}
              stroke="#ffffff" strokeWidth="1.5" opacity="0.9" />
      </svg>
    </div>
  );
}

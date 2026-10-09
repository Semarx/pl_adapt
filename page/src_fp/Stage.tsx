import { useEffect, useMemo, useRef, useState } from "react";
import { C } from "../src/lib/palette";
import type { Run } from "./types";
import Strip from "./Strip";

const WRONG = "rgba(214,90,74,0.88)";
const NEWG = "#3b3560";              // new ground, not yet walked
const ROUTE_OK = "rgba(255,255,255,0.9)";
const ROUTE_BAD = "rgba(232,161,58,0.95)";

type Phase = "learn" | "move" | "adapt" | "done";
const k = (n: number) => Math.round(n).toLocaleString();

function timing(run: Run) {
  return run.world.change
    ? { learn: 7000, move: 1600, adapt: 8500, hold: 1500 }
    : { learn: 10000, move: 0, adapt: 0, hold: 1500 };
}

function simAt(run: Run, ms: number) {
  const T = timing(run);
  const ch = run.world.change;
  const end = run.summary.steps;
  const learnEnd = ch ? ch.t : end;
  if (ms < T.learn) return { phase: "learn" as Phase, t: (ms / T.learn) * learnEnd, flash: 0 };
  if (ch && ms < T.learn + T.move) {
    const p = (ms - T.learn) / T.move;
    return { phase: "move" as Phase, t: ch.t, flash: Math.sin(p * Math.PI) };
  }
  if (ch && ms < T.learn + T.move + T.adapt) {
    const p = (ms - T.learn - T.move) / T.adapt;
    return { phase: "adapt" as Phase, t: ch.t + p * (end - ch.t), flash: 0 };
  }
  return { phase: "done" as Phase, t: end, flash: 0 };
}

/** Everything that does not depend on time, computed once per run. */
function prep(run: Run) {
  const ch = run.world.change;
  const wb = new Set(run.world.wallsBefore);
  const wa = ch && ch.kind !== "goal" ? new Set(ch.wallsAfter) : wb;
  const added = new Set(ch?.added ?? []);
  const flipped = new Set(ch?.flipped ?? []);
  const vOrder: number[] = [], vCount: number[] = [];
  const fOrder: number[] = [], fCount: number[] = [], ft: number[] = [];
  for (const fr of run.frames) {
    for (const x of fr.n) vOrder.push(x);
    for (const x of fr.f) fOrder.push(x);
    vCount.push(vOrder.length); fCount.push(fOrder.length); ft.push(fr.t);
  }
  return { wb, wa, added, flipped, vOrder, vCount, fOrder, fCount, ft };
}

function frameAt(ft: number[], t: number) {
  let lo = 0, hi = ft.length - 1, j = -1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (ft[m] <= t) { j = m; lo = m + 1; } else hi = m - 1;
  }
  return j;
}

export default function Stage({ runs, sel }: { runs: Run[]; sel: number }) {
  const run = runs[sel];
  const P = useMemo(() => prep(run), [run]);
  const T = timing(run);
  const total = T.learn + T.move + T.adapt + T.hold;
  const ch = run.world.change;
  const G = run.world.grid;

  const [ms, setMs] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);

  useEffect(() => { setMs(0); setPlaying(true); }, [run]);
  useEffect(() => {
    if (!playing) return;
    let raf = 0, last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) * speed; last = now;
      setMs(v => {
        const n = v + dt;
        if (n >= total) { setPlaying(false); return total; }
        raf = requestAnimationFrame(tick);
        return n;
      });
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, total]);

  const st = simAt(run, ms);
  const j = frameAt(P.ft, st.t);
  const nv = j < 0 ? 0 : P.vCount[j];
  const nf = j < 0 ? 0 : P.fCount[j];
  const agent = j < 0 ? null : run.frames[j].a;
  const after = st.phase !== "learn";
  const target = after && ch ? ch.targetAfter : run.world.target;
  // the latest check at or before now, for the CURRENT target only
  const chk = [...run.checks].reverse().find(c => c.t <= st.t + 1e-6 && c.target === target)
    ?? null;
  const latest = [...run.checks].reverse().find(c => c.t <= st.t + 1e-6) ?? null;

  // counts for the caption
  const fixedSet = useMemo(() => new Set(P.fOrder.slice(0, nf)), [P, nf]);
  const visSet = useMemo(() => new Set(P.vOrder.slice(0, nv)), [P, nv]);
  const wrongLeft = ch?.kind === "shift" ? P.flipped.size - fixedSet.size : 0;
  let newLeft = 0;
  if (ch?.kind === "grow") for (const x of P.added) if (!visSet.has(x)) newLeft++;

  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const dpr = window.devicePixelRatio || 1;
    const w = el.clientWidth, h = el.clientHeight;
    el.width = w * dpr; el.height = h * dpr;
    const ctx = el.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const b = run.world.bounds;
    const rows = b.rMax - b.rMin, cols = b.cMax - b.cMin;
    const cell = Math.min(w / cols, h / rows);
    const ox = (w - cell * cols) / 2, oy = (h - cell * rows) / 2;
    const size = Math.max(cell - 0.2, 0.5);
    const cx = (id: number) => ox + ((id % G) - b.cMin + 0.5) * cell;
    const cy = (id: number) => oy + (Math.floor(id / G) - b.rMin + 0.5) * cell;
    const walls = after ? P.wa : P.wb;

    for (let r = b.rMin; r < b.rMax; r++) {
      for (let c = b.cMin; c < b.cMax; c++) {
        const id = r * G + c;
        const x = ox + (c - b.cMin) * cell, y = oy + (r - b.rMin) * cell;
        if (walls.has(id)) { ctx.globalAlpha = 1; ctx.fillStyle = C.wall; }
        else if (visSet.has(id)) { ctx.globalAlpha = 0.55; ctx.fillStyle = C.pl; }
        else if (after && P.added.has(id)) { ctx.globalAlpha = 1; ctx.fillStyle = NEWG; }
        else { ctx.globalAlpha = 1; ctx.fillStyle = C.unknown; }
        ctx.fillRect(x, y, size, size);
      }
    }
    ctx.globalAlpha = 1;
    // what it now believes wrongly: flipped squares it has not yet stood beside
    if (after && P.flipped.size) {
      ctx.fillStyle = WRONG;
      for (const id of P.flipped) if (!fixedSet.has(id))
        ctx.fillRect(cx(id) - cell / 2, cy(id) - cell / 2, size, size);
    }
    if (st.flash > 0) {
      ctx.globalAlpha = 0.75 * st.flash; ctx.fillStyle = "#ffffff";
      for (const id of (P.flipped.size ? P.flipped : P.added))
        ctx.fillRect(cx(id) - cell / 2, cy(id) - cell / 2, size, size);
      ctx.globalAlpha = 1;
    }
    // a test trip from the latest check, planned from the agent's own map
    if (chk && chk.route.length > 1) {
      ctx.strokeStyle = chk.arrived ? ROUTE_OK : ROUTE_BAD;
      ctx.lineWidth = Math.max(1.6, cell * 0.42);
      ctx.lineJoin = "round"; ctx.lineCap = "round";
      ctx.beginPath();
      chk.route.forEach((id, i) => i ? ctx.lineTo(cx(id), cy(id)) : ctx.moveTo(cx(id), cy(id)));
      ctx.stroke();
      ctx.fillStyle = ROUTE_OK;
      ctx.beginPath(); ctx.arc(cx(chk.route[0]), cy(chk.route[0]), Math.max(3, cell * 0.8), 0, 7);
      ctx.fill();
    }
    // the old target, once it has moved
    if (after && ch?.kind === "goal") {
      ctx.strokeStyle = C.target; ctx.globalAlpha = 0.45; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(cx(ch.targetBefore), cy(ch.targetBefore), Math.max(6, cell * 2.2), 0, 7);
      ctx.stroke(); ctx.globalAlpha = 1;
    }
    ctx.fillStyle = C.target;
    ctx.fillRect(cx(target) - cell * 1.1, cy(target) - cell * 1.1, cell * 2.2, cell * 2.2);
    ctx.strokeStyle = C.target; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx(target), cy(target), Math.max(7, cell * 3), 0, 7); ctx.stroke();
    if (agent != null && st.phase !== "done") {
      ctx.fillStyle = "#ffffff";
      ctx.beginPath(); ctx.arc(cx(agent), cy(agent), Math.max(3.5, cell * 1.1), 0, 7); ctx.fill();
      ctx.strokeStyle = C.pl; ctx.lineWidth = 2; ctx.stroke();
    }
  }, [run, P, st.t, st.flash, st.phase, visSet, fixedSet, chk, agent, after, target, ch, G]);

  // ---- the four numbers -------------------------------------------------
  const learnTile = st.phase === "learn" ? k(st.t) : k(run.summary.learnSteps);
  const recoverTile = !ch ? "no change"
    : st.phase === "learn" || st.phase === "move" ? "—"
    : st.phase === "done" ? k(run.summary.recoverSteps ?? 0)
    : k(st.t - ch.t);
  const arrTile = latest ? `${Math.round(latest.rate * 100)}%` : "…";
  const routeTile = latest && latest.ratio != null ? `${latest.ratio.toFixed(2)}×` : "…";

  // ---- words --------------------------------------------------------------
  const cond = run.run.condition;
  let caption: JSX.Element | string = "learning the building";
  if (st.phase === "move") caption = <b>{ch?.kind === "goal" ? "the target moves"
    : ch?.kind === "shift" ? "the walls are moved" : "the building grows"}</b>;
  if (st.phase === "adapt" || st.phase === "done") {
    caption = ch?.kind === "shift" ? `${wrongLeft.toLocaleString()} squares it still believes wrongly`
      : ch?.kind === "grow" ? `${newLeft.toLocaleString()} new squares not yet walked`
      : ch?.kind === "goal" ? "same building, new target" : "learning the building";
  }
  if (st.phase === "done" && !ch) caption = "ready";

  const S = run.summary;
  const pct = (v: number) => `${Math.round(v * 100)} of 100`;
  const rr = S.finalRoute != null ? `${S.finalRoute.toFixed(2)}×` : "—";
  let verdict: JSX.Element;
  if (st.phase === "learn") {
    verdict = <span className="wait">{cond === "slip"
      ? "Learning the building while one move in ten lands somewhere else. It is not told which."
      : "Learning the building. It is told nothing — not the layout, not the size."}</span>;
  } else if (st.phase === "move") {
    verdict = <>{ch?.kind === "goal" ? <>The target moves. <b>Nothing about the building changed.</b></>
      : ch?.kind === "shift" ? <><b>{P.flipped.size / 2} inner walls</b> just moved. It is not told.</>
      : <>New ground on all four sides, <b>{P.added.size.toLocaleString()} squares</b>, and the next target is in it. It is not told.</>}</>;
  } else if (st.phase === "adapt") {
    verdict = ch?.kind === "goal"
      ? <>The map holds no goal, so only the plan is rebuilt. Nothing about the building is relearned.</>
      : ch?.kind === "shift"
        ? <>What it knew is now partly wrong. It finds out where only by walking past it, and repairs each place where it stands.</>
        : <>Nothing it knew became false — there is simply more. It walks into the new part and adds it to the map.</>;
  } else {
    verdict = !ch
      ? <>Ready after <b className="mult">&nbsp;{k(S.learnSteps)}&nbsp;</b> steps: {pct(S.finalArrival)} test trips arrive, routes {rr} the shortest{cond === "slip" ? " — longer, because one move in ten goes astray on the trips too" : ""}.</>
      : ch.kind === "goal"
        ? <>At the first check after the move, {pct(run.checks.find(c => c.t > ch.t)?.rate ?? 0)} trips reach the new target. <b className="mult">&nbsp;No extra learning.&nbsp;</b></>
        : <>Back to {pct(S.finalArrival)} trips, routes {rr} the shortest, after <b className="mult">&nbsp;{k(S.recoverSteps ?? 0)}&nbsp;</b> more steps. Nothing was reset, resized or retrained.</>;
  }
  const ended = st.phase === "done";

  return (
    <div className="objs">
      <div className="fpstage">
        <div className="gside">
          <div className="fhead"><span className="name" style={{ color: C.pl }}>PL</span>
            <span style={{ color: C.dim, fontSize: 12 }}>run {sel + 1} · {k(st.t)} steps walked</span></div>
          <canvas ref={ref} />
          <div className="gcap">{caption}</div>
        </div>
        <div className="fpright">
          <div className="hero3 hero4">
            <div className="h"><div className="hv">{learnTile}</div>
              <div className="hl">steps to learn the building</div></div>
            <div className="h"><div className="hv">{recoverTile}</div>
              <div className="hl">steps to be ready again</div></div>
            <div className="h"><div className="hv">{arrTile}</div>
              <div className="hl">test trips that arrive</div></div>
            <div className="h"><div className="hv">{routeTile}</div>
              <div className="hl">route length vs shortest</div></div>
          </div>
          <Strip runs={runs} sel={sel} t={st.t} />
          <div className={"verdict on" + (ended ? " ended" : "")}><div>{verdict}</div></div>
        </div>
      </div>

      <div className="controls">
        <button className="play" onClick={() => { if (ended) setMs(0); setPlaying(p => !p); }}>
          {playing ? "❚❚" : ended ? "↻" : "▶"}
        </button>
        <input className="scrub" type="range" min={0} max={total} value={ms}
               onChange={e => { setPlaying(false); setMs(+e.target.value); }} />
        <div className="clock">{st.phase === "learn" ? "learning"
          : st.phase === "move" ? "the change" : st.phase === "adapt" ? "after the change" : "done"}</div>
        <select value={speed} onChange={e => setSpeed(+e.target.value)}>
          {[0.25, 0.5, 1, 2].map(v => <option key={v} value={v}>{v}×</option>)}
        </select>
      </div>

      <div className="legend">
        <Sw c="rgba(57,197,207,0.55)" l="ground it has walked" />
        <Sw c={C.unknown} l="not yet walked" />
        <Sw c={C.wall} l="wall" />
        {ch?.kind === "grow" && <Sw c={NEWG} l="new ground, not yet walked" />}
        {ch?.kind === "shift" && <Sw c={WRONG} l="squares it still believes wrongly" />}
        <Sw c={C.target} l="the target" />
        <Sw c="#ffffff" l="a test trip, planned from its own map" />
        <Sw c={ROUTE_BAD} l="a test trip that does not arrive" />
      </div>
    </div>
  );
}

function Sw({ c, l }: { c: string; l: string }) {
  return <div className="sw"><span style={{ background: c }} />{l}</div>;
}

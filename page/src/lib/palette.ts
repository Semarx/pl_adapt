export const C = {
  bg: "#0b0f14",
  panel: "#121a24",
  line: "#1f2b39",
  text: "#dbe6f2",
  dim: "#7387a0",

  wall: "#182029",
  unknown: "#232e3c",   // ground the agent has not stood on
  known: "#2f6d8f",     // ground it has
  target: "#3fb950",
  agent: "#ffffff",

  pl: "#39c5cf",
  dyna: "#e8a13a",
  done: "#3fb950",
  model: "#b389f5",   // the control: a learned model plus a planner
} as const;

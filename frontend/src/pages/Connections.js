import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getConnections } from "../api";

const FALLBACK_GRAPH = {
  nodes: [
    { id: "1", title: "Meeting notes — Q2 planning", group: 2 },
    { id: "2", title: "Research: vector embeddings", group: 1 },
    { id: "3", title: "Book notes — Thinking Fast and Slow", group: 3 },
    { id: "4", title: "Notes on information retrieval", group: 1 },
  ],
  links: [
    { source: "2", target: "4", value: 0.88 },
    { source: "1", target: "2", value: 0.61 },
    { source: "1", target: "4", value: 0.55 },
    { source: "3", target: "1", value: 0.38 },
  ],
};

const GROUP_COLORS = {
  1: "#00e5ff",
  2: "#bf5af2",
  3: "#32d74b",
  4: "#ff9f0a",
};
const DEFAULT_COLOR = "#4a4a6a";

function nodeColor(group) {
  return GROUP_COLORS[group] ?? DEFAULT_COLOR;
}

function buildPositions(nodes, cx, cy, radius) {
  return nodes.reduce((acc, node, i) => {
    const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
    acc[node.id] = {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
    return acc;
  }, {});
}

function truncate(str, max = 22) {
  return str.length > max ? str.slice(0, max) + "…" : str;
}

export default function Connections() {
  const navigate = useNavigate();
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getConnections()
      .then((data) => setGraph(data))
      .catch(() => setGraph(FALLBACK_GRAPH))
      .finally(() => setLoading(false));
  }, []);

  const W = 760, H = 480;
  const cx = W / 2, cy = H / 2;

  return (
    <div className="min-h-screen">
      <header
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid #1a1a2e" }}
      >
        <a href="/" className="mono text-base font-bold tracking-tight neon-cyan" style={{ textDecoration: "none" }}>
          note<span style={{ color: "#bf5af2", textShadow: "0 0 8px rgba(191,90,242,0.55)" }}>search</span>
          <span style={{ color: "#3a3a5a" }}>.app</span>
        </a>
        <nav className="flex gap-6 text-sm">
          <a href="/" className="mono text-xs hover:text-white transition-colors" style={{ color: "#4a4a6a" }}>home</a>
          <a href="/connections" className="mono text-xs" style={{ color: "#00e5ff", textShadow: "0 0 8px rgba(0,229,255,0.4)" }}>connections</a>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-6 pt-10 pb-20">
        <div className="mb-8">
          <p className="mono text-xs mb-1" style={{ color: "#3a3a5a", letterSpacing: "0.15em" }}>
            note graph
          </p>
          <h1 className="mono text-2xl font-bold gradient-text">connections</h1>
          <p className="text-sm mt-2" style={{ color: "#4a4a6a" }}>
            notes linked by semantic similarity — click any node to open it
          </p>
        </div>

        {loading && (
          <p className="mono text-xs text-center py-20" style={{ color: "#3a3a5a" }} role="status" aria-label="loading">
            building graph...
          </p>
        )}

        {error && !loading && (
          <div
            className="rounded-xl px-4 py-3 mono text-xs"
            role="alert"
            style={{ background: "rgba(255,45,85,0.07)", border: "1.5px solid rgba(255,45,85,0.2)", color: "#ff2d55" }}
          >
            something went wrong — {error}
          </div>
        )}

        {!loading && graph && graph.nodes.length === 0 && (
          <div className="text-center py-20">
            <p className="mono text-xs mb-1" style={{ color: "#3a3a5a" }}>// no connections yet</p>
            <p className="text-sm" style={{ color: "#252540" }}>
              upload more notes to start seeing relationships
            </p>
          </div>
        )}

        {!loading && graph && graph.nodes.length > 0 && (
          <div
            className="rounded-xl overflow-hidden"
            style={{ background: "#0a0a14", border: "1.5px solid #1a1a2e" }}
            data-testid="graph-container"
          >
            <svg
              viewBox={`0 0 ${W} ${H}`}
              width="100%"
              style={{ display: "block" }}
              aria-label="Note connections graph"
            >
              <defs>
                {graph.nodes.map((node) => {
                  const color = nodeColor(node.group);
                  return (
                    <radialGradient key={node.id} id={`glow-${node.id}`} cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor={color} stopOpacity="0.35" />
                      <stop offset="100%" stopColor={color} stopOpacity="0" />
                    </radialGradient>
                  );
                })}
              </defs>

              {(() => {
                const radius = Math.min(190, Math.max(100, 40 * graph.nodes.length));
                const positions = buildPositions(graph.nodes, cx, cy, radius);

                return (
                  <>
                    {graph.links.map((link, i) => {
                      const s = positions[link.source];
                      const t = positions[link.target];
                      if (!s || !t) return null;
                      return (
                        <line
                          key={i}
                          x1={s.x} y1={s.y}
                          x2={t.x} y2={t.y}
                          stroke="#00e5ff"
                          strokeOpacity={0.1 + link.value * 0.55}
                          strokeWidth={0.5 + link.value * 1.5}
                          data-testid="graph-edge"
                        />
                      );
                    })}

                    {graph.nodes.map((node) => {
                      const pos = positions[node.id];
                      const color = nodeColor(node.group);
                      const isHovered = hovered === node.id;

                      return (
                        <g
                          key={node.id}
                          transform={`translate(${pos.x},${pos.y})`}
                          onClick={() => navigate(`/note/${node.id}`)}
                          onMouseEnter={() => setHovered(node.id)}
                          onMouseLeave={() => setHovered(null)}
                          style={{ cursor: "pointer" }}
                          data-testid="graph-node"
                          aria-label={node.title}
                        >
                          <circle r={isHovered ? 28 : 22} fill={`url(#glow-${node.id})`} />
                          <circle
                            r={isHovered ? 8 : 6}
                            fill={isHovered ? color : "#0e0e1c"}
                            stroke={color}
                            strokeWidth={isHovered ? 2 : 1.5}
                            style={{
                              filter: isHovered ? `drop-shadow(0 0 6px ${color})` : "none",
                            }}
                          />
                          <text
                            y={isHovered ? 22 : 18}
                            textAnchor="middle"
                            fill={isHovered ? color : "#4a4a6a"}
                            fontSize={isHovered ? 10 : 9}
                            fontFamily="'Space Mono', monospace"
                            style={{
                              textShadow: isHovered ? `0 0 6px ${color}` : "none",
                              pointerEvents: "none",
                            }}
                          >
                            {truncate(node.title)}
                          </text>
                        </g>
                      );
                    })}
                  </>
                );
              })()}
            </svg>

            <div
              className="px-5 py-3 flex items-center gap-6 flex-wrap"
              style={{ borderTop: "1px solid #1a1a2e" }}
            >
              {Object.entries(GROUP_COLORS).map(([group, color]) => (
                <span key={group} className="flex items-center gap-1.5 mono text-xs" style={{ color: "#3a3a5a" }}>
                  <span
                    className="inline-block w-2 h-2 rounded-full"
                    style={{ background: color, boxShadow: `0 0 4px ${color}` }}
                  />
                  group {group}
                </span>
              ))}
              <span className="mono text-xs ml-auto" style={{ color: "#252540" }}>
                {graph.nodes.length} notes · {graph.links.length} connections
              </span>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

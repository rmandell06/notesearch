import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { getConnections } from "../api";
import { gradientHex, gradientClass } from "../lib/colors";

const FALLBACK_GRAPH = {
  nodes: [
    { id: "1", title: "Q2 planning" },
    { id: "2", title: "Vector embeddings" },
    { id: "3", title: "Thinking, Fast and Slow" },
    { id: "4", title: "Information retrieval" },
  ],
  links: [
    { source: "2", target: "4", value: 0.88 },
    { source: "1", target: "2", value: 0.61 },
    { source: "1", target: "4", value: 0.55 },
    { source: "3", target: "1", value: 0.38 },
  ],
};

function layoutNodes(nodes, links, { width, height, iterations = 250 }) {
  const cx = width / 2, cy = height / 2;
  const n = nodes.length;
  const pos = nodes.map((_, i) => ({
    x: cx + Math.cos((i / n) * Math.PI * 2) * 100,
    y: cy + Math.sin((i / n) * Math.PI * 2) * 100,
    vx: 0, vy: 0,
  }));
  const idx = new Map(nodes.map((n, i) => [n.id, i]));
  for (let iter = 0; iter < iterations; iter++) {
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = pos[i].x - pos[j].x, dy = pos[i].y - pos[j].y;
        const d2 = Math.max(dx * dx + dy * dy, 30);
        const f = 9000 / d2; const d = Math.sqrt(d2);
        pos[i].vx += (dx / d) * f; pos[i].vy += (dy / d) * f;
        pos[j].vx -= (dx / d) * f; pos[j].vy -= (dy / d) * f;
      }
    }
    for (const link of links) {
      const a = idx.get(link.source), b = idx.get(link.target);
      if (a == null || b == null) continue;
      const dx = pos[b].x - pos[a].x, dy = pos[b].y - pos[a].y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      const f = (d - (160 - link.value * 70)) * 0.05;
      pos[a].vx += (dx / d) * f; pos[a].vy += (dy / d) * f;
      pos[b].vx -= (dx / d) * f; pos[b].vy -= (dy / d) * f;
    }
    for (let i = 0; i < n; i++) {
      pos[i].vx += (cx - pos[i].x) * 0.012;
      pos[i].vy += (cy - pos[i].y) * 0.012;
      pos[i].vx *= 0.85; pos[i].vy *= 0.85;
      pos[i].x += pos[i].vx; pos[i].y += pos[i].vy;
    }
  }
  return Object.fromEntries(nodes.map((n, i) => [n.id, pos[i]]));
}

export default function Connections() {
  const navigate = useNavigate();
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hovered, setHovered] = useState(null);
  const [minSim, setMinSim] = useState(0);

  useEffect(() => {
    setLoading(true);
    getConnections()
      .then((data) => setGraph(data && data.nodes?.length ? data : FALLBACK_GRAPH))
      .catch(() => setGraph(FALLBACK_GRAPH))
      .finally(() => setLoading(false));
  }, []);

  const W = 880, H = 560;
  const positions = useMemo(() => {
    if (!graph) return {};
    return layoutNodes(graph.nodes, graph.links, { width: W, height: H });
  }, [graph]);

  const filteredLinks = useMemo(
    () => (graph?.links ?? []).filter((l) => l.value >= minSim),
    [graph, minSim]
  );
  const linkedTo = useMemo(() => {
    if (!hovered || !graph) return new Set();
    const ids = new Set();
    for (const l of graph.links) {
      if (l.source === hovered) ids.add(l.target);
      if (l.target === hovered) ids.add(l.source);
    }
    return ids;
  }, [hovered, graph]);

  const hoveredNode = graph?.nodes.find((n) => n.id === hovered);
  const hoveredLinks = (graph?.links ?? [])
    .filter((l) => l.source === hovered || l.target === hovered)
    .map((l) => ({ otherId: l.source === hovered ? l.target : l.source, value: l.value }))
    .sort((a, b) => b.value - a.value);

  return (
    <AppShell>
      <header className="text-center mb-10 rise">
        <p className="eyebrow mb-3">Note graph</p>
        <h1 className="display" style={{ fontSize: "clamp(48px, 7vw, 88px)", margin: 0, marginBottom: 12 }}>
          Constellations<span style={{ color: "var(--accent)" }}>.</span>
        </h1>
        <p className="muted" style={{ fontSize: 15, maxWidth: 520, margin: "0 auto" }}>
          Each note is a star. Edges are cosine similarity from the trained encoder. Hover any node to highlight its neighbours.
        </p>
      </header>

      {loading && (
        <p className="serif italic text-center" style={{
          fontSize: 24, color: "var(--ink-muted)", padding: "60px 0",
        }}>building graph…</p>
      )}

      {!loading && graph && graph.nodes.length === 0 && (
        <div className="text-center" style={{ padding: "60px 0" }}>
          <p className="serif italic mb-2" style={{ fontSize: 28 }}>No connections yet.</p>
          <p className="muted" style={{ fontSize: 13 }}>Upload more notes to start seeing relationships.</p>
        </div>
      )}

      {!loading && graph && graph.nodes.length > 0 && (
        <>
          <div className="glass-2 r-xl mb-6 fade" style={{ overflow: "hidden" }}>
            {/* Toolbar */}
            <div className="row between" style={{ padding: "14px 20px", borderBottom: "1px solid var(--hairline)" }}>
              <div className="row gap-4">
                <span className="eyebrow">Min similarity</span>
                <input
                  type="range" min="0" max="1" step="0.05"
                  value={minSim}
                  onChange={(e) => setMinSim(parseFloat(e.target.value))}
                  style={{ width: 140, accentColor: "var(--accent)" }}
                  aria-label="Minimum similarity threshold"
                />
                <span className="muted tabular" style={{ fontSize: 12 }}>{Math.round(minSim * 100)}%</span>
              </div>
              <span className="subtle" style={{ fontSize: 12 }}>
                {graph.nodes.length} notes · {filteredLinks.length} links
              </span>
            </div>

            {/* SVG */}
            <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: "block", aspectRatio: `${W}/${H}` }}
                 aria-label="Note connections graph">
              <defs>
                {graph.nodes.map((node) => (
                  <radialGradient key={node.id} id={`glow-${node.id}`} cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor={gradientHex(node.id ?? node.title)} stopOpacity="0.45" />
                    <stop offset="100%" stopColor={gradientHex(node.id ?? node.title)} stopOpacity="0" />
                  </radialGradient>
                ))}
              </defs>

              {filteredLinks.map((link, i) => {
                const s = positions[link.source], t = positions[link.target];
                if (!s || !t) return null;
                const isHi = hovered && (link.source === hovered || link.target === hovered);
                const isDimmed = hovered && !isHi;
                return (
                  <line key={i}
                    x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                    stroke={isHi ? "var(--accent)" : "var(--ink-soft)"}
                    strokeOpacity={isDimmed ? 0.05 : 0.15 + link.value * 0.4}
                    strokeWidth={0.5 + link.value * 2}
                    data-testid="graph-edge"
                  />
                );
              })}

              {graph.nodes.map((node) => {
                const pos = positions[node.id]; if (!pos) return null;
                const color = gradientHex(node.id ?? node.title);
                const isH = hovered === node.id;
                const isLinked = linkedTo.has(node.id);
                const isDimmed = hovered && !isH && !isLinked;
                return (
                  <g key={node.id} transform={`translate(${pos.x},${pos.y})`}
                     onClick={() => navigate(`/note/${node.id}`)}
                     onMouseEnter={() => setHovered(node.id)}
                     onMouseLeave={() => setHovered(null)}
                     style={{ cursor: "pointer", opacity: isDimmed ? 0.25 : 1, transition: "opacity 200ms" }}
                     data-testid="graph-node" aria-label={node.title}
                  >
                    <circle r={isH ? 38 : 28} fill={`url(#glow-${node.id})`} />
                    <circle r={isH ? 12 : 9} fill={color} stroke="var(--paper)" strokeWidth={2.5} />
                    {(isH || graph.nodes.length <= 14) && (
                      <text y={isH ? 30 : 24} textAnchor="middle"
                        fill={isH ? "var(--ink)" : "var(--ink-muted)"}
                        fontSize={isH ? 14 : 12}
                        fontFamily="var(--font-display)"
                        fontStyle="italic" fontWeight={500}
                        style={{ pointerEvents: "none" }}
                      >
                        {node.title.length > 28 ? node.title.slice(0, 27) + "…" : node.title}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Detail panel below the graph (centered column) */}
          {hoveredNode && (
            <div className="glass r-xl fade" style={{ padding: 24 }}>
              <div className="row gap-4 mb-5">
                <div
                  className={gradientClass(hoveredNode.id ?? hoveredNode.title)}
                  style={{ width: 56, height: 56, borderRadius: 12, flexShrink: 0 }}
                />
                <div className="flex-1">
                  <p className="eyebrow mb-1">Selected</p>
                  <p className="serif" style={{ fontSize: 19, fontWeight: 600, lineHeight: 1.2, margin: 0 }}>
                    {hoveredNode.title}
                  </p>
                </div>
                <button onClick={() => navigate(`/note/${hoveredNode.id}`)} className="btn-accent">
                  Open
                </button>
              </div>

              <p className="eyebrow mb-3">Connections ({hoveredLinks.length})</p>
              {hoveredLinks.length === 0 ? (
                <p className="serif italic muted" style={{ fontSize: 14 }}>
                  None at the current threshold.
                </p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {hoveredLinks.map(({ otherId, value }) => {
                    const node = graph.nodes.find((n) => n.id === otherId);
                    if (!node) return null;
                    return (
                      <li key={otherId}>
                        <button
                          onClick={() => navigate(`/note/${otherId}`)}
                          className="row gap-3 w-full"
                          style={{
                            padding: "8px 10px", borderRadius: 8, marginBottom: 4,
                            textAlign: "left", transition: "background 150ms",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(20,17,13,0.04)")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                        >
                          <div className={gradientClass(otherId)} style={{ width: 8, height: 8, borderRadius: 999, flexShrink: 0 }} />
                          <span className="flex-1 clamp-1 muted" style={{ fontSize: 13 }}>{node.title}</span>
                          <span className="tabular" style={{ fontSize: 12, fontWeight: 500, color: "var(--accent)" }}>
                            {Math.round(value * 100)}%
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}

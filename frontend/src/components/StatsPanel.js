import { useMemo } from "react";

/**
 * User-stat dashboard for the Home page.
 *
 * Computes stats from data the app already has — total notes, average
 * connection strength, the strongest pairing, etc. — plus a small
 * histogram of similarity distribution and a per-source bar chart.
 */
export default function StatsPanel({ notes = [], graph = null }) {
  const stats = useMemo(() => {
    const links = graph?.links ?? [];
    const nodes = graph?.nodes ?? [];

    const total = notes.length;
    const totalLinks = links.length;
    const avgSim = links.length
      ? links.reduce((s, l) => s + (l.value ?? 0), 0) / links.length
      : 0;
    const maxSim = links.length
      ? Math.max(...links.map((l) => l.value ?? 0))
      : 0;

    // Source distribution (text vs upload)
    const bySource = notes.reduce((acc, n) => {
      const k = (n.source || "text").toLowerCase();
      acc[k] = (acc[k] ?? 0) + 1;
      return acc;
    }, {});

    // Similarity histogram (5 buckets across 0..1)
    const buckets = [0, 0, 0, 0, 0];
    for (const l of links) {
      const v = Math.max(0, Math.min(0.999, l.value ?? 0));
      buckets[Math.floor(v * 5)]++;
    }
    const bucketsMax = Math.max(1, ...buckets);

    // Most-connected note (degree centrality)
    const degree = new Map();
    for (const l of links) {
      degree.set(l.source, (degree.get(l.source) ?? 0) + 1);
      degree.set(l.target, (degree.get(l.target) ?? 0) + 1);
    }
    let topNode = null, topDeg = 0;
    for (const [id, d] of degree.entries()) {
      if (d > topDeg) { topDeg = d; topNode = nodes.find((n) => n.id === id) || null; }
    }

    // Activity sparkline — counts per local day for the last DAYS days,
    // ordered oldest → newest. Notes whose date can't be parsed silently
    // drop out (they're old fallback data or otherwise malformed).
    const DAYS = 14;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dayBuckets = Array.from({ length: DAYS }, (_, i) => {
      const d = new Date(today);
      d.setDate(d.getDate() - (DAYS - 1 - i));
      return { date: d, count: 0 };
    });
    const dayMs = 24 * 60 * 60 * 1000;
    for (const note of notes) {
      const raw = note.created_at ?? note.date;
      const ts = new Date(raw);
      if (Number.isNaN(ts.getTime())) continue;
      ts.setHours(0, 0, 0, 0);
      const idx = DAYS - 1 - Math.floor((today - ts) / dayMs);
      if (idx >= 0 && idx < DAYS) dayBuckets[idx].count++;
    }
    const dayMax = Math.max(1, ...dayBuckets.map((b) => b.count));
    const recent7 = dayBuckets.slice(-7).reduce((s, b) => s + b.count, 0);

    return {
      total, totalLinks, avgSim, maxSim, bySource, buckets, bucketsMax,
      topNode, topDeg, dayBuckets, dayMax, recent7,
    };
  }, [notes, graph]);

  const sourceEntries = Object.entries(stats.bySource);
  const sourceMax = Math.max(1, ...sourceEntries.map(([, n]) => n));

  return (
    <div className="glass-2 r-xl rise" style={{ padding: 28 }}>
      <div className="row between mb-6" style={{ alignItems: "baseline" }}>
        <p className="eyebrow">Your library at a glance</p>
        {stats.topNode && (
          <p className="subtle" style={{ fontSize: 12 }}>
            Most-connected:{" "}
            <span className="serif italic" style={{ color: "var(--ink)" }}>{stats.topNode.title}</span>
          </p>
        )}
      </div>

      {/* Top-line stat tiles */}
      <div className="grid-4 gap-5 mb-8">
        <Stat label="Notes" value={stats.total} />
        <Stat label="Connections" value={stats.totalLinks} />
        <Stat label="Avg. similarity" value={pct(stats.avgSim)} muted />
        <Stat label="Strongest link" value={pct(stats.maxSim)} accent />
      </div>

      {/* Activity sparkline — last 14 days of uploads */}
      <Sparkline buckets={stats.dayBuckets} max={stats.dayMax} recent7={stats.recent7} />

      {/* Two viz blocks side by side */}
      <div className="grid-2 gap-6">
        {/* Histogram */}
        <div>
          <p className="eyebrow mb-3">Similarity distribution</p>
          <div className="row" style={{ alignItems: "flex-end", height: 96, gap: 6 }}>
            {stats.buckets.map((count, i) => {
              const h = count === 0 ? 4 : (count / stats.bucketsMax) * 96;
              return (
                <div key={i} className="flex-1 col" style={{ alignItems: "stretch" }}>
                  <div style={{ flex: 1 }} />
                  <div
                    style={{
                      height: h,
                      background: i === stats.buckets.length - 1 ? "var(--accent)" : `rgba(210, 74, 44, ${0.18 + i * 0.16})`,
                      borderRadius: 4,
                      transition: "height 600ms cubic-bezier(.2,.7,.2,1)",
                    }}
                    title={`${count} link${count === 1 ? "" : "s"} in ${i * 20}–${(i + 1) * 20}% range`}
                  />
                </div>
              );
            })}
          </div>
          <div className="row between mt-2 subtle" style={{ fontSize: 10 }}>
            <span>0%</span><span>20</span><span>40</span><span>60</span><span>80</span><span>100%</span>
          </div>
        </div>

        {/* Source bar chart */}
        <div>
          <p className="eyebrow mb-3">By source</p>
          {sourceEntries.length === 0 ? (
            <p className="subtle serif italic" style={{ fontSize: 13 }}>No notes yet.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {sourceEntries.map(([k, n]) => {
                const pctW = (n / sourceMax) * 100;
                return (
                  <li key={k} className="mb-3">
                    <div className="row between mb-1" style={{ fontSize: 12 }}>
                      <span style={{ textTransform: "capitalize", color: "var(--ink)" }}>{k}</span>
                      <span className="muted tabular">{n}</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${pctW}%` }} />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function Sparkline({ buckets, max, recent7 }) {
  // SVG canvas — fixed viewBox; CSS scales it to container width.
  const W = 560;
  const H = 60;
  const padX = 4;
  const innerW = W - padX * 2;
  const barW = innerW / buckets.length;
  const gap = 3;
  const firstLabel = buckets[0].date;
  const lastLabel = buckets[buckets.length - 1].date;
  const fmt = (d) => d.toLocaleDateString(undefined, { month: "short", day: "numeric" });

  return (
    <div className="mb-8">
      <div className="row between mb-3" style={{ alignItems: "baseline" }}>
        <p className="eyebrow">Activity · last 14 days</p>
        <p className="subtle" style={{ fontSize: 12 }}>
          <span className="tabular" style={{ color: "var(--ink)", fontWeight: 500 }}>
            {recent7}
          </span>{" "}
          this week
        </p>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        preserveAspectRatio="none"
        style={{ display: "block", height: 60 }}
        aria-label="Notes added per day, last 14 days"
      >
        {buckets.map((b, i) => {
          const h = b.count === 0 ? 2 : Math.max(2, (b.count / max) * (H - 4));
          const isToday = i === buckets.length - 1;
          // Subtle warm-coral fade across the 14-day axis. Today is full-saturation accent.
          const fill = isToday
            ? "var(--accent)"
            : `rgba(210, 74, 44, ${0.18 + (i / buckets.length) * 0.42})`;
          return (
            <rect
              key={i}
              x={padX + i * barW + gap / 2}
              y={H - h - 2}
              width={Math.max(2, barW - gap)}
              height={h}
              rx={2}
              fill={fill}
            >
              <title>
                {fmt(b.date)} — {b.count} note{b.count === 1 ? "" : "s"}
              </title>
            </rect>
          );
        })}
      </svg>

      <div className="row between mt-2 subtle" style={{ fontSize: 10 }}>
        <span>{fmt(firstLabel)}</span>
        <span>today · {fmt(lastLabel)}</span>
      </div>
    </div>
  );
}

function Stat({ label, value, accent = false, muted = false }) {
  return (
    <div>
      <p className="eyebrow mb-2">{label}</p>
      <p className="display" style={{
        fontSize: 44, lineHeight: 1, margin: 0,
        color: accent ? "var(--accent)" : muted ? "var(--ink-soft)" : "var(--ink)",
      }}>
        {value}
      </p>
    </div>
  );
}

function pct(v) {
  if (!v) return "0%";
  return `${Math.round(v * 100)}%`;
}

import katex from "katex";
import "katex/dist/katex.min.css";

/**
 * Render text with embedded LaTeX as a mix of plain spans and KaTeX-rendered
 * HTML. Detects:
 *
 *   $$ ... $$        display math
 *   $ ... $          inline math (single line, no nested $)
 *   \[ ... \]        display math
 *   \( ... \)        inline math
 *   \begin{env} ... \end{env}   display math (env in MATH_ENVS below)
 *
 * Anything we can't parse falls through as plain text. KaTeX itself runs
 * with `throwOnError: false`, so malformed LaTeX renders as a red-tinted
 * literal instead of crashing the whole note view.
 *
 * Linebreaks in surrounding prose are preserved via white-space: pre-wrap.
 */

const MATH_ENVS = [
  "equation", "equation*", "align", "align*", "gather", "gather*",
  "multline", "multline*", "split", "matrix", "pmatrix", "bmatrix",
  "vmatrix", "Vmatrix", "smallmatrix", "cases", "array",
];

const ENV_PATTERN = MATH_ENVS.map((e) => e.replace("*", "\\*")).join("|");
// Order matters: longer/more-specific patterns first so $$ wins over $.
const PATTERN = new RegExp(
  [
    "\\$\\$[\\s\\S]+?\\$\\$",                       // $$...$$
    "\\\\\\[[\\s\\S]+?\\\\\\]",                     // \[...\]
    `\\\\begin\\{(?:${ENV_PATTERN})\\}[\\s\\S]+?\\\\end\\{(?:${ENV_PATTERN})\\}`,
    "\\\\\\([\\s\\S]+?\\\\\\)",                     // \(...\)
    "\\$[^\\$\\n]+?\\$",                            // $...$
  ].join("|"),
  "g"
);

function renderTeX(latex, displayMode) {
  try {
    return katex.renderToString(latex, {
      displayMode,
      throwOnError: false,
      strict: "ignore",
      trust: false,
    });
  } catch {
    return null;
  }
}

function classify(match) {
  if (match.startsWith("$$")) {
    return { tex: match.slice(2, -2), display: true };
  }
  if (match.startsWith("\\[")) {
    return { tex: match.slice(2, -2), display: true };
  }
  if (match.startsWith("\\(")) {
    return { tex: match.slice(2, -2), display: false };
  }
  if (match.startsWith("\\begin")) {
    // Pass the whole environment block to KaTeX as display math.
    return { tex: match, display: true };
  }
  // Fallback: inline $...$
  return { tex: match.slice(1, -1), display: false };
}

export default function MathText({ text }) {
  if (!text) return null;
  const parts = [];
  let last = 0;
  PATTERN.lastIndex = 0;
  let m;
  while ((m = PATTERN.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ type: "text", value: text.slice(last, m.index) });
    }
    const { tex, display } = classify(m[0]);
    const html = renderTeX(tex, display);
    parts.push(html != null
      ? { type: "math", value: html, display }
      : { type: "text", value: m[0] });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ type: "text", value: text.slice(last) });

  return (
    <>
      {parts.map((p, i) => {
        if (p.type === "text") {
          return (
            <span key={i} style={{ whiteSpace: "pre-wrap" }}>{p.value}</span>
          );
        }
        const Tag = p.display ? "div" : "span";
        return (
          <Tag
            key={i}
            // KaTeX-rendered HTML — safe because KaTeX runs with trust=false
            // and strict=ignore, so user-controlled latex can't inject scripts.
            dangerouslySetInnerHTML={{ __html: p.value }}
            style={{ display: p.display ? "block" : "inline" }}
          />
        );
      })}
    </>
  );
}

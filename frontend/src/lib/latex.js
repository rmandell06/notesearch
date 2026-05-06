// Tiny preprocessor that takes a full LaTeX-document source and emits
// something MathText can render: extract the body, drop preamble noise,
// flatten environments to plain-text-with-bullets, and rescue commands
// that only make sense in math mode (\boxed) by wrapping them in $…$.
//
// This is not a real LaTeX engine. It handles the patterns we actually
// see in homework PDFs and pasted .tex files. Anything more exotic
// renders as plain text — better than raw source, less than ideal.

function findMatchingBrace(s, openIdx) {
  // openIdx points at '{' — return index of matching '}' or s.length
  let depth = 1;
  for (let i = openIdx + 1; i < s.length; i++) {
    if (s[i] === "{") depth++;
    else if (s[i] === "}") {
      depth--;
      if (depth === 0) return i;
    }
  }
  return s.length;
}

function wrapStandaloneBoxed(s) {
  // Track $-state so we don't double-wrap \boxed already inside math.
  let out = "";
  let i = 0;
  let state = 0; // 0 = prose, 1 = inside $, 2 = inside $$
  while (i < s.length) {
    if (state === 0 && s[i] === "$" && s[i + 1] === "$") {
      out += "$$"; i += 2; state = 2; continue;
    }
    if (state === 2 && s[i] === "$" && s[i + 1] === "$") {
      out += "$$"; i += 2; state = 0; continue;
    }
    if (state === 0 && s[i] === "$") {
      out += "$"; i++; state = 1; continue;
    }
    if (state === 1 && s[i] === "$") {
      out += "$"; i++; state = 0; continue;
    }
    if (state === 0 && s.startsWith("\\boxed{", i)) {
      const open = i + 6; // index of '{'
      const close = findMatchingBrace(s, open);
      out += `$\\boxed{${s.slice(open + 1, close)}}$`;
      i = close + 1;
      continue;
    }
    out += s[i];
    i++;
  }
  return out;
}

function looksLikeFullDocument(text) {
  return /\\documentclass\b|\\begin\{document\}/.test(text);
}

export function preprocessLatex(input) {
  if (!input || !looksLikeFullDocument(input)) return input;

  let s = input;

  // Body extraction: keep what's between \begin{document} and \end{document}.
  const docMatch = s.match(/\\begin\{document\}([\s\S]*?)\\end\{document\}/);
  if (docMatch) s = docMatch[1];

  // Preamble cruft (anywhere it lingers).
  s = s.replace(/\\documentclass(?:\[[^\]]*\])?\{[^}]+\}/g, "");
  s = s.replace(/\\usepackage(?:\[[^\]]*\])?\{[^}]+\}/g, "");
  s = s.replace(/\\newcommand\{[^}]+\}\{[^}]*\}/g, "");
  s = s.replace(/\\renewcommand\{[^}]+\}\{[^}]*\}/g, "");
  s = s.replace(/\\title\{[^}]*\}/g, "");
  s = s.replace(/\\author\{[^}]*\}/g, "");
  s = s.replace(/\\date\{[^}]*\}/g, "");
  s = s.replace(/\\maketitle\b/g, "");

  // Structural commands → plain-text equivalents.
  s = s.replace(/\\section\*?\{([^}]+)\}/g, "\n\n§ $1\n");
  s = s.replace(/\\subsection\*?\{([^}]+)\}/g, "\n\n› $1\n");
  s = s.replace(/\\pagebreak\b/g, "\n\n");
  s = s.replace(/\\newpage\b/g, "\n\n");
  s = s.replace(/\\noindent\b/g, "");

  // List environments — flatten to bullet points. Real numbering would
  // need a recursive parser; bullets are good enough.
  s = s.replace(/\\begin\{(?:enumerate|itemize|description)\}/g, "\n");
  s = s.replace(/\\end\{(?:enumerate|itemize|description)\}/g, "\n");
  s = s.replace(/\\item\b\s*/g, "\n• ");

  // Plain-text formatting. We don't render bold/italic — strip the wrapper.
  s = s.replace(/\\textbf\{([^{}]*)\}/g, "$1");
  s = s.replace(/\\textit\{([^{}]*)\}/g, "$1");
  s = s.replace(/\\emph\{([^{}]*)\}/g, "$1");
  s = s.replace(/\\underline\{([^{}]*)\}/g, "$1");

  // \\ used as a line-break inside prose. We leave it alone if immediately
  // adjacent to a $ (might be a math-mode artifact like \\$ that the user
  // typed in error — wrapping doesn't help, but at least we don't mangle
  // adjacent math).
  s = s.replace(/\\\\(?!\$)/g, "\n");

  // Spurious lone $\\$ from broken titles, etc. — drop.
  s = s.replace(/\$\s*\\\\\s*\$/g, " ");

  // \boxed{} only renders inside math; wrap any standalone occurrences.
  s = wrapStandaloneBoxed(s);

  // Collapse runs of whitespace at line boundaries; keep paragraph breaks.
  s = s
    .split("\n")
    .map((line) => line.replace(/[ \t]+/g, " ").trim())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return s;
}

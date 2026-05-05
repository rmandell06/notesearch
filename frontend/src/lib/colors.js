// Stable hash → cover-gradient index. Used so each note keeps the same
// generated color across renders without storing it server-side.
const NUM_GRADIENTS = 8;

export function gradientIndex(seed) {
  if (!seed) return 0;
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % NUM_GRADIENTS;
}

export function gradientClass(seed) {
  return `cover-grad-${gradientIndex(seed)}`;
}

const HEX_PALETTE = [
  "#a78bfa", "#06b6d4", "#10b981", "#f59e0b",
  "#ec4899", "#f97316", "#8b5cf6", "#14b8a6",
];

export function gradientHex(seed) {
  return HEX_PALETTE[gradientIndex(seed)];
}

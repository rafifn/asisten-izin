const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

/** "2026-11-15" -> "15 Nov 2026" (presentation only). */
export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return iso;
  return `${d} ${MONTHS[m - 1]} ${y}`;
}

const RISK_LABELS: Record<string, string> = {
  rendah: "rendah",
  menengah_rendah: "menengah rendah",
  menengah_tinggi: "menengah tinggi",
  tinggi: "tinggi",
};

/** "menengah_rendah" -> "menengah rendah" (presentation only). */
export function formatRisk(level: string): string {
  return RISK_LABELS[level] ?? level.replaceAll("_", " ");
}

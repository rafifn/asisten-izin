import type { AnalyzeResult, PermitItem } from "@/lib/api";

export const permit = (over: Partial<PermitItem> = {}): PermitItem => ({
  order: 1,
  name: "NIB",
  issuer: "OSS",
  description: "Nomor Induk Berusaha",
  how_to: "Daftar di oss.go.id",
  for_kbli: ["10791"],
  condition_note: null,
  regional_note: null,
  source: { regulation: "PP 28/2025", article: "Pasal 10", url: "https://example.test/pp28" },
  last_verified: "2026-11-01",
  ...over,
});

export const okResult = (over: Partial<AnalyzeResult> = {}): AnalyzeResult => ({
  activities: [
    {
      label: "produksi keripik",
      primary: {
        code: "10791",
        title: "Industri Kerupuk",
        definition: "Definisi resmi kerupuk.",
        reason: "Keripik termasuk kerupuk.",
        risk_level: "menengah rendah",
      },
      alternatives: [
        {
          code: "10793",
          title: "Industri Makanan Ringan",
          definition: "Definisi makanan ringan.",
          when_to_choose: "Jika bukan kerupuk.",
          risk_level: "rendah",
        },
      ],
    },
  ],
  permits: [permit()],
  assumptions: ["Dianggap usaha mikro/kecil"],
  scope_note: null,
  kbli_2020_mapping: null,
  data_as_of: "2026-11-15",
  stale_warning: false,
  request_id: "11111111-1111-1111-1111-111111111111",
  ...over,
});

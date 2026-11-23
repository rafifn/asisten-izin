# Data sources

All dates accessed: 2026-11-23. Downloaded files are kept outside git
(`.superpowers/sdd/2026-11-23-phase1/downloads/`) and are not part of the repo.

## 1. KBLI 2025 publication (titles cross-check, all definitions)

- Title: Klasifikasi Baku Lapangan Usaha Indonesia (KBLI) 2025
- Publisher: Badan Pusat Statistik (BPS). Katalog 1302017, Nomor Publikasi
  03100.25003, ISBN 978-602-438-530-9 (PDF), xiv+1021 halaman. Released
  2025-12-24. It sets out the classification established by Peraturan BPS
  Nomor 7 Tahun 2025, and includes Tabel 5.3, the corrections made after the
  Perban was issued.
- URL (publication page): https://www.bps.go.id/id/publication/2025/12/24/a9b2f130776c7bea36008556/klasifikasi-baku-lapangan-usaha-indonesia-kbli-2025-.html
  (file served as `BPS0000-klasifikasi_baku_lapangan_usaha_indonesia_kbli_2025.pdf`
  via the page's "Unduh Publikasi" link)
- Format: PDF, 1040 pages, sha256
  `169ec324af12c3e535d081dbe3789e019f9131ab81460357c2453fd0651a56b3`
- Supports: `kbli_scope.yaml`, the `definition` of every row (75 rows). Each
  definition is copied verbatim from the kelompok (5-digit) entry in the body
  (Kategori C pp. 300–335 and p. 394 for 21022, G pp. 612–645, I pp. 708–715,
  D for 35302, G for 46333). The uppercase headings in the body were used to check every
  `title`.
- Corrections: Tabel 5.3 (Koreksi kode KBLI 2025 pada Perban KBLI 2025) lists
  31 corrections. The only food-related ones are 104, 1041, 10413 and 1073
  (title change to "Industri Pengolahan Kakao; …"). None of these are rows
  here, though 10732 sits under 1073. The body text already includes the
  corrections.

## 2. KBLI 2020–2025 conversion table (titles, mapping)

- Title: Tabel Konversi Klasifikasi Baku Lapangan Usaha Indonesia (KBLI)
  2020—2025, Volume 2, 2026
- Publisher: Badan Pusat Statistik (BPS). Katalog 1302033, Nomor Publikasi
  03100.26007, xii+428 halaman. Published 2026-04-22.
- URL (publication page): https://www.bps.go.id/id/publication/2026/04/22/909d503355d2b7664e43dea8/tabel-konversi-kbli-2020---kbli-2025.html
  (file served as `BPS0000-tabel_konversi_kbli_2020_kbli_2025.pdf`)
- Format: PDF, 444 pages, sha256
  `29f17b3b133497a88c5bfd0eaa3f73c90233b9b95dd76dd0ea2ccaed31724949`
- Supports:
  - `kbli_scope.yaml` `title` (all 75 rows): the "Judul KBLI 2025" column of
    Lampiran 5 (Tabel Konversi Kelompok KBLI 2020—2025), in BPS's title case.
    For every row this title matches the publication's uppercase heading
    exactly, ignoring case.
  - `kbli_2020_map.yaml` (all 64 rows): taken from Lampiran 5 (KBLI 2020 →
    2025, kelompok level). It holds every 2020 kelompok that maps to at least
    one in-scope 2025 code, with all of that code's 2025 targets. Out-of-scope
    neighbour 21022 (Industri Produk Obat Bahan Alam untuk Manusia, which
    covers "pembuatan minuman jamu") has no mapping row: its only 2020 source,
    21022, maps only to 21022. The in-scope
    targets were checked against Lampiran 10 (KBLI 2025 → 2020): every pair
    matches in both directions.
  - **Partial row:** 2020 code `47911` (Perdagangan Eceran Melalui Media Untuk
    Komoditi Makanan, Minuman, Tembakau, Kimia, Farmasi, Kosmetik Dan Alat
    Laboratorium) also maps to 12 non-food 2025 codes: 47721–47729, 47773,
    47774 and 47779 (pharmacy, cosmetics, medical devices, chemicals). Those
    codes are not in `kbli_scope.yaml` (they are not food or beverage), so this
    row lists only its food, drink and tobacco targets.

## 3. Context sources (no data rows)

- BPS news, "BPS Rilis Klasifikasi Baku Lapangan Usaha Indonesia (KBLI) 2025",
  2025-12-19, HTML:
  https://www.bps.go.id/en/news/2025/12/19/828/bps-rilis-klasifikasi-baku-lapangan-usaha-indonesia--kbli--2025.html.
  It confirms that KBLI 2025 is set by Peraturan BPS 7/2025 and gives the
  short link s.bps.go.id/perbanKBLI2025. That link leads to a BPS Nextcloud
  folder ("2025.12.19 Rilis KBLI 2025"); the publication above was used
  instead.
- BPS news, "BPS Rilis Tabel Konversi … (KBLI) 2020-2025", 2026-04-27, HTML:
  https://www.bps.go.id/id/news/2026/04/27/897/bps-rilis-tabel-konversi-klasifikasi-baku-lapangan-usaha-indonesia--kbli--2020-2025-.html.
  It describes the conversion table (one-to-one, one-to-many, many-to-one) and
  says national implementation is due by 2026-06-18.

## Method notes

- Text was extracted with pdfplumber. The diagonal "https://www.bps.go.id"
  watermark characters (Arial-BoldMT, size > 15) were filtered out.
- Line wraps inside a paragraph were joined. A hyphen at the end of a line was
  kept and joined without a space (for example "buah-" + "buahan"). Bullets
  "–"/"−" are written as "- ". Each bullet and each "Kelompok ini …" block
  starts a new line. The wording, punctuation and BPS's own typos (for example
  "mempertemuan", "subgolonogan" in 56400) are unchanged. Italics are not
  kept.
- No code, title or definition comes from KBLI 2020 text, OSS, or any source
  other than the two BPS publications above.

## Unverified

None. Every row was read from the sources above.

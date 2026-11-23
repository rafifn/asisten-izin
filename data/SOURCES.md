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

## Method notes (KBLI files)

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

## Unverified (KBLI files)

None. Every row was read from the sources above.

---

# Permits and rules (`permits.yaml`, `rules.yaml`), added in Task 4

All accessed 2026-11-23. PP 5/2021 was not used anywhere.

## 4. PP 28/2025 (body and attachments)

- Title: Peraturan Pemerintah Nomor 28 Tahun 2025 tentang Penyelenggaraan
  Perizinan Berusaha Berbasis Risiko
- Publisher: Pemerintah RI, via JDIH BPK (peraturan.bpk.go.id)
- URL: https://peraturan.bpk.go.id/Details/319773/pp-no-28-tahun-2025
  (files from the page's "Download" links)
- Files read (PDF, scanned copies with a text layer; text extracted with
  pypdfium2):
  - Body, `PP Nomor 28 Tahun 2025.pdf`, 383 pages, sha256
    `8808de485eab2499cf3d8369921c097beaea68ae55aa767c61095d47a5a118fb`
  - Lampiran I.F (Perindustrian) part 1, I.F.1-700, sha256
    `fcdadc0ec9d831e0e4e8ddad18178ad972cee2c1a7aa79eff42a8ee6c7438ed3`
  - Lampiran I.G (Perdagangan), I.G.1-341, sha256
    `892a82d1631cd9ae581f6406259fe9724ba0475809d6ca2371e6a8aaef3a3d65`
  - Lampiran I.J to I.P (incl. I.J Kesehatan, I.L Pariwisata), sha256
    `17870d64d5b60ddfb7dd7a763a6aafea9e645df0850888beee135232b85e60d2`
  - Lampiran II (PB UMKU), sha256
    `83c1c651889194d176ac206b86a67f4a3a85da458820498693d84be590f094cb`
- Supports:
  - `permits.yaml`: kkpr (Pasal 8, 12, 13, 15, 17-19, 32),
    persetujuan-lingkungan-sppl (Pasal 8 ayat (3), 101, 220-222), nib (Pasal
    206, 207, 220, 234), sertifikat-standar (Pasal 221, 234),
    sertifikat-standar-terverifikasi (Pasal 11, 222-224, 234), pbg-slf
    (Pasal 10, 12, 13, 106-108), label-hsp (Lampiran I.L kewajiban; Lampiran
    II.J1 no. 7, p. II.J1.14-15), label-hsp-atau-slhs (Lampiran I.L; Lampiran
    II.J1 no. 5 and 7, p. II.J1.10-15), izin-edar-pangan-olahan and
    izin-edar-bpom (Lampiran II.J2 no. 6-8 and 11-12, p. II.J2.25-36).
  - `rules.yaml`: step order (Pasal 4, 8, 10, 11) and, through section 5, the
    risk level of every rule.
  - Cross-checks of the OSS data in section 5 against the attachment text
    (KBLI 2020 codes): I.L no. 13 (56101 Restoran: mikro menengah rendah with
    SLHS, kecil-besar menengah tinggi), 14 (56102 Warung/Rumah Makan), 15
    (56103 Kedai Makanan: HSP mikro, SLHS kecil), 16 (56104), 18 (56210: mikro
    and kecil menengah rendah, Label HSP), 19 (56290); I.F no. 40 (10531 es
    krim, rendah), 57 (10710, rendah), 60 (10723 sirop, menengah tinggi), 68
    (10750, menengah rendah), 71 (10763 teh, rendah), 78 (10792, rendah); I.G
    no. 83 (47222), 86 (47242), 90 (47249), all rendah. All match the OSS KBLI
    2025 pages.

## 5. OSS KBLI 2025 risk pages (risk level of every rule)

- Title: KBLI detail pages, Sistem OSS RBA (oss.go.id), version "KBLI 2025"
- Publisher: Kementerian Investasi dan Hilirisasi/BKPM (Lembaga OSS)
- Context: PP 28/2025 Lampiran I lists KBLI 2020 codes. OSS states it has
  applied KBLI 2025 to all new applications since 2026-06-15 (Peraturan BPS
  7/2025 and the Surat Edaran Bersama Menteri Investasi dan Hilirisasi/Kepala
  BKPM, Menteri Hukum and Kepala BPS). Each KBLI 2025 page lists, per "ruang
  lingkup" and business scale, the risk level, perizinan berusaha,
  persyaratan, kewajiban and kewenangan carried over from PP 28/2025 Lampiran
  I, plus the PB UMKU for the code. Sources for that context:
  https://oss.go.id/id/kbli (HTML) and the OSS news item "Memahami Transisi
  KBLI 2025 dalam Ekosistem Perizinan Berusaha", 2026-06-24,
  https://oss.go.id/berita/memahami-transisi-kbli-2025-dalam-ekosistem-perizinan-berusaha
  (HTML).
- Format: HTML (Next.js server-rendered page; the data block embedded in the
  page was read). Every page was checked to be "KBLI 2025" and its title
  matches `kbli_scope.yaml`.
- Supports: `risk_level` of all 300 rules, the presence of Sertifikat
  Standar, the hygiene permit (Label HSP / SLHS) per food-service code, and
  which codes list SPP-IRT vs only BPOM izin edar as PB UMKU. Rule rows cite
  the page of their code as `source_url` (except halal rows, see section 8,
  and the izin edar rows of 10762 and 10795, see section 6).
- Pages (micro / small risk per ruang lingkup as shown on 2026-11-23):

| Code | Ruang lingkup in OSS (micro / small risk) | URL |
|---|---|---|
| 10120 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/076ba047-e626-5942-914d-d719336484ab |
| 10218 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/2f65f6fe-6d9e-5751-9f24-cff969e2189e |
| 10296 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/6c31fbdc-30dd-5af4-85b8-87e3c8b8555f |
| 10301 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/68223e45-a514-5f73-bee4-3798b5f910b0 |
| 10302 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/2bc99f4d-b0e1-5b39-8a82-cb3222d4f8b8 |
| 10303 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/7bf1263b-87b5-5e58-a2fe-2bc70fb62dfd |
| 10304 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/5ac3a700-23ab-58da-9e04-b4af443160c8 |
| 10306 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/2827cbdd-db35-5941-8a48-91cb57da57ac |
| 10307 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/eea51c75-b579-5607-a7c7-0051050ade70 |
| 10308 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/49767c21-9599-5250-bd27-52fb6f2f9fec |
| 10309 | Pengolahan dan Pengawetan Kedelai dan Kaca...: Rendah / Rendah; Pengolahan dan Pengawetan Lainnya untuk Bu...: Rendah / Rendah; Pemanggangan berbagai jenis kacang, sepert...: Rendah / Rendah | https://oss.go.id/id/kbli/detail/3219bac2-7c61-5268-954c-870a726686cc |
| 10503 | Selain pracampur/premix es krim: Rendah / Rendah; Pracampur/premix es krim: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/d65a1411-5289-5657-ab20-85276b40e068 |
| 10504 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/a01d02a2-b80a-5ddc-8d20-69e7da14730d |
| 10509 | Pengolahan produk susu lainnya, seperti me...: Menengah Rendah / Menengah Rendah; Pembuatan laktosa: Tinggi / Tinggi | https://oss.go.id/id/kbli/detail/df436cfe-93f8-5254-8f32-131958dd4b52 |
| 10710 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/02df412b-ac74-56cc-bd6b-5fc92feb866c |
| 10722 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/8b634ab8-52cf-56e2-ae83-7acac0a38474 |
| 10723 | Seluruh: Menengah Tinggi / Menengah Tinggi | https://oss.go.id/id/kbli/detail/4a6a7b0e-fe47-5e7c-b29d-61b844281ff9 |
| 10732 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/84c42b2b-8bc7-5524-a8d8-a943231631fb |
| 10733 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/9b1da6ed-38e5-5b04-b961-c0110b8424f1 |
| 10739 | Pembuatan kembang gula termasuk kembang gu...: Rendah / Rendah; Pembuatan kembang gula lainnya seperti per...: Rendah / Rendah | https://oss.go.id/id/kbli/detail/54d9ca4d-8643-556e-b2e1-85fc101a6850 |
| 10740 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/97f48e51-d6dd-5b3d-927f-a41c160aa8b6 |
| 10750 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/de13f696-63bb-56ee-8e9f-37bb6307b388 |
| 10761 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/37180921-3574-5cf1-b936-ac54bed78d52 |
| 10762 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/b13c4d32-e2c9-594e-8f8b-b0fd79eac08f |
| 10771 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/3d6547e3-921b-5030-b67f-f06ca2c3a7d7 |
| 10779 | Pembuatan bumbu masakan, baik dalam keadaa...: Rendah / Rendah; Pembuatan petis, saus tiram, dan cuka makan.: Rendah / Rendah | https://oss.go.id/id/kbli/detail/c9c4b706-0732-5be8-bc6e-1e51d345caf8 |
| 10792 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/c20e4935-0a00-590b-a4c6-6e28f08aa84d |
| 10793 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/53e98c02-3fe0-521a-8c1c-9b072599c010 |
| 10794 | Pembuatan keripik/peyek dari berbagai maca...: Rendah / Rendah; Selain pembuatan keripik/peyek dari berbag...: Rendah / Rendah | https://oss.go.id/id/kbli/detail/f38670f7-a302-5f2f-b2dc-77fce993fa5d |
| 10795 | Pembuatan krimer nabati emulsi lemak nabat...: Rendah / Rendah; Pembuatan sari nabati dari berbagai jenis ...: Rendah / Rendah | https://oss.go.id/id/kbli/detail/e215a215-0f39-50b3-beeb-dc87e1e8be73 |
| 10796 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/d8b043f9-4a01-5d70-89a1-63cdd9d47fbc |
| 10797 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/3432d1e5-a7ea-593f-b776-28f099bc2395 |
| 10799 | Pembuatan ekstrak dan jus dari daging, ika...: Rendah / Rendah; Pembuatan pangan protein produk seperti pr...: Rendah / Rendah; Pembuatan produk makanan jadi lainnya yang...: Rendah / Rendah; Pembuatan pemanis buatan: Tinggi / Tinggi; Pembuatan gula stevia: Rendah / Rendah; Pembuatan bahan tambahan pangan (perisa).: Rendah / Rendah; Pembuatan bahan tambahan pangan yang hanya...: Rendah / Rendah | https://oss.go.id/id/kbli/detail/acec5d9d-7daf-5374-8f95-0a46faed81aa |
| 11053 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/2c41a51e-e500-5f61-885a-25160910872b |
| 11059 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/b14a74a0-bb6d-5d66-b457-3f0eb600322e |
| 47222 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/5b1a2970-f88d-5bc1-8e52-12432368a334 |
| 47242 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/d474c721-3aca-51af-88fd-91e8abd88d20 |
| 47243 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/fe19c160-02ab-5568-9d27-e32ed943aab3 |
| 47244 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/daf29649-baee-53a9-9c62-7c66d9de8d66 |
| 47245 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/30eb2934-1fa5-55ff-8e0a-86edc08cf53d |
| 47246 | Usaha Perdagangan eceran berbagai jenis ik...: Rendah / Rendah; Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/7fefb305-7904-5619-a32d-f07421480b4e |
| 47249 | Seluruh: Rendah / Rendah | https://oss.go.id/id/kbli/detail/4b0c4cb3-93bd-5932-96d7-14914ba67ec0 |
| 56101 | Restoran: Menengah Rendah / Menengah Tinggi; Rumah / Warung Makan: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/586aff30-3e89-5c99-9bd5-b2333439ebcb |
| 56102 | Kedai Makan: Menengah Rendah / Menengah Rendah; Penyediaan Makanan Keliling / Tempat Tidak...: Menengah Rendah / Menengah Rendah; Restoran dan Penyediaan Makanan Keliling L...: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/745ac82e-8336-5930-bc92-5176125b68d7 |
| 56210 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/b7bb1ae3-5f1b-5b92-9731-04e9653ca455 |
| 56290 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/02411e38-0091-5db6-b5b2-ec7bd17bca4d |
| 56303 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/6c75f121-83a3-5878-a849-621ba4dbeabb |
| 56304 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/6df07938-6bd6-5a19-840c-5d38cf21c5f4 |
| 56305 | Kedai Jamu/ Depot Jamu: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/b0287593-7582-539c-9880-21af0e63c00f |
| 56306 | Seluruh: Menengah Rendah / Menengah Rendah | https://oss.go.id/id/kbli/detail/52b2aee8-e2ba-52a5-9050-6d3f223fbafc |

## 6. Peraturan BPOM Nomor 4 Tahun 2024 (SPP-IRT)

- Title: Peraturan Badan Pengawas Obat dan Makanan Nomor 4 Tahun 2024 tentang
  Pedoman Penerbitan Sertifikat Pemenuhan Komitmen Produksi Pangan Olahan
  Industri Rumah Tangga (replaces Peraturan BPOM 22/2018)
- Publisher: BPOM, via sppirt.pom.go.id
- URL: https://sppirt.pom.go.id/uploads/regulasi/8b6f95b8e4c2385a433627a4bff97014.pdf
- Format: PDF, 70 pages, sha256
  `17dbfdd90c71aea2fb38aec915dabb8e7daf8cb905af2a81f156c39a638763b4`
- Supports: permit izin-edar-pangan-olahan (Pasal 3 incl. exemptions in ayat
  (3), 4, 5, 8, 9, 10, 15, 20; Lampiran I list of IRT food types, which
  includes "08 Kopi dan teh kering" and soy drink powder, the basis for using
  this permit for 10762 and 10795, whose OSS pages list no PB UMKU). Source URL
  of the izin edar rules for 10762 and 10795.

## 7. BPOM registrasi pangan olahan service page

- Title: "Layanan", Direktorat Registrasi Pangan Olahan
- Publisher: BPOM
- URL: https://registrasipangan.pom.go.id/layanan
- Format: HTML
- Supports: permit izin-edar-bpom and the MD part of
  izin-edar-pangan-olahan: "BPOM RI MD" numbers for domestic products,
  exemptions (umur simpan < 7 hari, pangan siap saji, IRT uses SPP-IRT),
  registration at ereg-rba.pom.go.id linked to OSS, products under
  registration may not be sold. Note: the regulation list on this page is
  partly out of date (it still lists Peraturan BPOM 22/2018 for SPP-IRT); only
  the facts above were used.

## 8. Halal: PP 42/2024 and PP 40/2026

- PP 42/2024: Peraturan Pemerintah Nomor 42 Tahun 2024 tentang Penyelenggaraan
  Bidang Jaminan Produk Halal, JDIH BPK,
  https://peraturan.bpk.go.id/Details/304896/pp-no-42-tahun-2024 (PDF, 96
  pages, sha256
  `0863219864c2edaa81bdd2f1b9fcdb4868d2a86cccf13f5855f9c5334a6b0259`).
  Supports: sertifikat-halal (Pasal 2: obligation and "keterangan tidak halal";
  Pasal 98: pernyataan halal for UMK with pendampingan PPH; Pasal 155, 159,
  160). Source URL of all 42 halal rules.
- PP 40/2026 (amends PP 42/2024; set and promulgated 2026-10-14): the official
  PDF could not be found on JDIH BPK or peraturan.go.id on 2026-11-23. The new
  UMK deadline is taken from BPJPH's official article "Penyesuaian Penahapan
  Kewajiban Sertifikasi Halal Diatur dalam PP 40 Tahun 2026, Begini
  Rinciannya", published 2026-10-24,
  https://bpjph.halal.go.id/read/penyesuaian-penahapan-kewajiban-sertifikasi-halal-diatur-dalam-pp-40-tahun-2026-begini-rinciannya
  (HTML): UMK food, beverage, slaughter products and slaughter services are
  phased in until 17 Oktober 2028. Supports: the 2028 date in
  sertifikat-halal and its `source_url`.
- BPJPH home page https://bpjph.halal.go.id/ (HTML): application portal
  ptsp.halal.go.id ("Pendaftaran Sertifikasi Halal"). Supports: how_to of
  sertifikat-halal.

## Method notes (permits and rules)

- Risk levels are for micro and small businesses only. Where an OSS page has
  several ruang lingkup with different risks, the rule uses the ruang lingkup
  that fits this app's users and the others are noted here as not covered:
  - 10503: "Selain pracampur/premix es krim" (rendah) used; premix es krim
    (menengah rendah) not covered.
  - 10509: yoghurt, keju, mentega etc. (menengah rendah) used; "Pembuatan
    laktosa" (tinggi) not covered.
  - 10799: all ruang lingkup are rendah except "Pembuatan pemanis buatan"
    (tinggi), which is not covered.
  - 56101: "Restoran" is menengah rendah for micro but menengah tinggi for
    small; "Rumah / Warung Makan" is menengah rendah for both. The rule uses
    menengah rendah. A small-scale restaurant is under-stated (see the Task 4
    report concerns).
- The hygiene permit per food-service code follows the OSS kewajiban:
  Label HSP only (56210, 56290, 56304, 56306); Label HSP or SLHS depending on
  ruang lingkup/scale (56101, 56102, 56303); none listed for 56305 (Kedai
  Jamu, Kesehatan sector).
- Izin edar: codes whose OSS PB UMKU list includes SPP-IRT use
  izin-edar-pangan-olahan; codes whose list has only the BPOM permits (10218,
  10296, 10304, 10307, 10308, 10503, 10504, 10509, 10750, 10792, 10797) use
  izin-edar-bpom. Both apply only when `packaged: true`.
- Halal rules: every manufacturing code (10xxx, 11xxx) and every food-service
  code except 56305. 56305 is "Rumah/Kedai Obat Bahan Alam"; obat bahan alam
  has its own timeline in PP 42/2024 Pasal 161 ayat (1) huruf a, and whether
  PP 40/2026 changed it for UMK could not be confirmed. Retail codes (472xx)
  have no halal rule: the obligation attaches to the product (Pasal 2), and
  PP 42/2024 Pasal 159 ayat (2)-(3) puts services other than slaughter (such
  as penjualan) in a later phase.
- PBG/SLF applies only when a building is built (PP 28/2025 Pasal 106); the
  permit text says so. It is not attached to 56102 and 56306 (non-permanent or
  mobile premises).
- `valid_from`: 2025-10-05 for permits based on PP 28/2025; 2026-06-15 for
  rules (OSS applies KBLI 2025 from that date); 2026-10-14 for the halal
  permit and halal rules (PP 40/2026).
- Not included: NKV (Nomor Kontrol Veteriner) and other conditional PB UMKU
  (alcohol, import, TKDN, irradiation), sector kewajiban such as wajib lapor
  Data Industri (SIINas) and laporan kegiatan usaha, and anything specific to
  selling online (no rule uses `sells_online`).

## Descoped in Task 4

None. Every in-scope code has a sourced risk level and permit list.

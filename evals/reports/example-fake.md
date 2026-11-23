> **FAKE MODE REPORT: NOT A QUALITY MEASUREMENT.** (LLM_MODE=fake, EMBEDDER=fake.) It only exercises the eval plumbing; low scores are expected.

# Eval report 2026-11-23 20:47

- Mode: LLM_MODE=fake, EMBEDDER=fake
- Data release id: 2
- Cases: 55 (55 expected activities)
- Latency: the first case's latency includes loading the embedding model.

| Metric | All | Clarified (0) | Not clarified (55) | Bar (on All) |
|---|---|---|---|---|
| KBLI top-1 | 0.327 | n/a | 0.327 |  |
| KBLI top-3 | 0.327 | n/a | 0.327 | >= 0.90 FAIL |
| Permit exact match (47 cases) | 0.319 | n/a | 0.319 |  |
| Risk match, primary acceptable (18 cases) | 0.889 | n/a | 0.889 |  |
| Scope accuracy, 3-way (in / partial / out) | 0.818 | n/a | 0.818 |  |
| Out-of-scope accuracy (5 expected-out cases) | 0.000 | n/a | 0.000 | >= 0.95 FAIL |
| Clarification rate | 0.000 | n/a | 0.000 |  |
| Invented codes/permits | 0 | n/a | 0 | == 0 PASS |
| Average cost per case (USD) | 0.0000 | n/a | 0.0000 |  |
| Total cost (USD) | 0.0000 | n/a | 0.0000 |  |
| Latency p50 / p95 (s) | 0.0 / 0.0 | n/a | 0.0 / 0.0 | |

Cases that ended in clarification were re-run once with each question answered by its
first option; the second pass is the one scored. Vague cases are scored for scope only.
Costs include every logged request of a case, also requests that ended in an error.

Clarified (auto-answered) cases: none

## Failed cases (41)

| Failure type | Count |
|---|---|
| clarify | 3 |
| kbli | 30 |
| permits | 32 |
| scope | 10 |

| id | description | failures |
|---|---|---|
| single-warung-01 | Saya buka warung makan nasi rawon dan soto ayam, pelanggan makan di tempat, ada meja kursi biasa, bukan restoran besar | permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar-terverifikasi', 'slhs'] for primaries ['56101'] (not matching the expected set for the chosen acceptable codes) |
| single-warung-02 | jualan seblak depan rumah, pembeli makan di situ pakai bangku plastik | permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar-terverifikasi', 'slhs'] for primaries ['56101'] (not matching the expected set for the chosen acceptable codes) |
| single-resto-01 | Restoran seafood keluarga dengan pelayan, 60 kursi dan AC, bayar di kasir, sebagian pesanan lewat GoFood | kbli: expected 56101; got 10303+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10303'] (not matching the expected set for the chosen acceptable codes) |
| single-foodtruck-01 | Food truck burger dan kentang goreng, parkir di acara bazar dan car free day | kbli: expected 56102; got 10303+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10303'] (not matching the expected set for the chosen acceptable codes) |
| single-kafe-01 | Kafe kecil di ruko, jual kopi susu dan teh, pelanggan nongkrong di dalam, ada wifi | kbli: expected 56303; got 10761+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10761'] (not matching the expected set for the chosen acceptable codes) |
| single-kedaikopi-01 | Kedai kopi pakai tenda di pinggir jalan, es kopi susu gula aren, bisa bawa pulang atau duduk di bangku | kbli: expected 56304; got 47243+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47243'] (not matching the expected set for the chosen acceptable codes) |
| single-catering-02 | Katering harian untuk karyawan pabrik, kontrak bulanan, makan siang diantar tiap hari | kbli: expected 56290; got 47242+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47242'] (not matching the expected set for the chosen acceptable codes) |
| single-tahu-01 | Bikin tahu putih tiap hari, dijual curah ke pedagang pasar tanpa kemasan | kbli: expected 10308; got 47244+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47244'] (not matching the expected set for the chosen acceptable codes) |
| single-bakery-01 | Toko roti kecil, bikin roti manis, bolu dan kue ulang tahun pesanan, dijual di etalase sendiri tanpa kemasan bermerek | kbli: expected 10710; got 47242+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47242'] (not matching the expected set for the chosen acceptable codes) |
| single-kuebasah-01 | Buat kue basah lemper, kue lapis dan risoles, dibungkus plastik mika dan dititip ke warung dan pasar pagi | kbli: expected 10792; got 47242+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47242'] (not matching the expected set for the chosen acceptable codes) |
| single-bumbu-01 | Produksi bumbu rempah bubuk, bubuk jahe dan bumbu gulai, dikemas sachet dan dijual online | kbli: expected 10779; got 10309+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10309'] (not matching the expected set for the chosen acceptable codes) |
| single-kopi-01 | Sangrai dan giling biji kopi sendiri, jual kopi bubuk kemasan 200 gram lewat Instagram dan Tokopedia | kbli: expected 10761; got 10733+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10733'] (not matching the expected set for the chosen acceptable codes) |
| single-dodol-01 | Bikin dodol garut tradisional, dijual per kotak sebagai oleh-oleh | kbli: expected 10796; got 47222+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47222'] (not matching the expected set for the chosen acceptable codes) |
| single-jus-01 | Jus buah segar dalam botol plastik, dijual keliling ke kantor-kantor dan dititip di kantin | kbli: expected 10306; got 10733+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10733'] (not matching the expected set for the chosen acceptable codes) |
| single-yogurt-01 | Yoghurt dan keju mozzarella rumahan dalam kemasan botol | kbli: expected 10509; got 10733+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10733'] (not matching the expected set for the chosen acceptable codes) |
| single-mie-01 | Produksi mi basah dan bihun, dijual ke penjual bakso dan warung, dikemas plastik | kbli: expected 10740; got 10218+[]<br>permits: got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] for primaries ['10218'] (not matching the expected set for the chosen acceptable codes) |
| single-bakso-01 | Produksi bakso sapi dan sosis, dibekukan dan dikemas, dijual ke toko-toko kecil | kbli: expected 10120; got 10218+[]<br>permits: got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] for primaries ['10218'] (not matching the expected set for the chosen acceptable codes) |
| single-bakso-02 | Produksi bakso udang dan bakso cumi beku kemasan | kbli: expected 10296; got 10120+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] for primaries ['10120'] (not matching the expected set for the chosen acceptable codes) |
| single-nabati-01 | Susu kedelai dan susu oat botolan, dijual online | kbli: expected 10795; got 10306+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10306'] (not matching the expected set for the chosen acceptable codes) |
| single-minuman-01 | Produksi minuman teh rasa lemon dalam botol, dijual ke warung dan minimarket | kbli: expected 11053; got 56306+[]<br>permits: got ['kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] for primaries ['56306'] (not matching the expected set for the chosen acceptable codes) |
| single-frozen-01 | PO-an lewat IG: rendang dan gulai dikemas vakum frozen, dikirim ke seluruh kota | kbli: expected 10750; got 10794+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10794'] (not matching the expected set for the chosen acceptable codes) |
| multi-01 | Restoran padang: makan di tempat, juga terima catering nasi box untuk acara, dan jual rendang kemasan vakum lewat online | kbli: expected 56101, 56210, 10750; got 56101+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar-terverifikasi', 'slhs'] for primaries ['56101'] (not matching the expected set for the chosen acceptable codes) |
| multi-02 | Toko roti yang punya kafe di dalamnya: roti buatan sendiri dijual dikemas dan pengunjung bisa duduk minum kopi | kbli: expected 10710, 56303; got 47242+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47242'] (not matching the expected set for the chosen acceptable codes) |
| multi-03 | Kedai kopi tenda pinggir jalan, selain itu juga sangrai biji kopi sendiri dan jual kopi bubuk kemasan | kbli: expected 56304, 10761; got 10309+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10309'] (not matching the expected set for the chosen acceptable codes) |
| multi-04 | Saya bikin tahu dan tempe sendiri dijual curah, dan juga buka warung pecel lele pakai tenda | kbli: expected 10308, 10307, 56102; got 47244+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47244'] (not matching the expected set for the chosen acceptable codes) |
| multi-05 | Ibu rumah tangga: bikin kue basah dibungkus plastik, es krim homemade di cup, dan terima pesanan snack box acara kantor | kbli: expected 10792, 10503, 56210; got 47242+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47242'] (not matching the expected set for the chosen acceptable codes) |
| partial-01 | Warung nasi di pinggir jalan, sekalian jual rokok dan pulsa | scope: expected partial, got in<br>kbli: expected 56101; got 10795+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10795'] (not matching the expected set for the chosen acceptable codes) |
| partial-02 | Kafe kopi yang juga jual bir dan minuman beralkohol lainnya | scope: expected partial, got in<br>kbli: expected 56303; got 47222+[]<br>permits: got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] for primaries ['47222'] (not matching the expected set for the chosen acceptable codes) |
| partial-03 | Produksi keripik tempe kemasan, dan juga pembuatan pakan ternak ayam | scope: expected partial, got in<br>kbli: expected 10794; got 10307+[]<br>permits: got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10307'] (not matching the expected set for the chosen acceptable codes) |
| partial-04 | Kios kue basah di pinggir jalan (lemper, kue lapis, bolu), selain itu juga jual sedikit beras eceran | scope: expected partial, got in |
| partial-05 | Warung bakso dan depot air minum isi ulang | scope: expected partial, got in<br>kbli: expected 56101; got 10296+[]<br>permits: got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] for primaries ['10296'] (not matching the expected set for the chosen acceptable codes) |
| out-01 | Mau buka toko minuman keras, jual bir, wine dan whisky | scope: expected out, got in |
| out-02 | Produksi tuak dan arak tradisional rumahan | scope: expected out, got in |
| out-03 | Pabrik mi instan dengan 300 karyawan dan omzet puluhan miliar per bulan, ekspor ke luar negeri | scope: expected out, got in |
| out-04 | Jasa laundry kiloan dan dry cleaning | scope: expected out, got in |
| out-05 | Bengkel motor dan jual sparepart | scope: expected out, got in |
| vague-01 | kopi | clarify: expected a clarification question on the first pass |
| vague-02 | jualan makanan | clarify: expected a clarification question on the first pass |
| vague-03 | usaha rumahan | clarify: expected a clarification question on the first pass |
| old-kbli-01 | Kode KBLI lama saya 56102 (rumah makan), jualan nasi campur di ruko, ada meja dan kursi | kbli: expected 56101; got 10302+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10302'] (not matching the expected set for the chosen acceptable codes) |
| old-kbli-02 | Saya punya NIB lama dengan KBLI 10392, produksi tahu putih dan tahu goreng, dijual ke pasar tanpa kemasan | kbli: expected 10308; got 10309+[]<br>permits: got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] for primaries ['10309'] (not matching the expected set for the chosen acceptable codes) |

> **FAKE MODE REPORT: NOT A QUALITY MEASUREMENT.** (LLM_MODE=fake, EMBEDDER=fake.) It only exercises the eval plumbing; low scores are expected.

# Eval report 2026-11-23 20:00

- Mode: LLM_MODE=fake, EMBEDDER=fake
- Data release id: 1
- Cases: 55 (55 expected activities)

| Metric | Value | Bar |
|---|---|---|
| KBLI top-1 | 0.545 | |
| KBLI top-3 | 0.545 | >= 0.90 FAIL |
| Permit exact match (47 cases) | 0.532 | |
| Risk match when primary exact (30 cases) | 0.933 | |
| Scope accuracy | 0.818 | >= 0.95 FAIL |
| Clarification rate | 0.000 | |
| Invented codes/permits | 0 | == 0 PASS |
| Average cost per case (USD) | 0.0000 | |
| Total cost (USD) | 0.0000 | |
| Latency p50 / p95 (s) | 0.0 / 0.0 | |

Cases that ended in clarification were re-run once with each question answered by its
first option; the second pass is the one scored. Vague cases are scored for scope only.

## Failed cases (32)

| id | description | failures |
|---|---|---|
| single-warung-01 | Saya buka warung makan nasi rawon dan soto ayam, pelanggan makan di tempat, ada meja kursi biasa, bukan restoran besar | permits: expected ['kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar-terverifikasi', 'slhs'] |
| single-warung-02 | jualan seblak depan rumah, pembeli makan di situ pakai bangku plastik | permits: expected ['kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar-terverifikasi', 'slhs'] |
| single-gerobak-01 | Jualan bakso keliling pakai gerobak dorong, pembeli makan di pinggir jalan | kbli: expected 56102; got 47222+[]<br>permits: expected ['kkpr', 'label-hsp-atau-slhs', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| single-foodtruck-01 | Food truck burger dan kentang goreng, parkir di acara bazar dan car free day | kbli: expected 56102; got 10303+[]<br>permits: expected ['kkpr', 'label-hsp-atau-slhs', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |
| single-kafe-01 | Kafe kecil di ruko, jual kopi susu dan teh, pelanggan nongkrong di dalam, ada wifi | kbli: expected 56303; got 10761+[]<br>permits: expected ['kkpr', 'label-hsp-atau-slhs', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |
| single-tahu-01 | Bikin tahu putih tiap hari, dijual curah ke pedagang pasar tanpa kemasan | kbli: expected 10308; got 47244+[]<br>permits: expected ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| single-bakery-01 | Toko roti kecil, bikin roti manis, bolu dan kue ulang tahun pesanan, dijual di etalase sendiri tanpa kemasan bermerek | kbli: expected 10710; got 47242+[]<br>permits: expected ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| single-dodol-01 | Bikin dodol garut tradisional, dijual per kotak sebagai oleh-oleh | kbli: expected 10796; got 47222+[]<br>permits: expected ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| single-yogurt-01 | Yoghurt dan keju mozzarella rumahan dalam kemasan botol | kbli: expected 10509; got 10733+[]<br>permits: expected ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |
| single-mie-01 | Produksi mi basah dan bihun, dijual ke penjual bakso dan warung, dikemas plastik | kbli: expected 10740; got 10296+[]<br>permits: expected ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] |
| single-bakso-01 | Produksi bakso sapi dan sosis, dibekukan dan dikemas, dijual ke toko-toko kecil | kbli: expected 10120; got 10296+[]<br>permits: expected ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] |
| single-nabati-01 | Susu kedelai dan susu oat botolan, dijual online | kbli: expected 10795; got 10509+[]<br>permits: expected ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal']; got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] |
| multi-01 | Restoran padang: makan di tempat, juga terima catering nasi box untuk acara, dan jual rendang kemasan vakum lewat online | kbli: expected 56101, 56210, 10750; got 56101+[]<br>permits: expected ['izin-edar-bpom', 'kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar', 'sertifikat-standar-terverifikasi', 'slhs']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar-terverifikasi', 'slhs'] |
| multi-02 | Toko roti yang punya kafe di dalamnya: roti buatan sendiri dijual dikemas dan pengunjung bisa duduk minum kopi | kbli: expected 10710, 56303; got 10710+[]<br>permits: expected ['izin-edar-pangan-olahan', 'kkpr', 'label-hsp-atau-slhs', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |
| multi-03 | Kedai kopi tenda pinggir jalan, selain itu juga sangrai biji kopi sendiri dan jual kopi bubuk kemasan | kbli: expected 56304, 10761; got 10761+[]<br>permits: expected ['izin-edar-pangan-olahan', 'kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |
| multi-04 | Saya bikin tahu dan tempe sendiri dijual curah, dan juga buka warung pecel lele pakai tenda | kbli: expected 10308, 10307, 56102; got 10309+[]<br>permits: expected ['kkpr', 'label-hsp-atau-slhs', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |
| multi-05 | Ibu rumah tangga: bikin kue basah dibungkus plastik, es krim homemade di cup, dan terima pesanan snack box acara kantor | kbli: expected 10792, 10503, 56210; got 47242+[]<br>permits: expected ['izin-edar-bpom', 'kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| partial-01 | Warung nasi di pinggir jalan, sekalian jual rokok dan pulsa | scope: expected partial, got in<br>kbli: expected 56101; got 47222+[]<br>permits: expected ['kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| partial-02 | Kafe kopi yang juga jual bir dan minuman beralkohol lainnya | scope: expected partial, got in<br>kbli: expected 56303; got 47222+[]<br>permits: expected ['kkpr', 'label-hsp-atau-slhs', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| partial-03 | Produksi keripik tempe kemasan, dan juga pembuatan pakan ternak ayam | scope: expected partial, got in |
| partial-04 | Toko kelontong kecil jual kue basah dan beras eceran | scope: expected partial, got in |
| partial-05 | Warung bakso dan depot air minum isi ulang | scope: expected partial, got in<br>kbli: expected 56101; got 10296+[]<br>permits: expected ['kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['izin-edar-bpom', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar'] |
| out-01 | Mau buka toko minuman keras, jual bir, wine dan whisky | scope: expected out, got in |
| out-02 | Produksi tuak dan arak tradisional rumahan | scope: expected out, got in |
| out-03 | Pabrik mi instan dengan 300 karyawan dan omzet puluhan miliar per bulan, ekspor ke luar negeri | scope: expected out, got in |
| out-04 | Jasa laundry kiloan dan dry cleaning | scope: expected out, got in |
| out-05 | Bengkel motor dan jual sparepart | scope: expected out, got in |
| vague-01 | kopi | expected a clarification question on the first pass |
| vague-02 | jualan makanan | expected a clarification question on the first pass |
| vague-03 | usaha rumahan | expected a clarification question on the first pass |
| old-kbli-01 | Kode KBLI lama saya 56102 (rumah makan), jualan nasi campur di ruko, ada meja dan kursi | kbli: expected 56101; got 47222+[]<br>permits: expected ['kkpr', 'label-hsp', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal', 'sertifikat-standar']; got ['kkpr', 'nib', 'persetujuan-lingkungan-sppl'] |
| old-kbli-02 | Saya punya NIB lama dengan KBLI 10392, produksi tahu putih dan tahu goreng, dijual ke pasar tanpa kemasan | kbli: expected 10308; got 10309+[]<br>permits: expected ['kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal']; got ['izin-edar-pangan-olahan', 'kkpr', 'nib', 'persetujuan-lingkungan-sppl', 'sertifikat-halal'] |

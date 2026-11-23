# Eval case review

Please review each case: is the description realistic, is the expected KBLI code right,
and are the listed alternatives genuinely acceptable? Write OK or a note in the last
column. Expected permits and risk are generated from the rules engine, not reviewed here.

`primary` is the expected code; `also ok` lists extra acceptable codes. Vague cases are
expected to trigger a clarification question first; their second pass is scored for scope.

| id | description | expected scope | expected codes | OK? / note |
|---|---|---|---|---|
| single-warung-01 | Saya buka warung makan nasi rawon dan soto ayam, pelanggan makan di tempat, ada meja kursi biasa, bukan restoran besar | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap | |
| single-warung-02 | jualan seblak depan rumah, pembeli makan di situ pakai bangku plastik | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap (also ok: 56102 Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap) | |
| single-resto-01 | Restoran seafood keluarga dengan pelayan, 60 kursi dan AC, bayar di kasir, sebagian pesanan lewat GoFood | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap | |
| single-gerobak-01 | Jualan bakso keliling pakai gerobak dorong, pembeli makan di pinggir jalan | in | **56102** Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap | |
| single-foodtruck-01 | Food truck burger dan kentang goreng, parkir di acara bazar dan car free day | in | **56102** Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap | |
| single-kafe-01 | Kafe kecil di ruko, jual kopi susu dan teh, pelanggan nongkrong di dalam, ada wifi | in | **56303** Aktivitas Rumah Minum/Kafe | |
| single-kedaikopi-01 | Kedai kopi pakai tenda di pinggir jalan, es kopi susu gula aren, bisa bawa pulang atau duduk di bangku | in | **56304** Aktivitas Kedai Minuman | |
| single-jamu-01 | Jamu gendong keliling kampung tiap pagi | in | **56306** Aktivitas Penyediaan Minuman Keliling/Tempat Tidak Tetap | |
| single-jamu-02 | Kedai jamu di ruko permanen, pelanggan minum jamu di tempat, ada bangku | in | **56305** Aktivitas Rumah/Kedai Obat Bahan Alam | |
| single-catering-01 | Terima pesanan nasi box untuk acara kantor, arisan dan pengajian, dimasak di rumah lalu diantar | in | **56210** Aktivitas Jasa Boga untuk Acara Tertentu (Event Catering) | |
| single-catering-02 | Katering harian untuk karyawan pabrik, kontrak bulanan, makan siang diantar tiap hari | in | **56290** Aktivitas Penyediaan Jasa Boga Lainnya | |
| single-tempe-01 | Produksi tempe kedelai rumahan, dibungkus plastik per papan dan dijual ke pasar | in | **10307** Pembuatan Tempe Kedelai | |
| single-tahu-01 | Bikin tahu putih tiap hari, dijual curah ke pedagang pasar tanpa kemasan | in | **10308** Pembuatan Tahu Kedelai | |
| single-keripik-01 | Bikin kerupuk udang dan peyek kacang kemasan plastik, dititip di warung-warung sekitar | in | **10794** Industri Kerupuk, Keripik, Peyek, dan Sejenisnya | |
| single-bakery-01 | Toko roti kecil, bikin roti manis, bolu dan kue ulang tahun pesanan, dijual di etalase sendiri tanpa kemasan bermerek | in | **10710** Industri Produk Bakeri | |
| single-kuebasah-01 | Buat kue basah lemper, kue lapis dan risoles, dibungkus plastik mika dan dititip ke warung dan pasar pagi | in | **10792** Industri Kue Basah | |
| single-bumbu-01 | Produksi bumbu rempah bubuk, bubuk jahe dan bumbu gulai, dikemas sachet dan dijual online | in | **10779** Industri Bumbu Masakan Lainnya | |
| single-kopi-01 | Sangrai dan giling biji kopi sendiri, jual kopi bubuk kemasan 200 gram lewat Instagram dan Tokopedia | in | **10761** Pengolahan Kopi | |
| single-dodol-01 | Bikin dodol garut tradisional, dijual per kotak sebagai oleh-oleh | in | **10796** Industri Dodol | |
| single-asinan-01 | Asinan sayur dan asinan kedondong botolan untuk dijual ke toko | in | **10301** Pengasinan Buah-buahan dan Sayuran | |
| single-jus-01 | Jus buah segar dalam botol plastik, dijual keliling ke kantor-kantor dan dititip di kantin | in | **10306** Pengolahan Sari Buah-buahan dan Sayuran | |
| single-eskrim-01 | Es krim susu homemade dalam cup, dititip di freezer toko | in | **10503** Industri Es Krim | |
| single-yogurt-01 | Yoghurt dan keju mozzarella rumahan dalam kemasan botol | in | **10509** Industri Produk Susu Lainnya | |
| single-coklat-01 | Bikin cokelat praline dan cokelat batang, kemasan hampers, PO-an lewat IG | in | **10732** Industri Cokelat dan Kembang Gula dari Cokelat | |
| single-mie-01 | Produksi mi basah dan bihun, dijual ke penjual bakso dan warung, dikemas plastik | in | **10740** Industri Makaroni, Mi, Couscous, dan Produk Sejenisnya | |
| single-pempek-01 | Pempek dan siomai ikan frozen kemasan, dikirim ke reseller | in | **10218** Pengolahan dan Pengawetan Ikan Menjadi Produk Olahan | |
| single-bakso-01 | Produksi bakso sapi dan sosis, dibekukan dan dikemas, dijual ke toko-toko kecil | in | **10120** Pengolahan dan Pengawetan Daging dan Produk Daging | |
| single-bakso-02 | Produksi bakso udang dan bakso cumi beku kemasan | in | **10296** Pengolahan dan Pengawetan Biota Air Lainnya dengan Pelumatan | |
| single-nabati-01 | Susu kedelai dan susu oat botolan, dijual online | in | **10795** Industri Sari Nabati dan Krimer Nabati (also ok: 11053 Industri Minuman Ringan) | |
| single-minuman-01 | Produksi minuman teh rasa lemon dalam botol, dijual ke warung dan minimarket | in | **11053** Industri Minuman Ringan | |
| single-frozen-01 | PO-an lewat IG: rendang dan gulai dikemas vakum frozen, dikirim ke seluruh kota | in | **10750** Industri Makanan dan Masakan Olahan | |
| single-retail-01 | Toko kecil jual roti dan kue kering eceran | in | **47242** Perdagangan Eceran Roti, Kue Kering, serta Kue Basah dan Sejenisnya | |
| single-retail-02 | Jual kopi bubuk dan gula pasir eceran di kios kecil | in | **47243** Perdagangan Eceran Kopi, Gula Pasir, Gula Merah, dan Sejenisnya | |
| single-retail-03 | Lapak tahu dan tempe di pasar, jual eceran | in | **47244** Perdagangan Eceran Tahu, Tempe, Tauco, dan Oncom | |
| single-retail-04 | Kios kecil jual minuman ringan botol dan es teh bungkus bawa pulang, tidak ada tempat duduk | in | **47222** Perdagangan Eceran Minuman Tidak Beralkohol | |
| multi-01 | Restoran padang: makan di tempat, juga terima catering nasi box untuk acara, dan jual rendang kemasan vakum lewat online | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap<br>**56210** Aktivitas Jasa Boga untuk Acara Tertentu (Event Catering)<br>**10750** Industri Makanan dan Masakan Olahan | |
| multi-02 | Toko roti yang punya kafe di dalamnya: roti buatan sendiri dijual dikemas dan pengunjung bisa duduk minum kopi | in | **10710** Industri Produk Bakeri<br>**56303** Aktivitas Rumah Minum/Kafe | |
| multi-03 | Kedai kopi tenda pinggir jalan, selain itu juga sangrai biji kopi sendiri dan jual kopi bubuk kemasan | in | **56304** Aktivitas Kedai Minuman<br>**10761** Pengolahan Kopi | |
| multi-04 | Saya bikin tahu dan tempe sendiri dijual curah, dan juga buka warung pecel lele pakai tenda | in | **10308** Pembuatan Tahu Kedelai<br>**10307** Pembuatan Tempe Kedelai<br>**56102** Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap | |
| multi-05 | Ibu rumah tangga: bikin kue basah dibungkus plastik, es krim homemade di cup, dan terima pesanan snack box acara kantor | in | **10792** Industri Kue Basah<br>**10503** Industri Es Krim<br>**56210** Aktivitas Jasa Boga untuk Acara Tertentu (Event Catering) | |
| partial-01 | Warung nasi di pinggir jalan, sekalian jual rokok dan pulsa | partial | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap (also ok: 56102 Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap) | |
| partial-02 | Kafe kopi yang juga jual bir dan minuman beralkohol lainnya | partial | **56303** Aktivitas Rumah Minum/Kafe | |
| partial-03 | Produksi keripik tempe kemasan, dan juga pembuatan pakan ternak ayam | partial | **10794** Industri Kerupuk, Keripik, Peyek, dan Sejenisnya | |
| partial-04 | Toko kelontong kecil jual kue basah dan beras eceran | partial | **47242** Perdagangan Eceran Roti, Kue Kering, serta Kue Basah dan Sejenisnya | |
| partial-05 | Warung bakso dan depot air minum isi ulang | partial | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap (also ok: 56102 Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap) | |
| out-01 | Mau buka toko minuman keras, jual bir, wine dan whisky | out | (none) | |
| out-02 | Produksi tuak dan arak tradisional rumahan | out | (none) | |
| out-03 | Pabrik mi instan dengan 300 karyawan dan omzet puluhan miliar per bulan, ekspor ke luar negeri | out | (none) | |
| out-04 | Jasa laundry kiloan dan dry cleaning | out | (none) | |
| out-05 | Bengkel motor dan jual sparepart | out | (none) | |
| vague-01 | kopi | in | (clarify first) | |
| vague-02 | jualan makanan | in | (clarify first) | |
| vague-03 | usaha rumahan | in | (clarify first) | |
| old-kbli-01 | Kode KBLI lama saya 56102 (rumah makan), jualan nasi campur di ruko, ada meja dan kursi | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap | |
| old-kbli-02 | Saya punya NIB lama dengan KBLI 10392, produksi tahu putih dan tahu goreng, dijual ke pasar tanpa kemasan | in | **10308** Pembuatan Tahu Kedelai | |

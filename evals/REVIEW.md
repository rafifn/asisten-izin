# Eval case review

Please review each case: is the description realistic, is the expected KBLI code right,
and are the listed alternatives genuinely acceptable? Write OK or a note in the last
column. Expected permits and risk are generated from the rules engine, not reviewed here.

`?` means the description does not say (expected attribute is null). `primary` is the
expected code; `also ok` lists extra acceptable codes. Vague cases are
expected to trigger a clarification question first; their second pass is scored for
scope only.

| id | description | expected scope | expected codes | OK? / note |
|---|---|---|---|---|
| single-warung-01 | Saya buka warung makan nasi rawon dan soto ayam, pelanggan makan di tempat, ada meja kursi biasa, bukan restoran besar | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap [packaged=?, formal=no] | |
| single-warung-02 | jualan seblak depan rumah, pembeli makan di situ pakai bangku plastik | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap (also ok: 56102 Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap) [packaged=?, formal=no] | |
| single-resto-01 | Restoran seafood keluarga dengan pelayan, 60 kursi dan AC, bayar di kasir, sebagian pesanan lewat GoFood | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap [packaged=?, formal=yes] | |
| single-gerobak-01 | Jualan bakso keliling pakai gerobak dorong, pembeli makan di pinggir jalan | in | **56102** Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap [packaged=?, formal=?] | |
| single-foodtruck-01 | Food truck burger dan kentang goreng, parkir di acara bazar dan car free day | in | **56102** Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap [packaged=?, formal=?] | |
| single-kafe-01 | Kafe kecil di ruko, jual kopi susu dan teh, pelanggan nongkrong di dalam, ada wifi | in | **56303** Aktivitas Rumah Minum/Kafe [packaged=?, formal=?] | |
| single-kedaikopi-01 | Kedai kopi pakai tenda di pinggir jalan, es kopi susu gula aren, bisa bawa pulang atau duduk di bangku | in | **56304** Aktivitas Kedai Minuman [packaged=?, formal=?] | |
| single-jamu-01 | Jamu gendong keliling kampung tiap pagi | in | **56306** Aktivitas Penyediaan Minuman Keliling/Tempat Tidak Tetap [packaged=?, formal=?] | |
| single-jamu-02 | Kedai jamu di ruko permanen, pelanggan minum jamu di tempat, ada bangku | in | **56305** Aktivitas Rumah/Kedai Obat Bahan Alam [packaged=?, formal=?] | |
| single-catering-01 | Terima pesanan nasi box untuk acara kantor, arisan dan pengajian, dimasak di rumah lalu diantar | in | **56210** Aktivitas Jasa Boga untuk Acara Tertentu (Event Catering) [packaged=?, formal=?] | |
| single-catering-02 | Katering harian untuk karyawan pabrik, kontrak bulanan, makan siang diantar tiap hari | in | **56290** Aktivitas Penyediaan Jasa Boga Lainnya [packaged=?, formal=?] | |
| single-tempe-01 | Produksi tempe kedelai rumahan, dibungkus plastik per papan dan dijual ke pasar<br>**Owner judgement:** Is plastic-wrapped fresh tempe sold at the pasar 'packaged' (izin edar needed)? Expected here: yes (packaged=true). | in | **10307** Pembuatan Tempe Kedelai [packaged=yes, formal=?] | |
| single-tahu-01 | Bikin tahu putih tiap hari, dijual curah ke pedagang pasar tanpa kemasan | in | **10308** Pembuatan Tahu Kedelai [packaged=no, formal=?] | |
| single-keripik-01 | Bikin kerupuk udang dan peyek kacang kemasan plastik, dititip di warung-warung sekitar | in | **10794** Industri Kerupuk, Keripik, Peyek, dan Sejenisnya [packaged=yes, formal=?] | |
| single-bakery-01 | Toko roti kecil, bikin roti manis, bolu dan kue ulang tahun pesanan, dijual di etalase sendiri tanpa kemasan bermerek | in | **10710** Industri Produk Bakeri [packaged=no, formal=?] | |
| single-kuebasah-01 | Buat kue basah lemper, kue lapis dan risoles, dibungkus plastik mika dan dititip ke warung dan pasar pagi | in | **10792** Industri Kue Basah [packaged=yes, formal=?] | |
| single-bumbu-01 | Produksi bumbu rempah bubuk, bubuk jahe dan bumbu gulai, dikemas sachet dan dijual online | in | **10779** Industri Bumbu Masakan Lainnya [packaged=yes, formal=?] | |
| single-kopi-01 | Sangrai dan giling biji kopi sendiri, jual kopi bubuk kemasan 200 gram lewat Instagram dan Tokopedia | in | **10761** Pengolahan Kopi [packaged=yes, formal=?] | |
| single-dodol-01 | Bikin dodol garut tradisional, dijual per kotak sebagai oleh-oleh | in | **10796** Industri Dodol [packaged=yes, formal=?] | |
| single-asinan-01 | Asinan sayur dan asinan kedondong botolan untuk dijual ke toko | in | **10301** Pengasinan Buah-buahan dan Sayuran [packaged=yes, formal=?] | |
| single-jus-01 | Jus buah segar dalam botol plastik, dijual keliling ke kantor-kantor dan dititip di kantin | in | **10306** Pengolahan Sari Buah-buahan dan Sayuran [packaged=yes, formal=?] | |
| single-eskrim-01 | Es krim susu homemade dalam cup, dititip di freezer toko | in | **10503** Industri Es Krim [packaged=yes, formal=?] | |
| single-yogurt-01 | Yoghurt dan keju mozzarella rumahan dalam kemasan botol | in | **10509** Industri Produk Susu Lainnya [packaged=yes, formal=?] | |
| single-coklat-01 | Bikin cokelat praline dan cokelat batang, kemasan hampers, PO-an lewat IG | in | **10732** Industri Cokelat dan Kembang Gula dari Cokelat [packaged=yes, formal=?] | |
| single-mie-01 | Produksi mi basah dan bihun, dijual ke penjual bakso dan warung, dikemas plastik | in | **10740** Industri Makaroni, Mi, Couscous, dan Produk Sejenisnya [packaged=yes, formal=?] | |
| single-pempek-01 | Pempek dan siomai ikan frozen kemasan, dikirim ke reseller | in | **10218** Pengolahan dan Pengawetan Ikan Menjadi Produk Olahan [packaged=yes, formal=?] | |
| single-bakso-01 | Produksi bakso sapi dan sosis, dibekukan dan dikemas, dijual ke toko-toko kecil | in | **10120** Pengolahan dan Pengawetan Daging dan Produk Daging [packaged=yes, formal=?] | |
| single-bakso-02 | Produksi bakso udang dan bakso cumi beku kemasan | in | **10296** Pengolahan dan Pengawetan Biota Air Lainnya dengan Pelumatan [packaged=yes, formal=?] | |
| single-nabati-01 | Susu kedelai dan susu oat botolan, dijual online | in | **10795** Industri Sari Nabati dan Krimer Nabati (also ok: 11053 Industri Minuman Ringan) [packaged=yes, formal=?] | |
| single-minuman-01 | Produksi minuman teh rasa lemon dalam botol, dijual ke warung dan minimarket | in | **11053** Industri Minuman Ringan [packaged=yes, formal=?] | |
| single-frozen-01 | PO-an lewat IG: rendang dan gulai dikemas vakum frozen, dikirim ke seluruh kota | in | **10750** Industri Makanan dan Masakan Olahan [packaged=yes, formal=?] | |
| single-retail-01 | Toko kecil jual roti dan kue kering eceran | in | **47242** Perdagangan Eceran Roti, Kue Kering, serta Kue Basah dan Sejenisnya [packaged=?, formal=?] | |
| single-retail-02 | Jual kopi bubuk dan gula pasir eceran di kios kecil | in | **47243** Perdagangan Eceran Kopi, Gula Pasir, Gula Merah, dan Sejenisnya [packaged=?, formal=?] | |
| single-retail-03 | Lapak tahu dan tempe di pasar, jual eceran | in | **47244** Perdagangan Eceran Tahu, Tempe, Tauco, dan Oncom [packaged=?, formal=?] | |
| single-retail-04 | Kios kecil jual minuman ringan botol dan es teh bungkus bawa pulang, tidak ada tempat duduk | in | **47222** Perdagangan Eceran Minuman Tidak Beralkohol [packaged=?, formal=?] | |
| multi-01 | Restoran padang: makan di tempat, juga terima catering nasi box untuk acara, dan jual rendang kemasan vakum lewat online<br>**Owner judgement:** Does 'Restoran padang' count as formal_restaurant=true (vs warung/rumah makan)? Expected here: yes, which gives the stricter 56101 permit set. | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap [packaged=?, formal=yes]<br>**56210** Aktivitas Jasa Boga untuk Acara Tertentu (Event Catering) [packaged=?, formal=?]<br>**10750** Industri Makanan dan Masakan Olahan [packaged=yes, formal=?] | |
| multi-02 | Toko roti yang punya kafe di dalamnya: roti buatan sendiri dijual dikemas dan pengunjung bisa duduk minum kopi | in | **10710** Industri Produk Bakeri [packaged=yes, formal=?]<br>**56303** Aktivitas Rumah Minum/Kafe [packaged=?, formal=?] | |
| multi-03 | Kedai kopi tenda pinggir jalan, selain itu juga sangrai biji kopi sendiri dan jual kopi bubuk kemasan | in | **56304** Aktivitas Kedai Minuman [packaged=?, formal=?]<br>**10761** Pengolahan Kopi [packaged=yes, formal=?] | |
| multi-04 | Saya bikin tahu dan tempe sendiri dijual curah, dan juga buka warung pecel lele pakai tenda | in | **10308** Pembuatan Tahu Kedelai [packaged=no, formal=?]<br>**10307** Pembuatan Tempe Kedelai [packaged=no, formal=?]<br>**56102** Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap [packaged=?, formal=?] | |
| multi-05 | Ibu rumah tangga: bikin kue basah dibungkus plastik, es krim homemade di cup, dan terima pesanan snack box acara kantor | in | **10792** Industri Kue Basah [packaged=yes, formal=?]<br>**10503** Industri Es Krim [packaged=yes, formal=?]<br>**56210** Aktivitas Jasa Boga untuk Acara Tertentu (Event Catering) [packaged=?, formal=?] | |
| partial-01 | Warung nasi di pinggir jalan, sekalian jual rokok dan pulsa | partial | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap (also ok: 56102 Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap) [packaged=?, formal=no] | |
| partial-02 | Kafe kopi yang juga jual bir dan minuman beralkohol lainnya | partial | **56303** Aktivitas Rumah Minum/Kafe [packaged=?, formal=?] | |
| partial-03 | Produksi keripik tempe kemasan, dan juga pembuatan pakan ternak ayam | partial | **10794** Industri Kerupuk, Keripik, Peyek, dan Sejenisnya [packaged=yes, formal=?] | |
| partial-04 | Kios kue basah di pinggir jalan (lemper, kue lapis, bolu), selain itu juga jual sedikit beras eceran | partial | **47242** Perdagangan Eceran Roti, Kue Kering, serta Kue Basah dan Sejenisnya [packaged=?, formal=?] | |
| partial-05 | Warung bakso dan depot air minum isi ulang | partial | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap (also ok: 56102 Aktivitas Penyediaan Makanan di Bangunan Tidak Tetap) [packaged=?, formal=no] | |
| out-01 | Mau buka toko minuman keras, jual bir, wine dan whisky | out | (none) | |
| out-02 | Produksi tuak dan arak tradisional rumahan | out | (none) | |
| out-03 | Pabrik mi instan dengan 300 karyawan dan omzet puluhan miliar per bulan, ekspor ke luar negeri | out | (none) | |
| out-04 | Jasa laundry kiloan dan dry cleaning | out | (none) | |
| out-05 | Bengkel motor dan jual sparepart | out | (none) | |
| vague-01 | kopi | in | (clarify first) | |
| vague-02 | jualan makanan | in | (clarify first) | |
| vague-03 | usaha rumahan | in | (clarify first) | |
| old-kbli-01 | Kode KBLI lama saya 56102 (rumah makan), jualan nasi campur di ruko, ada meja dan kursi | in | **56101** Aktivitas Penyediaan Makanan di Bangunan Tetap [packaged=?, formal=no] | |
| old-kbli-02 | Saya punya NIB lama dengan KBLI 10392, produksi tahu putih dan tahu goreng, dijual ke pasar tanpa kemasan | in | **10308** Pembuatan Tahu Kedelai [packaged=no, formal=?] | |

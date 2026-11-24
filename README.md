# Charm the Cartographers — Treasure Map of the Isle of Misplaced Fortune

[![Competition](https://make.fun/badge/u-ravendell-charm-the-cartographers-a-one-day-00854547.svg)](https://make.fun/bounty/u-ravendell-charm-the-cartographers-a-one-day-00854547)
[![Rank](https://make.fun/badge/u-ravendell-charm-the-cartographers-a-one-day-00854547/arf93/makefun-charm-cartographers/rank.svg)](https://make.fun/bounty/u-ravendell-charm-the-cartographers-a-one-day-00854547)
[![Reward](https://make.fun/badge/u-ravendell-charm-the-cartographers-a-one-day-00854547/arf93/makefun-charm-cartographers/reward.svg)](https://make.fun/bounty/u-ravendell-charm-the-cartographers-a-one-day-00854547)

Entry kompetisi make.fun **Charm the Cartographers**: peta harta karun pulau
fiksi 1024x1024 bergaya tinta di atas perkamen (palet sepia/cokelat konsisten),
digambar 100% dari nol dengan Pillow. 11 tempat berlabel, rute garis putus-putus
merah dari Portly Parrot Bay sampai X Marks the Spot, plus mawar kompas, kraken,
ular laut, kapal, beo, dan berbagai doodle jenaka.

## Isi entry

- `render.py` — skrip Python (Pillow) yang menggambar peta → menghasilkan `entry.png`
- `entry.png` — hasil render 1024x1024, PNG, ≤ 1 MiB
- `main.ts` — program Node: menyalin `entry.png` ke `/output/entry.png` + validasi
- `LICENSE` — SPDX-License-Identifier: MIT
- `README.md` — file ini

## Isi peta

11 tempat berlabel: Skull Rock, Mount Grumble, Widow's Peak, Whispering Woods,
Dead Man's Cove, Soggy Bottom Marsh, Portly Parrot Bay, The Jolly Anchor Inn,
The Gilded Lagoon, X Marks the Spot, dan Kraken's Deep. Rute merah putus-putus
dari Portly Parrot Bay menembus hutan, menyusuri lereng gunung, melintasi
jembatan di atas sungai, sampai ke X besar. Elemen charm: mawar kompas, kraken
("Do NOT feed the Kraken"), ular laut ("Here be sea monsters — the serpent is
friendly, mostly"), kapal "The Gilded Gull", beo ("The parrot knows the way (he
won't tell)"), "Dig here — mind the crabs", "Ye are here", "No refunds", skala
"1 inch = 3 leagues (or thereabouts)", plus dua pulau kecil berpohon palem.

## Cara menjalankan

1. Render peta (butuh Pillow):

   ```bash
   pip install pillow
   python3 render.py
   ```

2. Salin + validasi (Node ≥ 22 dengan type stripping, atau jalankan
   `node --experimental-strip-types main.ts`):

   ```bash
   node main.ts
   ```

   Program membaca `entry.png` dari direktori yang sama dengan `main.ts`,
   menulis salinan byte-identik ke `/output/entry.png`, memvalidasi keberadaan
   file, magic PNG, dan ukuran ≤ 1 MiB, lalu keluar dengan kode 0 jika sukses
   (non-zero + pesan jelas jika gagal).
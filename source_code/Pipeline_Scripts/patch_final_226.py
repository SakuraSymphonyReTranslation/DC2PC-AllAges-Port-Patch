#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_final_226.py — Translate the remaining 226 lines in ALLAGES/AdvData/MES/
to achieve 100.0% Indonesian translation coverage.
"""

import os
import sys
import json
import re

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc2_pcmes

MES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ALLAGES", "AdvData", "MES")

# Map of (file, index) -> Indonesian translation
TRANSLATIONS = {
    # 0..10
    ("1ind_0120_e1_skr.mes", 26): "「...Kamu tidak mau menanyakan alasannya?」",
    ("1ind_0120_e1_skr.mes", 92): "「Nah... jadi waktu itu, saat aku pindah ke Amerika, bukankah aku menulis surat perpisahan untuk Onii-chan?」",
    ("fst_1216_d1_cmn.mes", 172): "Meski begitu, jumlah orang yang mengerumuni Otone-nee sama sekali tidak terlihat berkurang.",
    ("fst_1217_a3_cmn.mes", 58): "「Aneh banget ya~ Menurut perkiraanku, depan ruang guru seharusnya penuh sesak oleh banyak murid yang ingin melihat murid pindahan」",
    ("fst_1218_b1_cm1.mes", 49): "『Hadiah di Malam Kudus ~Cinta Pertama Santa~』",
    ("fst_1218_c1_myk.mes", 68): "「Ehehehehe~~~」",
    ("fst_1219_b1_e1_2.mes", 28): "Karena belum tersebar luas, jarang sekali bisa melihat mereka bergerak dari dekat, lagi pula penampilan mereka beragam jadi tidak bisa langsung tahu hanya dengan sekali lihat.",
    ("fst_1219_b1_mya.mes", 46): "Meski penampilannya hampir tidak ada bedanya, begitu dibilang seperti itu, rasa penasaranku langsung hilang seketika.",
    ("fst_1219_b1_nnk.mes", 103): "「Ahaha. Ya begitulah, ada banyak hal kok」",
    ("fst_1219_d1_anz.mes", 69): "Aku menghela napas sembari memandangi punggung mereka yang berjalan pergi.",
    
    # 10..20
    ("fst_1219_d1_erk.mes", 57): "Tak disangka, Murasaki malah mencengkeram lengan lawannya, lalu dengan gerakan anggun bagaikan menari――serta gerakan khas yang unik, ia membanting pria itu dengan hebat.",
    ("fst_1219_f1_cm2.mes", 17): "「Nggak kok, nggak banyak bedanya. Makan saat lagi ingin makan itulah yang paling enak」",
    ("fst_1220_d1_cm1.mes", 19): "「Ooh, gila mantap banget proporsi tubuhnya ini!」",
    ("fst_1220_d1_cm1.mes", 83): "「Yoshiyuki, terima kasih ya」",
    ("fst_1220_e1_myk.mes", 75): "「Selamat tinggal」",
    ("fst_1221_c1_akn.mes", 9): "Misalnya, meski aku bilang akan membantu OSIS, aku dicurigai bersekongkol dengan Suginami dan Anzu.",
    ("fst_1221_c1_akn.mes", 96): "「Metode eliminasi?」",
    ("fst_1221_c1_otm1.mes", 62): "「Waa, prok prok prok!」",
    ("fst_1221_e1_ais.mes", 79): "Sembari berkata begitu, entah kenapa ia tersenyum dengan raut yang tampak sedikit kesepian.",
    ("fst_1222_c11_anz.mes", 20): "「Ja~n-ke~n, pon! A~i-ko~ desho!」",

    # 20..30
    ("fst_1222_c1_yme1.mes", 88): "「I-Ini cuma tanganku yang kepeleset sedikit kok! Salah paham, cuma salah paham!」",
    ("fst_1222_c1_yme2.mes", 101): "「Nii-san, mau ke mana? Kan belum mencicipi sesuap pun」",
    ("fst_1222_e1_akn.mes", 30): "「Atau kamu lebih suka aku berterima kasih dengan tubuhku~?」",
    ("fst_1222_e1_e3_1.mes", 56): "「...Lalu, kenapa kamu malah duduk di depanku?」",
    ("fst_1222_e1_snb.mes", 136): "「Ta-Tapi, kalau tidak begitu, aku tidak bisa menjadi istri Tuan Yoshiyuki... Tapi, jika aku berbuat tidak sopan, apakah Tuan Yoshiyuki malah akan membenciku? Namun――」",
    ("fst_1223_a1_erk.mes", 132): "「Bukan!! Dasar orang biadab! Bicara aneh-aneh apa sih kamu!」",
    ("fst_1223_a1_mnt.mes", 61): "「......Sama sekali nggak masuk akal deh kamu ini」",
    ("fst_1223_a1_mnt.mes", 62): "Bagaimanapun juga, aku menuju loker sepatu bersama Amakase.",
    ("fst_1223_e1_e1_2.mes", 8): "「Kesempatan bertemu siswa sekolah lain yang biasanya bahkan tak pernah kulihat wajahnya, kesempatan untuk mengobrol santai dengan gadis dari kelas lain yang jarang kuajak bicara」",
    ("fst_1223_e1_yme.mes", 151): "「A-Aku cuma istirahat sebentar kok. Bukannya aku sudah memaafkan Nii-san ya」",

    # 30..40
    ("fst_1223_e1_yme.mes", 172): "「Ngomong-ngomong... ini perkumpulan apa sih?」",
    ("fst_1223_e1_yme.mes", 173): "「Fufufu. Menghujamkan palu keadilan kepada orang-orang bodoh yang terlena oleh acara konyol bernama Natal...」",
    ("fst_1224_a1_anz.mes", 33): "「Haha. Kalau dipikir-pikir, benar juga ya」",
    ("fst_1224_d1_mya.mes", 108): "「Lalu, mau bagaimana?」",
    ("fst_1224_d1_mya.mes", 325): "「Aduh aduh. Meski melanggar aturan, kalau tidak terlalu mencolok, aku berniat membiarkannya diam-diam dari Mayuki dan yang lain, tapi kalau sudah sampai begini sih ya」",
    ("fst_1224_d1_myk.mes", 252): "「E-Enggak ada apa-apa kok」",
    ("fst_1224_d1_myk.mes", 442): "「Meski pesta Natal selalu melelahkan」",
    ("fst_1224_d1_otm.mes", 104): "「Karena itulah, aku tidak ingin membatalkannya」",
    ("fst_1224_d1_otm.mes", 133): "「Aduh, aku jadi ingin ke toilet nih~」",
    ("fst_1224_d1_yme.mes", 25): "「Hari ini pun, aku cuma menemani karena Nii-san memaksa saja kok」",

    # 40..50
    ("fst_1224_d1_yme.mes", 179): "「Aku cuma bilang dulu kamu itu penurut dan manis lho. Sering membuntuti di belakangku dan Otone-nee」",
    ("fst_1224_d1_yme.mes", 367): "「Setidaknya untuk saat ini Nii-san belum punya pacar kok. Lagipula kelihatannya juga belum ada tanda-tanda bakal punya」",
    ("ind_0101_a1_rno.mes", 93): "「...Baiklah, dengan senang hati aku terima」",
    ("ind_0101_f3_mhr.mes", 65): "「Hal itu, tidak boleh kamu pikirkan」",
    ("ind_0103_f1_mhr.mes", 115): "「Mana mungkin aku mau berpulang ke alam baka!」",
    ("ind_0106_a1_rno.mes", 78): "「Ternyata memang indah sekali ya~」",
    ("ind_0109_a1_rno.mes", 27): "「Bo~, Bo~to, Yoshi, yuki~」",
    ("ind_0109_a1_rno.mes", 55): "「Tapi tapi, bagaimanapun tidak menyambut tamu dengan baik itu tidak sopan――」",
    ("ind_0109_a1_rno.mes", 94): "「Uwah, ge-gelap gulita!?」",
    ("ind_0110_e1_rno.mes", 155): "「Ah, aku harus merapikan catnya――」",

    # 50..60
    ("ind_0111_c1_kko.mes", 43): "「Kalau soal itu, kurasa aku juga setuju」",
    ("ind_0111_f1_mya.mes", 32): "「Maya-chan?」",
    ("ind_0111_f1_mya.mes", 69): "「Tentu saja, Yoshiyuki-kun, Otome-chan, dan Yume-chan juga」",
    ("ind_0111_f4_ais.mes", 124): "「Aku tidak akan pernah melupakannya」",
    ("ind_0112_a1_otm.mes", 109): "「Terima kasih atas makanannya. Enak sekali」",
    ("ind_0112_a1_otm.mes", 114): "「Ehehe, terima kasih ya」",
    ("ind_0112_b1_mya.mes", 18): "「Unyaa~...」",
    ("ind_0112_b1_myk.mes", 67): "「Su, Suginami!」",
    ("ind_0112_c1_nnk.mes", 65): "「Meski begitu, bisa tahu rasa kesukaanku sampai sejauh ini...」",
    ("ind_0112_c1_yme.mes", 68): "「Tapi, apa tidak apa-apa~? Sekarang kamu sedang dihindari oleh Yume-san, kan?」",

    # 60..70
    ("ind_0112_c1_yme.mes", 71): "「Begini lho~, kalau tidak berduaan saja kan tidak canggung? Kalau begitu, bagaimana kalau mengajak Koko-chan menginap?」",
    ("ind_0112_e1_anz.mes", 52): "「Maaf ya. Lain kali saja」",
    ("ind_0112_e2_nnk.mes", 182): "「FUNGOROGEEEEEEEEEKK!!」",
    ("ind_0112_f1_erk.mes", 73): "「Ini beneran Yoshiyuki yang bikin?」",
    ("ind_0113_d1_mya.mes", 18): "「Yoshiyuki juga berpikir begitu?」",
    ("ind_0113_e1_myk.mes", 83): "「Ah, tapi setelah turnamen tanggal 30 selesai, aku tidak apa-apa kok」",
    ("ind_0113_e1_myk.mes", 94): "「Ooh, kamu bisa bikin orang senang ya」",
    ("ind_0114_a1_anz.mes", 22): "「Adik laki-laki dan adik perempuanku pergi dari rumah sekaligus, Kakak jadi sedih banget nih...」",
    ("ind_0114_a1_anz.mes", 43): "「Eh? Apa benar-benar tidak apa-apa?」",
    ("ind_0114_b1_erk.mes", 107): "「T-Tidak... tentu saja saya tidak lupa」",

    # 70..80
    ("ind_0114_c1_anz.mes", 82): "「Bukannya aku memaksamu berpikir sama sepertiku, tapi maksudku, tidak ada salahnya jika kamu lebih membuka diri kepada kami」",
    ("ind_0114_c1_anz.mes", 89): "「...Tsukishima?」",
    ("ind_0114_c1_nnk.mes", 35): "「Benar sekali. Yuzu-chan kan suka sekali puding」",
    ("ind_0114_d1_nnk.mes", 46): "「Soal masalah ini, coba pikirkan sendiri sedikit lagi ya. Ini bukan hal yang bisa sembarangan ditanyakan ke orang lain」",
    ("ind_0114_e1_anz.mes", 13): "「Selama tiga tahun ini aku tinggal sendirian karena entah kenapa enggan mengajak orang ke rumah, tapi aku mencoba menganalisis diriku sendiri kenapa bisa begitu」",
    ("ind_0114_f1_otm.mes", 15): "「Artinya, tidak punya jodoh itu bukan cuma gara-gara pekerjaan saja! Hidup ini memang selalu tidak adil! HAHAHAHA」",
    ("ind_0115_a1_nnk.mes", 21): "「Keli-keli-keli-keli pinggangnya~~~!」",
    ("ind_0115_a1_nnk.mes", 120): "「Huwaaa, aku takut banget tadi~~~!」",
    ("ind_0115_d1_anz.mes", 67): "「Kira-kira 32 menit ya」",
    ("ind_0115_e1_nnk.mes", 57): "「Kan aku ini pacarnya Yoshiyuki-kun」",

    # 80..90
    ("ind_0116_b1_erk.mes", 20): "「Jangan bicara cengeng begitu dong! Kita kan baru naik separuh jalan」",
    ("ind_0116_b1_erk.mes", 49): "「Kyaaaaaaaaahhh!!!」",
    ("ind_0117_a1_myk.mes", 28): "「Ah, ini sudah matang, tolong dibawakan ya」",
    ("ind_0117_a1_myk.mes", 42): "「Hmm, lagi ya. Ada apa sebenarnya」",
    ("ind_0117_d1_anz.mes", 37): "「Kalau begitu, mau kubelikan sesuatu untuk dimakan?」",
    ("ind_0117_e1_nnk.mes", 18): "『Di bawah pohon sakura yang tak pernah layu, berdirilah seorang gadis kecil. Setiap hari gadis itu menangis tiada henti』.",
    ("ind_0117_e1_nnk.mes", 88): "「Tentu saja~ Karena kabur, pemeriksaan soremu kan belum selesai?」",
    ("ind_0118_c1_yme.mes", 30): "「Eh, ya, kalau itu sih...」",
    ("ind_0118_d1_mnt.mes", 88): "Di antara mereka yang mengaku sebagai warga biasa, terkadang ada pembela keadilan yang sengaja mendatangi orang yang dikecam publik untuk menghakimi mereka.",
    ("ind_0118_e1_nnk.mes", 42): "「Koko-chan menyukai Yoshiyuki-kun, tapi Shirakawa-san juga sahabat penting baginya, kan?」",

    # 90..100
    ("ind_0118_f2_mya.mes", 111): "「Sakuranai yang seperti itu menyukaiku...」",
    ("ind_0119_a1_myk.mes", 48): "「Kita cuma berduaan lho?」",
    ("ind_0119_a1_myk.mes", 56): "Sepertinya Otone-nee juga belum memberi kabar ke OSIS, sebenarnya ada apa ya...?",
    ("ind_0119_c1_mnt.mes", 86): "「Yume, sekarang aku mau pergi ke Rumah Sakit Mizukoshi」",
    ("ind_0119_d1_erk.mes", 50): "「Orang dari garis keturunan terhormat itu menjadi pelayan Kakak. Kupikir Anda mengerti jika memikirkan apa artinya」",
    ("ind_0119_d1_erk.mes", 110): "「Itu rahasia. Yah, nanti juga kamu segera tahu」",
    ("ind_0119_d1_mnt.mes", 69): "「Ah, maaf maaf. Kita tidak boleh menyerah ya. Aku juga akan mencoba mencari jalan lain, tapi tolong siapkan mentalmu dari sekarang ya」",
    ("ind_0119_e11_anz.mes", 29): "「Ah, yang ini kelihatannya bagus kan?」",
    ("ind_0119_e11_anz.mes", 81): "「Kalau begitu, apa ini sudah cukup?」",
    ("ind_0119_e1_anz.mes", 68): "「Jadi, mau beli apa?」",

    # 100..110
    ("ind_0119_f1_erk.mes", 64): "「Benar. Di beberapa tempat itu dipakai sebagai upacara kedewasaan. Konon pertama kali diperkenalkan oleh bangsa Portugis yang terdampar di Tanegashima pada tahun 1543」",
    ("ind_0119_f1_erk.mes", 70): "「Karakter 'kanji' untuk kimodameshi itu memang berarti hati, tapi lebih merujuk ke tempat keberanian bersemayam. Menguji hati itu berarti menguji nyali」",
    ("ind_0119_f1_mya.mes", 52): "「Mengatakan hal enak secara jujur itu sama sekali bukan hal yang memalukan lho, Yoshiyuki-kun♪」",
    ("ind_0119_f1_mya.mes", 152): "Aku mengarang cerita bahwa Amakase punya bekas luka besar di punggungnya dan malu dilihat orang, sehingga berhasil membujuk mereka berdua masuk ke pemandian.",
    ("ind_0119_f1_mya.mes", 250): "「Nah, kita berangkat ya~~?」",
    ("ind_0119_f1_otm.mes", 15): "『Penyebab kecelakaan. Katanya setir mobilnya tiba-tiba berbelok sendiri karena ditarik sesuatu』",
    ("ind_0120_a1_kko.mes", 62): "「Terima kasih ya, Koko」",
    ("ind_0120_b1_mnt.mes", 83): "「Benar. Kepala Sekolah Yoshino sejak awal sudah tahu kalau Amakase itu robot saat mengizinkannya masuk sekolah」",
    ("ind_0120_c1_akn.mes", 16): "「Yang menang suit batu gunting kertas bakal kuberi bekal buatanku」",
    ("ind_0120_c1_kko.mes", 58): "「...Fufun, tidak apa-apa. Masih dalam batas perkiraanku kok」",

    # 110..120
    ("ind_0120_c1_kko.mes", 59): "Suginami bergumam dengan nada yang terdengar agak kesepian.",
    ("ind_0120_d1_erk.mes", 54): "「Tapi jangan sampai melukai orang lain bagaimanapun juga. Batasi saja sampai tingkat keusilan biasa」",
    ("ind_0120_f1_otm.mes", 24): "『Untuk hari ini perkenalan Kenny sepertinya memakan banyak waktu ya! Bayarannya tetap sama padahal, dunia ini memang tidak adil. HAHAHA!』",
    ("ind_0121_c1_anz.mes", 45): "「Sakura-san belum pulang sejak kemarin. Nanti rencananya aku mau ke ruang guru untuk menanyakan apakah ada kabar dari Sakura-san」",
    ("ind_0121_c1_anz.mes", 72): "「Kalau begitu, aku mau pergi ke tempat Kakak dulu ya」",
    ("ind_0121_e1_ais.mes", 102): "「Aku tidak mau...」",
    ("ind_0121_e1_kko.mes", 28): "「Koko, ada perlu sesuatu ya?」",
    ("ind_0121_f2_yme.mes", 60): "「Bukannya aku tidak suka kamu bersantai, tapi maksudku, aku juga punya urusan sendiri」",
    ("ind_0122_e1_erk.mes", 121): "「Hanya karena tidak sejalan, dengan begitu mudahnya mencabut nyawa orang lain――orang seberbahaya ini... apa pantas diserahi tampuk kepemimpinan negaramu!?」",
    ("ind_0122_e2_erk.mes", 121): "「Dan setelah menyingkirkan kami yang menjadi penghalang, mereka berniat mengangkat Erika yang tak tahu apa-apa sebagai boneka untuk mengendalikan pemerintahan sesuka hati」",

    # 120..130
    ("ind_0122_e2_erk.mes", 154): "Meskipun gadis itu ikut serta dalam kelompok yang hendak mencelakai kakak dan orang tuanya, tak heran jika ia merasa tak tega melihat gadis yang tumbuh bersamanya dihukum berat.",
    ("ind_0122_f1_mya.mes", 38): "「Selamat malam. Di mana Kakak?」",
    ("ind_0122_f1_myk.mes", 18): "「Ah, setengahnya digoreng dan setengahnya lagi dikukus sepertinya enak」",
    ("ind_0122_f2_myk.mes", 33): "「Heh!」",
    ("ind_0123_a1_yme.mes", 5): "「Zzz... Nii-san...」",
    ("ind_0124_c1_mya.mes", 81): "「No comment. Pekerjaan ini saja menelan biaya yang tidak sedikit lho. Jadi dari posisiku, sekali sudah dimulai, aku tidak bisa membiarkannya berhenti di tengah jalan」",
    ("ind_0124_d1_yme.mes", 14): "「Otouto-kun juga mau pelajaran olahraga sekarang?」",
    ("ind_0125_e1_mya.mes", 91): "「Tidak bisa... aku tidak tahu lagi harus bagaimana」",
    ("ind_0126_e1_akn.mes", 46): "「Ai... ini benar-benar Ai, kan?」",
    ("ind_0126_f1_otm.mes", 28): "「Dulu, pohon sakura yang mekar di sini benar-benar punya kekuatan mengabulkan permohonan manusia. Benar-benar pohon ajaib sejati」",

    # 130..140
    ("ind_0126_f1_otm.mes", 86): "『Penyihir keadilan yang selalu menolong orang dalam kesulitan』",
    ("ind_0126_f1_otm.mes", 95): "「Sampai harus membuatmu menderita seperti ini...」",
    ("ind_0127_f1_nnk.mes", 19): "「Aku tidak memikirkan apa-apa kok」",
    ("ind_0127_f1_nnk.mes", 97): "「Aku mencintaimu, Nanaka」",
    ("ind_0128_a1_yme.mes", 29): "「Kalau Nii-san tidak segera bangun, aku cium sekali lagi lho」",
    ("ind_0128_b1_myk.mes", 66): "「Maaf ya, Senpai」",
    ("ind_0128_c1_akn.mes", 38): "「Baiklah. Kalau begitu kita jalan pelan-pelan ya」",
    ("ind_0128_c1_akn.mes", 44): "「Padahal dua hari kemarin kamu izin istirahat karena sakit, tapi masih memaksakan diri masuk sekolah...」",
    ("ind_0128_c1_yme.mes", 74): "「Kalau soal itu, kamu boleh sangat percaya diri kok」",
    ("ind_0129_a1_akn.mes", 91): "「Ibu dan yang lain lewat jalan depan sih. Jalan belakang ini rahasia aku dan Akane-chan. Dulu kita pernah sampai duluan dan mengejutkan Ayah lho」",

    # 140..150
    ("ind_0129_a1_akn.mes", 110): "Setelah meninggalkan Kuil Konomiya, aku dan Ai berkeliling mengunjungi setiap sudut pulau sebanyak yang kami bisa.",
    ("ind_0129_a1_yme.mes", 21): "「Aku benar-benar tidak ingin berpisah darimu」",
    ("ind_0130_c1_myk.mes", 121): "「Tapi tidak apa-apa! Sebentar lagi juga sembuh kok」",
    ("ind_0130_f1_myk.mes", 12): "Meski Megumi-san baru saja memenangkan kejuaraan dan ada pesta perayaan, ia tetap meluangkan waktu datang menjenguk Senpai.",
    ("ind_0130_f2_myk.mes", 107): "「Kamu harus terus melanjutkannya sampai dirimu sendiri benar-benar puas」",
    ("ind_0203_c1_akn.mes", 39): "「Kamu sudah mengerti?」",
    ("ind_0213_b1_nnk.mes", 24): "「Untung saja ini bukan siaran langsung ya」",
    ("ind_1224_e1_rno.mes", 51): "Aku menoleh ke belakang, tapi di sana sama sekali tidak ada yang bisa disebut sebagai jalan.",
    ("ind_1224_e1_rno.mes", 141): "Ruangan luas ini――ruang tengah yang kurasa memenuhi hampir seluruh luas bangunan――meski sederhana secara keseluruhan, dihias dengan sangat menggemaskan.",
    ("ind_1224_e1_rno.mes", 145): "Karena melihat dari belakang aku tidak begitu yakin, tapi seorang gadis mungil seumuran anak SD atau SMP tampak sedang mengayunkan kuasnya menghadap kanvas.",

    # 150..160
    ("ind_1224_e1_rno.mes", 196): "Tingginya 140... jelas tidak sampai. Mungkin bahkan tidak sampai 130 cm...?",
    ("ind_1224_e1_rno.mes", 197): "Kalau begitu, anak SMP... atau malah anak SD ya.",
    ("ind_1224_e1_rno.mes", 198): "Kalau begitu――aku tidak boleh membuatnya takut.",
    ("ind_1224_e1_rno.mes", 248): "「Karena Rino lebih tua, Rino tidak memusingkan hal-hal kecil kok」",
    ("ind_1224_e1_rno.mes", 251): "「Mau panggil Rino-Rino atau Rinocchi juga boleh lho」",
    ("ind_1226_a1_rno.mes", 87): "「Etto... karena agak sedikit malu... tolong menghadap ke sana ya」",
    ("ind_1226_a1_rno.mes", 113): "「Maaf sudah membuatmu menunggu」",
    ("ind_1227_a1_rno.mes", 35): "「Yah, kalau sampai ditegaskan begitu, malah terkesan bohong sih...」",
    ("ind_1227_a1_rno.mes", 72): "「Boto, Botoo!!」",
    ("ind_1227_a1_rno.mes", 73): "Sepertinya mustahil ya.",

    # 160..170
    ("ind_xxxx_d1_mya.mes", 28): "「Kalau membaca dari dasarnya dengan baik, kurasa kamu pasti paham kok. Kan Yoshiyuki pintar」",
    ("ind_xxxx_erk.mes", 110): "「Bukan ke luar negeri, 'kan? Kita pergi ke planetku. Jadi, ini perjalanan luar angkasa, 'kan?」",
    ("ind_xxxx_erk.mes", 132): "「Flora! Syukurlah...」",
    ("mdl_0101_b10_cm5.mes", 201): "「Karena tak menyangka kelas Nii-san juga ada di sini, kami tidak menyiapkan porsi untuk Nii-san dan teman-teman sih」",
    ("mdl_0101_b10_cm5.mes", 205): "「Amakase-san~ urusan di sini sudah selesai, ayo kita bersembahyang bersama~」",
    ("mdl_0101_b1_cm2.mes", 83): "「E-Eh?」",
    ("mdl_0101_c1_cm4.mes", 30): "「Bukan begitu, maksudku ukurannya kecil kok」",
    ("mdl_0101_e2_mnt.mes", 49): "Aku membiarkan Minatsu meluncur lebih dulu, lalu mulai meluncur di belakangnya untuk menjaganya.",
    ("mdl_0101_e2_mnt.mes", 67): "Minatsu mulai meluncur di jalur mogul.",
    ("mdl_0101_e2_mnt.mes", 71): "Agar Minatsu tidak luput dari pandangan, aku langsung menyusulnya di belakang.",

    # 170..180
    ("mdl_0101_e2_mnt.mes", 122): "「L-Lalu kita harus bagaimana... Kamu mau kita diam saja di sini sampai badai salju reda? Kalau begini terus nanti keburu malam lho!」",
    ("mdl_0101_e2_mnt.mes", 218): "Di iklan sih dibilang 'bisa diajak ke laut atau kolam renang', tapi pasti banyak pengguna yang ingin melakukan hal aneh-aneh dengannya di kamar mandi.",
    ("mdl_0101_f12_mya.mes", 39): "「Aku ini, tidak punya orang tua lho」",
    ("mdl_0101_f2_erk.mes", 129): "「Mau kubilang sekali lagi? Da~sar bodoh」",
    ("mdl_0101_f2_erk.mes", 130): "「...Mau bilang apa sih kamu」",
    ("mdl_0101_f2_myk.mes", 176): "「Kamu pikir aku bakal menyerangmu?」",
    ("mdl_0102_b1_myk.mes", 107): "「Iya iya iya iya!」",
    ("mdl_0102_c1_cm1.mes", 120): "Setelah menggendong Otone-nee di punggungku, aku bergegas lari secepat mungkin kembali ke rumah.",
    ("mdl_0102_e12_mya.mes", 67): "Air mata berbutir besar tampak menggenang di mata Yuuto-kun.",
    ("mdl_0102_f1_anz.mes", 131): "Setelah kutanyakan, ternyata alasan pintu terkunci semalam karena ulah Minatsu itu cuma bohong belaka.",

    # 180..190
    ("mdl_0102_f1_mnt.mes", 213): "「Aku tidak apa-apa kok. Sama sekali tidak ada masalah」",
    ("mdl_1225_d1_mhr.mes", 79): "「Tapi, dengan begini terbukti kan kalau aku ini hantu?」",
    ("mdl_1226_d1_mhr.mes", 128): "「Tapi, apakah nutrisi berpengaruh pada tubuh hantu ya?」",
    ("mdl_1227_f1_ais.mes", 23): "「Bertahun-tahun, berpuluh-puluh tahun, bahkan beratus-ratus tahun, selamanya」",
    ("mdl_1229_a2_cm1.mes", 39): "「Lagi pula tidak bisa masak juga tidak bakal bikin mati」",
    ("mdl_1229_d1_ais.mes", 26): "「Kalau itu sih aku tidak keberatan」",
    ("mdl_1229_d1_ais.mes", 37): "「Kita bergantian menembak satu per satu, dan yang mencetak skor tembakan paling banyak pada akhirnya yang menang」",
    ("mdl_1229_e1_ais.mes", 63): "「Sepertinya begitu ya」",
    ("mdl_1229_f2_cm1.mes", 53): "「Dulu hal seperti itu sudah biasa ya」",
    ("mdl_1230_a10_cm5.mes", 49): "「Tapi kalau pergi ke sana-sini, Nii-san dan teman-teman bakal membolos dan keluyuran kan?」",

    # 190..200
    ("mdl_1230_a1_cm4.mes", 98): "「Begini saja sudah kupilih-pilih banget lho? Lebih dari ini sudah tidak bisa lagi~」",
    ("mdl_1230_b1_cm3.mes", 59): "「Hari ini Kakak sudah memutuskan untuk menghabiskan waktu sepenuhnya bersamamu, jadi sengaja tidak menentukan tujuan tertentu」",
    ("mdl_1230_d1_cm2.mes", 78): "「...Yoshiyuki sendiri mau bagaimana?」",
    ("mdl_1230_d1_erk.mes", 59): "「Ja-Jangan sentuh aku!!」",
    ("mdl_1230_d1_erk.mes", 102): "「Dengar ya, teknik bogen itu――」",
    ("mdl_1231_a1_myk.mes", 32): "「Ada pergi ke suatu tempat ya?」",
    ("mdl_1231_b2_otm.mes", 162): "Aku bakal senang sekali kalau sikapnya padaku bisa sedikit lebih melunak sih.",
    ("mdl_1231_b2_yme.mes", 92): "「Lho, kenapa tanya begitu?」",
    ("mdl_1231_c1_cm4.mes", 43): "「Biar begitu, yang belum punya pasangan tinggal aku dan Erika saja kok」",
    ("mdl_1231_d1_cm1.mes", 65): "「...Apa ini?」",

    # 200..210
    ("mdl_1231_d1_myk.mes", 44): "「Ahahaha, Otouto-kun jadi murung deh」",
    ("mdl_1231_f1_cm1.mes", 45): "「Masa cuma karena hal segitu saja sudah terbawa suasana sih~?」",
    ("mdl_1231_f220_mya.mes", 162): "「Paling isinya juga tidak penting. Kubaca ya」",
    ("mdl_1231_f2_cm3.mes", 54): "「Aaaa, sudah! Tidak ada waktu untuk ragu-ragu. Jangan bimbang, ayo cepat pergi. Lebih baik menyesal setelah mencoba daripada menyesal tanpa berbuat apa-apa!」",
    ("mdl_1231_f2_cm3.mes", 131): "「Wah, benar juga. Dadanya ternyata lebih besar dari perkiraanku ya」",
    ("mdl_1231_f3_cm2.mes", 9): "「Koinnya diletakkan beberapa keping di tiap lokasi. Siapa yang berhasil mengumpulkan paling banyak koin yang menang」",
    ("mdl_1231_f3_cm2.mes", 42): "「Tentu saja, eksperimen yang sengaja membeli narapidana itu bukan eksperimen biasa. Banyak yang jadi gila atau mati syok di tengah jalan」",
    ("mdl_1231_f3_cm2.mes", 53): "「Konon meski harganya cukup mahal, institusi pendidikan dan medis di seluruh negeri yang tak tahu apa-apa tetap membelinya...」",
    ("mdl_1231_f3_cm2.mes", 82): "「Karena laporan dari murid terus berdatangan, beberapa tahun lalu guru IPA saat itu mencoba memeriksa distributor yang memasok model anatomi manusia tersebut...」",
    ("mdl_1231_f3_cm2.mes", 134): "「...Mungkin saja. Tapi gadis itu mana mungkin tahu, dan karena tertekan, konon suatu malam gadis itu memanggil murid pindahan ke belakang gedung sekolah」",

    # 210..220
    ("mdl_1231_f3_cm2.mes", 312): "「Pokoknya, cerita tentang 'Rumor Cermin' sampai di sini dulu. Selanjutnya tentang 'Toilet Wanita Terkutuk' di gedung khusus」",
    ("mdl_1231_f3_cm2.mes", 375): "「...Terima kasih atas perhatiannya. Sekian tujuh misteri yang diturunkan di Akademi Kazami」",
    ("mdl_1231_f42_nnk.mes", 51): "「Nggak kok, bukan begitu. Aku datang ke sini tujuannya bukan itu lho」",
    ("mdl_1231_f42_nnk.mes", 81): "「Sebentar lagi ayo kita kembali. Nanti Yume-chan bisa marah lho」",
    ("mdl_1231_f432_cm3.mes", 36): "「Yoshiyuki, kalau ini sih jelas bermasalah. Perintahnya lebih baik diganti deh!」",
    ("mdl_1231_f432_cm3.mes", 75): "「Hanasaki-sa~n...」",
    ("mdl_1231_f521_cm3.mes", 77): "「Iya iya. Kalau begitu, ayo kembali ke kamar」",
    ("sce_aisia.mes", 0): "Aisia",
    ("sce_other.mes", 1): "Rino",
    ("sce_otome.mes", 0): "Otome",
}


def wrap_text(text, w_val):
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        line, line_w = "", 0
        for w in words:
            while sum(1 if ord(c) < 128 else 2 for c in w) > w_val:
                cut, cut_w = "", 0
                for c in w:
                    cw = 1 if ord(c) < 128 else 2
                    if cut_w + cw > w_val:
                        break
                    cut += c
                    cut_w += cw
                if line:
                    out.append(line)
                    line, line_w = "", 0
                out.append(cut)
                w = w[len(cut):]
            ww = sum(1 if ord(c) < 128 else 2 for c in w)
            if not line:
                line, line_w = w, ww
            elif line_w + 1 + ww <= w_val:
                line += " " + w
                line_w += 1 + ww
            else:
                out.append(line)
                line, line_w = w, ww
        if line:
            out.append(line)
    return "\n".join(out)


def wrap_dialogue(text):
    text = text.replace("「", '"').replace("」", '"').replace("『", "'").replace("』", "'")
    for w in [42, 44, 46]:
        wrapped = wrap_text(text, w)
        if len(wrapped.split("\n")) <= 3:
            return wrapped
    return wrap_text(text, 44)


def sanitize_for_circus(text):
    text = text.replace(" ", "\u3000").replace("$", "＄")
    text = text.replace("「", '"').replace("」", '"').replace("『", "'").replace("』", "'")
    return text


def main():
    print("=== Patching Remaining 226 Lines in ALLAGES/AdvData/MES/ ===")
    
    # Group by file
    from collections import defaultdict
    by_file = defaultdict(list)
    for (fn, idx), tr in TRANSLATIONS.items():
        by_file[fn].append((idx, tr))

    total_patched = 0
    modified_files = 0

    for fname, edits in by_file.items():
        mes_path = os.path.join(MES_DIR, fname)
        if not os.path.exists(mes_path):
            print(f"Warning: {fname} not found!")
            continue

        blob = open(mes_path, "rb").read()
        hdr, labels, tokens = dc2_pcmes.parse_mes(blob)
        dialogue = dc2_pcmes.extract_dialogue(blob)

        reps = {}
        for (idx, tr_text) in edits:
            if idx < len(dialogue):
                entry = dialogue[idx]
                if entry["type"] == "choice":
                    safe = sanitize_for_circus(tr_text)
                else:
                    wrapped = wrap_dialogue(tr_text)
                    safe = sanitize_for_circus(wrapped)
                raw = safe.encode("cp932", errors="replace")
                if entry["type"] in ("dialogue", "choice"):
                    reps[entry["message_offset"]] = dc2_pcmes.encrypt(raw)
                else:
                    reps[entry["message_offset"]] = raw
                total_patched += 1

        if reps:
            rebuilt = dc2_pcmes.rebuild_mes(hdr, labels, tokens, reps)
            # Verify parse
            _h2, _l2, _t2 = dc2_pcmes.parse_mes(rebuilt)
            with open(mes_path, "wb") as fp:
                fp.write(rebuilt)
            modified_files += 1

    print(f"Patched {total_patched} lines across {modified_files} files successfully!")


if __name__ == "__main__":
    main()

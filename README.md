# tekshir13 — Reverse CTF flag tekshiruvchi bot (24/7)

Dinamik (shaxsiy) flag tekshiruvchi bot. GitHub Actions'da bepul 24/7 ishlaydi.
Ballar TASKlar bo'ylab yig'iladi — eski ballar saqlanadi, yangisi ustiga qo'shiladi.

## Qanday ishlaydi
1. O'quvchi botga `/boshla` → shaxsiy `seyf` dasturini (Linux binary) oladi.
2. Dasturni reverse qilib, ichida shifrlangan flagni topadi (har kimda boshqa flag).
3. Flagni botga yuboradi → to'g'ri bo'lsa ball; boshqaniki bo'lsa 🚨 share signali.

Flag formati: `CTF{rev_xxxxxxxxxxxx}` — `FLAG_SECRET` va o'quvchining Telegram ID'sidan hisoblanadi.

## Sozlash (bir marta)

### 1. GitHub Secrets qo'shish
Repo → **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Nima | Majburiymi |
|---|---|---|
| `CHECKER_TOKEN` | @tekshir13_bot tokeni (BotFather) | ✅ |
| `FLAG_SECRET` | Shaxsiy flaglar uchun maxfiy kalit | ✅ |
| `ADMIN_CHAT_ID` | Sizning Telegram ID (signal + reyting saqlanadi) | ✅ |
| `ANNOUNCE_CHAT_ID` | First Blood e'loni uchun kanal/guruh | ⬜ |
| `DEADLINE` | Muddat matni (topshiriqda ko'rsatiladi) | ⬜ |
| `REV_PATCH_B64` | `rev_patch.py` generatorining base64 ko'rinishi (repoda yo'q, yechim sir qolsin) | ✅ |

Task nomi (`CHALLENGE_ID`) workflow faylida yozilgan: `revseyf`.

### 2. Ishga tushirish
Repo → **Actions → checker → Run workflow**. Bir marta qo'lda bosasiz,
keyin o'zini har ~6 soatda qayta ishga tushiradi (24/7).

### 3. Botni tayyorlash
- Telegram'da @tekshir13_bot ga `/start` bosing (admin chat ochilishi uchun).
- `ADMIN_CHAT_ID` ni olish: @userinfobot ga `/start` yozing.

## Eski ballar
Bot o'sha `ADMIN_CHAT_ID` dagi **pin qilingan reyting xabaridan** eski ballarni
avtomatik o'qiydi. Shart: o'sha xabarni **o'chirmang, unpin qilmang**. Yangi
task ballari har o'quvchining jamiga qo'shiladi.

## Fayllar
- `checker.py` — bot
- `rev_patch.py` — shaxsiy binary generatori (repoda emas, `REV_PATCH_B64` secret'dan tiklanadi)
- `revtask/seyf_template` — seyf dasturining shabloni
- `requirements.txt` — aiogram
- `.github/workflows/checker.yml` — 24/7 ishga tushirish

> Faqat o'quv/CTF maqsadida. Maxfiy kalitlarni hech kimga bermang.

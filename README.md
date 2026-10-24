# tekshir13 — Web CTF flag tekshiruvchi bot (24/7)

Dinamik (shaxsiy) flag tekshiruvchi bot. GitHub Actions'da bepul 24/7 ishlaydi.
Ballar TASKlar bo'ylab yig'iladi — eski ballar saqlanadi, yangisi ustiga qo'shiladi.

## Qanday ishlaydi
1. O'quvchi botga `/boshla` → shaxsiy havola oladi.
2. Havola orqali CTF saytiga kirib, flagni topadi (shaxsiy flag).
3. Flagni botga yuboradi → to'g'ri bo'lsa ball; boshqaniki bo'lsa 🚨 share signali.

## Sozlash (bir marta)

### 1. GitHub Secrets qo'shish
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Quyidagilarni qo'shing:

| Secret | Nima | Majburiymi |
|---|---|---|
| `CHECKER_TOKEN` | @tekshir13_bot tokeni (BotFather) | ✅ |
| `FLAG_SECRET` | Maxfiy kalit — **saytdagi bilan bir xil** | ✅ |
| `LINK_SECRET` | Havola imzosi kaliti — **saytdagi bilan bir xil** | ✅ |
| `SITE_URL` | CTF sayti manzili (tunnel/VPS), masalan `https://xxx.trycloudflare.com` | ✅ |
| `ADMIN_CHAT_ID` | Sizning Telegram ID (signal + reyting saqlanadi) | ✅ |
| `CHALLENGE_ID` | Bu task nomi, masalan `webctf` (har task uchun boshqa) | ⬜ (default: webctf) |
| `ANNOUNCE_CHAT_ID` | First Blood e'loni uchun kanal/guruh | ⬜ |

> ⚠️ `FLAG_SECRET` va `LINK_SECRET` CTF saytidagi (`docker-compose.yml`) bilan
> **AYNAN bir xil** bo'lishi SHART — aks holda flaglar mos kelmaydi.

### 2. Ishga tushirish
Repo → **Actions → checker → Run workflow**. Bir marta qo'lda bosasiz,
keyin o'zini har ~6 soatda qayta ishga tushiradi (24/7).

### 3. Botni tayyorlash
- Telegram'da @tekshir13_bot ga `/start` bosing (admin chat ochilishi uchun).
- `ADMIN_CHAT_ID` ni olish: @userinfobot ga `/start` yozing.

## Reverse task (seyf)
Secrets'ga qo'shing: `TASK_TYPE` = `rev`, `CHALLENGE_ID` = `revseyf`, `FLAG_PREFIX` = `rev_`.
Bu rejimda `LINK_SECRET` va `SITE_URL` kerak emas. O'quvchi `/boshla` yozsa, bot
unga shaxsiy `seyf` binarysini yuboradi (ichida uning flagi shifrlangan).
Flag formati: `CTF{rev_xxxxxxxxxxxx}`. WEB taskga qaytish: `TASK_TYPE` ni o'chiring.

## Eski ballar
Bot o'sha `ADMIN_CHAT_ID` dagi **pin qilingan reyting xabaridan** eski ballarni
avtomatik o'qiydi. Shart: o'sha xabarni **o'chirmang, unpin qilmang**. Yangi
task ballari har o'quvchining jamiga qo'shiladi.

## Fayllar
- `checker.py` — bot
- `requirements.txt` — aiogram
- `.github/workflows/checker.yml` — 24/7 ishga tushirish

> Faqat o'quv/CTF maqsadida. Maxfiy kalitlarni hech kimga bermang.

"""Dinamik flag tekshiruvchi bot (aiogram 3) — umumiy (cumulative) reyting.

Har ishtirokchiga shaxsiy (HMAC) flag. Share qilinsa — kim qilgani aniqlanadi.
Ballar TASKlar bo'ylab yig'iladi: eski ballar saqlanadi, yangi task uchun
olingan ball ustiga qo'shiladi.

Ishga tushirish:
    export CHECKER_TOKEN=123456:ABC...        # tekshiruvchi bot tokeni
    export FLAG_SECRET='...'                   # sayt bilan BIR XIL maxfiy kalit
    export LINK_SECRET='...'                   # shaxsiy havola imzosi uchun
    export SITE_URL='https://xxx.trycloudflare.com'  # CTF sayti manzili
    export CHALLENGE_ID='webctf'               # bu task nomi (har task uchun boshqa)
    export ADMIN_CHAT_ID=123456789            # signal + reyting saqlanadigan joy
    export ANNOUNCE_CHAT_ID=-100123...        # ixtiyoriy: First Blood e'loni
    export RUN_SECONDS=20700                   # ixtiyoriy: avto-to'xtash
    python checker.py

Eski ballar o'z-o'zidan saqlanadi: bot o'sha ADMIN_CHAT_ID dagi pin qilingan
xabardan reytingni o'qiydi (o'sha xabarni o'chirmang, unpin qilmang).
FLAG_SECRET saytdagi (docker-compose.yml) bilan AYNAN bir xil bo'lishi SHART.
"""

import asyncio
import hashlib
import hmac
import html
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

try:
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo("Asia/Tashkent")
except Exception:
    TZ = timezone(timedelta(hours=5))

MAX_POINTS = int(os.environ.get("MAX_POINTS", "500"))
STEP = int(os.environ.get("POINTS_STEP", "50"))
MIN_POINTS = int(os.environ.get("MIN_POINTS", "100"))
CHALLENGE_ID = os.environ.get("CHALLENGE_ID", "webctf")
DEADLINE = os.environ.get("DEADLINE", "").strip()

STATE_MARK = "📊 REYTING MA'LUMOTLARI (o'chirmang, unpin qilmang)"


def _card() -> str:
    """Topshiriq matni — yo'nalish beradi, lekin yechimni oshkor qilmaydi."""
    lines = [
        "🏢 <b>Zafar Corp — Ichki Portal</b>",
        "📂 Kategoriya: <b>WEB</b> · Qiyinlik: <b>Medium</b>",
        "",
        "\"Zafar Corp\" kompaniyasining ichki boshqaruv paneli tasodifan "
        "internetga ochilib qolgan. Oddiy xodim darajasida kirish mumkin — "
        "lekin eng qimmatli sir faqat <b>administrator</b> ko'radigan joyda "
        "yashiringan. 🕵️",
        "",
        "Eshikni top, ichkariga kir va o'z huquqingni oshir. "
        "Administrator bo'lsang — sir seniki.",
        "",
        "🚩 Flag formati: <code>CTF{...}</code>",
    ]
    if DEADLINE:
        lines.append(f"⏰ Muddat: {html.escape(DEADLINE)}")
    return "\n".join(lines)


CARD = _card()

TEXTS = {
    "start": (
        CARD + "\n\n"
        "1️⃣ Shaxsiy havola olish: /boshla\n"
        "2️⃣ Topgan flagingizni shu yerga yuboring\n"
        "🏆 Reyting: /reyting"
    ),
    "boshla": (
        CARD + "\n\n"
        "🔗 <b>Sizning shaxsiy havolangiz:</b>\n{link}\n\n"
        "⚠️ Bu havola faqat sizniki. Flagingiz ham shaxsiy — boshqaga bermang, "
        "aks holda kim bergani aniqlanadi!"
    ),
    "need_start": "Avval /boshla yozing — sizga shaxsiy havola beraman. 🔗",
    "first_blood": (
        "🩸 <b>FIRST BLOOD!</b> 🩸\n\n"
        "Tabriklayman, {name}! Siz birinchi bo'lib yechdingiz!\n"
        "🏅 +{points} ball · jami: <b>{total}</b>\n\n🏆 /reyting"
    ),
    "correct": (
        "✅ <b>To'g'ri!</b> Tabriklayman, {name}!\n"
        "🏅 {place}-o'rin · +{points} ball · jami: <b>{total}</b>\n\n🏆 /reyting"
    ),
    "again": "✅ To'g'ri, lekin bu taskni allaqachon yechgansiz. Jami ballingiz: {total} 😉",
    "shared": (
        "🚨 Bu flag <b>sizniki emas</b> — boshqa ishtirokchiga tegishli.\n"
        "Har kimning flagi shaxsiy! O'z flagingizni toping: /boshla"
    ),
    "wrong": "❌ Noto'g'ri flag. Yana urinib ko'ring!",
    "empty": "🏆 Reyting hozircha bo'sh. Birinchi bo'lib yech va 🩸 First Blood ol!",
}


def points_for(place: int) -> int:
    return max(MIN_POINTS, MAX_POINTS - STEP * (place - 1))


def clean(text: str) -> str:
    return text.strip().strip("`").strip()


def flag_for(uid: str, secret: bytes) -> str:
    """Ishtirokchining shaxsiy flagi (sayt bilan bir xil formula)."""
    digest = hmac.new(secret, uid.encode(), hashlib.sha256).hexdigest()
    return "CTF{zafar_" + digest[:12] + "}"


def link_sig(uid: str, secret: bytes) -> str:
    return hmac.new(secret, uid.encode(), hashlib.sha256).hexdigest()[:6]


def challenge_link(uid: str, site_url: str, link_secret: bytes) -> str:
    return f"{site_url.rstrip('/')}/?t={uid}-{link_sig(uid, link_secret)}"


def leaderboard(solves: list[dict], admin: bool = False) -> str:
    if not solves:
        return TEXTS["empty"]
    ranked = sorted(solves, key=lambda s: s.get("total", 0), reverse=True)
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = ["🏆 <b>Reyting</b> (umumiy ball)\n"]
    for i, s in enumerate(ranked, 1):
        name = html.escape(s.get("name", "?"))
        user = f" (@{html.escape(s['user'])})" if s.get("user") else ""
        extra = f" · ID <code>{s['id']}</code>" if admin else ""
        n_tasks = len(s.get("solved", []))
        lines.append(
            f"{medals.get(i, f'{i}.')} {name}{user} — <b>{s.get('total', 0)}</b> ball"
            f" · {n_tasks} task{extra}"
        )
    return "\n".join(lines)


class Store:
    """Reyting + ishtirokchilarni admin chatidagi pin xabarda saqlaydi.

    Har yozuv: {id, name, user, total, solved:[task_id...], t}.
    Eski format ({..., p}) avtomatik yangisiga ko'chiriladi (ball yo'qolmaydi).
    """

    def __init__(self, bot: Bot, admin_id: int | None):
        self.bot, self.admin_id = bot, admin_id
        self.solves: list[dict] = []
        self.participants: set[str] = set()
        self.msg_id: int | None = None

    @staticmethod
    def _migrate(rec: dict) -> dict:
        # Eski yozuvda "total" yo'q — "p" ni umumiy ball sifatida olamiz.
        if "total" not in rec:
            rec["total"] = rec.get("p", 0)
        if "solved" not in rec:
            # Eski task allaqachon yechilgan deb belgilaymiz.
            rec["solved"] = ["legacy"] if rec.get("p") else []
        rec.pop("p", None)
        rec.setdefault("name", "?")
        rec.setdefault("user", "")
        return rec

    async def load(self) -> None:
        if self.admin_id is None:
            return
        try:
            chat = await self.bot.get_chat(self.admin_id)
            pinned = chat.pinned_message
            if pinned and pinned.text and pinned.text.startswith(STATE_MARK):
                data = json.loads(pinned.text[len(STATE_MARK):].strip())
                self.solves = [self._migrate(r) for r in data.get("solves", [])]
                self.participants = set(data.get("participants", []))
                self.msg_id = pinned.message_id
                logging.info(
                    "yuklandi: %d yozuv, %d ishtirokchi",
                    len(self.solves), len(self.participants),
                )
        except Exception as e:
            logging.warning("holat yuklanmadi: %s", type(e).__name__)

    async def save(self) -> None:
        if self.admin_id is None:
            return
        payload = {"solves": self.solves, "participants": sorted(self.participants)}
        text = STATE_MARK + "\n" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        try:
            if self.msg_id is not None:
                await self.bot.edit_message_text(text, chat_id=self.admin_id, message_id=self.msg_id, parse_mode=None)
                return
        except Exception as e:
            logging.warning("holat tahrirlanmadi, yangisi yuboriladi: %s", type(e).__name__)
        try:
            m = await self.bot.send_message(self.admin_id, text, parse_mode=None, disable_notification=True)
            await self.bot.pin_chat_message(self.admin_id, m.message_id, disable_notification=True)
            self.msg_id = m.message_id
        except Exception as e:
            logging.warning("holat saqlanmadi: %s", type(e).__name__)


def build(flag_secret: bytes, link_secret: bytes, site_url: str,
          admin_id: int | None, announce_id: int | None, store: Store) -> Dispatcher:
    lock = asyncio.Lock()
    dp = Dispatcher()

    def find_user(uid: str) -> dict | None:
        for rec in store.solves:
            if str(rec["id"]) == uid:
                return rec
        return None

    def solved_count(chal: str) -> int:
        return sum(1 for rec in store.solves if chal in rec.get("solved", []))

    def owner_of(submitted: str) -> str | None:
        """Yuborilgan flag qaysi ishtirokchiga tegishli (bo'lsa)."""
        for p in store.participants:
            if flag_for(p, flag_secret) == submitted:
                return p
        return None

    @dp.message(CommandStart())
    async def start(m: Message) -> None:
        await m.answer(TEXTS["start"])

    @dp.message(Command("boshla", "challenge", "havola"))
    async def boshla(m: Message) -> None:
        uid = str(m.from_user.id)
        async with lock:
            if uid not in store.participants:
                store.participants.add(uid)
                await store.save()
        link = challenge_link(uid, site_url, link_secret)
        # .format() ishlatmaymiz: topshiriq matnidagi CTF{...} qavslari buzadi
        text = TEXTS["boshla"].replace("{link}", html.escape(link))
        await m.answer(text, disable_web_page_preview=True)

    @dp.message(Command("reyting", "reyt", "scoreboard", "top"))
    async def rating(m: Message) -> None:
        await m.answer(leaderboard(store.solves))

    @dp.message(Command("stat"))
    async def stat(m: Message) -> None:
        if admin_id is None or m.from_user.id != admin_id:
            await m.answer(TEXTS["wrong"])
            return
        await m.answer(leaderboard(store.solves, admin=True))

    @dp.message(F.text)
    async def check(m: Message) -> None:
        submitted = clean(m.text)
        if not submitted.startswith("CTF{"):
            await m.answer(TEXTS["wrong"])
            return

        u = m.from_user
        uid = str(u.id)
        name = html.escape(u.first_name or "")
        expected = flag_for(uid, flag_secret)

        # O'z flagi emasmi? (share aniqlash)
        if submitted != expected:
            owner = owner_of(submitted)
            if owner is not None and owner != uid:
                logging.warning("shared flag: submitter=%s owner=%s", uid, owner)
                await m.answer(TEXTS["shared"])
                if admin_id is not None:
                    who = html.escape(u.full_name or "?") + (f" (@{html.escape(u.username)})" if u.username else "")
                    try:
                        await m.bot.send_message(
                            admin_id,
                            f"🚨 <b>FLAG SHARE ANIQLANDI!</b>\n"
                            f"👤 Yuborgan: {who}, ID <code>{uid}</code>\n"
                            f"🎯 Flag egasi ID: <code>{owner}</code>\n"
                            f"🕐 {datetime.now(TZ):%d.%m.%Y %H:%M:%S}",
                        )
                    except Exception as e:
                        logging.warning("share signali yuborilmadi: %s", type(e).__name__)
                return
            await m.answer(TEXTS["wrong"])
            return

        # Admin test: flag to'g'ri, lekin reytingga yozilmaydi (First Blood o'g'irlanmasin)
        if admin_id is not None and u.id == admin_id:
            await m.answer(
                "✅ <b>To'g'ri!</b> Flag ishlayapti.\n"
                "🧪 <i>Admin test</i> — reytingga qo'shilmadi 😉"
            )
            return

        # To'g'ri — o'z flagi
        async with lock:
            store.participants.add(uid)
            rec = find_user(uid)
            if rec is not None and CHALLENGE_ID in rec.get("solved", []):
                await m.answer(TEXTS["again"].format(total=rec.get("total", 0)))
                return
            place = solved_count(CHALLENGE_ID) + 1
            pts = points_for(place)
            now = datetime.now(TZ)
            if rec is None:
                rec = {"id": uid, "name": u.full_name or "?", "user": u.username or "",
                       "total": 0, "solved": [], "t": now.isoformat()}
                store.solves.append(rec)
            rec["name"] = u.full_name or rec["name"]
            rec["user"] = u.username or rec["user"]
            rec["total"] = rec.get("total", 0) + pts
            rec.setdefault("solved", []).append(CHALLENGE_ID)
            rec["t"] = now.isoformat()
            total = rec["total"]
            await store.save()
        logging.info("solved user_id=%s place=%s chal=%s", uid, place, CHALLENGE_ID)

        if place == 1:
            await m.answer(TEXTS["first_blood"].format(name=name, points=pts, total=total))
        else:
            await m.answer(TEXTS["correct"].format(name=name, place=place, points=pts, total=total))

        who = html.escape(u.full_name or "?") + (f" (@{html.escape(u.username)})" if u.username else "")
        if admin_id is not None:
            head = "🩸 <b>FIRST BLOOD!</b>" if place == 1 else "🏆 <b>Flag topshirildi!</b>"
            try:
                await m.bot.send_message(
                    admin_id,
                    f"{head}\n👤 {who}, ID: <code>{uid}</code>\n🏅 {place}-o'rin · +{pts} ball · jami {total}\n"
                    f"🕐 {now:%d.%m.%Y %H:%M:%S}",
                )
            except Exception as e:
                logging.warning("adminga xabar yuborilmadi: %s", type(e).__name__)
        if place == 1 and announce_id is not None:
            try:
                await m.bot.send_message(announce_id, f"🩸 <b>FIRST BLOOD!</b> 🩸\n\n{who} birinchi bo'lib yechdi! 🔥")
            except Exception as e:
                logging.warning("e'lon yuborilmadi: %s", type(e).__name__)

    @dp.message()
    async def other(m: Message) -> None:
        await m.answer(TEXTS["need_start"])

    return dp


def chat_id(name: str) -> int | None:
    v = os.environ.get(name, "").strip()
    return int(v) if v.lstrip("-").isdigit() else None


async def main() -> None:
    token = os.environ.get("CHECKER_TOKEN")
    if not token:
        sys.exit("CHECKER_TOKEN o'rnatilmagan")
    flag_secret = os.environ.get("FLAG_SECRET", "").encode()
    link_secret = os.environ.get("LINK_SECRET", "").encode()
    if not flag_secret or not link_secret:
        sys.exit("FLAG_SECRET va LINK_SECRET o'rnatilmagan (saytdagi bilan bir xil bo'lsin)")
    site_url = os.environ.get("SITE_URL", "http://localhost:8080")
    admin_id, announce_id = chat_id("ADMIN_CHAT_ID"), chat_id("ANNOUNCE_CHAT_ID")
    logging.basicConfig(level=logging.INFO)
    if admin_id is None:
        logging.warning("ADMIN_CHAT_ID yo'q: signal yuborilmaydi, reyting qayta ishga tushganda yo'qoladi")

    bot = Bot(token, default=DefaultBotProperties(parse_mode="HTML"))
    store = Store(bot, admin_id)
    await store.load()
    dp = build(flag_secret, link_secret, site_url, admin_id, announce_id, store)

    run_seconds = int(os.environ.get("RUN_SECONDS", "0"))
    if run_seconds > 0:
        async def stop_later() -> None:
            await asyncio.sleep(run_seconds)
            logging.info("RUN_SECONDS tugadi, bot to'xtayapti")
            await dp.stop_polling()

        asyncio.create_task(stop_later())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

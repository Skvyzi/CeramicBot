import os
import json
import sqlite3
from datetime import datetime, timedelta
import telebot
from telebot import types
import gspread

# === НАСТРОЙКИ ===
TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 1213775571  # ID мамы для уведомлений
ADMIN_SECRET = "secret_admin_777"  # Пароль для ссылки-приглашения в админы
SUPPORT_GROUP_URL = "https://t.me/+wJqlXr8Q4TdmNzA0"
LOCATION_URL = "https://maps.app.goo.gl/3marsJJvmUzWL3qy8"
INSTAGRAM_URL = "https://www.instagram.com/artelceramics/"
LOCATION_PHOTO = "location.jpg"  # Имя файла с фото в папке с ботом
MAX_PEOPLE = 6

# Настройки Google Таблицы
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/100Ss455op1E0W00_mAFLn3VItBoIJ7GEcyGJEdHuKk8/edit?usp=sharing"
CREDENTIALS_FILE = "credentials.json"

bot = telebot.TeleBot(TOKEN)

# === РАСПИСАНИЕ ===
SCHEDULE = {
    "tue_17": {"ru": "Вт 17:00–18:00", "en": "Tue 5:00–6:00 PM"},
    "tue_18": {"ru": "Вт 18:00–19:00", "en": "Tue 6:00–7:00 PM"},
    "tue_19": {"ru": "Вт 19:00–20:00", "en": "Tue 7:00–8:00 PM"},
    "wed_17": {"ru": "Ср 17:00–18:00", "en": "Wed 5:00–6:00 PM"},
    "wed_18": {"ru": "Ср 18:00–19:00", "en": "Wed 6:00–7:00 PM"},
    "wed_19": {"ru": "Ср 19:00–20:30 (взрослая)", "en": "Wed 7:00–8:30 PM (Adult)"},
    "thu_17": {"ru": "Чт 17:00–18:00", "en": "Thu 5:00–6:00 PM"},
    "thu_18": {"ru": "Чт 18:00–19:00", "en": "Thu 6:00–7:00 PM"},
}

# День недели (Пн=0, Вт=1, Ср=2, Чт=3) и время окончания урока (час, минута)
SLOT_END_TIME = {
    "tue_17": (1, 18, 0),
    "tue_18": (1, 19, 0),
    "tue_19": (1, 20, 0),
    "wed_17": (2, 18, 0),
    "wed_18": (2, 19, 0),
    "wed_19": (2, 20, 30),
    "thu_17": (3, 18, 0),
    "thu_18": (3, 19, 0),
}

# === ТЕКСТЫ НА ДВУХ ЯЗЫКАХ (ВЕЖЛИВОЕ ОБРАЩЕНИЕ) ===
TEXTS = {
    "ru": {
        "welcome": "Здравствуйте! Это бот мастерской керамики 🏺\nВыберите, пожалуйста, нужный раздел:",
        "btn_schedule": "📅 Расписание и запись",
        "btn_my": "📋 Мои записи",
        "btn_prices": "💰 Цены",
        "btn_about_classes": "🎨 О занятиях",
        "btn_about_studio": "🏺 О мастерской",
        "btn_process": "🔥 Технологии",
        "btn_announcements": "📢 Анонсы",
        "btn_works": "🖼 Посмотреть все работы",
        "btn_location": "📍 Узнать локацию",
        "btn_support": "💬 Технические вопросы",
        "btn_lang": "🌐 Switch to English",

        "choose_type": "Как Вы хотите записаться на <b>{title}</b>?",
        "btn_regular": "🔄 На постоянную (каждую неделю)",
        "btn_onetime": "1️⃣ Одноразово",
        "type_regular": "Постоянная",
        "type_onetime": "Одноразовая",

        "location_text": "Наша уютная мастерская расположена в центре города Бар.",
        "location_btn": "Открыть на карте 🗺",
        "works_text": "Наши работы можно посмотреть в Инстаграме:",
        "works_btn": "Открыть Instagram 📸",
        "announcements_text": (
            "📢 <b>Анонсы мастер-классов</b>\n\n"
            "Пока новых анонсов нет — следите за обновлениями в нашей группе!"
        ),

        "prices_text": (
            "<b>Стоимость занятий, постоянные группы:</b>\n"
            "• Детское занятие (1 час) — 12 €\n"
            "• Взрослое занятие (1.5 часа) — 20 €\n\n"
            "<b>Разовый мастер-класс:</b>\n"
            "1 час — 15 €, группы от 2-х человек. Расписание и анонсы мастер-классов в разделе «Анонсы».\n\n"
            "<b>Индивидуальные занятия:</b>\n"
            "• Индивидуальное занятие (1 час) — 25 €\n"
            "• Занятие на гончарном круге — только индивидуально, 25 €/час, время обговаривается отдельно.\n\n"
            "<i>В стоимость занятия входят все материалы и обжиги.</i>\n\n"
            "<b>Принимаем изделия на обжиг:</b>\n\n"
            "<b>1050 °C (утель и политой):</b>\n"
            "• Полностью полка в печи (диаметр полки 45 см, высота изделия до 10 см) — 25 €\n"
            "• Поштучно (высота до 10 см):\n"
            "  – диаметр до 3 см — 1 €\n"
            "  – от 3 до 10 см — 2 €\n"
            "  – от 10 до 20 см — 3 €\n"
            "  – от 20 до 30 см — 10 €\n"
            "  – свыше 30 см — стоимость полки.\n\n"
            "<b>1200 °C (политой):</b>\n"
            "• Только полка, поштучно не обжигаем. Стоимость обжига полки — 40 €.\n\n"
            "<i>Для изделий высотой более 10 см стоимость увеличивается пропорционально.</i>"
        ),

        "about_classes_text": (
            "<b>О концепции занятий</b>\n\n"
            "В нашей мастерской мы придерживаемся концепции свободного творчества.\n"
            "Это значит, что на занятии мастер в первую очередь спрашивает, какие идеи начинающие керамисты хотят воплотить, и помогает реализовать их замысел.\n\n"
            "Мастер показывает разные техники лепки и декора, подсказывает, как лучше сделать форму, соединить детали, украсить изделие и довести его до результата.\n"
            "В мастерской всегда есть много готовых изделий для примера — каждый творец может вдохновиться, выбрать идею или форму, которая ему понравится.\n\n"
            "Если идей пока нет — это совершенно нормально.\n"
            "В этом случае мастер предложит выполнить несложное, но эффектное изделие, например:\n"
            "• кружку из пласта\n"
            "• свистульку\n"
            "• подсвечник\n"
            "• небольшую фигурку или тарелочку 🤍"
        ),

        "about_studio_text": (
            "🏺 <b>О нашей мастерской</b>\n\n"
            "Мы проводим занятия по керамике, обучаем работе на гончарном круге и создаём керамику ручной работы — от сувениров до функциональной посуды.\n\n"
            "Наша мастерская существует уже более 10 лет. За это время мы участвовали в ярмарках мастеров по всей Черногории, ездили в Сербию, выставлялись на 4ceramic Market в Москве и отправляли наши работы по всему миру через магазин на Etsy:\n"
            "https://www.etsy.com/shop/AllGoodDreamsByMarta\n"
            "Также наши изделия представлены в сувенирных магазинах в Которе и Херцег-Нови.\n\n"
            "<b>В нашей мастерской есть:</b>\n"
            "• Гончарный круг\n"
            "• Печь для обжига до 1300 °C\n"
            "• Немецкая и испанская глина\n"
            "• Ангобы\n"
            "• Большой выбор простых и эффектных глазурей\n\n"
            "Мы рады новичкам и сопровождаем вас на всех этапах — от создания первой формы до готового керамического изделия.\n"
            "По вопросам занятий или индивидуальных заказов пишите в нашу группу или администратору мастерской."
        ),

        "process_text": (
            "🏺 <b>Как мы создаём керамику</b>\n\n"
            "1️⃣ <b>Лепка</b>\n"
            "Сначала мы лепим изделие вручную или на гончарном круге. На этом этапе формируется форма, толщина стенок и все детали.\n\n"
            "2️⃣ <b>Сушка</b>\n"
            "Готовое изделие должно полностью высохнуть. Этот процесс занимает несколько дней — глина постепенно теряет влагу, чтобы при обжиге не появились трещины.\n\n"
            "3️⃣ <b>Первый обжиг — утельный</b>\n"
            "Высушенное изделие отправляется в муфельную печь. Этот обжиг называется утель. После него изделие остаётся неглазурованным и непокрашенным.\n"
            "Обжиг длится около 8 часов, так как температура поднимается постепенно по заданному графику благодаря программатору печи. Обычно декоративную керамику мы обжигаем до 1050 °C.\n"
            "После окончания обжига печь остывает ещё 8–12 часов. Открывать её можно не раньше, чем температура опустится до 200 °C.\n\n"
            "4️⃣ <b>Роспись и глазурование</b>\n"
            "После утельного обжига:\n"
            "• дети расписывают свои изделия ангобами\n"
            "• взрослые могут использовать кроме ангобов различные глазури\n"
            "Мы покрываем изделия, расписанные ангобом, прозрачной глазурью и отправляем их в повторный обжиг.\n\n"
            "5️⃣ <b>Второй обжиг — глазурный</b>\n"
            "Во время второго обжига глазурь расплавляется и превращается в прочное стекловидное покрытие. После него изделие становится гладким, водонепроницаемым и готовым к использованию.\n"
            "Для посуды температура обжига должна быть не менее 1200 °C с использованием высокотемпературных глазурей.\n\n"
            "После полного остывания печи изделие можно забирать 🤍"
        ),

        "schedule_header": (
            "<b>Расписание групп (до 6 человек):</b>\n\n"
            "Взрослые могут ходить в детские группы, а вот наоборот нельзя — дети во взрослую группу не ходят 😊\n\n"
            "Нажмите на нужное время, чтобы записаться:"
        ),
        "free": "мест: {free}/{max}",
        "full": "мест нет ❌",
        "support_text": "Если у Вас есть технические вопросы по занятиям — переходите в нашу группу:",
        "support_btn": "Перейти в группу 💬",
        "no_bookings": "Вы пока никуда не записаны.",
        "my_bookings": "Ваши текущие записи (нажмите, чтобы отменить):",
        "cancel_btn": "❌ Отменить: {title}",
        "booked_ok": "✅ Вы успешно записаны на занятие:\n<b>{title}</b>\nФормат: <b>{btype}</b>",
        "already_booked": "Вы уже записаны в эту группу!",
        "slot_full": "Извините, в этой группе уже нет свободных мест 😔",
        "canceled": "Ваша запись отменена ✅",
    },
    "en": {
        "welcome": "Hello! Welcome to our Ceramics Studio bot 🏺\nPlease choose an option below:",
        "btn_schedule": "📅 Schedule & Booking",
        "btn_my": "📋 My Bookings",
        "btn_prices": "💰 Prices",
        "btn_about_classes": "🎨 About Classes",
        "btn_about_studio": "🏺 About Our Studio",
        "btn_process": "🔥 Our Process",
        "btn_announcements": "📢 Announcements",
        "btn_works": "🖼 View All Works",
        "btn_location": "📍 Location",
        "btn_support": "💬 Support Group",
        "btn_lang": "🌐 Переключить на русский",

        "choose_type": "How would you like to book <b>{title}</b>?",
        "btn_regular": "🔄 Regular (every week)",
        "btn_onetime": "1️⃣ One-time visit",
        "type_regular": "Regular",
        "type_onetime": "One-time",

        "location_text": "Our cozy studio is located in the heart of Bar.",
        "location_btn": "Open in Google Maps 🗺",
        "works_text": "You can view our works on Instagram:",
        "works_btn": "Open Instagram 📸",
        "announcements_text": (
            "📢 <b>Workshop Announcements</b>\n\n"
            "No upcoming announcements yet — stay tuned in our group!"
        ),

        "prices_text": (
            "<b>Class Prices — Regular Classes:</b>\n"
            "• Children’s class (1 hour) — €12\n"
            "• Adult class (1.5 hours) — €20\n\n"
            "<b>One-Off Workshops:</b>\n"
            "1-hour workshop — €15 per person. Minimum group size: 2 people.\n"
            "You can find the schedule and announcements for upcoming workshops in the Announcements section.\n\n"
            "<b>Private Classes:</b>\n"
            "• Individual class (1 hour) — €25\n"
            "• Potter’s wheel session — €25 per hour, available for individual sessions only. The time must be arranged separately.\n\n"
            "<i>All materials and firings are included in the class price.</i>\n\n"
            "<b>Ceramic Firing Services:</b>\n"
            "We also accept ceramic pieces for firing.\n\n"
            "<b>1050°C — Bisque and Glaze Firing:</b>\n"
            "• Full kiln shelf (diameter 45 cm, max piece height 10 cm) — €25\n"
            "• Individual pieces (height up to 10 cm):\n"
            "  – diameter up to 3 cm — €1\n"
            "  – 3 to 10 cm — €2\n"
            "  – 10 to 20 cm — €3\n"
            "  – 20 to 30 cm — €10\n"
            "  – over 30 cm — price of a full kiln shelf.\n\n"
            "<b>1200°C — Glaze Firing:</b>\n"
            "• Full kiln shelf only — €40 (we do not accept individual pieces at this temperature).\n\n"
            "<i>For pieces taller than 10 cm, the price increases proportionally.</i>"
        ),

        "about_classes_text": (
            "<b>About Our Workshop Philosophy</b>\n\n"
            "At our studio, we believe in the freedom of creative expression.\n"
            "This means that at the beginning of each session, our instructor first asks what the budding ceramicists would like to create and then helps them bring their ideas to life.\n\n"
            "Our instructor introduces different hand-building and decorating techniques, offering guidance on shaping forms, joining pieces, adding decorative details, and bringing each creation to completion.\n\n"
            "There are always plenty of finished pieces in the studio to serve as inspiration. Everyone can find something they love, choose a design, or come up with their own idea.\n\n"
            "And if you don’t have any ideas yet, that’s absolutely fine!\n"
            "In that case, our instructor will suggest making something simple yet beautiful, such as:\n"
            "• A slab-built mug\n"
            "• A clay whistle\n"
            "• A candle holder\n"
            "• A small figurine or a little plate 🤍"
        ),

        "about_studio_text": (
            "🏺 <b>About Our Studio</b>\n\n"
            "We offer pottery classes, teach you how to work on the potter’s wheel, and create handmade ceramics, from souvenirs to functional tableware.\n\n"
            "Our studio has been around for over 10 years. During this time, we’ve taken part in craft fairs across Montenegro, travelled to Serbia, exhibited at the 4ceramic Market in Moscow, and shipped our creations all over the world through our Etsy shop:\n"
            "https://www.etsy.com/shop/AllGoodDreamsByMarta\n"
            "Our pieces are also available in souvenir shops in Kotor and Herceg Novi.\n\n"
            "<b>Our studio is equipped with:</b>\n"
            "• A potter’s wheel\n"
            "• A kiln capable of firing up to 1300°C\n"
            "• German and Spanish clay\n"
            "• Underglazes\n"
            "• A selection of simple and spectacular glazes\n\n"
            "We welcome beginners and guide you through the entire process, from shaping your very first piece to creating a finished ceramic work.\n"
            "For class enquiries or custom orders, please send us a message in our group or contact our studio administrator."
        ),

        "process_text": (
            "🏺 <b>How We Make Our Ceramics</b>\n\n"
            "1️⃣ <b>Shaping</b>\n"
            "First, we shape each piece by hand or on the potter’s wheel. At this stage, we create the form, determine the wall thickness, and add all the details.\n\n"
            "2️⃣ <b>Drying</b>\n"
            "The finished piece must dry completely. This takes several days, as the clay gradually loses moisture. Proper drying helps prevent cracks during firing.\n\n"
            "3️⃣ <b>First Firing — Bisque Firing</b>\n"
            "Once completely dry, the piece goes into our kiln for its first firing (bisque firing). After this stage, the piece remains unglazed and unpainted.\n"
            "The firing takes around 8 hours, as the temperature rises gradually according to a preset schedule. We usually fire decorative ceramics to around 1050°C.\n"
            "After firing, the kiln needs another 8–12 hours to cool down. We can open it only when the temperature has dropped to 200°C or below.\n\n"
            "4️⃣ <b>Painting and Glazing</b>\n"
            "After the bisque firing:\n"
            "• Children decorate their pieces using underglazes.\n"
            "• Adults can use a variety of glazes as well as underglazes.\n"
            "We apply a transparent glaze over pieces decorated with underglazes, then return them to the kiln for a second firing.\n\n"
            "5️⃣ <b>Second Firing — Glaze Firing</b>\n"
            "During the second firing, the glaze melts and forms a durable, glass-like coating. Once fired and cooled, the piece has a smooth, water-resistant surface and is ready to use.\n"
            "For functional tableware, the firing temperature must be at least 1200°C, and high-temperature glazes must be used.\n"
            "Once the kiln has cooled completely, your finished piece is ready to take home. 🤍\n\n"
            "<i>The entire process requires at least two sessions.</i>\n"
            "<i>Note about one-off workshops: we shape the clay and decorate with underglazes during the same visit, while the clay is still unfired. However, the piece still needs to go through both firings before it is finished.</i>"
        ),

        "schedule_header": (
            "<b>Regular Class Schedule (up to 6 people):</b>\n\n"
            "Adults are welcome to join the children's groups, but children cannot attend the adult group 😊\n\n"
            "Tap a time slot to book:"
        ),
        "free": "spots: {free}/{max}",
        "full": "full ❌",
        "support_text": "For any technical questions about classes, please join our group:",
        "support_btn": "Open Group 💬",
        "no_bookings": "You don't have any bookings yet.",
        "my_bookings": "Your current bookings (tap to cancel):",
        "cancel_btn": "❌ Cancel: {title}",
        "booked_ok": "✅ You are booked for:\n<b>{title}</b>\nType: <b>{btype}</b>",
        "already_booked": "You are already booked for this class!",
        "slot_full": "Sorry, this group is already full 😔",
        "canceled": "Your booking has been canceled ✅",
    }
}


# === РАБОТА С ЖИВОЙ GOOGLE ТАБЛИЦЕЙ ===
def get_sheet():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        gc = gspread.service_account_from_dict(json.loads(creds_json))
    else:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open_by_url(GOOGLE_SHEET_URL)
    return sh.sheet1


def init_sheet():
    try:
        ws = get_sheet()
        if not ws.row_values(1):
            ws.append_row(["Дата записи", "Группа", "Тип записи", "Клиент", "Telegram ID", "Статус"])
    except Exception as e:
        print(f"Ошибка подключения к Google Таблице: {e}")


def add_row_to_sheet(slot_id, booking_type, client_info, user_id):
    try:
        ws = get_sheet()
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        group_name = SCHEDULE.get(slot_id, {}).get("ru", slot_id)
        ws.append_row([now_str, group_name, booking_type, client_info, str(user_id), "Активна"])
    except Exception as e:
        print(f"Ошибка добавления в Google Таблицу: {e}")


def mark_canceled_in_sheet(slot_id, user_id):
    try:
        ws = get_sheet()
        group_name = SCHEDULE.get(slot_id, {}).get("ru", slot_id)
        rows = ws.get_all_values()
        # Ищем с конца самую свежую активную запись этого клиента в эту группу
        for idx in range(len(rows) - 1, 0, -1):
            row = rows[idx]
            if len(row) >= 6 and row[1] == group_name and row[4] == str(user_id) and row[5] == "Активна":
                ws.update_cell(idx + 1, 6, "Отменена")
                break
    except Exception as e:
        print(f"Ошибка обновления статуса в Google Таблице: {e}")


# === РАСЧЁТ ДАТЫ ДЛЯ ОДНОРАЗОВОЙ ЗАПИСИ ===
def get_next_slot_end(slot_id):
    now = datetime.now()
    target_wd, end_h, end_m = SLOT_END_TIME[slot_id]
    days_ahead = (target_wd - now.weekday()) % 7
    end_dt = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0) + timedelta(days=days_ahead)
    if end_dt <= now:
        end_dt += timedelta(days=7)
    return int(end_dt.timestamp()), end_dt.strftime("%d.%m")


# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            slot_id TEXT,
            booking_type TEXT DEFAULT 'Постоянная',
            expires_at INTEGER,
            UNIQUE(user_id, slot_id)
        )
    """)
    for col_sql in [
        "ALTER TABLE bookings ADD COLUMN booking_type TEXT DEFAULT 'Постоянная'",
        "ALTER TABLE bookings ADD COLUMN expires_at INTEGER",
    ]:
        try:
            cur.execute(col_sql)
        except sqlite3.OperationalError:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ru'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    """)
    cur.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (ADMIN_ID,))
    conn.commit()
    conn.close()
    init_sheet()


def cleanup_expired_bookings():
    now_ts = int(datetime.now().timestamp())
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE expires_at IS NOT NULL AND expires_at < ?", (now_ts,))
    conn.commit()
    conn.close()


def add_admin(user_id):
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def is_admin(user_id):
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    res = cur.fetchone() is not None
    conn.close()
    return res


def get_all_admins():
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins")
    rows = [row[0] for row in cur.fetchall()]
    conn.close()
    return rows


def get_lang(user_id):
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "ru"


def set_lang(user_id, lang):
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (user_id, lang) VALUES (?, ?)", (user_id, lang))
    conn.commit()
    conn.close()


def get_slot_count(slot_id):
    cleanup_expired_bookings()
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM bookings WHERE slot_id = ?", (slot_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def add_booking(user_id, user_name, slot_id, booking_type, expires_at=None):
    cleanup_expired_bookings()
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO bookings (user_id, user_name, slot_id, booking_type, expires_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, user_name, slot_id, booking_type, expires_at)
        )
        conn.commit()
        add_row_to_sheet(slot_id, booking_type, user_name, user_id)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_booking(user_id, slot_id):
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE user_id = ? AND slot_id = ?", (user_id, slot_id))
    conn.commit()
    conn.close()
    mark_canceled_in_sheet(slot_id, user_id)


def get_user_bookings(user_id):
    cleanup_expired_bookings()
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("SELECT slot_id FROM bookings WHERE user_id = ?", (user_id,))
    rows = [row[0] for row in cur.fetchall()]
    conn.close()
    return rows


# === КЛАВИАТУРЫ ===
def main_menu(lang):
    t = TEXTS[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(t["btn_schedule"], t["btn_my"])
    markup.add(t["btn_prices"], t["btn_about_classes"])
    markup.add(t["btn_about_studio"], t["btn_process"])
    markup.add(t["btn_announcements"], t["btn_works"])
    markup.add(t["btn_location"], t["btn_support"])
    markup.add(t["btn_lang"])
    return markup


def schedule_keyboard(lang):
    t = TEXTS[lang]
    markup = types.InlineKeyboardMarkup()
    for slot_id, names in SCHEDULE.items():
        taken = get_slot_count(slot_id)
        free = MAX_PEOPLE - taken
        status = t["free"].format(free=free, max=MAX_PEOPLE) if free > 0 else t["full"]
        markup.add(types.InlineKeyboardButton(
            text=f"{names[lang]} ({status})",
            callback_data=f"book:{slot_id}"
        ))
    return markup


# === СТАРТ И ВЫБОР ЯЗЫКА ===
@bot.message_handler(commands=["start"])
def start(message):
    parts = message.text.split()
    if len(parts) > 1 and parts[1] == ADMIN_SECRET:
        add_admin(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "✅ Вы добавлены в список админов!\nТеперь Вам будут приходить уведомления о записях. Команды: /table (ссылка на таблицу) и /clear_onetime."
        )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")
    )
    bot.send_message(message.chat.id, "Выберите язык / Choose your language:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang:"))
def handle_lang(call):
    lang = call.data.split(":")[1]
    set_lang(call.from_user.id, lang)
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, TEXTS[lang]["welcome"], reply_markup=main_menu(lang))


# === КОМАНДЫ ДЛЯ АДМИНОВ ===
@bot.message_handler(commands=["table", "excel"])
def send_table_link(message):
    if not is_admin(message.from_user.id):
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Открыть живую таблицу 📊", url=GOOGLE_SHEET_URL))
    bot.send_message(message.chat.id, "Вот ссылка на общую таблицу записей:", reply_markup=markup)


@bot.message_handler(commands=["clear_onetime"])
def clear_onetime(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE expires_at IS NOT NULL OR booking_type LIKE 'Одноразовая%'")
    conn.commit()
    conn.close()
    notify_admins("🧹 Все одноразовые записи очищены из бота вручную (в таблице история сохранена).")


# === КНОПКИ ГЛАВНОГО МЕНЮ ===
@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_lang"], TEXTS["en"]["btn_lang"]])
def switch_language(message):
    new_lang = "en" if get_lang(message.from_user.id) == "ru" else "ru"
    set_lang(message.from_user.id, new_lang)
    bot.send_message(message.chat.id, TEXTS[new_lang]["welcome"], reply_markup=main_menu(new_lang))


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_schedule"], TEXTS["en"]["btn_schedule"]])
def show_schedule(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, TEXTS[lang]["schedule_header"], parse_mode="HTML", reply_markup=schedule_keyboard(lang))


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_prices"], TEXTS["en"]["btn_prices"]])
def show_prices(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, TEXTS[lang]["prices_text"], parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_about_classes"], TEXTS["en"]["btn_about_classes"]])
def show_about_classes(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, TEXTS[lang]["about_classes_text"], parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_about_studio"], TEXTS["en"]["btn_about_studio"]])
def show_about_studio(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, TEXTS[lang]["about_studio_text"], parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_process"], TEXTS["en"]["btn_process"]])
def show_process(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, TEXTS[lang]["process_text"], parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_announcements"], TEXTS["en"]["btn_announcements"]])
def show_announcements(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, TEXTS[lang]["announcements_text"], parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_works"], TEXTS["en"]["btn_works"]])
def show_works(message):
    lang = get_lang(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(TEXTS[lang]["works_btn"], url=INSTAGRAM_URL))
    bot.send_message(message.chat.id, TEXTS[lang]["works_text"], reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_location"], TEXTS["en"]["btn_location"]])
def show_location(message):
    lang = get_lang(message.from_user.id)
    t = TEXTS[lang]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t["location_btn"], url=LOCATION_URL))

    if os.path.exists(LOCATION_PHOTO):
        with open(LOCATION_PHOTO, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=t["location_text"], reply_markup=markup)
    else:
        bot.send_message(message.chat.id, t["location_text"], reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_support"], TEXTS["en"]["btn_support"]])
def show_support(message):
    lang = get_lang(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(TEXTS[lang]["support_btn"], url=SUPPORT_GROUP_URL))
    bot.send_message(message.chat.id, TEXTS[lang]["support_text"], reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in [TEXTS["ru"]["btn_my"], TEXTS["en"]["btn_my"]])
def show_my_bookings(message):
    lang = get_lang(message.from_user.id)
    slots = get_user_bookings(message.from_user.id)
    if not slots:
        bot.send_message(message.chat.id, TEXTS[lang]["no_bookings"])
        return

    markup = types.InlineKeyboardMarkup()
    for slot_id in slots:
        title = SCHEDULE[slot_id][lang]
        markup.add(types.InlineKeyboardButton(
            TEXTS[lang]["cancel_btn"].format(title=title),
            callback_data=f"cancel:{slot_id}"
        ))
    bot.send_message(message.chat.id, TEXTS[lang]["my_bookings"], reply_markup=markup)


# === УВЕДОМЛЕНИЯ АДМИНАМ (БЕЗ ФАЙЛОВ, ПРОСТО С КНОПКОЙ) ===
def notify_admins(text):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Открыть таблицу 📊", url=GOOGLE_SHEET_URL))
    for adm_id in get_all_admins():
        try:
            bot.send_message(adm_id, text, reply_markup=markup)
        except Exception:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("book:"))
def handle_booking(call):
    slot_id = call.data.split(":")[1]
    lang = get_lang(call.from_user.id)
    t = TEXTS[lang]

    if slot_id in get_user_bookings(call.from_user.id):
        bot.answer_callback_query(call.id, t["already_booked"], show_alert=True)
        return

    if get_slot_count(slot_id) >= MAX_PEOPLE:
        bot.answer_callback_query(call.id, t["slot_full"], show_alert=True)
        return

    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t["btn_regular"], callback_data=f"btype:{slot_id}:regular"))
    markup.add(types.InlineKeyboardButton(t["btn_onetime"], callback_data=f"btype:{slot_id}:onetime"))
    bot.send_message(
        call.message.chat.id,
        t["choose_type"].format(title=SCHEDULE[slot_id][lang]),
        parse_mode="HTML",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("btype:"))
def handle_booking_type(call):
    _, slot_id, btype_key = call.data.split(":")
    lang = get_lang(call.from_user.id)
    t = TEXTS[lang]

    if get_slot_count(slot_id) >= MAX_PEOPLE:
        bot.answer_callback_query(call.id, t["slot_full"], show_alert=True)
        return

    bot.answer_callback_query(call.id)
    ask_text = (
        "Напишите, пожалуйста, Ваше имя (и имя ребёнка, если записываете его):"
        if lang == "ru"
        else "Please enter your name (and your child's name if applicable):"
    )
    msg = bot.send_message(call.message.chat.id, ask_text)
    bot.register_next_step_handler(msg, process_booking_name, slot_id, btype_key)


def process_booking_name(message, slot_id, btype_key):
    lang = get_lang(message.from_user.id)
    t = TEXTS[lang]

    if not message.text:
        retry_text = "Пожалуйста, напишите имя текстом:" if lang == "ru" else "Please send your name as text:"
        msg = bot.send_message(message.chat.id, retry_text)
        bot.register_next_step_handler(msg, process_booking_name, slot_id, btype_key)
        return

    entered_name = message.text.strip()
    user = message.from_user
    tg_handle = f"@{user.username}" if user.username else "нет username"
    client_info = f"{entered_name} - {tg_handle}"

    if btype_key == "onetime":
        expires_at, date_str = get_next_slot_end(slot_id)
        btype_ru = f"{TEXTS['ru']['type_onetime']} ({date_str})"
        btype_user = f"{t['type_onetime']} ({date_str})"
    else:
        expires_at = None
        btype_ru = TEXTS["ru"]["type_regular"]
        btype_user = t["type_regular"]

    if get_slot_count(slot_id) >= MAX_PEOPLE:
        bot.send_message(message.chat.id, t["slot_full"])
        return

    if add_booking(user.id, client_info, slot_id, btype_ru, expires_at):
        bot.send_message(
            message.chat.id,
            t["booked_ok"].format(title=SCHEDULE[slot_id][lang], btype=btype_user),
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )
        notify_admins(
            f"🔔 Новая запись!\nКлиент: {client_info}\nГруппа: {SCHEDULE[slot_id]['ru']}\nТип: {btype_ru}"
        )
    else:
        bot.send_message(message.chat.id, t["already_booked"])


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel:"))
def handle_cancel(call):
    slot_id = call.data.split(":")[1]
    lang = get_lang(call.from_user.id)

    conn = sqlite3.connect("ceramics.db")
    cur = conn.cursor()
    cur.execute("SELECT user_name FROM bookings WHERE user_id = ? AND slot_id = ?", (call.from_user.id, slot_id))
    row = cur.fetchone()
    conn.close()
    client_info = row[0] if row else (call.from_user.first_name or "Клиент")

    remove_booking(call.from_user.id, slot_id)
    bot.answer_callback_query(call.id, TEXTS[lang]["canceled"])
    bot.edit_message_text(TEXTS[lang]["canceled"], call.message.chat.id, call.message.message_id)

    notify_admins(
        f"❌ Отмена записи!\nКлиент: {client_info}\nГруппа: {SCHEDULE[slot_id]['ru']}"
    )


if __name__ == "__main__":
    init_db()
    me = bot.get_me()
    print(f"Бот запущен: @{me.username}")
    print(f"Ссылка для добавления админа: https://t.me/{me.username}?start={ADMIN_SECRET}")
    bot.infinity_polling()
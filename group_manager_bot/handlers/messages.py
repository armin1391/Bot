import os
import sys
import time


# =========================================================
# 📁 اضافه کردن پوشه اصلی پروژه به مسیر پایتون
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(
        0,
        BASE_DIR
    )


# =========================================================
# 🗄️ دیتابیس
# =========================================================

from database.database import (
    activate_group,
    is_group_activated,
    register_user,
    set_group_setting,
    get_group_setting,
    reset_user_warnings,
    remove_user_mute,
    is_user_muted,
    is_user_banned,
    get_group_statistics
)


# =========================================================
# 🔨 امکانات مدیریتی
# =========================================================

from mute import mute_user
from ban import ban_user, unban_user


# =========================================================
# 🔤 سیستم فیلتر کلمات
# =========================================================

from .filter import (
    init_filters,
    add_filter,
    delete_filter,
    get_filter_reply
)


# =========================================================
# 👋 سیستم خوش‌آمدگویی و خداحافظی
# =========================================================

from .welcome import (
    handle_welcome
)


# =========================================================
# 🗄️ آماده‌سازی جدول فیلترها
# =========================================================

try:

    init_filters()

    print(
        "✅ [FILTER] جدول فیلترها آماده است."
    )

except Exception as e:

    print(
        f"❌ [FILTER INIT ERROR] {e}"
    )


# =========================================================
# 🔥 دستورات فعال‌سازی ربات
# =========================================================

ACTIVATE_COMMANDS = {

    "فعالسازی",
    "فعال سازی",
    "فعال‌سازی"
}


# =========================================================
# ⚙️ تنظیمات قابل مدیریت
# =========================================================

SETTING_COMMANDS = {

    "ضد اسپم": "anti_spam",
    "ضد فحش": "anti_bad_words",
    "ضد لینک": "anti_link",
    "ضد فوروارد": "anti_forward",
    "ضد فیلم": "anti_video",
    "ضد عکس": "anti_photo",
    "ضد ویس": "anti_voice"
}


# =========================================================
# 🧹 نرمال‌سازی متن
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    return " ".join(
        text.strip().split()
    )


# =========================================================
# ⚡ تشخیص فعال‌سازی
# =========================================================

def is_activate_command(text):

    return normalize_text(
        text
    ) in ACTIVATE_COMMANDS


# =========================================================
# ⚙️ تشخیص تنظیمات
# =========================================================

def parse_setting_command(text):

    normalized = normalize_text(
        text
    )

    for command, setting in SETTING_COMMANDS.items():

        if normalized in (
            f"{command} فعال",
            f"{command} روشن"
        ):

            return setting, True

        if normalized in (
            f"{command} خاموش",
            f"{command} غیرفعال"
        ):

            return setting, False

    return None, None


# =========================================================
# 👑 بررسی ادمین
# =========================================================

def is_admin(
    admins,
    user_id
):

    if not admins:
        return False

    if not admins.get("ok"):
        return False

    for admin in admins.get(
        "result",
        []
    ):

        user = admin.get(
            "user",
            {}
        )

        if user.get("id") == user_id:

            return admin.get(
                "status"
            ) in (
                "administrator",
                "creator"
            )

    return False


# =========================================================
# 📈 ساخت متن رشد اعضا
# =========================================================

def growth_text(data):

    if not data:
        return "➖ 0 نفر | 0%"

    current = data.get(
        "current",
        0
    )

    percentage = data.get(
        "percentage",
        0
    )

    if percentage > 0:

        percentage_text = (
            f"+{percentage:g}%"
        )

        emoji = "📈"

    elif percentage < 0:

        percentage_text = (
            f"{percentage:g}%"
        )

        emoji = "📉"

    else:

        percentage_text = "0%"
        emoji = "➖"

    return (
        f"{emoji} {current} نفر | "
        f"{percentage_text}"
    )


# =========================================================
# 👤 ساخت لیست کاربران پرپیام
# =========================================================

def build_top_users_text(
    users,
    empty_text
):

    if not users:
        return empty_text

    lines = []

    for index, user in enumerate(
        users,
        start=1
    ):

        username = user["username"]

        if username:

            username = str(
                username
            )

            if not username.startswith("@"):

                username = (
                    f"@{username}"
                )

        else:

            username = (
                f"کاربر {user['user_id']}"
            )

        lines.append(
            f"{index}. {username} "
            f"{user['message_count']} پیام"
        )

    return "\n".join(
        lines
    )


# =========================================================
# 📊 ساخت متن کامل آمار گروه
# =========================================================

def build_statistics_text(
    stats
):

    top_users_text = build_top_users_text(
        stats.get(
            "top_users",
            []
        ),
        "هنوز پیامی ثبت نشده."
    )

    today_top_users_text = build_top_users_text(
        stats.get(
            "today_top_users",
            []
        ),
        "امروز هنوز پیامی ثبت نشده."
    )

    day_growth = growth_text(
        stats.get(
            "day_growth",
            {}
        )
    )

    week_growth = growth_text(
        stats.get(
            "week_growth",
            {}
        )
    )

    month_growth = growth_text(
        stats.get(
            "month_growth",
            {}
        )
    )

    today_messages = stats.get(
        "today_messages",
        0
    )

    today_new_members = stats.get(
        "today_new_members",
        0
    )

    muted = stats.get(
        "muted",
        0
    )

    banned = stats.get(
        "banned",
        0
    )

    return (

        "📊 آمار گروه\n"
        "\n"

        "━━━━━━━━━━━━━━\n"
        "\n"

        f"💬 کل پیام‌ها: "
        f"{stats.get('messages', 0)}\n"
        "\n"

        f"📨 پیام‌های امروز: "
        f"{today_messages}\n"
        "\n"

        f"🆕 اعضای جدید امروز: "
        f"{today_new_members}\n"
        "\n"

        f"🔇 کاربران سکوت‌شده: "
        f"{muted}\n"
        "\n"

        f"🔨 کاربران بن‌شده: "
        f"{banned}\n"
        "\n"

        "📈 رشد اعضا\n"
        "\n"

        f"📅 روزانه: "
        f"{day_growth}\n"
        "\n"

        f"📆 هفتگی: "
        f"{week_growth}\n"
        "\n"

        f"🗓 ماهانه: "
        f"{month_growth}\n"
        "\n"

        "━━━━━━━━━━━━━━\n"
        "\n"

        "🏆 پرپیام‌ترین کاربران\n"
        "\n"

        f"{top_users_text}\n"
        "\n"

        "🔥 پرپیام‌ترین کاربران امروز\n"
        "\n"

        f"{today_top_users_text}"
    )


# =========================================================
# 🔤 پردازش دستور فیلتر
#
# ساخت:
#
# فیلتر پدرم
#
# روی پیام:
#
# آرمین
#
# نتیجه:
#
# آرمین ← کلمه تشخیص
# پدرم  ← پاسخ ربات
# =========================================================

def parse_filter_command(text):

    normalized = normalize_text(
        text
    )

    if normalized.startswith(
        "فیلتر "
    ):

        reply_text = normalized[
            len("فیلتر "):
        ].strip()

        if reply_text:

            return (
                "add",
                reply_text
            )

    if normalized.startswith(
        "حذف فیلتر "
    ):

        trigger_word = normalized[
            len("حذف فیلتر "):
        ].strip()

        if trigger_word:

            return (
                "delete",
                trigger_word
            )

    return (
        None,
        None
    )


# =========================================================
# 🔤 ساخت / حذف فیلتر
# =========================================================

def handle_filter_command(
    message,
    chat_id,
    user_id,
    admins,
    send_message
):

    text = message.get(
        "text"
    )

    action, value = (
        parse_filter_command(
            text
        )
    )

    if action is None:

        return False

    if not is_admin(
        admins,
        user_id
    ):

        send_message(
            chat_id,
            "⛔ فقط ادمین‌های گروه می‌توانند فیلتر بسازند یا حذف کنند."
        )

        return True

    if not is_group_activated(
        chat_id
    ):

        send_message(
            chat_id,
            "⚠️ ابتدا ربات را با دستور «فعال سازی» فعال کنید."
        )

        return True

    # =====================================================
    # ➕ ساخت فیلتر
    # =====================================================

    if action == "add":

        reply_message = message.get(
            "reply_to_message"
        )

        if not reply_message:

            send_message(
                chat_id,
                "⚠️ برای ساخت فیلتر باید روی پیام موردنظر ریپلای کنید."
            )

            return True

        trigger_word = reply_message.get(
            "text"
        )

        if not trigger_word:

            send_message(
                chat_id,
                "⚠️ پیام ریپلای‌شده باید دارای متن باشد."
            )

            return True

        trigger_word = normalize_text(
            trigger_word
        )

        reply_text = normalize_text(
            value
        )

        if not trigger_word:

            send_message(
                chat_id,
                "❌ کلمه فیلتر قابل شناسایی نیست."
            )

            return True

        if not reply_text:

            send_message(
                chat_id,
                "❌ متن پاسخ خالی است."
            )

            return True

        success = add_filter(

            chat_id=chat_id,

            trigger_word=trigger_word,

            reply_text=reply_text
        )

        if success:

            send_message(
                chat_id,
                (
                    "✅ فیلتر با موفقیت ساخته شد.\n"
                    "\n"
                    "━━━━━━━━━━━━━━\n"
                    "\n"
                    f"🔤 کلمه تشخیص: {trigger_word}\n"
                    "\n"
                    f"💬 پاسخ ربات: {reply_text}\n"
                    "\n"
                    "━━━━━━━━━━━━━━"
                )
            )

        else:

            send_message(
                chat_id,
                "❌ ساخت فیلتر انجام نشد."
            )

        return True

    # =====================================================
    # ❌ حذف فیلتر
    # =====================================================

    if action == "delete":

        trigger_word = normalize_text(
            value
        )

        success = delete_filter(

            chat_id=chat_id,

            trigger_word=trigger_word
        )

        if success:

            send_message(
                chat_id,
                (
                    "✅ فیلتر حذف شد.\n"
                    "\n"
                    f"🔤 کلمه: {trigger_word}"
                )
            )

        else:

            send_message(
                chat_id,
                "ℹ️ چنین فیلتری در این گروه وجود ندارد."
            )

        return True

    return False


# =========================================================
# 💬 بررسی فیلتر روی پیام عادی
# =========================================================

def handle_word_filter(
    message,
    chat_id,
    send_message
):

    text = message.get(
        "text"
    )

    if not text:
        return False

    normalized_text = normalize_text(
        text
    )

    if not normalized_text:
        return False

    reply_text = get_filter_reply(

        chat_id=chat_id,

        trigger_word=normalized_text
    )

    if reply_text is None:

        return False

    send_message(
        chat_id,
        reply_text
    )

    return True


# =========================================================
# 💬 پردازش پیام
# =========================================================

def handle_message(
    message,
    get_chat_administrators,
    send_message,
    unrestrict_user,
    restrict_user,
    ban_member,
    unban_member,
    delete_message
):

    # =====================================================
    # 👥 اطلاعات گروه
    # =====================================================

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get(
        "type"
    )

    if chat_type not in (
        "group",
        "supergroup"
    ):

        return

    chat_id = chat.get(
        "id"
    )

    if chat_id is None:

        return


    # =====================================================
    # 👋 سیستم خوش‌آمدگویی / خداحافظی
    #
    # باید قبل از پردازش پیام‌های عادی اجرا شود.
    # =====================================================

    if handle_welcome(
        message=message,
        send_message=send_message
    ):

        return


    # =====================================================
    # 👤 اطلاعات کاربر
    # =====================================================

    user = message.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )


    # =====================================================
    # 📝 متن پیام
    # =====================================================

    text = message.get(
        "text"
    )

    normalized_text = normalize_text(
        text
    )


    # =====================================================
    # 👤 ثبت / بروزرسانی کاربر
    # =====================================================

    if user_id:

        try:

            register_user(

                user_id=user_id,

                first_name=user.get(
                    "first_name"
                ),

                last_name=user.get(
                    "last_name"
                ),

                username=user.get(
                    "username"
                )
            )

        except Exception as e:

            print(
                f"❌ [USER REGISTER ERROR] {e}"
            )


    # =====================================================
    # 👑 دریافت ادمین‌ها
    # =====================================================

    try:

        admins = get_chat_administrators(
            chat_id
        )

    except Exception as e:

        print(
            f"❌ [ADMIN ERROR] {e}"
        )

        admins = None


    # =====================================================
    # 🔤 دستورات فیلتر
    # =====================================================

    if handle_filter_command(

        message=message,

        chat_id=chat_id,

        user_id=user_id,

        admins=admins,

        send_message=send_message

    ):

        return


    # =====================================================
    # 🔤 بررسی فیلترهای ثبت‌شده
    # =====================================================

    if is_group_activated(
        chat_id
    ):

        if handle_word_filter(

            message=message,

            chat_id=chat_id,

            send_message=send_message

        ):

            return


    # =====================================================
    # 🔨 دستورات بن و آن‌بن
    # =====================================================

    BAN_COMMANDS = {

        "بن",
        "ban"
    }

    UNBAN_COMMANDS = {

        "آنبن",
        "آن بن",
        "آن‌بن",
        "ان بن",
        "ان‌بن",
        "انبن",
        "unban"
    }


    # =====================================================
    # 📊 دستور آمار
    # =====================================================

    if normalized_text in (
        "آمار",
        "آمار گروه",
        "آمارگروه"
    ):

        if not is_admin(
            admins,
            user_id
        ):

            send_message(
                chat_id,
                "⛔ فقط ادمین‌های گروه می‌توانند آمار گروه را مشاهده کنند."
            )

            return

        if not is_group_activated(
            chat_id
        ):

            send_message(
                chat_id,
                "⚠️ ابتدا ربات را با دستور «فعال سازی» فعال کنید."
            )

            return

        try:

            stats = get_group_statistics(
                chat_id
            )

        except Exception as e:

            print(
                f"❌ [STATISTICS ERROR] {e}"
            )

            send_message(
                chat_id,
                "❌ هنگام دریافت آمار خطایی رخ داد."
            )

            return

        statistics_text = build_statistics_text(
            stats
        )

        send_message(
            chat_id,
            statistics_text
        )

        return


    # =====================================================
    # 🔨 بن
    # =====================================================

    if normalized_text in BAN_COMMANDS:

        if not is_admin(
            admins,
            user_id
        ):

            send_message(
                chat_id,
                "⛔ فقط ادمین‌های گروه می‌توانند کاربر را بن کنند."
            )

            return

        reply_message = message.get(
            "reply_to_message"
        )

        if not reply_message:

            send_message(
                chat_id,
                "⚠️ دستور «بن» باید با ریپلای روی پیام کاربر استفاده شود."
            )

            return

        target_user = reply_message.get(
            "from",
            {}
        )

        target_user_id = target_user.get(
            "id"
        )

        if not target_user_id:

            send_message(
                chat_id,
                "❌ اطلاعات کاربر پیدا نشد."
            )

            return

        if is_admin(
            admins,
            target_user_id
        ):

            send_message(
                chat_id,
                "⛔ این دستور روی ادمین‌ها اعمال نمی‌شود."
            )

            return

        if is_user_banned(
            chat_id,
            target_user_id
        ):

            send_message(
                chat_id,
                "ℹ️ این کاربر از قبل بن است."
            )

            return

        success = ban_user(
            chat_id,
            target_user_id,
            ban_member
        )

        if success:

            send_message(
                chat_id,
                "🔨 کاربر با موفقیت بن شد."
            )

        else:

            send_message(
                chat_id,
                "❌ نتوانستم کاربر را بن کنم."
            )

        return


    # =====================================================
    # 🔓 آن‌بن
    # =====================================================

    if normalized_text in UNBAN_COMMANDS:

        if not is_admin(
            admins,
            user_id
        ):

            send_message(
                chat_id,
                "⛔ فقط ادمین‌های گروه می‌توانند کاربر را آن‌بن کنند."
            )

            return

        reply_message = message.get(
            "reply_to_message"
        )

        if not reply_message:

            send_message(
                chat_id,
                "⚠️ دستور «آنبن» باید با ریپلای روی پیام کاربر استفاده شود."
            )

            return

        target_user = reply_message.get(
            "from",
            {}
        )

        target_user_id = target_user.get(
            "id"
        )

        if not target_user_id:

            send_message(
                chat_id,
                "❌ اطلاعات کاربر پیدا نشد."
            )

            return

        if is_admin(
            admins,
            target_user_id
        ):

            send_message(
                chat_id,
                "⛔ این دستور روی ادمین‌ها اعمال نمی‌شود."
            )

            return

        if not is_user_banned(
            chat_id,
            target_user_id
        ):

            send_message(
                chat_id,
                "ℹ️ این کاربر بن نیست."
            )

            return

        success = unban_user(
            chat_id,
            target_user_id,
            unban_member
        )

        if success:

            send_message(
                chat_id,
                "✅ بن کاربر با موفقیت برداشته شد."
            )

        else:

            send_message(
                chat_id,
                "❌ نتوانستم بن کاربر را بردارم."
            )

        return


    # =====================================================
    # 🔇 سکوت
    # =====================================================

    if normalized_text in (
        "سکوت",
        "میوت"
    ):

        if not is_admin(
            admins,
            user_id
        ):

            send_message(
                chat_id,
                "⛔ فقط ادمین‌های گروه می‌توانند کاربر را ساکت کنند."
            )

            return

        reply_message = message.get(
            "reply_to_message"
        )

        if not reply_message:

            send_message(
                chat_id,
                "⚠️ دستور «سکوت» باید با ریپلای روی پیام کاربر استفاده شود."
            )

            return

        target_user = reply_message.get(
            "from",
            {}
        )

        target_user_id = target_user.get(
            "id"
        )

        if not target_user_id:

            send_message(
                chat_id,
                "❌ اطلاعات کاربر پیدا نشد."
            )

            return

        if is_admin(
            admins,
            target_user_id
        ):

            send_message(
                chat_id,
                "⛔ این دستور روی ادمین‌ها اعمال نمی‌شود."
            )

            return

        success = mute_user(
            chat_id,
            target_user_id,
            restrict_user
        )

        if success:

            send_message(
                chat_id,
                "🔇 کاربر با موفقیت سکوت شد."
            )

        else:

            send_message(
                chat_id,
                "❌ نتوانستم کاربر را سکوت کنم."
            )

        return


    # =====================================================
    # 🔊 حذف سکوت / حذف اخطارها
    # =====================================================

    if normalized_text in (
        "حذف سکوت",
        "حذف تمام اخطارها"
    ):

        if not is_admin(
            admins,
            user_id
        ):

            send_message(
                chat_id,
                "⛔ فقط ادمین‌های گروه می‌توانند این دستور را اجرا کنند."
            )

            return

        reply_message = message.get(
            "reply_to_message"
        )

        if not reply_message:

            send_message(
                chat_id,
                "⚠️ این دستور باید با ریپلای روی پیام کاربر استفاده شود."
            )

            return

        target_user = reply_message.get(
            "from",
            {}
        )

        target_user_id = target_user.get(
            "id"
        )

        if not target_user_id:

            send_message(
                chat_id,
                "❌ اطلاعات کاربر پیدا نشد."
            )

            return

        if is_admin(
            admins,
            target_user_id
        ):

            send_message(
                chat_id,
                "⛔ این دستور روی ادمین‌ها اعمال نمی‌شود."
            )

            return


        # =================================================
        # 🔊 حذف سکوت
        # =================================================

        if normalized_text == "حذف سکوت":

            result = unrestrict_user(
                chat_id,
                target_user_id
            )

            if result:

                remove_user_mute(
                    chat_id,
                    target_user_id
                )

                send_message(
                    chat_id,
                    "✅ سکوت کاربر با موفقیت حذف شد."
                )

            else:

                if is_user_muted(
                    chat_id,
                    target_user_id
                ):

                    send_message(
                        chat_id,
                        "❌ نتوانستم سکوت کاربر را از گروه حذف کنم."
                    )

                else:

                    send_message(
                        chat_id,
                        "ℹ️ این کاربر در حال حاضر سکوت نیست."
                    )

            return


        # =================================================
        # 🧹 حذف تمام اخطارها
        # =================================================

        if normalized_text == "حذف تمام اخطارها":

            reset_user_warnings(
                chat_id,
                target_user_id
            )

            send_message(
                chat_id,
                "✅ تمام اخطارهای این کاربر در این گروه حذف شد."
            )

            return


    # =====================================================
    # ⚡ فعال‌سازی ربات
    # =====================================================

    if is_activate_command(
        text
    ):

        if not is_admin(
            admins,
            user_id
        ):

            send_message(
                chat_id,
                "⛔ فقط ادمین‌های گروه می‌توانند ربات را فعال کنند."
            )

            return

        if is_group_activated(
            chat_id
        ):

            send_message(
                chat_id,
                "ℹ️ ربات از قبل در این گروه فعال است."
            )

            return

        title = (
            chat.get("title")
            or chat.get("first_name")
            or "بدون نام"
        )

        date = message.get(
            "date",
            int(time.time())
        )

        activate_group(
            chat_id=chat_id,
            title=title,
            created_at=date
        )

        send_message(
            chat_id,
            "✅ ربات با موفقیت در این گروه فعال شد."
        )

        return


    # =====================================================
    # ⚙️ تنظیمات ربات
    # =====================================================

    setting, value = parse_setting_command(
        text
    )

    if setting is None:
        return


    # =====================================================
    # 👑 بررسی ادمین
    # =====================================================

    if not is_admin(
        admins,
        user_id
    ):

        send_message(
            chat_id,
            "⛔ فقط ادمین‌های گروه می‌توانند تنظیمات ربات را تغییر دهند."
        )

        return


    # =====================================================
    # ⚡ بررسی فعال بودن ربات
    # =====================================================

    if not is_group_activated(
        chat_id
    ):

        send_message(
            chat_id,
            "⚠️ ابتدا ربات را با دستور «فعال سازی» فعال کنید."
        )

        return


    # =====================================================
    # 🔎 مقدار فعلی تنظیم
    # =====================================================

    current_value = get_group_setting(
        chat_id,
        setting
    )

    print(
        "⚙️ [SETTING DEBUG]",
        "chat_id=",
        chat_id,
        "setting=",
        setting,
        "current=",
        current_value,
        "requested=",
        value
    )


    # =====================================================
    # ℹ️ اگر مقدار از قبل همین باشد
    # =====================================================

    if current_value == value:

        if value:

            send_message(
                chat_id,
                "ℹ️ این قابلیت از قبل فعال است."
            )

        else:

            send_message(
                chat_id,
                "ℹ️ این قابلیت از قبل خاموش است."
            )

        return


    # =====================================================
    # 💾 ذخیره تنظیم جدید
    # =====================================================

    success = set_group_setting(
        chat_id,
        setting,
        value
    )

    if not success:

        send_message(
            chat_id,
            "❌ خطایی در ذخیره تنظیمات رخ داد."
        )

        return


    # =====================================================
    # 📢 پیام نتیجه
    # =====================================================

    if value:

        send_message(
            chat_id,
            f"✅ {get_setting_name(setting)} فعال شد."
        )

    else:

        send_message(
            chat_id,
            f"✅ {get_setting_name(setting)} خاموش شد."
        )


# =========================================================
# 🏷️ نام فارسی تنظیم
# =========================================================

def get_setting_name(
    setting
):

    names = {

        "anti_spam": "ضد اسپم",

        "anti_bad_words": "ضد فحش",

        "anti_link": "ضد لینک",

        "anti_forward": "ضد فوروارد",

        "anti_video": "ضد فیلم",

        "anti_photo": "ضد عکس",

        "anti_voice": "ضد ویس"
    }

    return names.get(
        setting,
        "این قابلیت"
    )
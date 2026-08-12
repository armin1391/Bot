import time

from database.database import (
    get_users_count,
    get_groups_count,
    get_connection
)

from api.bale import (
    send_message,
    get_chat
)


# =========================================================
# 👑 آیدی سازنده ربات
# =========================================================

OWNER_ID = 595450272


# =========================================================
# 📢 وضعیت ارسال همگانی
# =========================================================

broadcast_mode = False


# =========================================================
# 🔐 بررسی سازنده
# =========================================================

def is_owner(user_id):

    return user_id == OWNER_ID


# =========================================================
# 📊 تعداد کل گروه‌هایی که ربات در دیتابیس دارد
# =========================================================

def get_all_groups_count():

    connection = get_connection()

    try:

        result = connection.execute("""
            SELECT COUNT(*) AS count
            FROM groups
        """).fetchone()

        return result["count"]

    finally:

        connection.close()


# =========================================================
# 📊 دریافت آیدی تمام گروه‌ها
# =========================================================

def get_all_group_ids():

    connection = get_connection()

    try:

        result = connection.execute("""
            SELECT chat_id
            FROM groups
        """).fetchall()

        return [
            row["chat_id"]
            for row in result
        ]

    finally:

        connection.close()


# =========================================================
# 📊 دریافت آیدی تمام کاربران
# =========================================================

def get_all_user_ids():

    connection = get_connection()

    try:

        result = connection.execute("""
            SELECT user_id
            FROM users
        """).fetchall()

        return [
            row["user_id"]
            for row in result
        ]

    finally:

        connection.close()


# =========================================================
# 📊 آمار کاربران
# =========================================================

def users_statistics():

    count = get_users_count()

    return (
        "👥 آمار کاربران GuardX\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        f"👤 تعداد کل کاربران: {count}\n"
        "\n"
        "━━━━━━━━━━━━━━"
    )


# =========================================================
# 📊 آمار کامل گروه‌ها
# =========================================================

def groups_statistics():

    connection = get_connection()

    try:

        # =================================================
        # 📊 تعداد کل گروه‌ها
        # =================================================

        total_result = connection.execute("""
            SELECT COUNT(*) AS count
            FROM groups
        """).fetchone()

        # =================================================
        # 🟢 تعداد گروه‌های فعال
        # =================================================

        active_result = connection.execute("""
            SELECT COUNT(*) AS count
            FROM groups
            WHERE activated = 1
        """).fetchone()

        # =================================================
        # 📋 دریافت تمام گروه‌ها
        # =================================================

        groups = connection.execute("""
            SELECT
                chat_id,
                activated
            FROM groups
            ORDER BY created_at DESC
        """).fetchall()

    finally:

        connection.close()


    total_groups = total_result["count"]

    active_groups = active_result["count"]

    inactive_groups = (
        total_groups - active_groups
    )


    # =====================================================
    # 📋 ساخت لیست گروه‌ها
    # =====================================================

    group_list = []


    for group in groups:

        chat_id = group["chat_id"]

        activated = (
            group["activated"] == 1
        )

        username = None


        # =================================================
        # 🔎 دریافت username گروه
        # =================================================

        try:

            result = get_chat(
                chat_id
            )

            if result and result.get("ok"):

                chat = result.get(
                    "result",
                    {}
                )

                username = chat.get(
                    "username"
                )

        except Exception as e:

            print(
                f"❌ [GROUP INFO ERROR] "
                f"chat_id={chat_id} "
                f"error={e}"
            )


        # =================================================
        # 🆔 username یا آیدی عددی
        # =================================================

        if username:

            group_identifier = (
                f"@{username}"
            )

        else:

            group_identifier = (
                f"🆔 {chat_id}"
            )


        # =================================================
        # 🟢 / 🔴 وضعیت گروه
        # =================================================

        if activated:

            status = "🟢"

        else:

            status = "🔴"


        group_list.append(
            f"{status} {group_identifier}"
        )


    # =====================================================
    # 📋 اگر هیچ گروهی وجود نداشت
    # =====================================================

    if group_list:

        groups_text = "\n".join(
            group_list
        )

    else:

        groups_text = (
            "❌ هنوز هیچ گروهی ثبت نشده است."
        )


    # =====================================================
    # 📊 متن نهایی آمار گروه‌ها
    # =====================================================

    return (
        "📊 آمار گروه‌های GuardX\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        f"🏘️ کل گروه‌ها: {total_groups}\n"
        f"🟢 گروه‌های فعال: {active_groups}\n"
        f"🔴 گروه‌های غیرفعال: {inactive_groups}\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "📋 لیست گروه‌ها:\n"
        "\n"
        f"{groups_text}\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "🟢 فعال | 🔴 غیرفعال"
    )


# =========================================================
# 📢 شروع ارسال همگانی
# =========================================================

def start_broadcast():

    global broadcast_mode

    broadcast_mode = True


# =========================================================
# ❌ لغو ارسال همگانی
# =========================================================

def cancel_broadcast():

    global broadcast_mode

    broadcast_mode = False


# =========================================================
# 🔎 بررسی حالت ارسال همگانی
# =========================================================

def is_broadcast_mode():

    return broadcast_mode


# =========================================================
# 📢 ارسال همگانی
# =========================================================

def broadcast_message(
    text
):

    global broadcast_mode


    if not text:

        return {
            "success": 0,
            "failed": 0
        }


    user_ids = get_all_user_ids()

    group_ids = get_all_group_ids()


    targets = set(
        user_ids + group_ids
    )


    success = 0

    failed = 0


    for chat_id in targets:

        try:

            result = send_message(
                chat_id,
                text
            )


            if result:

                success += 1

            else:

                failed += 1


        except Exception as e:

            failed += 1


            print(
                f"❌ [BROADCAST ERROR] "
                f"chat_id={chat_id} "
                f"error={e}"
            )


        # -------------------------------------------------
        # کمی فاصله برای جلوگیری از فشار زیاد
        # -------------------------------------------------

        time.sleep(
            0.05
        )


    broadcast_mode = False


    return {
        "success": success,
        "failed": failed
    }


# =========================================================
# 🎛 پردازش دستورات سازنده
# =========================================================

def handle_admin_message(
    message,
    send_message_func=None
):

    global broadcast_mode


    user = message.get(
        "from",
        {}
    )


    user_id = user.get(
        "id"
    )


    # =====================================================
    # 🔐 فقط سازنده
    # =====================================================

    if not is_owner(
        user_id
    ):

        return False


    # =====================================================
    # 📝 متن پیام
    # =====================================================

    text = message.get(
        "text"
    )


    if not text:

        return False


    text = text.strip()


    # =====================================================
    # 📢 حالت ارسال همگانی
    # =====================================================

    if broadcast_mode:

        if text in (
            "لغو",
            "لغو ارسال",
            "لغو همگانی"
        ):

            cancel_broadcast()


            send_message(
                user_id,
                "❌ ارسال همگانی لغو شد."
            )


            return True


        result = broadcast_message(
            text
        )


        send_message(
            user_id,
            (
                "✅ ارسال همگانی انجام شد.\n"
                "\n"
                f"📤 موفق: {result['success']}\n"
                f"❌ ناموفق: {result['failed']}"
            )
        )


        return True


    # =====================================================
    # 📊 آمار کاربران
    # =====================================================

    if text in (
        "آمار کاربران",
        "آمار کاربر",
        "تعداد کاربران"
    ):

        send_message(
            user_id,
            users_statistics()
        )


        return True


    # =====================================================
    # 📊 آمار گروه‌ها
    # =====================================================

    if text in (
        "آمار گروه ها",
        "آمار گروه‌ها",
        "آمار گروه",
        "تعداد گروه ها",
        "تعداد گروه‌ها"
    ):

        send_message(
            user_id,
            groups_statistics()
        )


        return True


    # =====================================================
    # 📢 شروع ارسال همگانی
    # =====================================================

    if text in (
        "ارسال همگانی",
        "همگانی"
    ):

        start_broadcast()


        send_message(
            user_id,
            (
                "📢 حالت ارسال همگانی فعال شد.\n"
                "\n"
                "✏️ حالا پیام موردنظر خودت را بفرست.\n"
                "\n"
                "پیام برای تمام کاربران و گروه‌های ثبت‌شده "
                "ارسال خواهد شد.\n"
                "\n"
                "برای لغو بنویس:\n"
                "❌ لغو"
            )
        )


        return True


    return False

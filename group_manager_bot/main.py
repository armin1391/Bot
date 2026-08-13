import time
import queue
import threading


# =========================================================
# 🌐 API بله
# =========================================================

from api.bale import (
    api_request,
    get_chat_administrators,
    send_message,
    restrict_user,
    unrestrict_user,
    ban_member,
    unban_member,
    delete_message
)


# =========================================================
# 🗄️ دیتابیس
# =========================================================

from database.database import (
    init_database,
    register_group,
    record_group_message,
    record_member_event,
    is_group_activated
)


# =========================================================
# 👑 پنل سازنده ربات
# =========================================================

from admin import handle_admin_message


# =========================================================
# 🚀 سیستم /start و منوی اصلی
# =========================================================

from start import handle_start


# =========================================================
# 💬 پردازش اصلی پیام‌ها
# =========================================================

from handlers.messages import handle_message


# =========================================================
# 🛡️ قابلیت‌های امنیتی
# =========================================================

from anti_spam import handle_anti_spam
from anti_link import handle_anti_link
from anti_bad_words import handle_anti_bad_words
from anti_forward import handle_anti_forward
from anti_video import handle_anti_video
from anti_photo import handle_anti_photo
from anti_voice import handle_anti_voice


# =========================================================
# 📋 صف پیام‌ها
# =========================================================

update_queue = queue.Queue(
    maxsize=5000
)


# =========================================================
# 📥 دریافت آپدیت‌ها
# =========================================================

def get_updates(offset=None):

    data = {
        "timeout": 30,
        "limit": 100
    }

    if offset is not None:
        data["offset"] = offset

    return api_request(
        "getUpdates",
        data=data,
        timeout=35
    )


# =========================================================
# 🟢 ثبت خودکار گروه
#
# هر وقت از یک گروه آپدیت دریافت شود،
# گروه در دیتابیس ثبت می‌شود.
#
# اگر قبلاً فعال بوده باشد، فعال بودنش حفظ می‌شود.
# =========================================================

def ensure_group_registered(message):

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get(
        "type"
    )

    # فقط گروه و سوپرگروه
    if chat_type not in (
        "group",
        "supergroup"
    ):
        return False

    chat_id = chat.get(
        "id"
    )

    if chat_id is None:
        return False

    title = chat.get(
        "title"
    )

    try:

        register_group(
            chat_id=chat_id,
            title=title
        )

        print(
            f"👥 [GROUP REGISTERED] "
            f"chat_id={chat_id} "
            f"title={title}"
        )

        return True

    except Exception as e:

        print(
            f"❌ [GROUP REGISTER ERROR] {e}"
        )

        return False


# =========================================================
# 📊 ثبت آمار پیام گروه
# =========================================================

def record_message_statistics(message):

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

    user = message.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    if chat_id is None or user_id is None:
        return

    try:

        success = record_group_message(

            chat_id=chat_id,

            user_id=user_id,

            first_name=user.get(
                "first_name"
            ),

            last_name=user.get(
                "last_name"
            ),

            username=user.get(
                "username"
            ),

            message_id=message.get(
                "message_id"
            )
        )

        if success:

            print(
                f"📊 [MESSAGE RECORDED] "
                f"chat_id={chat_id} "
                f"user_id={user_id}"
            )

        else:

            print(
                f"ℹ️ [MESSAGE DUPLICATE] "
                f"chat_id={chat_id} "
                f"message_id={message.get('message_id')}"
            )

    except Exception as e:

        print(
            f"❌ [DATABASE ERROR] {e}"
        )


# =========================================================
# 👥 ثبت ورود اعضا
# =========================================================

def record_new_members(message):

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

    new_members = message.get(
        "new_chat_members",
        []
    )

    if not new_members:
        return

    for user in new_members:

        user_id = user.get(
            "id"
        )

        if user_id is None:
            continue

        try:

            success = record_member_event(

                chat_id=chat_id,

                user_id=user_id,

                event_type="join",

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

            if success:

                print(
                    f"🟢 [MEMBER JOIN] "
                    f"chat_id={chat_id} "
                    f"user_id={user_id}"
                )

        except Exception as e:

            print(
                f"❌ [MEMBER JOIN ERROR] {e}"
            )


# =========================================================
# 👋 ثبت خروج عضو
# =========================================================

def record_left_member(message):

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

    left_member = message.get(
        "left_chat_member"
    )

    if not left_member:
        return

    user_id = left_member.get(
        "id"
    )

    if user_id is None:
        return

    try:

        success = record_member_event(

            chat_id=chat_id,

            user_id=user_id,

            event_type="leave",

            first_name=left_member.get(
                "first_name"
            ),

            last_name=left_member.get(
                "last_name"
            ),

            username=left_member.get(
                "username"
            )
        )

        if success:

            print(
                f"🔴 [MEMBER LEAVE] "
                f"chat_id={chat_id} "
                f"user_id={user_id}"
            )

    except Exception as e:

        print(
            f"❌ [MEMBER LEAVE ERROR] {e}"
        )


# =========================================================
# 👥 پردازش رویدادهای اعضا
# =========================================================

def record_member_statistics(message):

    record_new_members(
        message
    )

    record_left_member(
        message
    )


# =========================================================
# 🛡️ اجرای قابلیت‌های امنیتی
# =========================================================

def run_security_handlers(
    message,
    admins
):

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get(
        "type"
    )

    chat_id = chat.get(
        "id"
    )

    if chat_type not in (
        "group",
        "supergroup"
    ):
        return False

    if chat_id is None:
        return False

    # -----------------------------------------------------
    # اگر گروه فعال نیست، امنیت اجرا نشود
    # -----------------------------------------------------

    if not is_group_activated(
        chat_id
    ):
        return False


    # =====================================================
    # ضد اسپم
    # =====================================================

    try:

        result = handle_anti_spam(

            message=message,

            admins=admins,

            send_message=send_message,

            restrict_user=restrict_user
        )

        if result:

            print(
                "🛡️ [ANTI-SPAM] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-SPAM ERROR] {e}"
        )


    # =====================================================
    # ضد لینک
    # =====================================================

    try:

        result = handle_anti_link(

            message=message,

            admins=admins,

            send_message=send_message,

            delete_message=delete_message,

            restrict_user=restrict_user
        )

        if result:

            print(
                "🛡️ [ANTI-LINK] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-LINK ERROR] {e}"
        )


    # =====================================================
    # ضد فوروارد
    # =====================================================

    try:

        result = handle_anti_forward(

            message=message,

            admins=admins,

            send_message=send_message,

            delete_message=delete_message,

            restrict_user=restrict_user
        )

        if result:

            print(
                "🛡️ [ANTI-FORWARD] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-FORWARD ERROR] {e}"
        )


    # =====================================================
    # ضد فیلم
    # =====================================================

    try:

        result = handle_anti_video(

            message=message,

            admins=admins,

            delete_message=delete_message
        )

        if result:

            print(
                "🛡️ [ANTI-VIDEO] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-VIDEO ERROR] {e}"
        )


    # =====================================================
    # ضد عکس
    # =====================================================

    try:

        result = handle_anti_photo(

            message=message,

            admins=admins,

            delete_message=delete_message
        )

        if result:

            print(
                "🛡️ [ANTI-PHOTO] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-PHOTO ERROR] {e}"
        )


    # =====================================================
    # ضد ویس
    # =====================================================

    try:

        result = handle_anti_voice(

            message=message,

            admins=admins,

            delete_message=delete_message
        )

        if result:

            print(
                "🛡️ [ANTI-VOICE] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-VOICE ERROR] {e}"
        )


    # =====================================================
    # ضد فحش
    # =====================================================

    try:

        result = handle_anti_bad_words(

            message=message,

            admins=admins,

            send_message=send_message,

            delete_message=delete_message,

            restrict_user=restrict_user
        )

        if result:

            print(
                "🛡️ [ANTI-BAD-WORDS] message handled"
            )

            return True

    except Exception as e:

        print(
            f"❌ [ANTI-BAD-WORDS ERROR] {e}"
        )


    return False


# =========================================================
# 👑 پردازش پنل سازنده
# =========================================================

def run_admin_handler(message):

    try:

        handled = handle_admin_message(
            message
        )

        if handled:

            print(
                "👑 [ADMIN] command handled"
            )

        return handled

    except Exception as e:

        print(
            f"❌ [ADMIN HANDLER ERROR] {e}"
        )

        return False


# =========================================================
# 💬 اجرای Handler اصلی
# =========================================================

def run_message_handler(message):

    try:

        handle_message(

            message=message,

            get_chat_administrators=(
                get_chat_administrators
            ),

            send_message=send_message,

            unrestrict_user=(
                unrestrict_user
            ),

            restrict_user=(
                restrict_user
            ),

            ban_member=ban_member,

            unban_member=unban_member,

            delete_message=delete_message
        )

    except Exception as e:

        print(
            f"❌ [MESSAGE HANDLER ERROR] {e}"
        )


# =========================================================
# ⚙️ پردازش اصلی آپدیت
# =========================================================

def process_update(update):

    message = update.get(
        "message"
    )

    if not message:
        return


    # =====================================================
    # اطلاعات پیام
    # =====================================================

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get(
        "type"
    )

    chat_id = chat.get(
        "id"
    )

    text = message.get(
        "text"
    )


    print(
        f"[MESSAGE] "
        f"type={chat_type} "
        f"chat_id={chat_id} "
        f"text={text}"
    )


    # =====================================================
    # 👥 ثبت خودکار گروه
    #
    # مهم:
    # این قسمت باید قبل از آمار و امنیت اجرا شود.
    #
    # اگر گروه قبلاً فعال شده باشد،
    # register_group فعال بودن آن را حفظ می‌کند.
    # =====================================================

    if chat_type in (
        "group",
        "supergroup"
    ):

        ensure_group_registered(
            message
        )


    # =====================================================
    # 🚀 سیستم /start و منوی اصلی
    # =====================================================

    try:

        start_handled = handle_start(

            message,

            send_message
        )

        if start_handled:

            print(
                "🚀 [START] command/button handled"
            )

            return

    except Exception as e:

        print(
            f"❌ [START HANDLER ERROR] {e}"
        )


    # =====================================================
    # 👑 پنل سازنده
    # =====================================================

    admin_handled = run_admin_handler(
        message
    )

    if admin_handled:

        return


    # =====================================================
    # 👥 ثبت ورود / خروج اعضا
    # =====================================================

    record_member_statistics(
        message
    )


    # =====================================================
    # 📊 ثبت پیام گروه
    # =====================================================

    record_message_statistics(
        message
    )


    # =====================================================
    # 👑 دریافت ادمین‌های گروه
    # =====================================================

    admins = None

    if chat_type in (
        "group",
        "supergroup"
    ):

        # -------------------------------------------------
        # فقط برای گروه فعال ادمین‌ها را بگیر
        #
        # گروه غیرفعال نیازی به API اضافی ندارد.
        # -------------------------------------------------

        if is_group_activated(
            chat_id
        ):

            try:

                admins = get_chat_administrators(
                    chat_id
                )

            except Exception as e:

                print(
                    f"❌ [ADMIN ERROR] {e}"
                )


    # =====================================================
    # 🛡️ اجرای سیستم امنیتی
    # =====================================================

    security_handled = run_security_handlers(

        message=message,

        admins=admins
    )


    # =====================================================
    # اگر امنیت پیام را مدیریت کرد
    # =====================================================

    if security_handled:

        return


    # =====================================================
    # 💬 Handler اصلی
    # =====================================================

    run_message_handler(
        message
    )


# =========================================================
# 👷 Worker
# =========================================================

def worker():

    while True:

        update = update_queue.get()

        try:

            process_update(
                update
            )

        except Exception as e:

            print(
                f"❌ [WORKER ERROR] {e}"
            )

        finally:

            update_queue.task_done()


# =========================================================
# 🚀 اجرای ربات
# =========================================================

def main():

    # =====================================================
    # 🗄️ ساخت دیتابیس
    # =====================================================

    try:

        init_database()

    except Exception as e:

        print(
            f"❌ [DATABASE INIT ERROR] {e}"
        )

        return


    print(
        "🚀 Bot starting..."
    )


    # =====================================================
    # 👷 ساخت Workerها
    # =====================================================

    workers = []

    for _ in range(4):

        thread = threading.Thread(

            target=worker,

            daemon=True
        )

        thread.start()

        workers.append(
            thread
        )


    # =====================================================
    # 📥 دریافت آپدیت‌ها
    # =====================================================

    offset = None


    while True:

        try:

            result = get_updates(
                offset
            )


            if not result:

                continue


            # =================================================
            # بررسی API
            # =================================================

            if not result.get(
                "ok"
            ):

                print(
                    "❌ [UPDATE ERROR]",
                    result
                )

                time.sleep(
                    1
                )

                continue


            updates = result.get(
                "result",
                []
            )


            # =================================================
            # قرار دادن آپدیت‌ها در صف
            # =================================================

            for update in updates:

                update_id = update.get(
                    "update_id"
                )

                if update_id is not None:

                    offset = (
                        update_id + 1
                    )


                try:

                    update_queue.put_nowait(
                        update
                    )

                except queue.Full:

                    print(
                        "⚠️ Update queue is full!"
                    )


        # =====================================================
        # 🛑 توقف دستی
        # =====================================================

        except KeyboardInterrupt:

            print(
                "\n🛑 Bot stopped."
            )

            break


        # =====================================================
        # ❌ خطای اصلی
        # =====================================================

        except Exception as e:

            print(
                f"❌ [MAIN ERROR] {e}"
            )

            time.sleep(
                1
            )


# =========================================================
# ▶️ شروع ربات
# =========================================================

if __name__ == "__main__":

    main()

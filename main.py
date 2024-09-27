import telebot
import json
import os
import threading
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import re

#✅ Подтвердить
#❎ Отклонить
#⛔ Заблокировать

def load_config():
    config_path = os.path.join(os.getcwd(), 'settings', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)


config = load_config()
TOKEN = config.get('token')

BAN_LIST_FILE = "user_data/ban_list.json"

bot = telebot.TeleBot(TOKEN)

USER_DATA_FILE = "./user_data/profile.json"

def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {}

    with open(USER_DATA_FILE, 'r') as file:
        data = json.load(file)
    return data


PROFILE_PATH = './user_data/profile.json'


def get_admin_profile(admin_id):
    try:
        with open(PROFILE_PATH, 'r') as profile_file:
            profiles = json.load(profile_file)

        if str(admin_id) not in profiles:
            return None

        profile = profiles[str(admin_id)]
        return {
            "nick": profile["nick"],
            "post": profile["post"],
            "ban": profile["ban"],
            "admin": profile["admin"]
        }
    except Exception as e:
        print(f"Ошибка при получении профиля: {e}")
        return None


@bot.message_handler(commands=['check'])
def handle_check_command(msg):
    command_parts = msg.text.split()
    if len(command_parts) < 2:
        bot.reply_to(msg, "Используйте команду вида: /check ID")
        return

    admin_id = command_parts[1]

    if admin_id.isdigit():
        try:
            admin_id = int(admin_id)

            if msg.from_user.id not in ADMIN_IDS:
                bot.reply_to(msg, f"Команда доступна только администраторам!")
                return

            profile = get_admin_profile(admin_id)
            if profile:
                output = f"""
Никнейм: {profile['nick']}
Постов: {profile['post']}
Блокировка: {'Да' if profile['ban'] else 'Нет'}
ID: {admin_id}
"""
                bot.reply_to(msg, output)
            else:
                bot.reply_to(msg, "Профиль не найден.")
        except ValueError:
            bot.reply_to(msg, "Ошибка: Введите корректный ID.")
    else:
        bot.reply_to(msg, "Ошибка: Введите корректный ID.")

def save_user_data(user_data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(user_data, file)


def create_or_update_profile(user_id, first_name, last_name=None):
    user_data = load_user_data()

    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "nick": f"{first_name} {last_name}" if last_name else first_name,
            "post": 0,
            "ban": False,
            "admin": user_id in ADMIN_IDS
        }
    else:
        if last_name:
            user_data[str(user_id)]["nick"] = f"{first_name} {last_name}"
        else:
            user_data[str(user_id)]["nick"] = first_name

    save_user_data(user_data)


def get_user_profile(user_id):
    user_data = load_user_data()
    return user_data.get(str(user_id), None)

def load_ban_list1():
    if not os.path.exists(BAN_LIST_FILE):
        return []

    with open(BAN_LIST_FILE, 'r') as file:
        data = json.load(file)
    return data.get("banned_users", [])


def save_ban_list(banned_users):
    with open(BAN_LIST_FILE, 'w') as file:
        json.dump({"banned_users": banned_users}, file)

@bot.message_handler(commands=['unban'])
def unban_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "У вас нет прав для использования этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 1:
        bot.reply_to(message, "Использование: /unban [ID]")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        bot.reply_to(message, "Неверный формат ID пользователя.")
        return

    banned_users = load_ban_list()
    if user_id not in banned_users:
        bot.reply_to(message, f"Пользователь с ID {user_id} не находится в бан-листе.")
        return

    banned_users.remove(user_id)
    save_ban_list(banned_users)

    bot.reply_to(message, f"Пользователь с ID {user_id} успешно удален из бан-листа.")
    bot.send_message(user_id, f"Администратор разблокировал доступ к боту.")
    bot.send_message(1118408954, f"Администратор {message.from_user.first_name} ({message.from_user.id}) снял блокировку {user_id}.")
    bot.send_message(7540267876, f"Администратор {message.from_user.first_name} ({message.from_user.id}) снял блокировку {user_id}.")

@bot.message_handler(commands=['ban'])
def ban_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "У вас нет прав для использования этой команды.")
        return

    args = message.text.split()[1:]
    if len(args) != 2:
        bot.reply_to(message, "Использование: /ban [ID] [Причина]")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        bot.reply_to(message, "Неверный формат ID пользователя.")
        return

    reason = args[1]

    banned_users = load_ban_list1()
    if user_id in banned_users:
        bot.reply_to(message, f"Пользователь с ID {user_id} уже находится в бан-листе.")
        return

    banned_users.append(user_id)
    save_ban_list(banned_users)

    bot.reply_to(message, f"Пользователь с ID {user_id} успешно добавлен в бан-лист.\nПричина: {reason}")
    bot.send_message(user_id, f"Администратор заблокировал доступ к боту. Причина: {reason}")
    bot.send_message(1118408954, f"Администратор {message.from_user.first_name} ({message.from_user.id}) выдал блокировку {user_id}. Причина: {reason}")
    bot.send_message(7540267876, f"Администратор {message.from_user.first_name} ({message.from_user.id}) выдал блокировку {user_id}. Причина: {reason}")

def load_ban_list():
    ban_list_path = os.path.join(os.getcwd(), 'user_data', 'ban_list.json')
    try:
        with open(ban_list_path, 'r') as f:
            data = json.load(f)
            banned_users = data.get('banned_users', [])
            if isinstance(banned_users, int):
                banned_users = [str(banned_users)]
            elif isinstance(banned_users, str):
                banned_users = [int(banned_users)]
            return banned_users
    except FileNotFoundError:
        print("Ban list file not found. Creating empty ban list.")
        return []

def load_config():
    config_path = os.path.join(os.getcwd(), 'settings', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()
channel_id = config.get('group')
banned_users = load_ban_list()



@bot.message_handler(commands=['start'], chat_types=['private'])
def start_message(message):
    create_or_update_profile(message.from_user.id, message.from_user.first_name, message.from_user.last_name)
    bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}! Чтобы написать пост в группу напиши команду /post. Перед тем, как отправлять какой либо пост рекомендуем вам ознакомиться с <a href="https://telegra.ph/Pravila-polzovaniya-bota-09-18">правилами</a>, незнание правил не освобождает от ответственности!', parse_mode="HTML")
"""
@bot.message_handler(commands=['post'], chat_types=['private'])
def start_message(message):
    banned_user_ids = load_ban_list()
    if message.from_user.id in banned_user_ids:
        bot.reply_to(message, "Вы заблокированы")
    else:
        bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}!')
        bot.reply_to(message, f"Для продолжения напишите текст поста.")
        bot.register_next_step_handler(message, check_for_banned_content)
"""

def check_for_banned_content(message):
    if message.content_type in ['sticker', 'photo', 'video', 'audio', 'document']:
        handle_media(message)
    else:
        report(message)
@bot.message_handler(content_types=['sticker', 'video', 'audio', 'document'], chat_types=['private'])
def handle_media(message):
    bot.reply_to(message, "Сообщение содержит запрещенный символ или контент (стикеры, медиа-файлы)")

@bot.message_handler(commands=['report', 'rep', 'реп', 'репорт'], chat_types=['private'])
def send_rep(message):
    bot.reply_to(message, "Опишите вашу проблему.")
    bot.register_next_step_handler(message, lambda msg: send_report(msg))

def send_report(message):
    bot.reply_to(message, 'Ваша жалоба успешно отправлена администраторам')
    bot.send_message(7540267876, f'Пользователь {message.from_user.first_name} ({message.from_user.id}) написал репорт:\n{message.text}\n\nОтветить: /answer [ID] [Text]')
    bot.send_message(1118408954, f'Пользователь {message.from_user.first_name} ({message.from_user.id}) написал репорт:\n{message.text}\n\nОтветить: /answer [ID] [Text]')

@bot.message_handler(commands=['answer'])
def handle_answer(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Команда доступна только администраторам.")

    if len(message.text.split()) < 3:
        bot.reply_to(message, "Использование: /answer [ID] [Text]")
        return

    match = re.match(r'/answer (\d+) (.+)', message.text)

    if match:
        chat_id, text = match.groups()

        bot.send_message(int(chat_id), "Ответ администратора: " + text)
        bot.reply_to(message, f"Сообщение отправлено пользователю {chat_id}")
    else:
        bot.reply_to(message, "Неверный формат команды")


ADMIN_IDS = [-1]


@bot.message_handler(commands=['sms'])
def handle_sms_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Эта команда доступна только администраторам.")
        delete_message_after_delay(message.chat.id, message.id, 5)
        return

    if message.reply_to_message:
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.id)

            # Отправляем подтверждение и сразу запускаем удаление через 5 секунд
            confirmation_message = bot.send_message(chat_id=message.chat.id, text="Сообщение успешно удалено.")
            delete_message_after_delay(message.chat.id, confirmation_message.id, 5)

            # Удаляем сообщение с командой через 5 секунд
            delete_message_after_delay(message.chat.id, message.id, 5)

        except Exception as e:
            bot.send_message(chat_id=message.chat.id, text=f"Ошибка при удалении сообщения: {str(e)}")
            delete_message_after_delay(message.chat.id, message.id, 5)
    else:
        bot.reply_to(message, "Пожалуйста, ответьте на сообщение, которое хотите удалить.")
        delete_message_after_delay(message.chat.id, message.id, 5)


@bot.message_handler(commands=['kick'])
def handle_kick_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Эта команда доступна только администраторам.")
        delete_message_after_delay(message.chat.id, message.id, 5)
        return

    args = message.text.split()[1:]

    if len(args) < 1:
        bot.reply_to(message, "Укажите ID или username пользователя для кика.")
        delete_message_after_delay(message.chat.id, message.id, 5)
        return

    target = args[0].strip('@')

    try:
        # Попытка найти пользователя по ID
        if target.isdigit():
            target_user = bot.get_chat_member(message.chat.id, int(target))
        else:
            # Поиск пользователя по username (предполагаем, что бот видит всех участников чата)
            chat_members = bot.get_chat_administrators(message.chat.id)
            target_user = next((member for member in chat_members if member.user.username.lower() == target.lower()),
                               None)

            if target_user is None:
                raise ValueError("Пользователь не найден в чате")

        if target_user.user.id == message.from_user.id:
            bot.reply_to(message, "Вы не можете кикнуть самого себя!")
            delete_message_after_delay(message.chat.id, message.id, 5)
            return

        if target_user.status == 'creator' or target_user.user.id in ADMIN_IDS:
            bot.reply_to(message, "Вы не можете кикнуть создателя чата или другого администратора.")
            delete_message_after_delay(message.chat.id, message.id, 5)
            return

        try:
            bot.kick_chat_member(message.chat.id, target_user.user.id)

            kick_message = bot.send_message(chat_id=message.chat.id,
                                            text=f"Пользователь @{target_user.user.username} был кикнут из чата.")
            delete_message_after_delay(message.chat.id, kick_message.id, 5)

            delete_message_after_delay(message.chat.id, message.id, 5)

        except Exception as e:
            bot.send_message(chat_id=message.chat.id, text=f"Ошибка при кике пользователя: {str(e)}")
            delete_message_after_delay(message.chat.id, message.id, 5)

    except Exception as e:
        bot.send_message(chat_id=message.chat.id, text=f"Ошибка при поиске пользователя: {str(e)}")
        delete_message_after_delay(message.chat.id, message.id, 5)


def delete_message_after_delay(chat_id, message_id, delay):
    threading.Timer(delay, lambda: bot.delete_message(chat_id=chat_id, message_id=message_id)).start()


def report(message):
    global message1
    message1 = message.text
    bot.send_message(message.chat.id, f'Сообщение отправлено.')
    bot.send_message(channel_id, message.text + "\n\n<a href='https://t.me/vnekrasovkeTheyhateit'>Подписаться «В Некрасовке ненавидят»</a>", parse_mode="HTML")
    bot.send_message(1118408954, f"Пользователь {message.from_user.first_name} ({message.chat.id}) написал:\n{message.text}")
    bot.send_message(7540267876, f"Пользователь {message.from_user.first_name} ({message.chat.id}) написал:\n{message.text}")
    bot.send_message(6588275554, f"Пользователь {message.from_user.first_name} ({message.chat.id}) написал:\n{message.text}")

@bot.message_handler(commands=['test'])
def start_message(message):
    bot.reply_to(message, f"Всё рабит.")

@bot.message_handler(commands=['test1'])
def start_message(message):
    bot.reply_to(message, f"{banned_users}")


@bot.message_handler(commands=['post'], chat_types=['private'])
def handle_apost1(message):
    create_or_update_profile(message.from_user.id, message.from_user.first_name, message.from_user.last_name)

    buttons = [
        InlineKeyboardButton("Текст", callback_data="text"),
        InlineKeyboardButton("Фотография", callback_data="photo")
    ]
    keyboard = InlineKeyboardMarkup([buttons])

    bot.send_message(
        message.chat.id,
        "Выберите тип поста:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    banned_users = load_ban_list1()
    if call.message.from_user.id in banned_users:
        bot.reply_to(call.message, "Вы заблокированы")
    else:
        if call.data == "text":
                markup = types.InlineKeyboardMarkup()
                cancel_button = types.InlineKeyboardButton(text="Отмена", callback_data="cancel")
                markup.add(cancel_button)
                bot.edit_message_text(text=f"Для продолжения напишите текст поста.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
                bot.register_next_step_handler(call.message, check_for_banned_content)
        elif call.data == "photo":
            send_photo_post_message(call.message.chat.id)
        elif call.data == "cancel":
            bot.edit_message_text(text="Выбор отменен.", chat_id=call.message.chat.id, message_id=call.message.message_id)


def send_text_post_message(chat_id):
    bot.send_message(
        chat_id,
        "Введите текст поста:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Отмена", callback_data="cancel")]
        ])
    )


def send_photo_post_message(chat_id):
    bot.send_message(
        chat_id,
        "Приложите фотографию:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Отмена", callback_data="cancel")]
        ])
    )

"""
@bot.message_handler(content_types=['text'])
def handle_text_post(message):
    if message.text.lower() == "отмена":
        bot.reply_to(message, "Действие отменено.")
        return

    send_post_to_admins(message.text)
    bot.reply_to(message, "Спасибо за пост! Он был успешно отправлен админам.")
"""

@bot.message_handler(content_types=['photo'], chat_types=["private"])
def handle_photo_post(message):
    if message.caption and message.caption.lower() == "отмена":
        bot.reply_to(message, "Действие отменено.")
        return
    admin_ids = ADMIN_IDS
    for admin_id in admin_ids:
        try:
            caption = f"Пользователь {message.from_user.first_name} ({message.from_user.id}) отправил фотографию"
            bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption)
        except Exception as e:
            print(f"Ошибка при отправке фото администратору {admin_id}: {e}")



if __name__ == '__main__':
    print("Бот love запущен.")
    bot.polling()

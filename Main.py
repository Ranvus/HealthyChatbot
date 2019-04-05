import telebot
from telebot import types
import sqlite3


bot = telebot.TeleBot("868448262:AAEyTx0GKka-N2u7Ptb1zPis5S8aZJk9514")
# 0 - на рассмотрении
# 1 - заказ взят
# 2 - заказ закрыт

@bot.message_handler(commands=['start'])
def start(message):

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT EXISTS(SELECT * FROM applications WHERE user_name = %s LIMIT 1)" % message.chat.id)
    rows = cursor.fetchall()
    print(rows[0][0])
    if rows[0][0] != 1:
        conn.close
        keyboard.add(*[types.KeyboardButton(name) for name in ["Записаться на консультацию"]])
        bot.send_message(message.chat.id,
                         "Привет! Спасибо что написали мне, я могу помочь вам с консультацией по вашему здоровью", reply_markup=keyboard)
        bot.register_next_step_handler(message, doctor_change)
    else:
        bot.send_message(message.chat.id, "Вы уже записаны на онлайн консультацию, пожалуйста ожидайте")
        conn.close


def doctor_change(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in
                   ["Терапевт", "Педиатр", "Кардиолог", "Травматолог", "Онколог", "Невролог", "Не знаю"]])
    bot.send_message(message.chat.id,
                     "У какого специалиста вы хотите пройти онлайн консультацию?", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_user_request_spec)


def get_user_request_spec(message):
    spec = message.text
    bot.send_message(message.chat.id, "Пожалуйста составьте краткое описание вашей проблемы")
    bot.register_next_step_handler(message, get_user_request_inf, spec)


def get_user_request_inf(message, spec):
    bot.send_message(message.chat.id, "Вы успешно отправили вашу заявку")
    col = (message.chat.id, spec, message.text, 0, message.from_user.username)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applications (user_name, doctor_spec, short_inf, status, user_login) VALUES (?,?,?,?,?)", col)
    conn.commit()
    conn.close


@bot.message_handler(commands=['work'])
def work(message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications")
    rows = cursor.fetchall()

    cursor.execute("SELECT status FROM applications")
    list = cursor.fetchall()
    conn.close()

    if any(0 in s for s in list):

        for i in rows:
            if i[4] == 0:
                keyboard = types.InlineKeyboardMarkup()
                callback_button = types.InlineKeyboardButton(text="Взять заказ", callback_data=str(i[0]))
                keyboard.add(callback_button)

                bot.send_message(message.chat.id, "Запрос №" + str(i[0]) + "\n" + "Нужен специалист: " + i[2] +
                             "\n" + "Клиент с номером: " + i[1] + "\n" + "Краткое описание проблемы: " + i[3],
                             reply_markup=keyboard)

    else:
        bot.send_message(message.chat.id, "Пока что запросов нет")


@bot.callback_query_handler(func=lambda c:True)
def inline(c):
    bot.send_message(c.message.chat.id, "Как врачу: \nПоздравляем, вы взяли заказ №" + str(c.data))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status = '%s'  WHERE app_id = '%s'" % (1, int(c.data)))
    cursor.execute("SELECT user_name FROM applications WHERE app_id = %s" % int(c.data))
    rows = cursor.fetchall()
    user_id = rows[0][0]

    cursor.execute("SELECT user_login FROM applications WHERE app_id = %s" % int(c.data))
    rows = cursor.fetchall()
    user_login = rows[0][0]
    bot.send_message(c.message.chat.id, "Как врачу: \nПожалуйста свяжитесь со своими клиентом @" + user_login)

    bot.send_message(user_id, "Как пользователю: \nВашу заявку принял специалист номер " + str(c.message.chat.id) +
                     ", он свяжется с вами в ближайшее время")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    bot.polling(none_stop=True)

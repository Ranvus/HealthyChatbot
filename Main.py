import telebot
from telebot import types
import sqlite3


bot = telebot.TeleBot("")


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
    col = (message.chat.id, spec, message.text)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applications (user_name, doctor_spec, short_inf) VALUES (?,?,?)", col)
    conn.commit()
    conn.close


@bot.message_handler(commands=['work'])
def work(message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications")
    rows = cursor.fetchall()
    for i in rows:
        bot.send_message(message.chat.id, "Запрос №" + str(i[0]) + "\n" + "Нужен специалист: " + i[2] +
                         "\n" + "Клиент с номером: " + i[1] + "\n" + "Краткое описание проблемы: " + i[3])
    conn.commit()
    conn.close


if __name__ == "__main__":
    bot.polling(none_stop=True)

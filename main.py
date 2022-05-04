import telebot
import json
import requests
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
import os

bot = telebot.TeleBot("5279674502:AAFXF-kDxk_WVVo9Br5YN5PmNQohsR3oxFQ")


def menu1():
    m = InlineKeyboardMarkup()
    m.row_width = 1
    m.add(InlineKeyboardButton("📈 Цены", callback_data='getprice'),
          InlineKeyboardButton("💼⟵ Добавить в портфель", callback_data='addtocase'),
          InlineKeyboardButton("💼⟶ Получить портфель", callback_data='getcase'),
          )
    return m


def menu2():
    m = InlineKeyboardMarkup()
    m.row_width = 1
    m.add(InlineKeyboardButton("‹ В меню", callback_data="tomenu"))
    return m


# def startkb():  # Добавление клавиатуры
#    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
#    Start = KeyboardButton("В меню")
#    keyboard.add(Start)
#    return keyboard


# @bot.message_handler(content_types=['text'])
# def start_msg(message): #Начало работы
#   bot.send_message(message.chat.id,"Добро пожаловать, для продолжения отправьте сообщение любого содержания",reply_markup=startkb())
#  bot.register_next_step_handler(message, mainmenu)

@bot.message_handler(func=lambda message: message.text == "/start")
def mainmenu(message):
    bot.send_message(message.chat.id,
                     '"Цены" - получение цены котировки\n"Добавить в портфель" - добавление котировки в портфель'
                     '\n"Получить портфель" - вывод портфеля и информации о прибыли', reply_markup=menu1())


@bot.message_handler(func=lambda message: message.text != "/start")
def errormsg(message):
    bot.send_message(message.chat.id, "Перемещайтесь по меню с помощью встроенных кнопок")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == "getprice":
                bot.edit_message_text(
                    '"Цены" - получение цены котировки\n"Добавить в портфель" - добавление котировки в портфель'
                    '\n"Получить портфель" - вывод портфеля и информации о прибыли',
                    call.message.chat.id, call.message.message_id,)
                bot.send_message(call.message.chat.id,'Введите тикер для получения информации')
                bot.answer_callback_query(call.id)
                bot.register_next_step_handler(call.message, send_ticker)
            elif call.data == "addtocase":
                bot.edit_message_text("Введите тикер для добавления в портфель", call.message.chat.id,
                                      call.message.message_id)
                bot.answer_callback_query(call.id)
                bot.register_next_step_handler(call.message, add_stock_case)
            elif call.data == "getcase":
                bot.send_message(call.message.chat.id, "Подсчитываю...")
                get_stock_case(call.message)
            elif call.data == "tomenu":
                bot.edit_message_text(
                    '"Цены" - получение цены котировки\n"Добавить в портфель" - добавление котировки в портфель'
                    '\n"Получить портфель" - вывод портфеля и информации о прибыли',
                    call.message.chat.id, call.message.message_id, reply_markup=menu1())
                bot.answer_callback_query(call.id)
    except Exception as e:
        print(repr(e))


def get_current_price(id):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        r = requests.get(url)
        data = r.json()
        print(data)
        r1 = data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['4. close']
        res = id + ' ' + r1
        return (res.split(' '))
    except:
        return (-1)


def add_stock_case(message):
    if (message.text == '/start'):
        mainmenu(message)
        return
    f = open('text.txt', 'a')
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        t = get_current_price(id)
        res = t[0] + ' ' + t[1]
        if (not os.stat("text.txt").st_size == 0): res = '\n' + res
        print(res)

        bot.send_message(message.chat.id, "Введите количество")
        bot.register_next_step_handler(message, add_num_of_stocks, res)
    except:
        bot.send_message(message.chat.id, 'Некорректный тикер. Попробуйте снова')
        bot.register_next_step_handler(message, add_stock_case)


def get_stock_case(message):
    f = open('text.txt', 'r')
    summC = 0
    summS = 0
    msg = ''
    while (True):
        s = f.readline().split(' ')
        print(s)
        if (s == ''): break
        id = s[0]
        t = get_current_price(id)
        if (t != -1):
            summC += float(s[1]) * float(s[2])
            summS += float(t[1]) * float(s[2])
            delta = (float(s[1]) - float(t[1])) * float(s[2])
            if (delta > 0):
                msg += id + ': Вы заработали ' + '{:8.3f}'.format(abs(delta)) + 'USD (' + '{:8.3f}'.format(
                    100 * float(s[1]) / float(t[1]) - 100) + ' %)'+'\n'
            else:
                msg += id + ': Вы потеряли ' + '{:8.3f}'.format(abs(delta)) + 'USD (' + '{:8.3f}'.format(
                                     100 * float(s[1]) / float(t[1]) - 100) + ' %)'+'\n'
        else:
            break
    bot.send_message(message.chat.id, msg)
    bot.send_message(message.chat.id,
                     'Итоговая разница в стоимости: ' + '{:8.3f}'.format(summC - summS) + 'USD (' + '{:8.3f}'.format(
                         100 * summC / summS - 100) + ' %)')


def send_ticker(message):
    if (message.text == '/start'):
        mainmenu(message)
        return
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        r = requests.get(url)
        data = r.json()
        print(data)
        res = 'Последнее обновление о тикере ' + id + ' от ' + data['Meta Data']['3. Last Refreshed'] + ' :\n'
        res += 'хуйня1 '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['1. open']+'\n'
        res += 'хуйня2 '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['2. high'] + '\n'
        res += 'хуйня3 '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['3. low'] + '\n'
        res += 'хуйня4 '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['4. close'] + '\n'
        res += 'хуйня5 '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['5. volume'] + '\n'
        # for r1 in (data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]):
        #     res = res + r1 + ' ' + data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']][r1] + '\n'
        bot.send_message(message.chat.id, res, reply_markup=menu2())
    except:
        bot.send_message(message.chat.id, 'Введен некорректный тикер', reply_markup=menu2())


def add_num_of_stocks(message, res):
    f = open('text.txt', 'a')
    if ((message.text).isdigit()):
        r = res + ' ' + message.text
        f.write(r)
        bot.send_message(message.chat.id, 'заебись заКИнул')
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод. Попробуйте снова')


bot.polling(none_stop=True, interval=0)
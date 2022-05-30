import telebot
import requests
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import  json
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':'https://invest-bot-ffad6-default-rtdb.firebaseio.com/'
})
bot = telebot.TeleBot("5279674502:AAFXF-kDxk_WVVo9Br5YN5PmNQohsR3oxFQ")

def menu1():
    m = InlineKeyboardMarkup()
    m.row_width = 1
    m.add(InlineKeyboardButton("📈 Цены", callback_data='getprice'),
          InlineKeyboardButton("💼⟵ Добавить в портфель", callback_data='addtocase'),
          InlineKeyboardButton("💼⟶ Получить портфель", callback_data='getcase'),
          InlineKeyboardButton("🚫 Очистить портфель", callback_data='clear')
          )
    return m


def menu2():
    m = InlineKeyboardMarkup()
    m.row_width = 1
    m.add(InlineKeyboardButton("‹ В меню", callback_data="tomenu"))
    return m

@bot.message_handler(func=lambda message: message.text == "/start")
def mainmenu(message):
    bot.send_message(message.chat.id,
                     '"Цены" - получение цены котировки\n"Добавить в портфель" - добавление котировки в портфель'
                     '\n"Получить портфель" - вывод портфеля и информации о прибыли', reply_markup=menu1())


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chatID = call.message.chat.id
    msgID = call.message.message_id
    try:
        if call.message:
            if call.data == "getprice":
                bot.edit_message_text('Введите тикер для получения информации',chatID,msgID)
                bot.answer_callback_query(call.id)
                bot.register_next_step_handler(call.message, send_ticker)
            elif call.data == "addtocase":
                c = get_count_of_stocks_case()
                if (c<5):
                    bot.edit_message_text("Введите тикер для добавления в портфель", chatID, msgID)
                    bot.answer_callback_query(call.id)
                    bot.register_next_step_handler(call.message, add_stock_case)
                else:
                    bot.edit_message_text("К сожалению, в текущей версии бота размер портфеля ограничен 5 позициями",
                                          chatID,msgID,reply_markup=menu2())
            elif call.data == "getcase":
                bot.edit_message_text("Подсчитываю...",chatID,msgID)
                bot.answer_callback_query(call.id)
                get_stock_case(call.message)
            elif call.data == "tomenu":
                bot.edit_message_text(
                    '"Цены" - получение цены котировки\n"Добавить в портфель" - добавление котировки в портфель'
                    '\n"Получить портфель" - вывод портфеля и информации о прибыли',
                    chatID, msgID, reply_markup=menu1())
                bot.answer_callback_query(call.id)
            elif call.data == "clear":
                clear_case()
                bot.edit_message_text("Данные портфеля очищены\n",chatID,msgID,reply_markup=menu2())
    except Exception as e:
        print(repr(e))


def add_stock_case(message):
    if (message.text == '/start'):
        mainmenu(message)
        return
    #f = open('text.txt', 'a')
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        t = get_current_price(id)
        if (t == -2):
            bot.send_message(message.chat.id,
                             "К сожалению, в данной версии бота присутствует ограничение, равное 5 запросов в минуту",
                             reply_markup=menu2())
            return
        bot.send_message(message.chat.id, "Введите количество")
        bot.register_next_step_handler(message, add_num_of_stocks, t,id)
    except:
        bot.send_message(message.chat.id, 'Некорректный тикер.',reply_markup=menu2())



def get_stock_case(message):
    flag = True
    summC = 0
    summS = 0
    msg = ''
    ref = db.reference("/")
    ticks = ref.get()
    try:
        for k in ticks:
            for k1 in ticks[k]:
                t = get_current_price(k1)
                if (t != -1 and t != -2):
                    summC+= float(ticks[k][k1]["Price"])*float(ticks[k][k1]["Amount"])
                    summS+= float(t)*float(ticks[k][k1]["Amount"])
                    delta = (float(t) - float(ticks[k][k1]["Price"])) * float(ticks[k][k1]["Amount"])
                    if (delta > 0):
                        msg += k1 + ': Вы заработали ' + '{:0.3f}'.format(abs(delta)) + ' USD (' + '{:0.1f}'.format(
                            100 * float(t) / float(ticks[k][k1]["Price"]) - 100) + ' %)'+'\n'
                    else:
                        msg += k1 + ': Вы потеряли ' + '{:0.3f}'.format(abs(delta)) + ' USD (' + '{:0.1f}'.format(
                            100 * float(t) / float(ticks[k][k1]["Price"]) - 100) + ' %)'+'\n'
                elif (t == -2):
                    flag = False
                    break
                else:
                    break
    except:
        bot.send_message(message.chat.id, "Данные по портфелю отсутствуют", reply_markup=menu2())
        return
    if (msg!=''): bot.send_message(message.chat.id, msg)
    if (flag):
        bot.send_message(message.chat.id,
                     'Итоговая разница в стоимости: ' + '{:0.3f}'.format(summS - summC) + ' USD (' + '{:0.1f}'.format(
                         100 * summS / summC - 100) + ' %)',reply_markup=menu2())
    else:
        bot.send_message(message.chat.id,
                         "К сожалению, в данной версии бота присутствует ограничение, равное 5 запросов в минуту",
                         reply_markup=menu2())

def get_current_price(id):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        r = requests.get(url)
        data = r.json()
        if 'Note' in data: return (-2)
        r1 = data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['4. close']
        return (r1)
    except:
        return (-1)

def send_ticker(message):
    if (message.text == '/start'):
        mainmenu(message)
        return
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        r = requests.get(url)
        data = r.json()
        if 'Note' in data:
            bot.send_message(message.chat.id,"К сожалению, в данной версии бота присутствует ограничение, равное 5 запросов в минуту",reply_markup=menu2())
            return
        res = 'Последнее обновление о тикере ' + id + ' от ' + data['Meta Data']['3. Last Refreshed'] + ' :\n'
        res += 'Открытие:  '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['1. open']+' USD\n'
        res += 'Максимум:  '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['2. high'] + ' USD\n'
        res += 'Минимум:  '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['3. low'] + ' USD\n'
        res += 'Закрытие:  '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['4. close'] + ' USD\n'
        res += 'Объем торгов:  '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]['5. volume'] + '\n'
        bot.send_message(message.chat.id, res, reply_markup=menu2())
    except:
        bot.send_message(message.chat.id, 'Введен некорректный тикер', reply_markup=menu2())

def add_num_of_stocks(message, res, id):
    if (message.text == '/start'):
        mainmenu(message)
        return
    if ((message.text).isdigit()):
        r = message.text
        json_ticker = {
            id:
                {
                    "Amount": r,
                    "Price": res
                }
        }
        ref = db.reference("/")
        ref.push(json_ticker)
        bot.send_message(message.chat.id, 'Данные добавлены в портфель',reply_markup=menu2())
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод.',reply_markup=menu2())

def get_count_of_stocks_case():
    count=0
    ref = db.reference("/")
    try:
        bd = ref.get()
        for k in bd:
            count+=1
        return count
    except:
        return 0

def clear_case():
    ref = db.reference("/")
    bd = ref.set({})

bot.polling(none_stop=True, interval=0)
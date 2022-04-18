import telebot
import json
import requests
from telebot import types
import os
bot = telebot.TeleBot("5279674502:AAFXF-kDxk_WVVo9Br5YN5PmNQohsR3oxFQ")

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

def catalog_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    Help = types.KeyboardButton(text="/help")
    Price = types.KeyboardButton(text="/get_price")
    Add_stock = types.KeyboardButton(text="/add_to_case")
    Get_stock = types.KeyboardButton(text="/get_case")
    keyboard.add(Help, Price, Add_stock, Get_stock)
    return keyboard

@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/help':
        bot.send_message(message.chat.id, 'Для получения цены котировки введите /get_price\nДля добавления котировки в портфель введите /add_to_case\nДля получения цены портфеля введите /get_case', reply_markup=catalog_keyboard())
        #bot.send_message(message.from_user.id, 'Для получения цены котировки введите /get_price\nДля добавления котировки в портфель введите /add_to_case\nДля получения цены портфеля введите /get_case')
    elif message.text == '/get_price':
        bot.send_message(message.from_user.id, "input ticker")
        bot.register_next_step_handler(message, send_ticker)  # следующий шаг – функция get_name
    elif message.text == '/add_to_case':
        bot.send_message(message.from_user.id, "input ticker")
        bot.register_next_step_handler(message, add_stock_case)
    elif message.text == '/get_case':
        bot.send_message(message.from_user.id, "calculating")
        get_stock_case(message)
    else:
        bot.send_message(message.from_user.id, 'Не смог разобрать команду.\nНапиши /help')

def add_stock_case(message):
    f = open('text.txt', 'a')
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        t = get_current_price(id)
        res = t[0]+' '+t[1]
        if (not os.stat("text.txt").st_size == 0): res = '\n'+res
        print(res)

        bot.send_message(message.from_user.id, "input amount of stocks")
        bot.register_next_step_handler(message, add_num_of_stocks, res)
    except:
        bot.send_message(message.from_user.id, 'incorrect ticker. Try again')
        bot.register_next_step_handler(message, add_stock_case)

def get_stock_case(message):
    f = open('text.txt', 'r')
    summC=0
    summS=0
    while (True):
        s = f.readline().split(' ')
        print(s)
        if (s == ''): break
        id = s[0]
        t = get_current_price(id)
        if (t!=-1):
            summC+=float(s[1])*float(s[2])
            summS+=float(t[1])*float(s[2])
            delta = (float(s[1]) - float(t[1])) * float(s[2])
            if (delta>0): bot.send_message(message.from_user.id, id +': u have rised up ' + str(abs(delta)) +'USD ('+'{:8.3f}'.format(100*float(s[1]) / float(t[1])-100)+' %)')
            else: bot.send_message(message.from_user.id, id +': u have lost ' + str(abs(delta)) +'USD ('+'{:8.3f}'.format(100*float(s[1]) / float(t[1])-100)+' %)')
        else: break
    bot.send_message(message.from_user.id, 'Итоговая разница в стоимости: '+ str(summC-summS) + 'USD ('+'{:8.3f}'.format(100*summC / summS-100)+' %)')

def send_ticker(message):
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=' + id + '&interval=1min&apikey=GA64HKYKKJO0LUUU'
    try:
        r = requests.get(url)
        data = r.json()
        print(data)
        res = 'Last refreshed information about ' + id + ' ticker at ' + data['Meta Data']['3. Last Refreshed'] + ':\n'
        for r1 in (data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]):
            res = res + r1 + ' ' + data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']][r1] + '\n'
        bot.send_message(message.from_user.id, res)
    except:
        bot.send_message(message.from_user.id, 'incorrect ticker. Try again')
        bot.register_next_step_handler(message, send_ticker)

def add_num_of_stocks(message,res):
    f = open('text.txt', 'a')
    if ((message.text).isdigit()):
            r = res+' '+message.text
            f.write(r)
            bot.send_message(message.from_user.id, 'good')
    else:
        bot.send_message(message.from_user.id,'incorrect num. Try again')
bot.polling(none_stop=True, interval=0)

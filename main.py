import telebot
import requests
bot = telebot.TeleBot("5279674502:AAFXF-kDxk_WVVo9Br5YN5PmNQohsR3oxFQ")

@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/help':
        bot.send_message(message.from_user.id,'Для получения цены котировки введите /get_price')
    elif message.text == '/get_price':
        bot.send_message(message.from_user.id, "input ticker")
        bot.register_next_step_handler(message, send_ticker) #следующий шаг – функция get_name
    else:
        bot.send_message(message.from_user.id, 'Не смог разобрать команду.\nНапиши /help')

def send_ticker(message):
    global id
    id = message.text
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='+id+'&interval=1min&apikey=GA64HKYKKJO0LUUU'
    r = requests.get(url)
    data = r.json()
    print(data)
    try:
        res='Last refreshed information about '+id+' ticker at '+data['Meta Data']['3. Last Refreshed']+':\n'
        for r1 in (data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']]):
            res = res + r1+' '+ data['Time Series (1min)'][data['Meta Data']['3. Last Refreshed']][r1]+'\n'
        bot.send_message(message.from_user.id,res)
    except:
        print(data)
        bot.send_message(message.from_user.id, 'incorrect ticker. Try again')
        message.text = '/get_price'
        bot.register_next_step_handler(message, start(message))



bot.polling(none_stop=True, interval=0)


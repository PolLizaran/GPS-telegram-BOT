
from telegram import *
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import igo
import os #new library

#import ig

#t.me/DrivingToBot


#start: conversa
#help: ajuda sobre commandes disponibles
#author: displays name of authors
#go desti:
#where:
#pos


#DIR QUE COMANDES NO EXISTEIXEN, WRONG INPUT

def trial(update, context):
    word = update.message.text
    try:
        dispatcher.add_handler(CommandHandler('word', word))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=
        "COMMAND NOT FOUND! 🤯 , try another one or look at '/help' to see what commands are available.")


def start(update, context):

    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! Where do you want to go today? 🔍🧭🚘" + "\n \n" +
    "Use '\go DESTINY' to find the optimal path")


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "__Functionalities__:" + "\n \n" +
    " 🟨️  /start: Enables the user to start a conversation with the bot" + "\n \n" +
    " 🟨️  /author: Displays the owners of the project" + "\n \n" +
    " 🟨️  /go: Displays a map containing the best path to go from the location of the user to the wished destiny" + "\n \n" +
    " 🟨️  /where: Shows the current position of the user", parse_mode= ParseMode.MARKDOWN_V2)

def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Created by: Andrea Bellmunt Fuentes & Pol Lizaran Campano")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('Authors.png', 'rb'))

def where(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "To use your location as the depart point, please click on 📎 and share your location")

    try:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        fitxer = "map_bcn.png"
        mapa = igo.StaticMap(500, 500)
        mapa.add_marker(igo.CircleMarker((lon, lat), 'blue', 10))
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fitxer, 'rb'))
        os.remove(fitxer)
    except Exception as e:
        print(e)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='💣')

#def __pos(update, context):



TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
word = updater.message.text

dispatcher.add_handler(CommandHandler('word', trial))
#dispatcher.add_handler(CommandHandler('start', start)) #relació de funció start amb /start
#dispatcher.add_handler(CommandHandler('help', help))
#dispatcher.add_handler(CommandHandler('author', author))
#dispatcher.add_handler(MessageHandler(Filters.location, where))


updater.start_polling() #posem en matxa al bot

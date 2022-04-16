from telegram import *
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from igo import *
import os #new library

#import ig

#t.me/DrivingToBot


#start: conversa
#help: ajuda sobre commandes disponibles
#author: displays name of authors
#go desti:
#where:
#pos
#d

#DIR QUE COMANDES NO EXISTEIXEN, WRONG INPUT
#s'ha de canviar el logo

#on està el text que surt a l'inici quan inicialitzem?


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! Where do you feel like going today? 🔍🧭🚘" + "\n \n" +
    "Use the command '/go DESTINATION' to find the optimal path to your desired destination.")

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "__Functionalities__:" + "\n \n" +
    " 🟨️  /start: Enables you to start a conversation with the bot" + "\n \n" + #conversation with the bot: emoji of someone talking
    " 🟨️  /author: Displays the owners of the project" + "\n \n" + #two people
    " 🟨️  /go: Displays a map containing the best path you can follow to go from your location to the wanted destination" + "\n \n" + #map
    " 🟨️  /where: Shows your current location", parse_mode= ParseMode.MARKDOWN_V2) #xinxeta location

def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Created by Andrea Bellmunt Fuentes & Pol Lizaran Campano, current students of the Data Science and Engineering degree in the UPC. ")
    #desenvolupar text sobre nosaltres i posar emoji al principi mateix que el que hem posat a help
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('Authors.png', 'rb'))

def where(update, context): #what to do we do if you already have a current location?
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "To use your location as the depart point, please click on 📎 and share your location")
    try:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        context.user_data['lloc'] = [lat, lon] #they need to be switched
        fitxer = "map_bcn.png"
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), 'blue', 10))
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
            text='Something went wrong! Try to send your location another time.')

def go(update, context):
    destination = update.message.text[4:]
    initial_steps(update, context, destination)

    #context.bot.send_message(chat_id=update.effective_chat.id, text=
    #"You have obtained the shortest path. Wait a few seconds for the map.")
    """file = "path_bcn.png"
    map = StaticMap(SIZE)
    image = map.render()
    image.save(file)
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open(file, 'rb'))
    os.remove(file)"""

def initial_steps(update, context, destination):

    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
    else:
        graph = load_graph(GRAPH_FILENAME)

    if not exists_highways(HIGHWAYS_FILENAME):
        highways = download_highways(HIGHWAYS_URL, graph)
        context.user_data['high'] = highways
        save_highways(highways, HIGHWAYS_FILENAME)
    else:
        highways = load_highways(HIGHWAYS_FILENAME)

    congestions = download_congestions(CONGESTIONS_URL)
    context.user_data['congest'] = congestions

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "ja em carregat")

    igraph = build_igraph(graph, highways, congestions)

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "igraph fet")

    #get 'intelligent path' between two addresses and plot it into a PNG image
    [lat, lon] = context.user_data['lloc']

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    destination)
    ipath = get_shortest_path_with_ispeeds(igraph, [lon, lat], destination)

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "path done")

    plot_path(igraph, ipath, SIZE, "hola.png")

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "FINISHED ;)")

    context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open("hola.png", 'rb'))

    return graph

#def __pos(update, context):




TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start)) #relació de funció start amb /start
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(MessageHandler(Filters.location, where))
dispatcher.add_handler(CommandHandler('go', go))
#dispatcher.add_handler(MessageHandler(Filters.location, pos))


updater.start_polling() #posem en matxa al bot

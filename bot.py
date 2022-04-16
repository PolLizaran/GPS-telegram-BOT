from telegram import *
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from igo import *
#libraries inherent from Python
import os 
import datetime

#import ig

#t.me/DrivingToBot


#we store all the objects in our dictionary
program_data = {}

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Downloading contents...")
    do_basics(update, context) #download the graph, highways, and congestions for the very first time
    context.bot.send_message(chat_id=update.effective_chat.id, text="Contents downloaded propperly 🙂" + "\n")
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
    try:
        program_data[update.effective_chat.id] #means a location already exists
        show_user_location(update, context)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=
        "No current location has been found. Please click on 📎 and share your location, to use it as the depart point.")


def go(update, context):
    destination = update.message.text[4:]
    compute_route(update, context, destination)


#falseja la posició d'inici
def pos(update, context):
    punt_departida = update.message.text[5:] #avoids copying \pos 
    try:
        program_data[update.effective_chat.id] = ox.geocode(punt_departida)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, 
        text= "Any location was found with the given position. Please change the format or try a new one.")



def do_basics(update, context):
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
    else:
        graph = load_graph(GRAPH_FILENAME)
    program_data['graph_downl'] = graph
    
    if not exists_highways(HIGHWAYS_FILENAME):
        highways = download_highways(HIGHWAYS_URL, graph)
        save_highways(highways, HIGHWAYS_FILENAME)
    else:
        highways = load_highways(HIGHWAYS_FILENAME)
    program_data['highways_downl'] = highways
    
    program_data['congestions_downl'] = download_congestions(CONGESTIONS_URL)
    program_data['last_load_cong'] = datetime.datetime.utcnow() #we save the time


def recharge_congestions_state(update, context):
    current_time = datetime.datetime.utcnow()
    last_load_time = program_data['last_load_cong']
    if current_time - last_load_time > datetime.timedelta(minutes=5):
        program_data['congestions_downl'] = download_congestions(CONGESTIONS_URL)
        program_data['last_load_cong'] = datetime.datetime.utcnow()
        

def compute_route(update, context, destination):
    context.bot.send_message(chat_id=update.effective_chat.id, text= "Calculating the best route 🔍 ...")
    try:
        recharge_congestions_state(update, context)
        igraph = build_igraph(program_data['graph_downl'], program_data['highways_downl'], program_data['congestions_downl'])
        #get 'intelligent path' between two addresses and plot it into a PNG image
        lat, lon = program_data[update.effective_chat.id]
        ipath = get_shortest_path_with_ispeeds(igraph, [lon, lat], destination)
        name_of_path = "path_" + str(update.effective_chat.id) + ".png"
        plot_path(igraph, ipath, SIZE, name_of_path)
        context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(name_of_path, 'rb'))
        os.remove(name_of_path) #si no se'ns guardaran moltes imatges
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, 
            text= "Unfortunately, I have not found a path from your location to your wanted destination." +"\n" +
            "Please, try a different place.")


def save_location(update, context):
    lat, lon = update.message.location.latitude, update.message.location.longitude
    program_data[update.effective_chat.id] = [lat, lon] 


def show_user_location(update, context):
    try:
        lat, lon = program_data[update.effective_chat.id]
        context.bot.send_message(chat_id=update.effective_chat.id,
        text='Your current location is:' + '\n' + str(lat) + " , "+ str(lon))
        fitxer = "map_bcn.png"
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), "#EF0994", 10)) #they need to be switched, color purple
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




TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start)) #relació de funció start amb /start
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(MessageHandler(Filters.location, save_location))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('pos', pos))


updater.start_polling() #posem en matxa al bot

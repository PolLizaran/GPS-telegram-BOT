from telegram import *
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from igo import *
# standard libraries from Python
import os
import datetime

# t.me/DrivingToBot

program_data = {}  # create a dictionary to store all the objects: with the ID of the user as a key we save their locations

# AUXILIARY FUNCTIONS #


def do_basics(update, context):
    """An auxiliary function used in the function 'start' that, if it is the first
    time that it is called, downloads the graph of the city and the highways, along
    with the congestions, and if it already has this information, it only downloads
    the congestion and starts keeping track of the time since the file has been
    last downloaded. It also calculates the igraph with this initial congestions """

    try:
        program_data['graph_downl']  # works if it already has the graph
    except:
        if not exists_graph(GRAPH_FILENAME):  # graph is not in memory
            graph = download_graph(PLACE)
            save_graph(graph, GRAPH_FILENAME)
        else:
            graph = load_graph(GRAPH_FILENAME)  # graph is in memory
        program_data['graph_downl'] = graph  # saves for future occasions in dictionary

    try:
        program_data['highways_downl']  # works if it already has the information of highways
    except:
        if not exists_highways(HIGHWAYS_FILENAME):  # highways are not in memory
            highways = download_highways(HIGHWAYS_URL, graph)
            save_highways(highways, HIGHWAYS_FILENAME)
        else:
            highways = load_highways(HIGHWAYS_FILENAME)  # highways in memory
        program_data['highways_downl'] = highways  # saves in dictionary

    program_data['congestions_downl'] = download_congestions(CONGESTIONS_URL)  # saves congestions in dictionary
    program_data['last_load_cong'] = datetime.datetime.utcnow()  # saves starting time
    program_data['igraph'] = build_igraph(program_data['graph_downl'], program_data['highways_downl'], program_data['congestions_downl'])


def show_user_location(update, context):
    """An auxiliary function that plots the current location of the user in a map,
    used with the function 'where'. """

    try:
        lat, lon = program_data[update.effective_chat.id]  # gets current location of user
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='📍 Your current location is:' + '\n' + str(lat) + " , " + str(lon))  # prints coordinates of location
        fitxer = "map_bcn.png"
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), "#EF0994", 10))  # marks the location
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fitxer, 'rb'))
        os.remove(fitxer)
    except Exception as e:  # if there is an error
        print(e)
        context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text='😢 Something went wrong! Try to send your location another time.')


def recharge_congestions_state_and_igraph(update, context):
    """An auxiliary function that checks if it has been more than 5 minutes from
    the last time the congestions have been downloaded and, if it has been,
    downloads them again, and computes the igraph again """

    current_time = datetime.datetime.utcnow()  # gets current time
    try:
        last_load_time = program_data['last_load_cong']
        if current_time - last_load_time > datetime.timedelta(minutes=5):  # difference is more than 5 min
            program_data['congestions_downl'] = download_congestions(CONGESTIONS_URL)
            program_data['last_load_cong'] = datetime.datetime.utcnow()  # saves starting time
            program_data['igraph'] = build_igraph(program_data['graph_downl'], program_data['highways_downl'], program_data['congestions_downl'])
    except:
        pass


def compute_route(update, context, destination):
    """An auxiliary function used when implementing the functionality 'go' that
    computes the fastest path from the current location of the user to the
    destination, which is a parameter,  by using functions from the module igo.py
    and plots a PNG image of the path. If the location is not accessible
    or the name or coordinate is not recognized, it reports an error."""

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="🔄 Finding the fastest path from your location to the destination..." + "\n \n" +
                             "❕ Note that the program might spend a few more seconds to obtain the best result." + "\n \n" +
                             "❔ If you have not updated your location, you can send your current one with '/where'.")
    try:
        recharge_congestions_state_and_igraph(update, context)  # if the congestions file has been updated, download again (checks time) and recompute igraph
        lat, lon = program_data[update.effective_chat.id]  # gets origin from dictionary
        ipath = get_shortest_path_with_ispeeds(program_data['igraph'], [lat, lon], destination)
        name_of_path = "path_" + str(update.effective_chat.id) + ".png"
        if plot_path(program_data['igraph'], ipath, SIZE, name_of_path):  # plot_path returns true: finds a path
            context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=open(name_of_path, 'rb'))
            os.remove(name_of_path)  # to free memory
        else:  # location or destination are not reachable
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="😢 It seems like your current location or wanted destination are closed at the moment.")
    except:  # does not understand the coordinates or name of the destination
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="😢 Unfortunately, I have not found a path from your location to your wanted destination." + "\n \n" +
                                 "❕ It could be that you have forgotten to initialize the bot. To do that, " +
                                 "please, use the function '/start' and try again." + "\n \n" +
                                 "If not, try to write your destination differently or change your current location.")


def save_location(update, context):
    """An auxiliary function used to save or update the current location of the
    user in the dictionary."""

    lat, lon = update.message.location.latitude, update.message.location.longitude  # gets position
    program_data[update.effective_chat.id] = [lat, lon]  # saves to dictionary
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="📍 Your current location has been updated. Now you can find a path to go to another place." + "\n \n" +
                             "🔍 Use '/go <destination>' to do that.")

# MAIN FUNCTIONS #


def start(update, context):
    """Functionality of the bot that allows the program to download the graph of
    Barcelona, along with a graph of all the highways and one with the congestions,
    by using an auxiliary function called "do_basics".It also includes a group of
    messages to interact with the users and indicate them how can they use the bot. """

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="🔄 Downloading all contents...")
    do_basics(update, context)  # download the graph, highways, and congestions for the very first time
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=" 😃 Contents have been downloaded correctly" + "\n")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hello! Where do you feel like going today? 🧭🚘" + "\n \n" +
                             "🔍 Use the command '/where' to send me your location and then use '/go <destination>'" +
                             " to find the optimal path to your desired destination." + "\n \n" +
                             "❓  If you want to know what else can you ask me to do, use '/help'.")


def help(update, context):
    """Command that prints a message with a short description of the other
    functionalities that are available in the bot. """

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="You can use any of the following functionalities:" + "\n \n" +
                             "▶️ '/start': Enables you to start a conversation with me" + "\n \n" +
                             "👩‍💻 '/author': Displays the owners of the project" + "\n \n" +
                             "🗺️ '/go <destination>'': Displays a map containing the best path you can" +
                             "follow to go from your location to the wanted destination" + "\n \n" +
                             "📍 '/where': Shows your current location")


def author(update, context):
    """Functionality that returns information about the authors of the project and
    prints a photo of their faces, which has been saved in a file called 'Authors.png'. """

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=" 💻 Project created by Andrea Bellmunt & Pol Lizaran, current students" +
                             " of the Data Science and Engineering degree in the UPC. ")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('Authors.png', 'rb'))


def where(update, context):
    """Command of the bot that, if it has not been done already, saves the current
    location of the user, which needs to be shared by using a functionality of Telegram,
    in the dictionary. It also prints an image with the marked location on a map,
    by using the auxiliary function "show_user_location". Notice that the location sent
    can't be in live. """

    try:
        # check if there is already an object with this key (ID of user)
        program_data[update.effective_chat.id]
        show_user_location(update, context)  # if it exists, it prints map
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="📍 This is your last updated current location. If you want to change it," +
                                 "please click on 📎 and share your location.")
    except:  # if there is no location saved in the dictionary from the user
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="📍 To use your location as the depart point, please click on 📎 and share your location.")


def go(update, context):
    """Functionality that reads a place, which is the wanted destination of the user,
    and computes the shortest path from the location of the user to the one from the input.
    To do that it uses an auxiliary function ("compute_route"). """

    destination = update.message.text[4:]  # reads the position given after '/go'
    compute_route(update, context, destination)  # computes path and prints map with it (if possible)


def pos(update, context):
    """Secret function that makes it possible to change the current location of
    the user by introducing coordinates or the name of the place, instead of
    sending the location with a map. """

    punt_departida = update.message.text[5:]  # reads place in input
    try:
        # possible to read the position from the input
        program_data[update.effective_chat.id] = ox.geocode(punt_departida)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="📍 Your wanted location has been updated. Now you can find a path to go to another place." + "\n \n" +
                                 "🔍 Use '/go <destination>' to do that.")
    except:
        # error when trying to find a place with that name or coordinates
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="😢 I have not been able to find this location." +
                                 "Please, change your input by using coordinates or by writing the place differently.")


TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# handles the inputs written by the user with the defined functions
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(MessageHandler(Filters.location, save_location))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('pos', pos))


updater.start_polling()  # starts the bot

import csv
import pickle
import urllib
import networkx as nx
import haversine
import sklearn
import osmnx as ox
from staticmap import StaticMap, Line, CircleMarker
import collections

# global variables
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
HIGHWAYS_FILENAME = 'highwaysdownload.graph'
SIZE = 750
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

# part of a main road defined by an ID, the streets names, the coordinates of the path, and the closest nodes of the edge
# by saving the close nodes we'll gain execution speed when computing the route as we won't wave to calculate them every time
Highway = collections.namedtuple('Highway', 'way_id street_name coordinates close_nodes')
# state of congestion in a part of a highway defined by the ID of the road, the current state, and the expected state in 15 min
Congestion = collections.namedtuple('Congestion', 'cong_id daily_time current_cong prox_cong')


def load_graph(g_filename):
    """Gets a file from the memory, that has the name that is passed as a
    parameter and contains the graph of the city, to be able to work with it. """

    with open(g_filename, 'rb') as file:
        graph = pickle.load(file)  # gets it from memory
    return graph


def load_highways(high_filename):
    """Gets the file with the highways from the memory by using the string
    'high_filename'(parameter), which is the name of the file, and returns it. """

    with open(high_filename, 'rb') as namedtuple:
        highways = pickle.load(namedtuple)  # gets it from memory
    return highways


def exists_graph(g_filename):
    """Checks if there is a file that corresponds to the graph by using the
    function 'load_graph', with the filename that is passed as a parameter,
    and returns a boolean value depending on the result. """

    try:
        load_graph(g_filename)  # gets the file called 'g_filename' from the memory
        return True
    except:
        return False


def exists_highways(high_filename):
    """Tries to get a file with the name received as a parameter ('high_filename')
    from the memory, and returns a boolean value depending on if it is there or not. """

    try:
        load_highways(high_filename)  # gets 'high_filename' from the memory
        return True
    except:
        return False


def download_graph(location):
    """Obtains a graph of the roads from the location indicated in
    the parameter and transforms it into a DiGraph, which is returned. """

    graph = ox.graph_from_place(location, network_type='drive', simplify=True)
    graph = ox.utils_graph.get_digraph(graph, weight='length')
    return graph


def download_highways(high_url, graph):
    """Collects the information from a CSV file containing all the highways
    in Barcelona, which is obtained using the link defined as 'HIGHWAYS_URL',
    passed as a parameter with the graph. This data is stored in a
    list of Highway (namedtuple already defined), which is the variable returned.
    By calculating the nearest nodes to each location in here, this will just be
    done once and not every time the ipath is created """

    mult_digraph = nx.MultiDiGraph(graph)  # transforms DiGraph into MultiDiGraph to ensure computing the nearest nodes
    with urllib.request.urlopen(high_url) as response:  # reads data stored in CSV file
        h_lines = [l.decode('utf-8') for l in response.readlines()]
        h_reader = csv.reader(h_lines, delimiter=',', quotechar='"')
        next(h_reader)  # ignore first line with description
        lst_high = []  # array to store the lines of the file (Highway)
        for line in h_reader:  # reading each line of file
            way_id, description, coordinates = line
            tram_coord = coordinates.split(',')  # converts the string to a list of strings to make data treatment easier
            n_coord = len(tram_coord)  # the number of coordinates in each line can be different
            pair_coord, u, v = [], [], []
            for i in range(0, n_coord - 1, 2):
                pair_coord.append([float(tram_coord[i]), float(tram_coord[i + 1])])
                u.append(float(tram_coord[i]))  # creates lat and long in 2 tuples
                v.append(float(tram_coord[i + 1]))
            neighbours = ox.nearest_nodes(mult_digraph, u, v)  # computes the neighbours of a given location
            lst_high.append(Highway(way_id, description, pair_coord, neighbours))  # includes Highway to the list
        return lst_high


def download_congestions(cong_url):
    """Gets the information from a CSV file containing all the congestions
    from the highways, which is obtained using the link defined as 'CONGESTIONS_URL',
    passed as a parameter called 'cong_url'. This data is stored in a
    list of Congestion (namedtuple already defined), which is the variable returned. """

    with urllib.request.urlopen(cong_url) as response:
        c_lines = [l.decode('utf-8') for l in response.readlines()]
        c_reader = csv.reader(c_lines, delimiter='#', quotechar='"')
        next(c_reader)  # ignore first line with description
        lst_cong = []  # array to store the lines of the file
        for line in c_reader:
            cong_id, daily_time, current_cong, prox_cong = line
            lst_cong.append(Congestion(cong_id, daily_time, current_cong, prox_cong))
    return lst_cong


def save_graph(graph, g_filename):
    """Saves a file to the memory which contains the graph (parameter) and is
    stored using the name passed as (g_filename). """

    with open(g_filename, 'wb') as file:
        pickle.dump(graph, file)  # stores in memory


def save_highways(highways, high_filename):
    """Stores a file to the memory containing the information from the highways,
    which is a parameter along with the name of the created file. """

    with open(high_filename, 'wb') as namedtuple:
        pickle.dump(highways, namedtuple)  # stores in memory


def plot_graph(graph):
    """Uses NetworkX library to transform the graph (parameter)
    to a MultiGraph, so that it can be plotted using OSMnx. """

    mult_graph = nx.MultiGraph(graph)
    ox.plot_graph(mult_graph, show=True, save=True, filepath="bcn.png")  # uses the name "bcn.png" to save it


def plot_highways(highways, name, g_size):
    """Creates a graph of size 'g_size', which is a parameter, using StaticMap,
    and prints the highways by using the coordinates from the list created in
    'download_highways' (parameter). It is saved as a PNG image with the 'name'
    from the parameters. """

    high_bcn = StaticMap(g_size, g_size)
    for tram in highways:
        m = []
        for pairs in tram.coordinates:  # goes through the column of Highway.coordinates
            m.append(pairs)  # saves lon and lat
        high_bcn.add_line(Line((m), "#0079FF", 1))  # creates a blue line in the map from one coordinate to another
    image = high_bcn.render()
    image.save(name)


def plot_congestions(highways, congestions, name, g_size):
    """Prints the state of the congestions in a graph by associating a color to
    each type of congestion. It uses the coordinates from the list of highways,
    to plot the lines in different colors (considering the traffic), as well as
    the ID of these streets to realate them with its correspondant congestion. """

    map_cong_bcn = StaticMap(g_size, g_size)
    # 0:no data:light blue, 1:very fluid:green, 2:fluid:light green, 3:dense:yellow, 4:very dense:orange, 5:congested:red, 6:closed:black
    color_list = ["#0079FF", "#0D840E", "#64E965", "#FFFE00", "#40dc32", "#F9821B", 'black']
    v = [0] * 540  # array containing the congestions initialized to 0 and in case there is a congestion that does not exist, it is printed like there is no data
    # this list has a length of 540 as more highways than expected could be added
    for x in congestions:  # x is the congestion of a highway
        v[int(x.cong_id)] = int(x.current_cong)  # change the value for all the congestions in which we have data
    for tram in highways:
        current_id = int(tram.way_id)
        m = []
        for y in tram.coordinates:
            m.append(y)
        # visits the position of the array of congestions, take this value and adds a line with the correspondant color of the 'color_list'
        map_cong_bcn.add_line(Line((m), color_list[v[current_id]], 2))
    image = map_cong_bcn.render()
    image.save(name)


def most_freq_cong(congestions):
    """Computes the most frequent state of congestion, using the list of congestions
    (parameter), every time the igraph needs to be built so that the congestions
    with no data can adopt this value."""

    total_number_congs = [0, 0, 0, 0, 0]  # represents congestions {1, 2, 3, 4, 5}
    for i in range(len(congestions)):  # visit all highways from which we have data
        cong_value = int(congestions[i].current_cong)
        # does not consider the values of 0 (would not change) and 6 (would close more roads limiting the movement in the city)
        if cong_value != 0 and cong_value != 6:
            total_number_congs[cong_value - 1] += 1
    return total_number_congs.index(max(total_number_congs)) + 1  # gets the index of the maximum value of the array


def build_igraph(graph, highways, congestions):
    """Transforms the graph (parameter with highways and congestions) by changing
    the attribute 'travel_time' according to the state of congestion in each edge.
    It is done by multiplying an arbitrary value that depends on the state. For example,
    for very fluid traffic the 'travel_time' does not change, and for closed roads
    it uses a very big number so that the shortest_path does not consider those edges.
    It also uses the function 'most_freq_cong' to change the edges with no congestion
    data. For accessing to the nearest nodes of each coordinate, we go across the list
    of highways. """

    mult_digraph = nx.MultiDiGraph(graph)  # uses a MultiDiGraph to be able to work
    mult_digraph = ox.speed.add_edge_speeds(mult_digraph)  # sets an attribute speed for all nodes
    mult_digraph = ox.speed.add_edge_travel_times(mult_digraph)  # computes the 'travel_time' of all edges taking into account the max_speed and its length
    highways_state = most_freq_cong(congestions)  # obtains most frequent state of congestion
    # no data: {0: h_state}, very fluid: {1: 1},  fluid: {2: 1,5}, dense: {3: 3},  very dense: {1: 5.5},  congested: {5: 9.5}, cut: {6: 100000}
    extra_time = [None, 1, 1.5, 3, 5.5, 9.5, 100000]
    extra_time[0] = extra_time[highways_state]  # changes the position 0 for the value of the position of most_freq_cong
    for i in range(len(highways)):
        n_nodes = len(highways[i].close_nodes)  # we acces to the attribute 'close_nodes' that cointains the nearest nodes
        for j in range(n_nodes - 1):
            try:  # there are nodes that do not have paths between them
                neighbour = highways[i].close_nodes
                route = nx.shortest_path(mult_digraph, neighbour[j], neighbour[j + 1], weight='length')  # tuple containing all the extra nodes between two nodes
                for x in range(len(route) - 1):
                    state = int(congestions[int(highways[i].way_id)].current_cong)  # calculates the current congestion of the highway i
                    mult_digraph[route[x]][route[x + 1]][0]['travel_time'] *= extra_time[state]  # changes 'travel_time' by multiplying for congestion factor
            except:  # if there is no path
                pass  # does nothing
    return mult_digraph


def get_shortest_path_with_ispeeds(igraph, origin, destination):
    """Computes and returns the fastest path from an origin to a destination,
    which are two of the parameters, considering the attribute of 'travel_time'
    in the igraph (parameter). It also uses the function 'shortest_path' of
    NetworkX to do that. The locations can be strings, which would be the
    name of the places, or coordinates. """

    coord_orig = origin
    if type(origin) is str:
        coord_orig = ox.geocode(origin)  # transforms string into coordinates
    if type(destination) is str:
        coord_dest = ox.geocode(destination)  # transforms string into coordinates
    # coordinates are switched as geocode returns the coordinates reversed: needs to be lon lat
    node1 = ox.nearest_nodes(igraph, coord_orig[1], coord_orig[0])
    node2 = ox.nearest_nodes(igraph,  coord_dest[1], coord_dest[0])
    return(nx.shortest_path(igraph, node1, node2, weight='travel_time'))


def plot_path(igraph, ipath, g_size, filename):
    """Prints the path computed by the function 'get_shortest_path_with_ispeeds'
    in a map created by StaticMap. It is saved as a PNG image with the name passed as
    a parameter ('filename'). It is a boolean function as it will help us to report
    an error when executing the bot"""

    map_with_path = StaticMap(g_size, g_size)
    # if origin of the path or destination of the path are in an edge that is closed (state of congestion 6)
    if igraph[ipath[0]][ipath[1]][0]['travel_time'] >= 100000 or igraph[ipath[-2]][ipath[-1]][0]['travel_time'] >= 100000:
        return False
    else:
        map_with_path.add_marker(CircleMarker((igraph.nodes[ipath[0]]['x'], igraph.nodes[ipath[0]]['y']), "#F33648", 8))  # origin in red
        m = []
        for node_place in ipath:
            x = igraph.nodes[node_place]['x']
            y = igraph.nodes[node_place]['y']
            m.append([x, y])
            map_with_path.add_line(Line((m), "#3243BB", 3))  # creates all the lines of the path
        map_with_path.add_marker(CircleMarker((igraph.nodes[ipath[-1]]['x'], igraph.nodes[ipath[-1]]['y']), "#32BB36", 8))  # destination in green
        image = map_with_path.render()
        image.save(filename)
    return True

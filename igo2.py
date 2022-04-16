#start of code
import csv #llegir format
import pickle #dades python -> fitxers
import urllib  #baixar fitxers web
import networkx as nx #manipular grafs
import haversine
import sklearn
import osmnx as ox #obtenir grafs de llocs
from staticmap import StaticMap , Line, CircleMarker
import collections #use namedtuple


#import telegram #interactuar bot
#import pandas as pd

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800 #mida del graf
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

Highway = collections.namedtuple('Highway', 'way_id street_name coordinates') # atributes
Congestion = collections.namedtuple('Congestion', 'cong_id daily_time current_cong prox_cong')


#know how to work with the url
#understand the elements that the osmnx graph contains
#pendent: mirar si canviar parametre funcio a un altre nom equivalent per no confondre unicament amb variable?
def download_highways(HIGHWAYS_URL):
    #this procedure is done to read files form an existing url.
    with urllib.request.urlopen(HIGHWAYS_URL) as response:
        h_lines = [l.decode('utf-8') for l in response.readlines()]
        h_reader = csv.reader(h_lines, delimiter=',', quotechar='"')
        next(h_reader)  # ignore first line with description
        lst_high = [] #vector to store the lines of the file
        for line in h_reader:
            way_id, description, coordinates = line #canviar nom parametres
            lst_high.append(Highway(way_id, description, coordinates))
        return lst_high

def download_congestions(CONGESTIONS_URL):
    """Primer valor: id
    Segon valor (AAAAMMDD) (HHMMSS): dia i hora
    Tercer valor: estat actual: *
    Quart valor: estat previst dintre 15 min: *
    * 0 -> sense dades, 1 -> molt fluid, 2 -> fluid, 3 -> dens, 4 -> molt dens, 5 -> congestió, 6 -> tallat """
    with urllib.request.urlopen(CONGESTIONS_URL) as response:
        c_lines = [l.decode('utf-8') for l in response.readlines()]
        c_reader = csv.reader(c_lines, delimiter='#', quotechar='"')
        next(c_reader)  # ignore first line with description
        lst_cong = [] #vector to store the lines of the file
        for line in c_reader:
            cong_id, daily_time, current_cong, prox_cong = line
            lst_cong.append(Congestion(cong_id, daily_time, current_cong, prox_cong))
    return lst_cong


def exists_graph(GRAPH_FILENAME):
    try:
        load_graph(GRAPH_FILENAME)
        return True
    except:
        return False


def download_graph(location):
    G_bcn = ox.graph_from_place(location, network_type = 'drive', simplify=True)
    Streets_bcn = ox.utils_graph.get_digraph(G_bcn, weight = 'length')
    return Streets_bcn


def save_graph(graph, GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump(graph, file) #carrega a memoria


def load_graph(GRAPH_FILENAME):
    with open(GRAPH_FILENAME, 'rb') as file:
        graph = pickle.load(file) #agafar-lo de la memoria
    return graph



#g = osmnx.graph_from_place('Vic, Catalonia')
#osmnx.plot_graph(g, show=False, save=True, filepath='vic.png')

def convert_to_multgraph(graph):
    return nx.MultiGraph(graph)

def plot_graph(mult_graph):
    ox.plot_graph(mult_graph,  show = True, save = True, filepath = "bcn.png")


#imprimir els camins: crear un graf a través de les dades que tenim i imprimir-lo
def plot_highways(highways, name, g_size):
    high_bcn = StaticMap(g_size, g_size)

    for tram in highways:
        #crear les linies
        #recorrem la row de Highways.coordinates per trobar les coordenades, ens guardem les x i y, i creem linia que les uneixi, això fins que no en tinguem més
        tram_coord = tram.coordinates.split(',')
        n_coord = len(tram_coord)
        m = []
        for j in range(0, n_coord, 2):
            x = float(tram_coord [ j ])
            y = float(tram_coord [ j + 1 ])
            m.append([x, y])
        high_bcn.add_line(Line((m),  "#0079FF" , 1)) #{black, brown, green, purple, yellow, blue, gray, orange, red, white}
    image = high_bcn.render()
    image.save(name)



#imprimir les congestions (amb camins): crear un graf afegint a les arestes el seu pes actual i imprimir-lo
#falta acabar, idea: crear un vector de llistes, recorrer les llistes highways i congestions i anar afeguint els termes per poder tractar-los
def plot_congestions(highways, congestions, name, g_size):
    cong_bcn = StaticMap(g_size, g_size)
    color_list = ["#0079FF", "#0D840E", "#64E965", "#FFFE00", "#40dc32", "#F9821B", 'black'] #en cas que alguna dada no quadri, com que les posicions del vector les hem inicialitzat a 0 ens ho pintarà com si no tinguessim dades
    #{                  light blue,     green          light green       yellow  ,      orange,          red,         black}
    v = [ 0] * 536 #no ens importa el 0
    for x in congestions: #x is the congestion of a tram
        value_cong_id = int(x.cong_id)
        v[value_cong_id] = int(x.current_cong)

    for tram in highways:
        current_id = int(tram.way_id)
        tram_coord = tram.coordinates.split(',')
        n_coord = len(tram_coord)
        m = []
        for j in range(0, n_coord, 2):
            x = float(tram_coord [ j ])
            y = float(tram_coord [ j + 1 ])
            m.append([x, y])
        #s.append(int(congestions[current_id].current_cong))
            cong_bcn.add_line(Line((m), color_list[v[current_id]] , 2))
    image = cong_bcn.render()
    image.save(name)


    """v = [[]*600]
    for tram in highways:
        v[int(tram.way_id)].append(tram)
    return v"""


#change state of congestions in which there is no info
#pendent canviar: hem de fer-ho de la manera que ens diu el Petit
def most_freq_cong(congestions):
    total_number_congs = [0, 0, 0, 0, 0] #represent congestions {1, 2, 3, 4, 5}
    for i in range(len(congestions)): #visit all highways from which we have data
        x = int(congestions[i].current_cong)
        if x != 0 and x != 6:
            total_number_congs[x - 1] += 1
    return total_number_congs.index(max(total_number_congs)) + 1


def build_igraph(graph, highways, congestions):
    mult_graph = convert_to_multgraph(graph)
    mult_digraph = nx.MultiDiGraph(graph)
    mult_digraph = ox.speed.add_edge_speeds(mult_digraph)
    mult_digraph = ox.speed.add_edge_travel_times(mult_digraph)


    mult_graph = ox.speed.add_edge_speeds(mult_graph)
    mult_graph = ox.speed.add_edge_travel_times(mult_graph)

    for tram in highways:
        tram_coord = tram.coordinates.split(',')
        n_coord = len(tram_coord)
        u = []
        v = []
        for d in range(0, n_coord - 1 , 2):
            u.append(float(tram_coord[d])) #creem lat i long en 2 tuples
            v.append(float(tram_coord[d + 1]))
        nodes = ox.nearest_nodes(mult_digraph, u, v)
        for k in range(len(nodes) - 1):
            try:

                route = nx.shortest_path(mult_digraph, nodes[k], nodes[k + 1], weight='length')

                for z in range(len(route) - 1):
                    print(route[z], ' ', z)


                    #print(mult_digraph.edges[route[z]][route[z + 1]]['travel_time'])
                    #print(int(sum(ox.utils_graph.get_edge_attributes(mult_digraph, route, 'length'))))

            except:
                """for j in range(len(nodes) - 1):
                #mult_graph[nodes[j]][nodes[j+1]][0]['maxspeed']
                print(ox.travel_time(mult_graph))"""



            #print(graph.edges[nodes[j], nodes[j + 1]]["maxspeed"])

        #u_len = len(u)
        #for j in range(0, n_coord - 1 , 2):
            #print(nx.get_edge_attributes(mult_graph, [u[ j ], u[j + 1], 0], "maxspeed"))"""
        #mult_graph.add_edge(tram_coord[0], tram_coord[1],  cong = 2)


    #crear un graf amb speed, length,
    #ox.graph_to_gdfs(graph, nodes = False, edges = tRUE)
    #print(edges.columns, edges.crs)
#def get_shortest_path_with_ispeeds(igraph, origin, destination):

#def plot_path(igraph, ipath, SIZE):

def test():
    # load/download graph (using cache) and plot it on the screen
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
    else:
        graph = load_graph(GRAPH_FILENAME)
    plot_graph(graph)

    # download highways and plot them into a PNG image
    highways = download_highways(HIGHWAYS_URL)
    plot_highways(highways, 'highways.png', SIZE)

    # download congestions and plot them into a PNG image
    congestions = download_congestions(CONGESTIONS_URL)
    plot_congestions(highways, congestions, 'congestions.png', SIZE)

    # get the 'intelligent graph' version of a graph taking into account the congestions of the highways
    igraph = build_igraph(graph, highways, congestions)

    # get 'intelligent path' between two addresses and plot it into a PNG image
    ipath = get_shortest_path_with_ispeeds(igraph, "Campus Nord", "Sagrada Família")
    plot_path(igraph, ipath, SIZE)

def main():
    highways = download_highways(HIGHWAYS_URL)
    congestions = download_congestions(CONGESTIONS_URL)

    #plot_congestions(highways, congestions, 'congestions_bef.png', SIZE)
    graph = load_graph(GRAPH_FILENAME)
    #graph = download_graph(PLACE)
    mult_graph = convert_to_multgraph(graph)
    #congestions = propagate_congestions(congestions)
    #plot_congestions(highways, congestions, 'congestions_lat.png', SIZE)
    #for x in congestions:
    #    print(x.current_cong)
    build_igraph(graph, highways, congestions)
    """plot_graph(graph)
    highways = download_highways(HIGHWAYS_URL)
    plot_highways(highways, 'highways.png', SIZE)

    print(exists_graph(GRAPH_FILENAME)
    for i in range (len(highways)):
        print(highways[i].way_id, highways[i].street_name, highways[i].coordinates)
    congestions = download_congestions(CONGESTIONS_URL)
    for j in range (len(congestions)):
        print(congestions[j].cong_id, congestions[j].daily_time, congestions[j].current_cong, congestions[j].prox_cong)"""
main()

#COLOR WEB: https://colordesigner.io/gradient-generator


   # G_bcn = ox.graph_from_place(PLACE, network_type='drive')
    #ox.plot_graph(G_bcn)

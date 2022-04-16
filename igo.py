
import csv
import pickle
import urllib
import networkx as nx
import haversine
import sklearn
import osmnx as ox
from staticmap import StaticMap , Line, CircleMarker
import collections


PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona4.graph'
HIGHWAYS_FILENAME = 'highwaysdescarrega.graph'
SIZE = 900
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

#part of a main road defined by an ID, the streets names and the coordinates of the path
Highway = collections.namedtuple('Highway', 'way_id street_name coordinates close_nodes')
#state of congestion in a part of a main street defined by the ID of the road, the current state and the expected state in 15 min
Congestion = collections.namedtuple('Congestion', 'cong_id daily_time current_cong prox_cong')

#A sobre ens guardem ena llista de nodes
def download_highways(highways_url, graph):
    """Collects the information from a CSV file containing all the highways
    in Barcelona, which is obtained using the link defined as 'HIGHWAYS_URL',
    passed as a parameter. This data is stored in a list of Highways (namedtuple
    already defined), which is the variable returned."""
    #this procedure is done to read files form an existing url.
    mult_digraph = nx.MultiDiGraph(graph)
    with urllib.request.urlopen(highways_url) as response:
        h_lines = [l.decode('utf-8') for l in response.readlines()]
        h_reader = csv.reader(h_lines, delimiter=',', quotechar='"')
        next(h_reader)  # ignore first line with description
        lst_high = [] #vector to store the lines of the file
        for line in h_reader:
            way_id, description, coordinates = line #canviar nom parametres
            tram_coord = coordinates.split(',') #ens guardem les coordenades en parelles, molt mes facil
            n_coord = len(tram_coord)
            pair_coord = []
            u = []
            v = []
            for i in range(0, n_coord - 1 , 2):
                pair_coord.append([float(tram_coord[i]), float(tram_coord[i + 1])])
                u.append(float(tram_coord[i]))#creem lat i long en 2 tuples
                v.append(float(tram_coord[i + 1]))
            neighbours = ox.nearest_nodes(mult_digraph, u, v)#we compute the neighbours here to gain execution speed
            lst_high.append(Highway(way_id, description, pair_coord, neighbours))
        return lst_high

def download_congestions(CONGESTIONS_URL):
    """Primer valor: id
    Segon valor (AAAAMMDD) (HHMMSS): dia i hora
    Tercer valor: estat actual: *
    Quart valor: estat previst dintre 15 min: *
    * 0 -> sense dades,1 -> molt fluid, 2 -> fluid, 3 -> dens, 4 -> molt dens, 5 -> congestió, 6 -> tallat """
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





"""AUXILIAR FUNCTIONS"""
def exists_highways(HIGHWAYS_FILENAME):
    try:
        load_highways(HIGHWAYS_FILENAME)
        return True
    except:
        return False


def save_highways(highways, HIGHWAYS_FILENAME):
    with open(HIGHWAYS_FILENAME, 'wb') as namedtuple:
        pickle.dump(highways, namedtuple) #carrega a memoria


def load_highways(HIGHWAYS_FILENAME):
    with open(HIGHWAYS_FILENAME, 'rb') as namedtuple:
        highways = pickle.load(namedtuple) #agafar-lo de la memoria
    return highways


#g = osmnx.graph_from_place('Vic, Catalonia')
#osmnx.plot_graph(g, show=False, save=True, filepath='vic.png')

def convert_to_multgraph(graph):
    return nx.MultiGraph(graph)

"""END AUXILIAR FUNCTIONS"""





def plot_graph(graph):
    mult_graph = convert_to_multgraph(graph)
    ox.plot_graph(mult_graph,  show = True, save = True, filepath = "bcn.png")


#imprimir els camins: crear un graf a través de les dades que tenim i imprimir-lo
def plot_highways(highways, name, g_size):
    high_bcn = StaticMap(g_size, g_size)
    for tram in highways:
        #crear les linies
        #recorrem la row de Highways.coordinates per trobar les coordenades, ens guardem les x i y, i creem linia que les uneixi, això fins que no en tinguem més
        m = []
        for pairs in tram.coordinates:
            m.append(pairs)
        high_bcn.add_line(Line((m),  "#0079FF" , 1)) #{black, brown, green, purple, yellow, blue, gray, orange, red, white}
    image = high_bcn.render()
    image.save(name)


#imprimir les congestions (amb camins): crear un graf afegint a les arestes el seu pes actual i imprimir-lo
#falta acabar, idea: crear un vector de llistes, recorrer les llistes highways i congestions i anar afeguint els termes per poder tractar-los
def plot_congestions(highways, congestions, name, g_size):
    map_cong_bcn = StaticMap(g_size, g_size)
    color_list = ["#0079FF", "#0D840E", "#64E965", "#FFFE00", "#40dc32", "#F9821B", 'black'] #en cas que alguna dada no quadri, com que les posicions del vector les hem inicialitzat a 0 ens ho pintarà com si no tinguessim dades
    #{                  light blue,     green          light green       yellow  ,      orange,          red,         black}
    v = [0] * 536 #no ens importa el 0
    for x in congestions: #x is the congestion of a tram
        v[int(x.cong_id)] = int(x.current_cong) #posem un valor a cada congestion de les quals teniem dades
    for tram in highways:
        current_id = int(tram.way_id)
        m = []
        for y in tram.coordinates:
            m.append(y)
        map_cong_bcn.add_line(Line((m), color_list[v[current_id]] , 2)) #visitem posicio vector de colors i afegim linia amb aquell color
    image = map_cong_bcn.render()
    image.save(name)


"""AUXILIAR FUNCTION"""
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
    #dubte sobre si hem de treballar directament sobre el itime i o afegir congestions al graf i dps calcular el itime

    #sinó no podem treballar bé
    mult_digraph = nx.MultiDiGraph(graph)
    mult_digraph = ox.speed.add_edge_speeds(mult_digraph)
    mult_digraph = ox.speed.add_edge_travel_times(mult_digraph)

    highways_state = most_freq_cong(congestions) #obtenim estat actual més freq
    extra_time = [None, 1, 1.5, 3, 5.5, 9.5, 100000]
    first_position = extra_time[highways_state]
    extra_time[0] = first_position
    #nodata: {0: h_state},  very fluid: {1: 1},  fluid: {2: 1,5},  dense: {3: 3},  very dense: {1: 5.5},  congestioned: {5: 9.5}, cut: {6: 100000}
    for i in range(len(highways)):
        n_nodes = len(highways[i].close_nodes) #we acces to the atribute close_nodes that cointains the nearest nodes
        for j in range(n_nodes - 1):
            try: #hi ha nodes que no tenen camí entre ells
                k = highways[i].close_nodes #we have to change the name to the variable
                route = nx.shortest_path(mult_digraph, k[j], k[j + 1], weight='length')#we look for the most near nodes, returns a tuple of the path we have to follow
                for x in range(len(route) - 1):
                    state = int(congestions[int(highways[i].way_id)].current_cong)
                    mult_digraph[route[x]][route[x + 1]][0]['travel_time'] *= extra_time[state] #multipliquem per un factor de congestion
            except:
                pass #does nothing
    return mult_digraph


def get_shortest_path_with_ispeeds(igraph, origin, destination):
    #origin = "UPC Campus Nord, Carrer de John Maynard Keynes, Pedralbes, les Corts, Barcelona, Barcelonès, Barcelona, Catalunya, 08001, Espanya"
    #destination = "Sagrada Família, 401, Carrer de Mallorca, la Sagrada Família, Eixample, Barcelona, Barcelonès, Barcelona, Catalunya, 08001, Espanya"
    coord_orig = origin
    if type(origin) is str:
        #print(origin)
        coord_orig = ox.geocode(origin)
    else:
        coord_orig[0], coord_orig[1] = coord_orig[1], coord_orig[0]
    if type(destination) is str:
        #print(destination)
        coord_dest = ox.geocode(destination)
    else:
        coord_dest[0], coord_dest[1] = coord_dest[1], coord_dest[0]
    node1 = ox.nearest_nodes(igraph, coord_orig[1], coord_orig[0]) #coordinates switched as geocode returns the coordinates reversed
    node2 = ox.nearest_nodes(igraph,  coord_dest[1], coord_dest[0])
    return(nx.shortest_path(igraph, node1, node2, weight='travel_time'))
    #implementació feta amb nodes random, hem d'aconseguir que donada una posició passar-ho a coordenades i calcular el nearest node des d'allà, la funció geocode ens ho permet


#instead of calling the function ox.plot_graph_route, what we've done now is to
def plot_path(igraph, ipath, SIZE, file_name):
    map_with_path = StaticMap(SIZE, SIZE)
    map_with_path.add_marker(CircleMarker((igraph.nodes[ipath[0]]['x'], igraph.nodes[ipath[0]]['y']), "#F33648", 8)) #red
    m = []
    for node_place in ipath:
        x = igraph.nodes[node_place]['x']
        y = igraph.nodes[node_place]['y']
        m.append([x, y])
        map_with_path.add_line(Line((m), "#3243BB" , 3)) 
    map_with_path.add_marker(CircleMarker((igraph.nodes[ipath[-1]]['x'], igraph.nodes[ipath[-1]]['y']), "#32BB36", 8)) #green
    image = map_with_path.render()
    image.save(file_name)
    
    #fig, ax  = ox.plot_graph_route(igraph, ipath,  route_color='b', route_linewidth=4)


def test():
    # load/download graph (using cache) and plot it on the screen
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
    else:
        graph = load_graph(GRAPH_FILENAME)
    #plot_graph(graph)

    # download highways and plot them into a PNG image
    if not exists_highways(HIGHWAYS_FILENAME):
        highways = download_highways(HIGHWAYS_URL, graph)
        save_highways(highways, HIGHWAYS_FILENAME)
    else:
        highways = load_highways(HIGHWAYS_FILENAME)

    plot_highways(highways, 'highways_prova.png', SIZE)

    # download congestions and plot them into a PNG image
    congestions = download_congestions(CONGESTIONS_URL)
    plot_congestions(highways, congestions, 'congestions.png', SIZE)

    # get the 'intelligent graph' version of a graph taking into account the congestions of the highways
    print("ja em carregat")

    igraph = build_igraph(graph, highways, congestions)

    print("igraph fet")

    #get 'intelligent path' between two addresses and plot it into a PNG image
    ipath = get_shortest_path_with_ispeeds(igraph, "Campus Nord, Barcelona", "Sagrada Família" )
    plot_path(igraph, ipath, SIZE, "afav.png")

#def main():
    #test()
    #highways = download_highways(HIGHWAYS_URL)
    #for i in range (len(highways)):
    #    print(highways[i].way_id, highways[i].street_name, highways[i].coordinates)

    #congestions = download_congestions(CONGESTIONS_URL)
    #for j in range (len(congestions)):
    #    print(congestions[j].cong_id, congestions[j].daily_time, congestions[j].current_cong, congestions[j].prox_cong)

    #print(exists_graph(GRAPH_FILENAME))

    #if not exists_graph(GRAPH_FILENAME):
    #    graph = download_graph(PLACE)
    #    save_graph(graph, GRAPH_FILENAME)
    #else:
    #graph = load_graph(GRAPH_FILENAME)

    #plot_graph(graph)

    #plot_highways(highways, 'highways.png', SIZE)

    #plot_congestions(highways, congestions, 'congestions.png', SIZE)

    #print(most_freq_cong(congestions))

    #igraph = build_igraph(graph, highways, congestions)

    #ipath = get_shortest_path_with_ispeeds(igraph, "Carrer de Balmes, Barcelona", "Avinguda de Sants, Barcelona")

    #plot_path(igraph, ipath, SIZE, file_name)


    #graph = download_graph(PLACE)
    #save_graph(graph, GRAPH_FILENAME)
    #plot_congestions(highways, congestions, 'congestions_bef.png', SIZE)
    #graph = load_graph(GRAPH_FILENAME)
    #graph = download_graph(PLACE)
    #mult_graph = convert_to_multgraph(graph)
    #congestions = propagate_congestions(congestions)
    #plot_congestions(highways, congestions, 'congestions_lat.png', SIZE)
    #for x in congestions:
    #    print(x.current_cong)
    #build_igraph3(graph, highways, congestions)

#main()

#COLOR WEB: https://colordesigner.io/gradient-generator


   # G_bcn = ox.graph_from_place(PLACE, network_type='drive')
    #ox.plot_graph(G_bcn)

 """for k in range(len(nodes) - 1):
            try:
                for (nodes[k], nodes[k+1], tt) in mult_digraph.edges(data='travel_time', default=999999):
                        print(tt)
            except:"""


def build_igraph2(graph, highways, congestions):
    graph = ox.add_edge_speeds(graph)
    #graph = ox.add_edge_travel_times(graph)

    for node1, info1 in graph.nodes.items():
        print(node1, info1)
    # for each adjacent node and its information...
        for node2, edge in graph.adj[node1].items():
            print('    ', node2, ' ', "hola")
            print('        ', edge)



        """for j in range(len(nodes) - 1):
                #mult_graph[nodes[j]][nodes[j+1]][0]['maxspeed']
                print(ox.travel_time(mult_graph))"""


                    #route = nx.shortest_path(mult_digraph, nodes[k], nodes[k + 1], weight='length')

                    #for z in range(len(route) - 1):
                    #print(route[z], ' ', z)
                    #print(mult_digraph.edges[route[z]][route[z + 1]]['travel_time'])
                    #print(int(sum(ox.utils_graph.get_edge_attributes(mult_digraph, route, 'length'))))

            #print(graph.edges[nodes[j], nodes[j + 1]]["maxspeed"])

        #u_len = len(u)
        #for j in range(0, n_coord - 1 , 2):
            #print(nx.get_edge_attributes(mult_graph, [u[ j ], u[j + 1], 0], "maxspeed"))"""
        #mult_graph.add_edge(tram_coord[0], tram_coord[1],  cong = 2)


    #crear un graf amb speed, length,
    #ox.graph_to_gdfs(graph, nodes = False, edges = tRUE)
    #print(edges.columns, edges.crs)











def build_igraph3(graph, highways, congestions):

    mult_digraph = nx.MultiDiGraph(graph)
    mult_digraph = ox.speed.add_edge_speeds(mult_digraph)
    mult_digraph = ox.speed.add_edge_travel_times(mult_digraph)

#canviar definició de highways per afegir-los com a tupla de parelles
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
                print(mult_digraph[nodes[k]][nodes[k+1]][0]['travel_time'])
            except:
                print("Error")

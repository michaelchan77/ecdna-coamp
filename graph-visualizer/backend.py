from flask import Flask, jsonify, request, g
from flask_cors import CORS
from neo4j import GraphDatabase

import json

app = Flask(__name__)

# Only allow requests from frontend domain
# CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5500"}})
CORS(app)

def get_driver():
    # Connect to Neo4j instance
    if 'neo4j_driver' not in g:
        uri = "bolt://localhost:7687"
        g.neo4j_driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
    return g.neo4j_driver

def fetch_subgraph(driver, name, min_weight, min_samples, oncogenes, all_edges):
    print("From fetch_subgraph: ")
    print(name)
    print(min_weight)
    print(min_samples)
    print(oncogenes)
    print(all_edges)
    print()
    if all_edges:
        if oncogenes:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and r.lenunion >= {ms}]-(m WHERE m.oncogene = "True")
            WHERE n.name = $name
            OPTIONAL MATCH (m)-[r2 WHERE r2.weight >= {mw} and r2.lenunion >= {ms}]-(o WHERE o.oncogene = "True")
            MATCH (o WHERE o.oncogene = "True")-[r3 WHERE r3.weight >= {mw} and r3.lenunion >= {ms}]-(n)
            RETURN n, r, m, r2, o
            LIMIT 50
            """.format(mw = min_weight, ms = min_samples)
        else:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and r.lenunion >= {ms}]-(m)
            WHERE n.name = $name
            OPTIONAL MATCH (m)-[r2 WHERE r2.weight >= {mw} and r2.lenunion >= {ms}]-(o)
            MATCH (o)-[r3 WHERE r3.weight >= {mw} and r3.lenunion >= {ms}]-(n)
            RETURN n, r, m, r2, o
            LIMIT 50
            """.format(mw = min_weight, ms = min_samples)
    else:
        if oncogenes:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and r.lenunion >= {ms}]-(m WHERE m.oncogene = "True")
            WHERE n.name = $name
            RETURN n, r, m
            LIMIT 50
            """.format(mw = min_weight, ms = min_samples)
        else:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and r.lenunion >= {ms}]-(m)
            WHERE n.name = $name
            RETURN n, r, m
            LIMIT 50
            """.format(mw = min_weight, ms = min_samples)
    print(query)
    result = driver.run(query, name=name)
    nodes = {}
    edges = {}
    print("DISPLAY RECORDS")
    print()
    for record in result:
        # ----------------------------------------------------------------------
        print(record)
        # source
        nodes.setdefault(record['n']['name'], 
                         {'data': {'id': record['n']['id'],
                                   'name': record['n']['name'],
                                   'oncogene': record['n']['oncogene'],
                                   'samples': record['n']['samples']}})
        # target
        nodes.setdefault(record['m']['name'], 
                         {'data': {'id': record['m']['id'],
                                   'name': record['m']['name'],
                                   'oncogene': record['m']['oncogene'],
                                   'samples': record['m']['samples']}})
        # edge
        edges.setdefault(record['n']['name'] + ' -- ' + record['m']['name'], 
                         {'data': {'source': record['n']['id'],
                                   'target': record['m']['id'],
                                   'weight': record['r']['weight'],
                                   'leninter': record['r']['leninter'],
                                   'inter': record['r']['inter'],
                                   'lenunion': record['r']['lenunion'],
                                   'union': record['r']['union'],
                                   'name': record['n']['name'] + ' -- ' + record['m']['name'],
                                   'interaction': 'interacts with'
                                   }})
        # neighbor nodes/edges
        if all_edges and record.get('r2') and record.get('o'):
            nodes.setdefault(record['o']['name'], 
                             {'data': {'id': record['o']['id'],
                                       'name': record['o']['name'],
                                       'oncogene': record['o']['oncogene'],
                                       'samples': record['o']['samples']}})
            edges.setdefault(record['m']['name'] + ' -- ' + record['o']['name'], 
                             {'data': {'source': record['m']['id'], 
                                       'target': record['o']['id'],
                                       'weight': record['r2']['weight'],
                                       'leninter': record['r2']['leninter'],
                                       'inter': record['r2']['inter'],
                                       'lenunion': record['r2']['lenunion'],
                                       'union': record['r2']['union'],
                                       'name': record['m']['name'] + ' -- ' + record['o']['name'],
                                       'interaction': 'interacts with'
                                       }})
        # ----------------------------------------------------------------------
        print()
        print("CURRENT:")
        print(nodes)
        print(edges)
        print()
    return list(nodes.values()), list(edges.values())

@app.route('/getNodeData', methods=['GET'])
def get_node_data():
    driver = get_driver()
    node_id = request.args.get('name')
    min_weight = request.args.get('min_weight')
    min_samples = request.args.get('min_samples')
    oncogenes = request.args.get('oncogenes', 'false').lower() == 'true'
    all_edges = request.args.get('all_edges', 'false').lower() == 'true'

    # Create a session and run fetch_subgraph
    with driver.session() as session:
        nodes, edges = session.execute_read(fetch_subgraph, node_id, min_weight, min_samples, oncogenes, all_edges)
        print()
        print("NODES:")
        print(nodes)
        print("LENGTH NODES", len(nodes))
        print()
        print("EDGES:")
        print(edges)
        print("LENGTH EDGES", len(edges))
        print()
        if nodes:
            return jsonify({
                'nodes': nodes,
                'edges': edges
            })
        else:
            return jsonify({"error": "Node not found"}), 404
        
# Ensure proper resource cleanup
@app.teardown_appcontext
def close_driver(exception=None):
    driver = g.pop('neo4j_driver', None)
    if driver is not None:
        try:
            driver.close()
        except Exception as e:
            print(f"Error closing driver: {e}")

def test_fetch_subgraph():
    driver = get_driver()
    test_node_name = "CASC15"
    # Create a session and run fetch_subgraph
    with driver.session() as session:
        nodes, edges = session.execute_read(fetch_subgraph, test_node_name)
        # Prepare the output dictionary
        output = {
            'nodes': nodes,
            'edges': edges
        }
        # Write the output to a file
        with open('subgraph_output.json', 'w') as outfile:
            json.dump(output, outfile, indent=4)

if __name__ == '__main__':
    app.run(debug=True)
    # # To see json output for test node, uncomment this and comment 'app.run'
    # with app.app_context():  # Create an application context
    #     test_fetch_subgraph()  # Call this to test fetch_subgraph
    

# # ChatGPT example load function to support dynamic user upload of datasets into Neo4j on site
# # -------

# from ../graph-constructor/src/graph import Graph

# @app.route('/loadGraph', methods=['POST'])
# def load_graph():
#     # in front end: project selector ui, function to iterate through json files 
#     # of selected projects and pass along all runs (?)
#     # to this function

#     driver = get_driver()

#     # extract relevant info from frontend request
#     project_info_as_jsons = request.json()

#     # construct graph
#     graph = Graph(project_info_as_jsons) # currently takes in aggregated results dataframe, so will need to rework CreateNodes()
#     nodes = graph.Nodes()
#     edges = graph.Edges()

#     if not nodes or not edges:
#         return jsonify({"error": "Nodes and edges data are required"}), 400

#     # drop existing graph (change to drop if required)
#     with driver.session() as session:
#         session.run("MATCH (n) DETACH DELETE n")
    
#     # load new graph
#     with driver.session() as session:
#         # add nodes (update query to reflect neo4j.txt)
#         session.run(
#             """
#             UNWIND $nodes AS node
#             CREATE (n:Node {id: node.id, name: node.name, oncogene: node.oncogene, samples: node.samples})
#             """,
#             nodes=nodes
#         )
#         # add edges (update query to reflect neo4j.txt)
#         session.run(
#             """
#             UNWIND $edges AS edge
#             MATCH (source:Node {id: edge.source}), (target:Node {id: edge.target})
#             CREATE (source)-[:CONNECTED {weight: edge.weight, inter: edge.inter, union: edge.union}]->(target)
#             """,
#             edges=edges
#         )
#     return jsonify({"message": "Graph loaded successfully"}), 200
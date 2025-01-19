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
            MATCH (n)-[r WHERE r.weight >= {mw} and SIZE(r.union) >= {ms}]-(m WHERE m.oncogene = "True")
            WHERE n.label = $name
            OPTIONAL MATCH (m)-[r2 WHERE r2.weight >= {mw} and SIZE(r2.union) >= {ms}]-(o WHERE o.oncogene = "True")
            MATCH (o WHERE o.oncogene = "True")-[r3 WHERE r3.weight >= {mw} and SIZE(r3.union) >= {ms}]-(n)
            RETURN n, r, m, r2, o
            """.format(mw = min_weight, ms = min_samples)
        else:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and SIZE(r.union) >= {ms}]-(m)
            WHERE n.label = $name
            OPTIONAL MATCH (m)-[r2 WHERE r2.weight >= {mw} and SIZE(r2.nunion) >= {ms}]-(o)
            MATCH (o)-[r3 WHERE r3.weight >= {mw} and SIZE(r3.union) >= {ms}]-(n)
            RETURN n, r, m, r2, o
            """.format(mw = min_weight, ms = min_samples)
    else:
        if oncogenes:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and SIZE(r.union) >= {ms}]-(m WHERE m.oncogene = "True")
            WHERE n.label = $name
            RETURN n, r, m
            """.format(mw = min_weight, ms = min_samples)
        else:
            query = """
            MATCH (n)-[r WHERE r.weight >= {mw} and SIZE(r.union) >= {ms}]-(m)
            WHERE n.label = $name
            RETURN n, r, m
            """.format(mw = min_weight, ms = min_samples)
    # print(query)
    result = driver.run(query, name=name)
    nodes = {}
    edges = {}
    # print("DISPLAY RECORDS")
    # print()
    for record in result:
        # ----------------------------------------------------------------------
        # print(record)
        # source
        nodes.setdefault(record['n']['label'], 
                         {'data': {'name': record['n']['label'],
                                   'oncogene': record['n']['oncogene'],
                                   'samples': record['n']['features']}})
        # target
        nodes.setdefault(record['m']['label'], 
                         {'data': {'name': record['m']['label'],
                                   'oncogene': record['m']['oncogene'],
                                   'samples': record['m']['features']}})
        # edge
        edges.setdefault(record['n']['label'] + ' -- ' + record['m']['label'], 
                         {'data': {'source': record['n']['label'],
                                   'target': record['m']['label'],
                                   'weight': record['r']['weight'],
                                   'leninter': len(record['r']['inter']),
                                   'inter': record['r']['inter'],
                                   'lenunion': len(record['r']['union']),
                                   'union': record['r']['union'],
                                   'interaction': 'interacts with'
                                   }})
        # neighbor nodes/edges
        if all_edges and record.get('r2') and record.get('o'):
            nodes.setdefault(record['o']['label'], 
                             {'data': {'id': record['o']['id'],
                                       'name': record['o']['label'],
                                       'oncogene': record['o']['oncogene'],
                                       'samples': record['o']['features']}})
            triple_intersect = [loc for loc in record['r2']['inter'] if loc in set(record['n']['samples'])]
            new_edge_weight = len(triple_intersect) / len(set(record['n']['samples']))
            print(list(nodes.values())[0]['data']["name"], list(nodes.values())[0]['data']["samples"])
            print(record['m']['label'], record['o']['label'], record['m']['samples'], record['o']['samples'], record['r2']['weight'], new_edge_weight)

            if record['m']['label'] < record['o']['label']:
                edges.setdefault(record['m']['label'] + ' -- ' + record['o']['label'], 
                                {'data': {'source': record['m']['label'], 
                                        'target': record['o']['label'],
                                        'weight': new_edge_weight,
                                        'leninter': len(triple_intersect),
                                        'inter': triple_intersect,
                                        'lenunion': len(list(nodes.values())[0]['data']["samples"]),
                                        'union': record['r2']['union'],
                                        'interaction': 'interacts with'
                                        }})
            else:
                edges.setdefault(record['o']['label'] + ' -- ' + record['m']['label'], 
                                {'data': {'source': record['o']['id'], 
                                        'target': record['m']['id'],
                                        'weight': new_edge_weight,
                                        'leninter': len(triple_intersect),
                                        'inter': triple_intersect,
                                        'lenunion': len(list(nodes.values())[0]['data']["samples"]),
                                        'union': record['r2']['union'],
                                        'interaction': 'interacts with'
                                        }})
        # ----------------------------------------------------------------------
        #print()
        #print("CURRENT:")
        #print(nodes)
        #print(edges)
        #print()
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
        nodes, edges = session.execute_read(fetch_subgraph, test_node_name, 0.1, 1, False, False)
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
    #    test_fetch_subgraph()  # Call this to test fetch_subgraph
    
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
        query = """
        MATCH (n)-[r WHERE r.weight >= {mw} and r.lenunion >= {ms}]-(m)
        WHERE n.name = $name
        OPTIONAL MATCH (m)-[r2 WHERE r2.weight > $min_weight and r2.lenunion > $min_samples]-(o)
        MATCH (o)-[r3 WHERE r3.weight > $min_weight and r3.lenunion > $min_samples]-(n)
        RETURN n, r, m, r2, o
        LIMIT 50
        """.format(mw = min_weight, ms = min_samples)
    else:
        query = """
        MATCH (n)-[r WHERE r.weight >= {mw} and r.lenunion >= {ms}]-(m)
        WHERE n.name = $name
        RETURN n, r, m
        LIMIT 50
        """.format(mw = min_weight, ms = min_samples)
    result = driver.run(query, name=name)
    nodes = []
    edges = []
    for record in result:
        if len(nodes) == 0:
            nodes.append({'data': {'id': record['n']['id'],
                                'name': record['n']['name'],
                                'oncogene': record['n']['oncogene']}})
        nodes.append({'data': {'id': record['m']['id'],
                               'name': record['m']['name'],
                               'oncogene': record['m']['oncogene']}})
        edges.append({'data': {'source': record['n']['id'], 
                               'target': record['m']['id'],
                               'weight': record['r']['weight'],
                               'lenunion': record['r']['lenunion'],
                               'union': record['r']['union'],
                               'name': record['n']['name'] + ' (interacts with) ' + record['m']['name'],
                               'interaction': 'interacts with'
                               }})
        if all_edges and record.get('r2') and record.get('o'):
            edges.append({'data': {'source': record['m']['id'], 
                                   'target': record['o']['id'],
                                   'weight': record['r2']['weight'],
                                   'lenunion': record['r2']['lenunion'],
                                   'union': record['r2']['union'],
                                   'name': record['m']['name'] + ' (interacts with) ' + record['o']['name'],
                                   'interaction': 'interacts with'}})
    return nodes, edges

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
    
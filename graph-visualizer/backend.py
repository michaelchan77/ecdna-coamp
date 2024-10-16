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

def fetch_subgraph(driver, name):
    query = """
    MATCH (n)-[r]-(m)
    WHERE n.name = $name
    RETURN n, r, m
    """
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
    return nodes, edges

@app.route('/getNodeData', methods=['GET'])
def get_node_data():
    driver = get_driver()
    node_id = request.args.get('name')
    print(node_id)
    # Create a session and run fetch_subgraph
    with driver.session() as session:
        nodes, edges = session.execute_read(fetch_subgraph, node_id)

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
    
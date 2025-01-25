from flask import Flask, jsonify, request, g
from flask_cors import CORS
from neo4j import GraphDatabase

import pandas as pd
from graph import Graph

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

def load_graph():
    driver = get_driver()

    # construct graph
    amp_repo_datasets_dir = "/Users/michael/Downloads/amplicon_repo_datasets/"
    ccle = pd.read_csv(amp_repo_datasets_dir + "ccle_aggregated_results.csv")
    graph = Graph(ccle)
    nodes = graph.Nodes()
    edges = graph.Edges()

    # drop existing graph (change to drop if required)
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    # load new graph
    with driver.session() as session:
        # add nodes (update query to reflect neo4j.txt)
        session.run(
            """
            UNWIND $nodes AS node
            CREATE (n:Node {id: node.id, name: node.name, oncogene: node.oncogene, samples: node.samples})
            """,
            nodes=nodes
        )
        # add edges (update query to reflect neo4j.txt)
        session.run(
            """
            UNWIND $edges AS edge
            MATCH (source:Node {id: edge.source}), (target:Node {id: edge.target})
            CREATE (source)-[:CONNECTED {weight: edge.weight, inter: edge.inter, union: edge.union}]->(target)
            """,
            edges=edges
        )
    return jsonify({"message": "Graph loaded successfully"}), 200


if __name__ == '__main__':
    # app.run(debug=True)
    # To see json output for test node, uncomment this and comment 'app.run'
    with app.app_context():  # Create an application context
        load_graph()  # Call this to test fetch_subgraph
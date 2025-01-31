from flask import Flask, jsonify, request, g
from flask_cors import CORS
from neo4j import GraphDatabase

import pandas as pd
from graph import Graph

import json
import time

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
    start = time.process_time()

    amp_repo_datasets_dir = "/Users/michael/Downloads/amplicon_repo_datasets/"
    ccle = pd.read_csv(amp_repo_datasets_dir + "ccle_aggregated_results.csv")
    graph = Graph(ccle)
    nodes = graph.Nodes()
    edges = graph.Edges()

    end = time.process_time()
    print('Construct Graph:', end-start, 's')

    # drop existing graph (change to drop if required)
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    # load new graph
    start = time.process_time()

    with driver.session() as session:
        
        # add nodes
        session.run(
            """
            UNWIND $nodes AS row
            CREATE (n:Node {label: row.label, oncogene: row.oncogene, features: row.features, cell_lines: row.cell_lines})
            """,
            nodes=nodes
        )
        # add index on label (can be done once)
        session.run("""
            CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.label)
        """)
        # add edges
        session.run(
            """
            UNWIND $edges AS row
            MATCH (a:Node {label: row.source}), (b:Node {label: row.target})
            MERGE (a)-[:COAMP {weight: toFloat(row.weight), inter: row.inter, union: row.union}]->(b)
            """,
            edges=edges
        )

    end = time.process_time()
    print('Upload to neo4j:', end-start, 's')

    return jsonify({"message": "Graph loaded successfully"}), 200


if __name__ == '__main__':
    # app.run(debug=True)
    # To see json output for test node, uncomment this and comment 'app.run'
    with app.app_context():  # Create an application context
        load_graph()  # Call this to test fetch_subgraph
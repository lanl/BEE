import os
import networkx as nx
import graphviz

from beeflow.common import paths

bee_workdir = paths.workdir()
dags_dir = os.path.join(bee_workdir, 'dags')
graphmls_dir = dags_dir + "/graphmls"

def generate_viz(wf_id):
    short_id = wf_id[:6]
    graphml_path = graphmls_dir + "/" + short_id + ".graphml"
    output_path = dags_dir + "/" + short_id

    # Load the GraphML file using NetworkX
    G = nx.read_graphml(graphml_path)

    # Create a new directed graph for Graphviz
    dot = graphviz.Digraph(comment='Hierarchical Graph')
    
    # Add nodes to the Graphviz graph
    for node in G.nodes(data=True):
        node_id = node[0]
        label = node[1].get('labels', node_id)
        if label == ":Workflow":
            node_label = "Workflow"
            color ='steelblue'
        if label == ":Output":
            node_label = node[1].get('glob', node_id)
            color = 'mediumseagreen'
        if label == ":Metadata":
            node_label = node[1].get('state', node_id)
            color = 'skyblue'
        if label == ":Task":
            node_label = node[1].get('name', node_id)
            color ='lightcoral'
        if label == ":Input":
            node_label = node[1].get('source', node_id)
            color ='sandybrown'

        dot.node(node_id, label=node_label, style='filled', fillcolor=color)

    # Add edges to the Graphviz graph
    for edge in G.edges(data=True):
        source = edge[0]
        target = edge[1]
        edge_label = edge[2].get('label', '')
        if edge_label == "INPUT_OF" or edge_label == "DESCRIBES":
            dot.edge(source, target, label=edge_label, fontsize="10")
        else:
            dot.edge(target, source, label=edge_label, fontsize="10")

    # Set the output format to PNG and render the graph
    dot.format = 'png'
    dot.render(output_path, view=False)

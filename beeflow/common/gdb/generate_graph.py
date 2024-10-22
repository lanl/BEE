"""Module to make a png of a graph from a graphml file."""

import os
import shutil
import networkx as nx
import graphviz

from beeflow.wf_manager.resources import wf_utils


def generate_viz(wf_id, output_dir, graphmls_dir, no_dag_dir, copy_dag_in_archive):
    """Generate a PNG of a workflow graph from a GraphML file."""
    short_id = wf_id[:6]
    graphml_path = graphmls_dir + "/" + short_id + ".graphml"

    if no_dag_dir:
        dags_dir = output_dir
    else:
        dags_dir = output_dir + "/" + short_id + "-dags"
        os.makedirs(dags_dir, exist_ok=True)

    output_path = dags_dir + "/" + short_id + ".png"
    backup_dag(output_path, dags_dir, short_id)

    # Load the GraphML file using NetworkX
    graph = nx.read_graphml(graphml_path)

    # Initialize Graphviz graph
    dot = graphviz.Digraph(comment='Hierarchical Graph')

    # Add nodes and edges using helper functions
    add_nodes_to_dot(graph, dot)
    add_edges_to_dot(graph, dot)

    # Render the graph and save as PNG
    png_data = dot.pipe(format='png')
    save_png(output_path, png_data)

    if copy_dag_in_archive:
        # Save and backup DAGs in the workflow_dir which will be archived
        workflow_dir = wf_utils.get_workflow_dir(wf_id)
        archive_dag_dir = workflow_dir + "/dags"
        os.makedirs(archive_dag_dir, exist_ok=True)
        archive_dag_path = archive_dag_dir + "/" + short_id + ".png"
        backup_dag(archive_dag_path, archive_dag_dir, short_id)
        save_png(archive_dag_path, png_data)


def backup_dag(path, dags_dir, short_id):
    """Backup DAGs."""
    if os.path.exists(path):
        i = 1
        backup_path = f'{dags_dir}/{short_id}_v{i}.png'
        while os.path.exists(backup_path):
            i += 1
            backup_path = f'{dags_dir}/{short_id}_v{i}.png'
        shutil.copy(path, backup_path)


def add_nodes_to_dot(graph, dot):
    """Add nodes from the graph to the Graphviz object with labels and colors."""
    label_to_color = {
        ":Workflow": 'steelblue',
        ":Output": 'mediumseagreen',
        ":Metadata": 'skyblue',
        ":Task": 'lightcoral',
        ":Input": 'sandybrown',
        ":Hint": 'plum',
        ":Requirement": 'lightpink1'
    }

    for node_id, attributes in graph.nodes(data=True):
        label = attributes.get('labels', node_id)
        node_label, color = get_node_label_and_color(label, attributes, label_to_color)
        dot.node(node_id, label=node_label, style='filled', fillcolor=color)


def get_node_label_and_color(label, attributes, label_to_color):
    """Return the appropriate node label and color based on node type."""
    label_to_attribute = {
        ":Workflow": "Workflow",
        ":Output": attributes.get('glob', label),
        ":Metadata": attributes.get('state', label),
        ":Task": attributes.get('name', label),
        ":Input": attributes.get('source', label),
        ":Hint": attributes.get('class', label),
        ":Requirement": attributes.get('class', label)
    }

    # Check if the label is in the predefined labels
    if label in label_to_attribute:
        return label_to_attribute[label], label_to_color.get(label, 'gray')

    # Default case if no match
    return label, 'gray'


def add_edges_to_dot(graph, dot):
    """Add edges from the graph to the Graphviz object with appropriate labels."""
    for source, target, attributes in graph.edges(data=True):
        edge_label = attributes.get('label', '')
        if edge_label in ('INPUT_OF', 'DESCRIBES', 'HINT_OF', 'REQUIREMENT_OF'):
            dot.edge(source, target, label=edge_label, fontsize="10")
        elif edge_label in ('DEPENDS_ON', 'RESTARTED_FROM'):
            dot.edge(target, source, label=edge_label, penwidth="3",
                     fontsize="10", fontname="times-bold")
        else:
            dot.edge(target, source, label=edge_label, fontsize="10")


def save_png(output_path, png_data):
    """Save png data."""
    with open(output_path, "wb") as png_file:
        png_file.write(png_data)

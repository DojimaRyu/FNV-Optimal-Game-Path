import networkx as nx
from plotly.graph_objs import Scatter, Figure

from classes import Graph

# Colours to use when visualizing different clusters.
COLOUR_SCHEME = [
    '#2E91E5', '#E15F99', '#1CA71C', '#FB0D0D', '#DA16FF', '#222A2A', '#B68100',
    '#750D86', '#EB663B', '#511CFB', '#00A08B', '#FB00D1', '#FC0080', '#B2828D',
    '#6C7C32', '#778AAE', '#862A16', '#A777F1', '#620042', '#1616A7', '#DA60CA',
    '#6C4516', '#0D2A63', '#AF0038'
]

LINE_COLOUR = 'rgb(210,210,210)'
VERTEX_BORDER_COLOUR = 'rgb(50, 50, 50)'
BOOK_COLOUR = 'rgb(89, 205, 105)'
USER_COLOUR = 'rgb(105, 89, 205)'

def setup_graph(graph: Graph,
                layout: str = 'spring_layout',
                max_vertices: int = 5000) -> list:
    graph_nx = graph.to_networkx(max_vertices)
    pos = getattr(nx, layout)(graph_nx)

    x_values = [pos[k][0] for k in graph_nx.nodes]
    y_values = [pos[k][1] for k in graph_nx.nodes]
    labels = list(graph_nx.nodes)

    kinds = [graph_nx.nodes[k]['kind'] for k in graph_nx.nodes]
    effective_ranges = [', '.join(graph_nx.nodes[k].get('effective_ranges', [])) for k in graph_nx.nodes]
    associated_skills = [graph_nx.nodes[i].get('skill') for i in graph_nx.nodes]

    colours = [BOOK_COLOUR if kind == 'book' else USER_COLOUR for kind in kinds]

    x_edges = []
    y_edges = []

    for edge in graph_nx.edges:
        x1, x2 = pos[edge[0]][0], pos[edge[1]][0]
        x_edges += [x1, x2, None]
        y1, y2 = pos[edge[0]][1], pos[edge[1]][1]
        y_edges += [y1, y2, None]

    trace3 = Scatter(x=x_edges,
                     y=y_edges,
                     mode='lines+text',
                     name='edges',
                     line=dict(color=LINE_COLOUR, width=1),
                     )

    hover_texts = [f"{label}<br>Effective Range(s): {ranges}" for label, ranges in zip(labels, effective_ranges)]
    hover_texts = [f"{label}<br>Associated Skill: {skill}" for label, skill in zip(hover_texts, associated_skills)]

    trace4 = Scatter(x=x_values,
                     y=y_values,
                     mode='markers',
                     name='nodes',
                     marker=dict(symbol='circle-dot',
                                 size=5,
                                 color=colours,
                                 line=dict(color=VERTEX_BORDER_COLOUR, width=0.5)
                                 ),
                     text=hover_texts,
                     hovertemplate='%{text}',
                     hoverlabel={'namelength': 0}
                     )

    data = [trace3, trace4]

    return data


def visualize_graph(graph: Graph,
                    layout: str = 'spring_layout',
                    max_vertices: int = 5000,
                    output_file: str = '') -> None:
    draw_graph(setup_graph(graph, layout, max_vertices), output_file)

def draw_graph(data: list, output_file: str = '', weight_positions=None) -> None:
    fig = Figure(data=data)
    fig.update_layout({'showlegend': False})
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)

    if weight_positions:
        for w in weight_positions:
            fig.add_annotation(
                x=w[0], y=w[1],
                xref="x", yref="y",
                text=w[2],
                showarrow=False
            )

    if output_file == '':
        fig.show()
    else:
        fig.write_image(output_file)

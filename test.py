import pyvis.network as net
import pickle

with open("saved_states/call_graphs/superagi_main_py.gpickle", "rb") as f:
    G = pickle.load(f)

network = net.Network(
    directed=True,
    notebook=True,
    height="800px",
    bgcolor="#1b1636",
    font_color="#4EC9B0",
    select_menu=True,
    filter_menu=True,
    layout=True,
    neighborhood_highlight=True,
)
network.from_nx(G)
network.show_buttons(filter_="physics")

network.show("call_graph.html")

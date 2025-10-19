# visualizer.py
import matplotlib.pyplot as plt
import networkx as nx
from tkinter import filedialog
import tkinter as tk

def draw_and_save_network(segments, global_rules, zone_rules, equipment, parent_window=None):
    G = nx.DiGraph()

    # Все сегменты как узлы
    for seg in segments:
        G.add_node(seg, type='segment')

    # Оборудование
    equipment_nodes = []
    for eq_type, count in equipment.items():
        if count > 0:
            node_name = f"{eq_type} ({count})"
            G.add_node(node_name, type='equipment')
            equipment_nodes.append(node_name)
            for seg in segments:
                G.add_edge(node_name, seg, style='dotted', color='gray')

    # Глобальные правила
    for src, dst, svc in global_rules:
        G.add_edge(src, dst, label=svc, rule_type='global')

    # Правила зон (отображаем так же, но можно стилизовать иначе при желании)
    for zone_name, (zone_segs, rules) in zone_rules.items():
        for src, dst, svc in rules:
            G.add_edge(src, dst, label=svc, rule_type='zone')

    # Позиции
    pos = nx.spring_layout(G, seed=42, k=1.2)

    plt.figure(figsize=(12, 8))

    segment_nodes = [n for n in G.nodes if G.nodes[n].get('type') == 'segment']
    nx.draw_networkx_nodes(G, pos, nodelist=segment_nodes, node_color="lightblue", node_size=2500)

    if equipment_nodes:
        nx.draw_networkx_nodes(G, pos, nodelist=equipment_nodes, node_color="lightgreen", node_size=2000)

    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Все рёбра
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrowstyle='->', arrowsize=15)

    # Подписи на рёбрах
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        if 'label' in d:
            edge_labels[(u, v)] = d['label']
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)

    plt.title("Схема сегментации и взаимодействия", fontsize=14)
    plt.axis('off')

    # Диалог сохранения
    root = parent_window if parent_window else tk.Tk()
    if not parent_window:
        root.withdraw()

    file_path = filedialog.asksaveasfilename(
        parent=root,
        title="Сохранить диаграмму сети",
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
    )

    if file_path:
        plt.savefig(file_path, bbox_inches='tight', dpi=150)
        plt.close()
        return file_path
    else:
        plt.close()
        return None


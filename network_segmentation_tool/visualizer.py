# visualizer.py
import matplotlib.pyplot as plt
import networkx as nx
from tkinter import filedialog
import tkinter as tk

def draw_and_save_network(segments, global_rules, user_rules, segment_equipment, parent_window=None):
    G = nx.DiGraph()

    # Узлы: сегменты
    for seg in segments:
        G.add_node(seg, type='segment')

    # Узлы: оборудование (привязано к сегментам)
    equipment_nodes = []
    for seg in segments:
        eq_dict = segment_equipment.get(seg, {})
        for eq_type, count in eq_dict.items():
            if count > 0:
                node_name = f"{seg}:{eq_type} ({count})"
                G.add_node(node_name, type='equipment', segment=seg)
                equipment_nodes.append(node_name)
                G.add_edge(node_name, seg, style='dotted', color='gray')

    # Узлы: пользователи
    user_nodes = []
    for seg, fio, pos, src, dst, svc in user_rules:
        user_id = f"{fio} ({seg})"
        G.add_node(user_id, type='user', segment=seg)
        user_nodes.append((user_id, seg, src, dst, svc))

    # Рёбра: глобальные правила
    for _, src, dst, svc in global_rules:
        G.add_edge(src, dst, label=svc, rule_type='global')

    # Рёбра: пользовательские правила
    for user_id, seg, src, dst, svc in user_nodes:
        G.add_edge(src, dst, label=f"{svc}\n({seg})", style='dashed', color='blue')

    # Позиционирование
    pos = {}

    # Сегменты по кругу
    if segments:
        seg_layout = nx.circular_layout(segments, scale=2.0)
        for seg in segments:
            pos[seg] = seg_layout[seg]

    # Оборудование — рядом с сегментом
    for node in equipment_nodes:
        seg = G.nodes[node].get('segment')
        if seg in pos:
            base_x, base_y = pos[seg]
            idx = equipment_nodes.index(node) % 5
            offset = 0.4
            pos[node] = (base_x + offset * (idx - 2), base_y - 0.6)

    # Пользователи — снизу от сегмента
    for user_id, seg, _, _, _ in user_nodes:
        if seg in pos:
            base_x, base_y = pos[seg]
            idx = user_nodes.index((user_id, seg, _, _, _)) % 3
            pos[user_id] = (base_x + 0.3 * (idx - 1), base_y - 1.0)
            G.add_edge(user_id, seg, style='dotted', color='orange')

    plt.figure(figsize=(14, 10))

    # Рисуем
    segment_nodes = [n for n in G.nodes if G.nodes[n].get('type') == 'segment']
    equipment_nodes_list = [n for n in G.nodes if G.nodes[n].get('type') == 'equipment']
    user_nodes_list = [n for n in G.nodes if G.nodes[n].get('type') == 'user']

    nx.draw_networkx_nodes(G, pos, nodelist=segment_nodes, node_color="lightblue", node_size=3000)
    if equipment_nodes_list:
        nx.draw_networkx_nodes(G, pos, nodelist=equipment_nodes_list, node_color="lightgreen", node_size=1800)
    if user_nodes_list:
        nx.draw_networkx_nodes(G, pos, nodelist=user_nodes_list, node_color="pink", node_size=1500)

    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold")

    # Рёбра
    solid_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') not in ('dotted', 'dashed')]
    dotted_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') == 'dotted']
    dashed_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style') == 'dashed']

    nx.draw_networkx_edges(G, pos, edgelist=solid_edges, arrowstyle='->', arrowsize=15)
    if dotted_edges:
        nx.draw_networkx_edges(G, pos, edgelist=dotted_edges, style='dotted', edge_color='gray', alpha=0.7)
    if dashed_edges:
        nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, style='dashed', edge_color='blue', alpha=0.8)

    # Подписи рёбер
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        if 'label' in d:
            edge_labels[(u, v)] = d['label']
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    plt.title("Схема сегментации сети с оборудованием и пользователями", fontsize=14)
    plt.axis('off')

    # Сохранение
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


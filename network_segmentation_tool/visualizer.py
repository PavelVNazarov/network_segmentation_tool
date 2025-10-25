# visualizer.py
import matplotlib.pyplot as plt
import networkx as nx
from tkinter import filedialog
import tkinter as tk

def draw_and_save_network(segments, global_rules, user_rules, segment_equipment, parent_window=None, show_legend=True):
    """
    Отрисовывает и сохраняет схему сети.
    :param show_legend: Если True, отображает легенду внизу графика.
    """
    if not segments:
        raise ValueError("Нет сегментов для отображения")

    G = nx.MultiDiGraph()  # Используем MultiDiGraph для поддержки нескольких рёбер между узлами

    # Сегменты
    for seg in segments:
        G.add_node(seg, type='segment')

    # Оборудование
    equipment_nodes = []
    for seg in segments:
        eq_dict = segment_equipment.get(seg, {})
        for eq_type, count in eq_dict.items():
            if count > 0:
                node_name = f"{seg}:{eq_type} ({count})"
                G.add_node(node_name, type='equipment', segment=seg)
                equipment_nodes.append(node_name)
                G.add_edge(node_name, seg, style='dotted', color='gray', width=0.5)

    # Пользователи
    user_nodes = []
    for seg, fio, pos, target, svc in user_rules:
        user_id = f"{fio} ({pos})\n{seg}"
        G.add_node(user_id, type='user', segment=seg, target=target, service=svc)
        user_nodes.append((user_id, seg, target, svc))

    # Глобальные правила (теперь с уникальными рёбрами)
    for rule_name, src, dst, svc in global_rules:
        G.add_edge(src, dst, rule_type='global', label=svc, color='darkgreen', style='solid', width=1.2)

    # Пользовательские правила (от пользователя к целевому сегменту)
    for user_id, seg, target, svc in user_nodes:
        G.add_edge(user_id, target, rule_type='user', label=svc, color='orange', style='dashed', width=1.2)

    # Позиционирование
    pos = {}
    if segments:
        seg_layout = nx.circular_layout(segments, scale=2.5)
        for seg in segments:
            pos[seg] = seg_layout[seg]

    # Оборудование
    for node in equipment_nodes:
        seg = G.nodes[node].get('segment')
        if seg in pos:
            base_x, base_y = pos[seg]
            idx = equipment_nodes.index(node) % 4
            pos[node] = (base_x + 0.35 * (idx - 1.5), base_y - 0.7)

    # Пользователи
    for user_id, seg, target, svc in user_nodes:
        if seg in pos:
            base_x, base_y = pos[seg]
            idx = user_nodes.index((user_id, seg, target, svc)) % 3
            pos[user_id] = (base_x + 0.3 * (idx - 1), base_y - 1.5)

    plt.figure(figsize=(16, 12))

    # Узлы
    segment_nodes = [n for n in G.nodes if G.nodes[n].get('type') == 'segment']
    equipment_nodes_list = [n for n in G.nodes if G.nodes[n].get('type') == 'equipment']
    user_nodes_list = [n for n in G.nodes if G.nodes[n].get('type') == 'user']

    nx.draw_networkx_nodes(G, pos, nodelist=segment_nodes, node_color="lightblue", node_size=3000, node_shape='o')
    if equipment_nodes_list:
        nx.draw_networkx_nodes(G, pos, nodelist=equipment_nodes_list, node_color="lightgreen", node_size=1800, node_shape='s')
    if user_nodes_list:
        nx.draw_networkx_nodes(G, pos, nodelist=user_nodes_list, node_color="pink", node_size=1600, node_shape='^')

    nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold")

    # Рёбра по типам
    edge_groups = {
        'global': {'edges': [], 'color': 'darkgreen', 'style': 'solid'},
        'user': {'edges': [], 'color': 'orange', 'style': 'dashed'},
        'dotted': {'edges': [], 'color': 'gray', 'style': 'dotted'}
    }

    for u, v, d in G.edges(data=True):
        if d.get('rule_type') == 'global':
            edge_groups['global']['edges'].append((u, v))
        elif d.get('rule_type') == 'user':
            edge_groups['user']['edges'].append((u, v))
        elif d.get('style') == 'dotted':
            edge_groups['dotted']['edges'].append((u, v))

    # Рисуем рёбра
    for group, data in edge_groups.items():
        if data['edges']:
            nx.draw_networkx_edges(
                G, pos, edgelist=data['edges'],
                edge_color=data['color'],
                style=data['style'],
                arrowsize=15,
                arrowstyle='->',
                width=1.2 if group != 'dotted' else 0.5,
                connectionstyle='arc3,rad=0.1'  # Слегка изогнём рёбра, чтобы они не сливались
            )

    # Метки рёбер
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        if 'label' in d:
            edge_labels[(u, v)] = d['label']

    if edge_labels:
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels,
            font_size=7,  # Уменьшенный размер шрифта
            font_color='black',
            label_pos=0.6
        )

    plt.title("Схема сегментации сети с оборудованием и пользователями", fontsize=14)
    plt.axis('off')

    # Легенда
    if show_legend:
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            Patch(facecolor='lightblue', label='Сегмент сети'),
            Patch(facecolor='lightgreen', label='Оборудование'),
            Patch(facecolor='pink', label='Пользователь'),
            Line2D([0], [0], color='darkgreen', lw=2, label='Глобальное правило'),
            Line2D([0], [0], color='orange', lw=2, linestyle='--', label='Правило пользователя'),
            Line2D([0], [0], color='gray', lw=1, linestyle=':', label='Принадлежность')
        ]
        plt.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=3)

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



# visualizer.py
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
import os
import math
from tkinter import filedialog
import tkinter as tk

ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")

EQUIPMENT_ICONS = {
    "Firewall": "firewall.png",
    "Router": "router.png",
    "Switch": "switch.png",
    "Server": "server.png",
    "Workstation": "computer.png",
    "Printer": "printer.png",
    "NAS": "NAS.png",
    "Storage": "storage.png",
    "Load Balancer": "balancer.png",
    # Добавьте сюда другие типы, если нужно (например, "Устройство Интернета вещей": "iot.png")
}

USER_ICON = "user.png"


def _load_icon(icon_name, size=(32, 32)):
    if not icon_name:
        return None
    path = os.path.join(ICONS_DIR, icon_name)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        return img
    except Exception:
        return None


def draw_and_save_network(segments, global_rules, user_rules, segment_equipment, parent_window=None, show_legend=True):
    # --- Фильтрация данных ---
    segments = [s.strip() for s in segments if s and isinstance(s, str) and s.strip()]
    if not segments:
        # Рисуем только легенду
        if not show_legend:
            return None
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        fig.text(0.5, 0.6, "Нет данных для визуализации", ha='center', va='center', fontsize=12, color='gray')
        legend_lines = [
            "Глобальное правило — сплошная тёмно-зелёная стрелка",
            "Правило пользователя — пунктирная оранжевая стрелка",
            "",
            "Оборудование:"
        ]
        legend_lines += [f" • {name}" for name in EQUIPMENT_ICONS.keys()]
        legend_lines.append(" • Пользователь")
        fig.text(0.02, 0.02, "\n".join(legend_lines), fontsize=9,
                 verticalalignment='bottom',
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

        root = parent_window if parent_window else tk.Tk()
        if not parent_window:
            root.withdraw()
        file_path = filedialog.asksaveasfilename(
            parent=root,
            title="Сохранить диаграмму сети",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
        )
        if file_path:
            plt.savefig(file_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return file_path
        else:
            plt.close(fig)
            return None

    global_rules = [
        (name.strip(), src.strip(), dst.strip(), svc.strip())
        for (name, src, dst, svc) in global_rules
        if all(isinstance(x, str) and x.strip() for x in (name, src, dst, svc))
           and src in segments and dst in segments
    ]
    user_rules = [
        (seg.strip(), fio.strip(), pos.strip(), target.strip(), svc.strip())
        for (seg, fio, pos, target, svc) in user_rules
        if all(isinstance(x, str) and x.strip() for x in (seg, fio, target, svc))
           and seg in segments and target in segments
    ]
    clean_equipment = {}
    for seg, eq_dict in segment_equipment.items():
        if seg in segments and isinstance(eq_dict, dict):
            clean_eq = {eq: cnt for eq, cnt in eq_dict.items() if eq and isinstance(cnt, int) and cnt > 0}
            if clean_eq:
                clean_equipment[seg] = clean_eq
    segment_equipment = clean_equipment

    # --- Построение графа ---
    G = nx.MultiDiGraph()
    pos = {}
    equipment_nodes = []   # (node_name, eq_type, count)
    user_nodes = []        # (user_id, seg, target, svc)

    for seg in segments:
        G.add_node(seg, type='segment')

    for seg in segments:
        eq_dict = segment_equipment.get(seg, {})
        for eq_type, count in eq_dict.items():
            node_name = f"{seg}:{eq_type} ({count})"
            G.add_node(node_name, type='equipment', segment=seg, equipment_type=eq_type, count=count)
            equipment_nodes.append((node_name, eq_type, count))

    for seg, fio, pos_val, target, svc in user_rules:
        user_id = f"{fio} ({pos_val})\n[{seg}]"
        G.add_node(user_id, type='user', segment=seg, target=target, service=svc)
        user_nodes.append((user_id, seg, target, svc))

    for _, src, dst, svc in global_rules:
        G.add_edge(src, dst, rule_type='global', label=svc)
    for user_id, _, target, svc in user_nodes:
        G.add_edge(user_id, target, rule_type='user', label=svc)

    # --- Расположение узлов ---
    seg_layout = nx.circular_layout(segments, scale=4.0)
    for seg in segments:
        pos[seg] = seg_layout[seg]

    # Оборудование вокруг сегментов
    for node_name, eq_type, count in equipment_nodes:
        seg = G.nodes[node_name]['segment']
        if seg in pos:
            base_x, base_y = pos[seg]
            # Все узлы оборудования в этом сегменте (в порядке добавления)
            same_seg_nodes = [n for (n, t, c) in equipment_nodes if G.nodes[n]['segment'] == seg]
            idx = same_seg_nodes.index(node_name)  # Индекс именно этого узла
            angle_step = 360 / max(1, len(same_seg_nodes))
            rad = math.radians(idx * angle_step)
            radius = 1.8
            pos[node_name] = (base_x + radius * math.cos(rad), base_y + radius * math.sin(rad))

    # Пользователи по дуге под сегментом
    for user_id, seg, target, svc in user_nodes:
        if seg in pos:
            base_x, base_y = pos[seg]
            # Все пользователи в этом сегменте (в порядке добавления)
            same_seg_users = [u for (u, s, _, _) in user_nodes if s == seg]
            idx = same_seg_users.index(user_id)  # Индекс именно этого пользователя
            angle_step = 180 / max(1, len(same_seg_users))
            rad = math.radians(-90 + idx * angle_step)  # дуга снизу
            radius = 2.8
            pos[user_id] = (base_x + radius * math.cos(rad), base_y + radius * math.sin(rad))

    # --- Отрисовка ---
    # Автоматическое определение границ
    all_x = [pos[n][0] for n in pos.keys()]
    all_y = [pos[n][1] for n in pos.keys()]
    if all_x and all_y:
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        padding = 1.5
    else:
        x_min, x_max, y_min, y_max = -5, 5, -5, 5
        padding = 0

    width = x_max - x_min + 2 * padding
    height = y_max - y_min + 2 * padding
    fig, ax = plt.subplots(figsize=(width * 1.2, height * 1.2))
    ax.set_aspect('equal')
    plt.subplots_adjust(bottom=0.15)

    ax.set_xlim(x_min - padding, x_max + padding)
    ax.set_ylim(y_min - padding, y_max + padding)

    # Сегменты
    for seg in segments:
        if seg in pos:
            x, y = pos[seg]
            circle = plt.Circle((x, y), 1.2, color='lightblue', alpha=0.15, zorder=0)
            ax.add_patch(circle)
            ax.text(x, y, seg, fontsize=11, fontweight='bold', ha='center', va='center',
                    zorder=5, color='darkblue')

    # Связи
    global_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rule_type') == 'global']
    user_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rule_type') == 'user']

    if global_edges:
        nx.draw_networkx_edges(G, pos, edgelist=global_edges, edge_color='darkgreen',
                               arrows=True, arrowstyle='->', arrowsize=12,
                               width=1.2, alpha=0.85, connectionstyle='arc3,rad=0.15', ax=ax)
    if user_edges:
        nx.draw_networkx_edges(G, pos, edgelist=user_edges, edge_color='orange',
                               arrows=True, arrowstyle='->', arrowsize=12,
                               width=1.2, alpha=0.85, style='dashed',
                               connectionstyle='arc3,rad=0.15', ax=ax)

    # Метки связей
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True) if 'label' in d}
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                     font_size=6, font_color='black', label_pos=0.7, ax=ax)

    # Оборудование
    for node_name, eq_type, count in equipment_nodes:
        if node_name not in pos:
            continue
        x, y = pos[node_name]
        icon_file = EQUIPMENT_ICONS.get(eq_type)
        icon_img = _load_icon(icon_file) if icon_file else None
        if icon_img:
            ax.imshow(icon_img, extent=(x-0.18, x+0.18, y-0.18, y+0.18), zorder=6)
        else:
            color = plt.cm.tab10(hash(eq_type) % 10)
            rect = plt.Rectangle((x-0.15, y-0.15), 0.3, 0.3, facecolor=color, edgecolor='black', zorder=6)
            ax.add_patch(rect)
        # Отображаем количество как xN
        if count > 1:
            label = f"{eq_type} x{count}"
        else:
            label = eq_type
        ax.text(x, y - 0.3, label, fontsize=6, ha='center', va='top', zorder=6, backgroundcolor='white', alpha=0.7)

    # Пользователи
    user_icon_img = _load_icon(USER_ICON)
    for user_id, _, _, _ in user_nodes:
        if user_id not in pos:
            continue
        x, y = pos[user_id]
        if user_icon_img:
            ax.imshow(user_icon_img, extent=(x-0.15, x+0.15, y-0.15, y+0.15), zorder=6)
        else:
            circle = plt.Circle((x, y), 0.14, facecolor='pink', edgecolor='black', zorder=6)
            ax.add_patch(circle)
        name_part = user_id.split('\n')[0]
        ax.text(x, y - 0.3, name_part, fontsize=6, ha='center', va='top', zorder=6, backgroundcolor='white', alpha=0.7)

    # Легенда
    if show_legend:
        legend_lines = [
            "Глобальное правило — сплошная тёмно-зелёная стрелка",
            "Правило пользователя — пунктирная оранжевая стрелка",
            "",
            "Оборудование:"
        ]
        legend_lines += [f" • {name}" for name in EQUIPMENT_ICONS.keys()]
        legend_lines.append(" • Пользователь")
        fig.text(0.02, 0.02, "\n".join(legend_lines), fontsize=9,
                 verticalalignment='bottom',
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

    ax.set_title("Схема сегментации сети", fontsize=16, pad=20)
    ax.set_axis_off()

    # Сохранение
    root = parent_window if parent_window else tk.Tk()
    if not parent_window:
        root.withdraw()

    file_path = filedialog.asksaveasfilename(
        parent=root,
        title="Сохранить диаграмму сети",
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
    )

    if file_path:
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return file_path
    else:
        plt.close(fig)
        return None


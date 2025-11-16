# visualizer.py
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
import os
import math
from tkinter import filedialog
import tkinter as tk

def generate_grid_positions(n, center_x, center_y, spacing=0.6):
    """Генерирует координаты для n элементов в сетке 3x3 (или больше)."""
    if n == 0:
        return []
    rows = int(math.ceil(math.sqrt(n)))
    cols = int(math.ceil(n / rows))
    positions = []
    for i in range(n):
        row = i // cols
        col = i % cols
        x = center_x + (col - (cols-1)/2) * spacing
        y = center_y + (row - (rows-1)/2) * spacing
        positions.append((x, y))
    return positions

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
        legend_lines.append(" • Пользователь x0")
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

    # Валидация правил
    global_rules = [
        (name.strip(), src.strip(), dst.strip(), svc.strip())
        for (name, src, dst, svc) in global_rules
        if all(isinstance(x, str) and x.strip() for x in (name, src, dst, svc))
           and src in segments and dst in segments
    ]
    user_rules = [
        (seg.strip(), fio.strip(), pos_val.strip(), target.strip(), svc.strip())
        for (seg, fio, pos_val, target, svc) in user_rules
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
        user_id = f"{seg}:{fio}:{pos_val}"
        G.add_node(user_id, type='user', segment=seg, target=target, service=svc)
        user_nodes.append((user_id, seg, target, svc))

    for _, src, dst, svc in global_rules:
        G.add_edge(src, dst, rule_type='global', label=svc)
    for user_id, _, target, svc in user_nodes:
        G.add_edge(user_id, target, rule_type='user', label=svc)

    # --- Расположение узлов ---
    seg_layout = nx.spring_layout(G.subgraph(segments), k=3, iterations=50, scale=4.0)
    for seg in segments:
        pos[seg] = seg_layout[seg]

    # Оборудование в сетке внутри сегментов (ограничено 4x4)
    equipment_by_segment = {}
    for node_name, eq_type, count in equipment_nodes:
        seg = G.nodes[node_name]['segment']
        if seg not in equipment_by_segment:
            equipment_by_segment[seg] = []
        equipment_by_segment[seg].append(node_name)

    for seg, node_names in equipment_by_segment.items():
        if seg in pos:
            base_x, base_y = pos[seg]
            # Смещаем центр сетки оборудования немного вверх
            grid_center_y = base_y + 0.3
            display_count = min(len(node_names), 16)
            positions = generate_grid_positions(display_count, base_x, grid_center_y, spacing=0.75)
            for i, node_name in enumerate(node_names[:display_count]):
                x, y = positions[i]
                pos[node_name] = (x, y)
            if len(node_names) > 16:
                last_x, last_y = positions[-1]
                extra_label_node = f"{seg}:extra_{eq_type}"
                G.add_node(extra_label_node, type='extra_label', segment=seg, equipment_type=eq_type,
                           count=len(node_names) - 16)
                pos[extra_label_node] = (last_x + 0.3, last_y)

    # Пользователи в сетке внутри сегментов (ограничено 4x4)
    users_by_segment = {}
    for user_id, seg, target, svc in user_nodes:
        if seg not in users_by_segment:
            users_by_segment[seg] = []
        users_by_segment[seg].append(user_id)

    for seg, user_ids in users_by_segment.items():
        if seg in pos:
            base_x, base_y = pos[seg]
            # Смещаем центр сетки пользователей немного вниз
            grid_center_y = base_y - 0.3
            display_count = min(len(user_ids), 16)
            positions = generate_grid_positions(display_count, base_x, grid_center_y, spacing=0.85)
            for i, user_id in enumerate(user_ids[:display_count]):
                x, y = positions[i]
                pos[user_id] = (x, y)
            if len(user_ids) > 16:
                last_x, last_y = positions[-1]
                extra_label_node = f"{seg}:extra_user"
                G.add_node(extra_label_node, type='extra_label', segment=seg, count=len(user_ids) - 16)
                pos[extra_label_node] = (last_x + 0.3, last_y)

    # --- Автоматический масштаб ---
    all_x = [pos[n][0] for n in pos]
    all_y = [pos[n][1] for n in pos]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    padding = 1.4

    width = x_max - x_min + 2 * padding
    height = y_max - y_min + 2 * padding
    fig, ax = plt.subplots(figsize=(width * 0.8, height * 0.8))
    ax.set_aspect('equal')
    plt.subplots_adjust(bottom=0.15)
    ax.set_xlim(x_min - padding, x_max + padding)
    ax.set_ylim(y_min - padding, y_max + padding)

    # --- Сегменты (голубые круги) ---
    SEGMENT_RADIUS = 1.35
    for seg in segments:
        if seg in pos:
            x, y = pos[seg]
            circle = plt.Circle((x, y), SEGMENT_RADIUS, color='lightblue', alpha=0.2, zorder=0)
            ax.add_patch(circle)
            ax.text(x, y + SEGMENT_RADIUS - 0.28, seg,
                    fontsize=10, fontweight='bold', ha='center', va='bottom',
                    zorder=10, color='darkblue')

    # --- Связи ---
    global_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rule_type') == 'global']
    user_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rule_type') == 'user']

    if global_edges:
        nx.draw_networkx_edges(G, pos, edgelist=global_edges, edge_color='darkgreen',
                               arrows=True, arrowstyle='->', arrowsize=10,
                               width=1.0, alpha=0.8, connectionstyle='arc3,rad=0.1', ax=ax)
    if user_edges:
        nx.draw_networkx_edges(G, pos, edgelist=user_edges, edge_color='orange',
                               arrows=True, arrowstyle='->', arrowsize=10,
                               width=1.0, alpha=0.8, style='dashed',
                               connectionstyle='arc3,rad=0.1', ax=ax)

    # --- Метки на связях ---
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True) if 'label' in d}
    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels,
                                     font_size=6, font_color='black', label_pos=0.8,
                                     bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'),
                                     ax=ax)

    # --- Оборудование (иконки 44x44) ---
    for node_name, eq_type, count in equipment_nodes:
        if node_name not in pos:  # пропускаем, если не отображаем (больше 16)
            continue
        x, y = pos[node_name]
        icon_file = EQUIPMENT_ICONS.get(eq_type)
        icon_img = _load_icon(icon_file, size=(44, 44)) if icon_file else None
        if icon_img:
            ax.imshow(icon_img, extent=(x - 0.22, x + 0.22, y - 0.22, y + 0.22), zorder=6)
        else:
            color = plt.cm.tab10(hash(eq_type) % 10)
            rect = plt.Rectangle((x - 0.2, y - 0.2), 0.4, 0.4, facecolor=color, edgecolor='gray', zorder=6)
            ax.add_patch(rect)

    # --- Пользователи (иконки 44x44) ---
    user_icon_img = _load_icon(USER_ICON, size=(44, 44))
    for user_id, _, _, _ in user_nodes:
        if user_id not in pos:  # пропускаем, если не отображаем
            continue
        x, y = pos[user_id]
        if user_icon_img:
            ax.imshow(user_icon_img, extent=(x - 0.22, x + 0.22, y - 0.22, y + 0.22), zorder=6)
        else:
            circle = plt.Circle((x, y), 0.20, color='pink', edgecolor='black', zorder=6)
            ax.add_patch(circle)

    # --- Дополнительные метки "+N" для оборудования и пользователей ---
    for node, data in G.nodes(data=True):
        if data.get('type') == 'extra_label':
            x, y = pos[node]
            count = data['count']
            text = f"+{count}"
            ax.text(x, y, text, fontsize=8, ha='center', va='center',
                    color='red', fontweight='bold', zorder=11,
                    bbox=dict(facecolor='white', edgecolor='red', alpha=0.7, boxstyle='round,pad=0.1'))

    # --- Легенда 1: типы правил и оборудование ---
    if show_legend:
        legend_lines = [
            "Глобальное правило — сплошная тёмно-зелёная стрелка",
            "Правило пользователя — пунктирная оранжевая стрелка",
            "",
            "Оборудование (количество):"
        ]
        eq_summary = {}
        for eq_dict in segment_equipment.values():
            for eq_type, count in eq_dict.items():
                eq_summary[eq_type] = eq_summary.get(eq_type, 0) + count
        for eq_type, total in sorted(eq_summary.items()):
            legend_lines.append(f" • {eq_type} x{total}")

        # Подсчёт пользователей
        total_users = sum(len(users_by_segment[seg]) for seg in users_by_segment)
        legend_lines.append(f" • Пользователь x{total_users}")

        fig.text(0.02, 0.02, "\n".join(legend_lines), fontsize=8,
                 verticalalignment='bottom',
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

    # --- Легенда 2: пользователи по сегментам (ограничена 5 сегментами) ---
    if show_legend and user_rules:
        users_by_segment = {}
        for seg, fio, pos_val, target, svc in user_rules:
            if seg not in users_by_segment:
                users_by_segment[seg] = []
            users_by_segment[seg].append(f"{pos_val} {fio}")

        if users_by_segment:
            fig.text(0.85, 0.02, "Пользователи по сегментам:", fontsize=8,
                     verticalalignment='bottom',
                     bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

            y_offset = 0.02
            displayed_segments = 0
            for seg, user_list in users_by_segment.items():
                if displayed_segments >= 5:  # ограничение — максимум 5 сегментов
                    break
                displayed_segments += 1
                y_offset -= 0.03
                text = f"{seg}:"
                for i, user in enumerate(user_list):
                    if i >= 3:  # максимум 3 пользователя, остальные — «+N»
                        remaining = len(user_list) - i
                        text += f"\n  • +{remaining} других"
                        break
                    text += f"\n  • {user}"
                fig.text(0.85, y_offset, text, fontsize=7, verticalalignment='top',
                         bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

    ax.set_title("Схема сегментации сети", fontsize=14, pad=15)
    ax.set_axis_off()

    # --- Сохранение ---
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

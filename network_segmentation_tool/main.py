# main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from example_data import STANDARD_SEGMENTS, STANDARD_SERVICES, STANDARD_EQUIPMENT
from validation import validate_subnets, validate_rules
from report_generator import generate_report
from visualizer import draw_and_save_network


class NetworkSegmentationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Автоматизация сегментации ЛВС")
        self.root.geometry("1000x800")
        self.show_welcome_screen()

    def show_welcome_screen(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        ttk.Label(frame, text="Разработка ПО для автоматизации сегментации\nи межсетевого взаимодействия в ЛВС",
                  font=("Arial", 16, "bold"), justify="center").pack(pady=20)
        ttk.Label(frame, text="Автор: [Ваше имя]", font=("Arial", 12)).pack()
        ttk.Label(frame, text="Цель: Проектирование безопасной сегментированной сети с поддержкой зон и пользовательских правил",
                  wraplength=600, justify="center").pack(pady=15)
        ttk.Label(frame, text="Программа позволяет использовать стандартные и пользовательские сегменты, сервисы, оборудование,\n"
                              "а также задавать глобальные правила и правила для выделенных зон сети.",
                  wraplength=600, justify="center").pack(pady=10)

        ttk.Button(frame, text="Начать", command=self.show_main_interface, width=20).pack(pady=30)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_main_interface(self):
        self.clear_window()
        self.setup_data()

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_segments = ttk.Frame(notebook)
        self.tab_global_rules = ttk.Frame(notebook)
        self.tab_zones = ttk.Frame(notebook)
        self.tab_equipment = ttk.Frame(notebook)

        notebook.add(self.tab_segments, text="Сегменты и подсети")
        notebook.add(self.tab_global_rules, text="Глобальные правила")
        notebook.add(self.tab_zones, text="Зоны сети")
        notebook.add(self.tab_equipment, text="Оборудование")

        self.build_segments_tab()
        self.build_global_rules_tab()
        self.build_zones_tab()
        self.build_equipment_tab()

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Анализ и отчёт", command=self.analyze).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Сохранить отчёт", command=self.save_report).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Назад", command=self.show_welcome_screen).pack(side='left', padx=5)

        self.output_text = tk.Text(self.root, height=10, wrap='word')
        self.output_text.pack(fill='both', padx=10, pady=5, expand=True)

    def setup_data(self):
        self.segments = []
        self.subnets = {}
        self.global_rules = []
        self.zones = {}  # имя_зоны -> (список_сегментов, правила)
        self.equipment = {}

    # === СЕГМЕНТЫ ===
    def build_segments_tab(self):
        control_frame = ttk.Frame(self.tab_segments)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить сегмент", command=self.add_segment_row).pack(side='left')
        ttk.Button(control_frame, text="Стандартные", command=self.load_standard_segments).pack(side='left', padx=5)

        self.segment_container = ttk.Frame(self.tab_segments)
        self.segment_container.pack(fill='both', expand=True)
        self.segment_rows = []

        for _ in range(2):
            self.add_segment_row()

    def add_segment_row(self):
        row_frame = ttk.Frame(self.segment_container)
        row_frame.pack(fill='x', pady=2)

        name_entry = ttk.Entry(row_frame, width=20)
        name_entry.pack(side='left', padx=2)
        cidr_entry = ttk.Entry(row_frame, width=20)
        cidr_entry.pack(side='left', padx=2)

        btn = ttk.Button(row_frame, text="×", width=3, command=lambda f=row_frame: self.remove_segment_row(f))
        btn.pack(side='left', padx=2)

        self.segment_rows.append((row_frame, name_entry, cidr_entry))

    def remove_segment_row(self, frame):
        frame.destroy()
        self.segment_rows = [(f, n, c) for f, n, c in self.segment_rows if f != frame]

    def load_standard_segments(self):
        from example_data import STANDARD_SEGMENTS, STANDARD_SERVICES
        # Очистим текущие
        for frame, _, _ in self.segment_rows:
            frame.destroy()
        self.segment_rows.clear()

        for seg in STANDARD_SEGMENTS:
            self.add_segment_row()
            self.segment_rows[-1][1].insert(0, seg)
            # Подсеть по умолчанию (можно улучшить)
            self.segment_rows[-1][2].insert(0, f"192.168.{10 + STANDARD_SEGMENTS.index(seg)}.0/24")

    # === ГЛОБАЛЬНЫЕ ПРАВИЛА ===
    def build_global_rules_tab(self):
        control_frame = ttk.Frame(self.tab_global_rules)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить правило", command=self.add_global_rule_row).pack(side='left')

        self.global_rule_container = ttk.Frame(self.tab_global_rules)
        self.global_rule_container.pack(fill='both', expand=True)
        self.global_rule_rows = []

        for _ in range(4):
            self.add_global_rule_row()

    def add_global_rule_row(self):
        row_frame = ttk.Frame(self.global_rule_container)
        row_frame.pack(fill='x', pady=2)

        src = ttk.Entry(row_frame, width=18)
        src.pack(side='left', padx=2)
        dst = ttk.Entry(row_frame, width=18)
        dst.pack(side='left', padx=2)
        svc = ttk.Combobox(row_frame, values=list(STANDARD_SERVICES.keys()), width=15)
        svc.pack(side='left', padx=2)

        btn = ttk.Button(row_frame, text="×", width=3, command=lambda f=row_frame: self.remove_global_rule_row(f))
        btn.pack(side='left', padx=2)

        self.global_rule_rows.append((row_frame, src, dst, svc))

    def remove_global_rule_row(self, frame):
        frame.destroy()
        self.global_rule_rows = [(f, s, d, v) for f, s, d, v in self.global_rule_rows if f != frame]

    # === ЗОНЫ ===
    def build_zones_tab(self):
        control_frame = ttk.Frame(self.tab_zones)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить зону", command=self.add_zone).pack(side='left')

        self.zones_container = ttk.Frame(self.tab_zones)
        self.zones_container.pack(fill='both', expand=True)
        self.zone_frames = []

    def add_zone(self):
        zone_name = f"Зона_{len(self.zone_frames) + 1}"
        zone_frame = ttk.LabelFrame(self.zones_container, text=zone_name, padding=10)
        zone_frame.pack(fill='x', pady=5)

        # Имя зоны
        name_frame = ttk.Frame(zone_frame)
        name_frame.pack(fill='x')
        ttk.Label(name_frame, text="Имя зоны:").pack(side='left')
        name_entry = ttk.Entry(name_frame, width=20)
        name_entry.insert(0, zone_name)
        name_entry.pack(side='left', padx=5)

        # Сегменты зоны
        seg_frame = ttk.Frame(zone_frame)
        seg_frame.pack(fill='x', pady=5)
        ttk.Label(seg_frame, text="Сегменты (через запятую):").pack(side='left')
        seg_entry = ttk.Entry(seg_frame, width=40)
        seg_entry.pack(side='left', padx=5)

        # Правила
        rule_frame = ttk.Frame(zone_frame)
        rule_frame.pack(fill='x', pady=5)
        ttk.Label(rule_frame, text="Правила зоны:").pack(anchor='w')
        rule_container = ttk.Frame(rule_frame)
        rule_container.pack(fill='x', pady=2)
        rule_rows = []

        def add_zone_rule():
            r_frame = ttk.Frame(rule_container)
            r_frame.pack(fill='x', pady=1)
            s1 = ttk.Entry(r_frame, width=15)
            s1.pack(side='left', padx=1)
            s2 = ttk.Entry(r_frame, width=15)
            s2.pack(side='left', padx=1)
            sv = ttk.Combobox(r_frame, values=list(STANDARD_SERVICES.keys()), width=12)
            sv.pack(side='left', padx=1)
            ttk.Button(r_frame, text="×", width=2, command=lambda f=r_frame: f.destroy()).pack(side='left', padx=1)
            rule_rows.append((s1, s2, sv))

        ttk.Button(rule_frame, text="+ Правило", command=add_zone_rule).pack(anchor='w', pady=2)

        # Кнопка удаления зоны
        ttk.Button(zone_frame, text="Удалить зону", command=lambda f=zone_frame: f.destroy()).pack(anchor='e')

        self.zone_frames.append((zone_frame, name_entry, seg_entry, rule_container, rule_rows, add_zone_rule))

        # Добавим одно правило по умолчанию
        add_zone_rule()

    # === ОБОРУДОВАНИЕ ===
    def build_equipment_tab(self):
        canvas = tk.Canvas(self.tab_equipment)
        scrollbar = ttk.Scrollbar(self.tab_equipment, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.equipment_vars = {}
        all_equipment = list(STANDARD_EQUIPMENT)

        # Поле для добавления пользовательского оборудования
        add_frame = ttk.Frame(scrollable_frame)
        add_frame.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        ttk.Label(add_frame, text="Добавить тип оборудования:").pack(side='left')
        custom_eq_entry = ttk.Entry(add_frame, width=20)
        custom_eq_entry.pack(side='left', padx=5)
        ttk.Button(add_frame, text="Добавить",
                   command=lambda: self.add_custom_equipment(custom_eq_entry.get(), scrollable_frame, all_equipment)
                  ).pack(side='left')

        # Стандартное оборудование
        for i, eq in enumerate(all_equipment):
            ttk.Label(scrollable_frame, text=eq).grid(row=i+1, column=0, sticky='w', padx=10, pady=2)
            var = tk.IntVar(value=0)
            spin = ttk.Spinbox(scrollable_frame, from_=0, to=1000, width=8, textvariable=var)
            spin.grid(row=i+1, column=1, padx=10, pady=2)
            self.equipment_vars[eq] = var

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def add_custom_equipment(self, name, parent_frame, equipment_list):
        name = name.strip()
        if not name or name in self.equipment_vars:
            return
        if name not in equipment_list:
            equipment_list.append(name)
        row = len(equipment_list)
        ttk.Label(parent_frame, text=name).grid(row=row, column=0, sticky='w', padx=10, pady=2)
        var = tk.IntVar(value=0)
        spin = ttk.Spinbox(parent_frame, from_=0, to=1000, width=8, textvariable=var)
        spin.grid(row=row, column=1, padx=10, pady=2)
        self.equipment_vars[name] = var

    # === СБОР ДАННЫХ И АНАЛИЗ ===
    def collect_data(self):
        # Сегменты
        self.segments = []
        self.subnets = {}
        for _, name_ent, cidr_ent in self.segment_rows:
            name = name_ent.get().strip()
            if name:
                if name in self.segments:
                    messagebox.showerror("Ошибка", f"Дублирование сегмента: {name}")
                    return False
                self.segments.append(name)
                self.subnets[name] = cidr_ent.get().strip()

        if not self.segments:
            messagebox.showwarning("Ошибка", "Добавьте хотя бы один сегмент!")
            return False

        # Глобальные правила
        self.global_rules = []
        for _, src, dst, svc_cb in self.global_rule_rows:
            s, d, v = src.get().strip(), dst.get().strip(), svc_cb.get().strip()
            if s and d and v:
                if v == "Custom":
                    v = "Custom"
                self.global_rules.append((s, d, v))

        # Зоны
        self.zones = {}
        for zone_frame, name_ent, seg_ent, _, rule_rows, _ in self.zone_frames:
            name = name_ent.get().strip()
            segs_str = seg_ent.get().strip()
            if not name or not segs_str:
                continue
            segs = [s.strip() for s in segs_str.split(',') if s.strip()]
            if not segs:
                continue
            # Проверка: все сегменты должны быть в общем списке
            for s in segs:
                if s not in self.segments:
                    messagebox.showerror("Ошибка", f"Сегмент '{s}' из зоны '{name}' не объявлен в списке сегментов")
                    return False

            rules = []
            for s1_ent, s2_ent, svc_cb in rule_rows:
                s1, s2, svc = s1_ent.get().strip(), s2_ent.get().strip(), svc_cb.get().strip()
                if s1 and s2 and svc:
                    if svc == "Custom":
                        svc = "Custom"
                    rules.append((s1, s2, svc))

            self.zones[name] = (segs, rules)

        # Оборудование
        self.equipment = {eq: var.get() for eq, var in self.equipment_vars.items()}

        return True

    def analyze(self):
        if not self.collect_data():
            return

        all_rules = self.global_rules[:]
        for _, (_, rules) in self.zones.items():
            all_rules.extend(rules)

        subnet_err = validate_subnets(self.subnets)
        rule_errs = validate_rules(all_rules, self.segments)

        errors = []
        if subnet_err:
            errors.append(subnet_err)
        if rule_errs:
            errors.extend(rule_errs)

        report = generate_report(
            self.segments, self.subnets, self.global_rules, self.zones, self.equipment, errors
        )
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, report)

        if not errors:
            img_path = draw_and_save_network(
                self.segments, self.global_rules, self.zones, self.equipment, self.root
            )
            if img_path:
                messagebox.showinfo("Успех", f"Схема сохранена:\n{img_path}")
        else:
            messagebox.showwarning("Внимание", "Обнаружены ошибки. Схема не создана.")

    def save_report(self):
        content = self.output_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Ошибка", "Нет данных для сохранения")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Сохранено", f"Отчёт сохранён:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSegmentationApp(root)
    root.mainloop()


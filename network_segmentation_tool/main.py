# main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from example_data import STANDARD_SEGMENTS, STANDARD_SERVICES, STANDARD_EQUIPMENT
from validation import validate_subnets, validate_rules, validate_user_rules
from report_generator import generate_report
from visualizer import draw_and_save_network


class NetworkSegmentationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Автоматизация сегментации ЛВС")
        self.root.geometry("1050x800")
        self.show_welcome_screen()

    def show_welcome_screen(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        ttk.Label(frame, text="Программа для автоматизации сегментации и межсетевого взаимодействия в локальных вычислительных сетях предприятий",
                  font=("Arial", 14), wraplength=700, justify="center").pack(pady=20)

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
        self.tab_user_rules = ttk.Frame(notebook)
        self.tab_equipment = ttk.Frame(notebook)

        notebook.add(self.tab_segments, text="Сегменты и подсети")
        notebook.add(self.tab_global_rules, text="Глобальные правила")
        notebook.add(self.tab_user_rules, text="Правила для пользователей")
        notebook.add(self.tab_equipment, text="Оборудование")

        self.build_segments_tab()
        self.build_global_rules_tab()
        self.build_user_rules_tab()
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
        self.user_rules = []
        self.segment_equipment = {}  # seg -> {eq: count}

    # === СЕГМЕНТЫ ===
    def build_segments_tab(self):
        control_frame = ttk.Frame(self.tab_segments)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить сегмент", command=self.add_segment_row).pack(side='left')
        ttk.Button(control_frame, text="Стандартные", command=self.load_standard_segments).pack(side='left', padx=5)

        # Заголовки
        header = ttk.Frame(self.tab_segments)
        header.pack(fill='x', pady=(0, 5))
        ttk.Label(header, text="Имя сегмента", width=20, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="Подсеть", width=20, anchor='w').pack(side='left', padx=2)

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
        for frame, _, _ in self.segment_rows:
            frame.destroy()
        self.segment_rows.clear()

        for i, seg in enumerate(STANDARD_SEGMENTS):
            self.add_segment_row()
            self.segment_rows[-1][1].insert(0, seg)
            self.segment_rows[-1][2].insert(0, f"192.168.{i+1}.0/24")

    # === ГЛОБАЛЬНЫЕ ПРАВИЛА ===
    def build_global_rules_tab(self):
        control_frame = ttk.Frame(self.tab_global_rules)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить правило", command=self.add_global_rule_row).pack(side='left')

        # Заголовки
        header = ttk.Frame(self.tab_global_rules)
        header.pack(fill='x', pady=(0, 5))
        ttk.Label(header, text="Имя правила", width=15, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="Сегмент 1", width=15, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="Сегмент 2", width=15, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="Сетевой протокол", width=18, anchor='w').pack(side='left', padx=2)

        self.global_rule_container = ttk.Frame(self.tab_global_rules)
        self.global_rule_container.pack(fill='both', expand=True)
        self.global_rule_rows = []

        for _ in range(3):
            self.add_global_rule_row()

    def add_global_rule_row(self):
        row_frame = ttk.Frame(self.global_rule_container)
        row_frame.pack(fill='x', pady=2)

        name_entry = ttk.Entry(row_frame, width=15)
        name_entry.pack(side='left', padx=2)

        src_cb = ttk.Combobox(row_frame, values=self.segments, width=13)
        src_cb.pack(side='left', padx=2)
        dst_cb = ttk.Combobox(row_frame, values=self.segments, width=13)
        dst_cb.pack(side='left', padx=2)

        svc_cb = ttk.Combobox(row_frame, values=list(STANDARD_SERVICES.keys()), width=16)
        svc_cb.pack(side='left', padx=2)

        btn = ttk.Button(row_frame, text="×", width=3, command=lambda f=row_frame: self.remove_global_rule_row(f))
        btn.pack(side='left', padx=2)

        self.global_rule_rows.append((row_frame, name_entry, src_cb, dst_cb, svc_cb))

    def remove_global_rule_row(self, frame):
        frame.destroy()
        self.global_rule_rows = [(f, n, s, d, v) for f, n, s, d, v in self.global_rule_rows if f != frame]

    # === ПРАВИЛА ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
    def build_user_rules_tab(self):
        control_frame = ttk.Frame(self.tab_user_rules)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить правило", command=self.add_user_rule_row).pack(side='left')

        # Заголовки
        header = ttk.Frame(self.tab_user_rules)
        header.pack(fill='x', pady=(0, 5))
        ttk.Label(header, text="Сегмент", width=12).pack(side='left', padx=2)
        ttk.Label(header, text="ФИО", width=18).pack(side='left', padx=2)
        ttk.Label(header, text="Должность", width=15).pack(side='left', padx=2)
        ttk.Label(header, text="Сегмент 1", width=12).pack(side='left', padx=2)
        ttk.Label(header, text="Сегмент 2", width=12).pack(side='left', padx=2)
        ttk.Label(header, text="Протокол", width=15).pack(side='left', padx=2)

        self.user_rule_container = ttk.Frame(self.tab_user_rules)
        self.user_rule_container.pack(fill='both', expand=True)
        self.user_rule_rows = []

        for _ in range(2):
            self.add_user_rule_row()

    def add_user_rule_row(self):
        row_frame = ttk.Frame(self.user_rule_container)
        row_frame.pack(fill='x', pady=2)

        seg_cb = ttk.Combobox(row_frame, values=self.segments, width=10)
        seg_cb.pack(side='left', padx=2)
        fio_entry = ttk.Entry(row_frame, width=16)
        fio_entry.pack(side='left', padx=2)
        pos_entry = ttk.Entry(row_frame, width=13)
        pos_entry.pack(side='left', padx=2)
        src_cb = ttk.Combobox(row_frame, values=self.segments, width=10)
        src_cb.pack(side='left', padx=2)
        dst_cb = ttk.Combobox(row_frame, values=self.segments, width=10)
        dst_cb.pack(side='left', padx=2)
        svc_cb = ttk.Combobox(row_frame, values=list(STANDARD_SERVICES.keys()), width=13)
        svc_cb.pack(side='left', padx=2)

        btn = ttk.Button(row_frame, text="×", width=3, command=lambda f=row_frame: self.remove_user_rule_row(f))
        btn.pack(side='left', padx=2)

        self.user_rule_rows.append((row_frame, seg_cb, fio_entry, pos_entry, src_cb, dst_cb, svc_cb))

    def remove_user_rule_row(self, frame):
        frame.destroy()
        self.user_rule_rows = [(f, s, fio, pos, src, dst, svc) for f, s, fio, pos, src, dst, svc in self.user_rule_rows if f != frame]

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

        # Заголовки
        header = ttk.Frame(scrollable_frame)
        header.grid(row=0, column=0, columnspan=3, sticky='w', pady=5)
        ttk.Label(header, text="Сегмент").pack(side='left', padx=(10, 20))
        ttk.Label(header, text="Тип оборудования").pack(side='left', padx=(0, 20))
        ttk.Label(header, text="Количество").pack(side='left')

        self.equipment_rows = []
        row_index = 1

        # Добавление оборудования
        def add_equipment_row():
            nonlocal row_index
            seg_cb = ttk.Combobox(scrollable_frame, values=self.segments, width=15)
            seg_cb.grid(row=row_index, column=0, padx=10, pady=2, sticky='w')
            eq_cb = ttk.Combobox(scrollable_frame, values=STANDARD_EQUIPMENT, width=20)
            eq_cb.grid(row=row_index, column=1, padx=10, pady=2, sticky='w')
            count_var = tk.IntVar(value=0)
            spin = ttk.Spinbox(scrollable_frame, from_=0, to=1000, width=8, textvariable=count_var)
            spin.grid(row=row_index, column=2, padx=10, pady=2, sticky='w')
            btn = ttk.Button(scrollable_frame, text="×", width=3,
                             command=lambda r=row_index: self.remove_equipment_row(r))
            btn.grid(row=row_index, column=3, padx=5, pady=2)
            self.equipment_rows.append((row_index, seg_cb, eq_cb, count_var))
            row_index += 1

        add_btn = ttk.Button(scrollable_frame, text="+ Добавить оборудование", command=add_equipment_row)
        add_btn.grid(row=row_index, column=0, columnspan=2, sticky='w', pady=10)
        row_index += 1

        # Добавим 3 строки по умолчанию
        for _ in range(3):
            add_equipment_row()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def remove_equipment_row(self, row_id):
        self.equipment_rows = [r for r in self.equipment_rows if r[0] != row_id]

    # === СБОР ДАННЫХ ===
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

        # Обновим выпадающие списки во всех вкладках
        self.update_comboboxes()

        # Глобальные правила
        self.global_rules = []
        for _, name_ent, src_cb, dst_cb, svc_cb in self.global_rule_rows:
            name = name_ent.get().strip()
            src = src_cb.get().strip()
            dst = dst_cb.get().strip()
            svc = svc_cb.get().strip()
            if name and src and dst and svc:
                if svc == "Custom":
                    svc = "Custom"
                self.global_rules.append((name, src, dst, svc))

        # Правила пользователей
        self.user_rules = []
        for _, seg_cb, fio_ent, pos_ent, src_cb, dst_cb, svc_cb in self.user_rule_rows:
            seg = seg_cb.get().strip()
            fio = fio_ent.get().strip()
            pos = pos_ent.get().strip()
            src = src_cb.get().strip()
            dst = dst_cb.get().strip()
            svc = svc_cb.get().strip()
            if seg and fio and src and dst and svc:
                if svc == "Custom":
                    svc = "Custom"
                self.user_rules.append((seg, fio, pos, src, dst, svc))

        # Оборудование по сегментам
        self.segment_equipment = {seg: {} for seg in self.segments}
        for _, seg_cb, eq_cb, count_var in self.equipment_rows:
            seg = seg_cb.get().strip()
            eq = eq_cb.get().strip()
            cnt = count_var.get()
            if seg in self.segments and eq and cnt > 0:
                if eq not in self.segment_equipment[seg]:
                    self.segment_equipment[seg][eq] = 0
                self.segment_equipment[seg][eq] += cnt

        return True

    def update_comboboxes(self):
        # Обновить все Combobox'ы с сегментами
        for _, name_ent, src_cb, dst_cb, svc_cb in self.global_rule_rows:
            src_cb['values'] = self.segments
            dst_cb['values'] = self.segments
        for _, seg_cb, fio_ent, pos_ent, src_cb, dst_cb, svc_cb in self.user_rule_rows:
            seg_cb['values'] = self.segments
            src_cb['values'] = self.segments
            dst_cb['values'] = self.segments
        for _, seg_cb, eq_cb, count_var in self.equipment_rows:
            seg_cb['values'] = self.segments

    # === АНАЛИЗ ===
    def analyze(self):
        if not self.collect_data():
            return

        all_rules = [(name, src, dst, svc) for name, src, dst, svc in self.global_rules]
        for seg, fio, pos, src, dst, svc in self.user_rules:
            all_rules.append((f"User:{fio}", src, dst, svc))

        subnet_errors = validate_subnets(self.subnets)
        rule_errors = validate_rules(all_rules, self.segments)
        user_errors = validate_user_rules(self.user_rules, self.segments)

        errors = []
        if subnet_errors:
            errors.extend(subnet_errors)
        if rule_errors:
            errors.extend(rule_errors)
        if user_errors:
            errors.extend(user_errors)

        report = generate_report(
            self.segments, self.subnets, self.global_rules, self.user_rules, self.segment_equipment, errors
        )
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, report)

        if not errors:
            img_path = draw_and_save_network(
                self.segments, self.global_rules, self.user_rules, self.segment_equipment, self.root
            )
            if img_path:
                messagebox.showinfo("Успех", f"Схема сохранена:\n{img_path}")
        else:
            messagebox.showwarning("Внимание", f"Обнаружено ошибок: {len(errors)}. Схема не создана.")

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


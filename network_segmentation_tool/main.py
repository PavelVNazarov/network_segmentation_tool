# main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from example_data import STANDARD_SEGMENTS, STANDARD_SERVICES, STANDARD_EQUIPMENT
from validation import validate_subnets, validate_rules, validate_user_rules
from report_generator import generate_report, generate_risk_report
from visualizer import draw_and_save_network
import ipaddress
import platform
import subprocess
import tempfile
import os

def open_image_file(filepath):
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{str(e)}")

class NetworkSegmentationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Автоматизация сегментации ЛВС")
        self.root.geometry("1050x700")
        self.show_welcome_screen()

    def create_scrollable_frame(self, parent):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

        return scrollable_frame

    def show_welcome_screen(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding=30)
        frame.pack(expand=True)

        ttk.Label(
            frame,
            text="Программа для автоматизации сегментации и межсетевого взаимодействия в локальных вычислительных сетях предприятий",
            font=("Arial", 14),
            wraplength=700,
            justify="center"
        ).pack(pady=20)

        ttk.Button(frame, text="Начать", command=self.show_main_interface, width=20).pack(pady=30)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_main_interface(self):
        self.clear_window()
        self.setup_data()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_segments = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_segments, text="1. Сегменты и подсети")

        self.tabs_created = False

        self.build_segments_tab()

        self.bottom_button_frame = ttk.Frame(self.root)
        self.bottom_button_frame.pack(pady=10)
        ttk.Button(self.bottom_button_frame, text="Сохранить отчёт", command=self.save_report).pack(side='left', padx=5)
        ttk.Button(self.bottom_button_frame, text="Назад", command=self.show_welcome_screen).pack(side='left', padx=5)

        self.output_text = tk.Text(self.root, height=10, wrap='word')
        self.output_text.pack(fill='both', padx=10, pady=5, expand=True)

    def setup_data(self):
        self.segments = []
        self.subnets = {}
        self.global_rules = []
        self.user_rules = []
        self.segment_equipment = {}
        self.equipment_rows = []  # ← КРИТИЧЕСКИ ВАЖНАЯ СТРОКА

    def build_segments_tab(self):
        scrollable = self.create_scrollable_frame(self.tab_segments)

        control_frame = ttk.Frame(scrollable)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить сегмент", command=self.add_segment_row).pack(side='left')
        ttk.Button(control_frame, text="Стандартные", command=self.load_standard_segments).pack(side='left', padx=5)

        header = ttk.Frame(scrollable)
        header.pack(fill='x', pady=(0, 5))
        ttk.Label(header, text="Имя сегмента", width=20, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="Подсеть", width=20, anchor='w').pack(side='left', padx=2)

        self.segment_container = ttk.Frame(scrollable)
        self.segment_container.pack(fill='both', expand=True)
        self.segment_rows = []

        for _ in range(2):
            self.add_segment_row()

        continue_btn = ttk.Button(
            scrollable,
            text="Продолжить (требуется минимум 2 сегмента)",
            command=self.try_continue
        )
        continue_btn.pack(pady=15)
        self.continue_button = continue_btn  # для блокировки

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

    def validate_segment_names_and_subnets(self):
        segments = []
        subnets = {}
        errors = []

        for _, name_ent, cidr_ent in self.segment_rows:
            name = name_ent.get().strip()
            cidr = cidr_ent.get().strip()
            if not name:
                continue
            if not name.replace('_', '').replace('-', '').isalnum():
                errors.append(f"Недопустимое имя сегмента: '{name}'")
            elif name in segments:
                errors.append(f"Дублирование сегмента: '{name}'")
            else:
                segments.append(name)
                subnets[name] = cidr

        if len(segments) < 2:
            errors.append("Требуется минимум 2 сегмента")

        for name, cidr in subnets.items():
            if cidr:
                try:
                    ipaddress.ip_network(cidr, strict=False)
                except ValueError:
                    errors.append(f"Некорректный CIDR для '{name}': {cidr}")

        return segments, subnets, errors

    def try_continue(self):
        # Блокируем кнопку, чтобы избежать двойного нажатия
        self.continue_button.config(state='disabled')
        self.root.update_idletasks()

        try:
            segments, subnets, errors = self.validate_segment_names_and_subnets()
            if errors:
                msg = "Исправьте ошибки:\n" + "\n".join(f" - {e}" for e in errors)
                messagebox.showerror("Ошибка в сегментах", msg)
                return

            self.segments = segments
            self.subnets = subnets

            if not self.tabs_created:
                self.create_remaining_tabs()
                self.tabs_created = True
            else:
                # Обновляем данные в уже созданных вкладках
                self.update_all_comboboxes()

            self.notebook.select(self.tab_global_rules)

        finally:
            # Всегда разблокируем кнопку
            self.continue_button.config(state='normal')

    def create_remaining_tabs(self):
        self.tab_global_rules = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_global_rules, text="2. Глобальные правила")
        self.build_global_rules_tab()

        self.tab_user_rules = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_user_rules, text="3. Правила для пользователей")
        self.build_user_rules_tab()

        self.tab_equipment = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_equipment, text="4. Оборудование")
        self.build_equipment_tab()

        self.tab_instructions = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_instructions, text="5. Инструкция")
        self.build_instructions_tab()

        self.update_all_comboboxes()

        self.bottom_button_frame.destroy()
        new_btn_frame = ttk.Frame(self.root)
        new_btn_frame.pack(pady=10)
        ttk.Button(new_btn_frame, text="Анализ и отчёт", command=self.analyze).pack(side='left', padx=5)
        ttk.Button(new_btn_frame, text="Сохранить отчёт", command=self.save_report).pack(side='left', padx=5)
        ttk.Button(new_btn_frame, text="Просмотреть схему", command=self.view_diagram).pack(side='left', padx=5)
        ttk.Button(new_btn_frame, text="Сохранить рисунок сети", command=self.save_diagram).pack(side='left', padx=5)
        ttk.Button(new_btn_frame, text="Назад", command=self.show_welcome_screen).pack(side='left', padx=5)

    def build_global_rules_tab(self):
        scrollable = self.create_scrollable_frame(self.tab_global_rules)

        control_frame = ttk.Frame(scrollable)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить правило", command=self.add_global_rule_row).pack(side='left')

        header = ttk.Frame(scrollable)
        header.pack(fill='x', pady=(0, 5))
        ttk.Label(header, text="Имя правила", width=15, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="SRC Сегмент", width=15, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="DST Сегмент", width=15, anchor='w').pack(side='left', padx=2)
        ttk.Label(header, text="Протокол", width=18, anchor='w').pack(side='left', padx=2)

        self.global_rule_container = ttk.Frame(scrollable)
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

    def build_user_rules_tab(self):
        scrollable = self.create_scrollable_frame(self.tab_user_rules)

        control_frame = ttk.Frame(scrollable)
        control_frame.pack(fill='x', pady=5)
        ttk.Button(control_frame, text="+ Добавить правило", command=self.add_user_rule_row).pack(side='left')

        header = ttk.Frame(scrollable)
        header.pack(fill='x', pady=(0, 5))
        ttk.Label(header, text="Сегмент", width=12).pack(side='left', padx=2)
        ttk.Label(header, text="ФИО", width=18).pack(side='left', padx=2)
        ttk.Label(header, text="Должность", width=15).pack(side='left', padx=2)
        ttk.Label(header, text="Доступ к сегменту", width=18).pack(side='left', padx=2)
        ttk.Label(header, text="Протокол", width=15).pack(side='left', padx=2)

        self.user_rule_container = ttk.Frame(scrollable)
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
        target_cb = ttk.Combobox(row_frame, values=self.segments, width=15)
        target_cb.pack(side='left', padx=2)
        svc_cb = ttk.Combobox(row_frame, values=list(STANDARD_SERVICES.keys()), width=13)
        svc_cb.pack(side='left', padx=2)

        btn = ttk.Button(row_frame, text="×", width=3, command=lambda f=row_frame: self.remove_user_rule_row(f))
        btn.pack(side='left', padx=2)

        self.user_rule_rows.append((row_frame, seg_cb, fio_entry, pos_entry, target_cb, svc_cb))

    def remove_user_rule_row(self, frame):
        frame.destroy()
        self.user_rule_rows = [(f, s, fio, pos, target, svc) for f, s, fio, pos, target, svc in self.user_rule_rows if f != frame]

    def build_equipment_tab(self):
        scrollable = self.create_scrollable_frame(self.tab_equipment)

        header = ttk.Frame(scrollable)
        header.pack(fill='x', pady=5)
        ttk.Label(header, text="Сегмент", width=15, anchor='w').pack(side='left', padx=(10, 5))
        ttk.Label(header, text="Оборудование", width=20, anchor='w').pack(side='left', padx=(0, 5))
        ttk.Label(header, text="Количество", width=12, anchor='w').pack(side='left')

        add_btn = ttk.Button(scrollable, text="+ Добавить оборудование", command=self.add_equipment_row)
        add_btn.pack(pady=5)

        self.equipment_container = ttk.Frame(scrollable)
        self.equipment_container.pack(fill='both', expand=True, pady=5)

        for _ in range(3):
            self.add_equipment_row()

    def add_equipment_row(self):
        row_frame = ttk.Frame(self.equipment_container)
        row_frame.pack(fill='x', pady=2)

        seg_cb = ttk.Combobox(row_frame, values=self.segments, width=15)
        seg_cb.pack(side='left', padx=5)
        eq_cb = ttk.Combobox(row_frame, values=STANDARD_EQUIPMENT, width=20)
        eq_cb.pack(side='left', padx=5)
        count_var = tk.IntVar(value=0)
        spin = ttk.Spinbox(row_frame, from_=0, to=1000, width=8, textvariable=count_var)
        spin.pack(side='left', padx=5)
        btn = ttk.Button(row_frame, text="×", width=3,
                         command=lambda f=row_frame: self.remove_equipment_row(f))
        btn.pack(side='left', padx=5)

        self.equipment_rows.append((row_frame, seg_cb, eq_cb, count_var))

    def remove_equipment_row(self, frame):
        frame.destroy()
        self.equipment_rows = [(f, s, e, c) for f, s, e, c in self.equipment_rows if f != frame]

    def build_instructions_tab(self):
        text = """ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ

1. Вкладка "1. Сегменты и подсети":
   - Добавьте минимум 2 сегмента.
   - Укажите подсеть в формате CIDR (например, 192.168.1.0/24).
   - Нажмите "Продолжить".

2. Вкладка "2. Глобальные правила":
   - Задайте правила взаимодействия между сегментами.
   - Укажите имя правила, SRC и DST сегменты, протокол.

3. Вкладка "3. Правила для пользователей":
   - Укажите сегмент пользователя, ФИО, должность.
   - Разрешите доступ к другому сегменту по выбранному протоколу.

4. Вкладка "4. Оборудование":
   - Привяжите оборудование к конкретному сегменту.
   - Укажите количество устройств.

5. Кнопки внизу окна:
   - "Анализ и отчёт" — проверка модели и генерация текстового отчёта.
   - "Сохранить рисунок сети" — экспорт схемы в PNG или PDF.
   - "Сохранить отчёт" — сохранение текстового отчёта в файл.

Примечание: схема отображает сегменты (голубые узлы), оборудование (зелёные), пользователей (розовые) и правила взаимодействия."""
        text_widget = tk.Text(self.tab_instructions, wrap='word', padx=10, pady=10)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
        text_widget.pack(fill='both', expand=True)

    def update_all_comboboxes(self):
        for _, name_ent, src_cb, dst_cb, svc_cb in self.global_rule_rows:
            src_cb['values'] = self.segments
            dst_cb['values'] = self.segments
        for _, seg_cb, fio_ent, pos_ent, target_cb, svc_cb in self.user_rule_rows:
            seg_cb['values'] = self.segments
            target_cb['values'] = self.segments
        for _, seg_cb, eq_cb, count_var in self.equipment_rows:
            seg_cb['values'] = self.segments

    def collect_data_for_analysis(self):
        self.global_rules = []
        for _, name_ent, src_cb, dst_cb, svc_cb in self.global_rule_rows:
            name = name_ent.get().strip()
            src = src_cb.get().strip()
            dst = dst_cb.get().strip()
            svc = svc_cb.get().strip()
            if name and src and dst and svc:
                self.global_rules.append((name, src, dst, svc))

        self.user_rules = []
        for _, seg_cb, fio_ent, pos_ent, target_cb, svc_cb in self.user_rule_rows:
            seg = seg_cb.get().strip()
            fio = fio_ent.get().strip()
            pos = pos_ent.get().strip()
            target = target_cb.get().strip()
            svc = svc_cb.get().strip()
            if seg and fio and target and svc:
                self.user_rules.append((seg, fio, pos, target, svc))

        self.segment_equipment = {seg: {} for seg in self.segments}
        for _, seg_cb, eq_cb, count_var in self.equipment_rows:
            seg = seg_cb.get().strip()
            eq = eq_cb.get().strip()
            cnt = count_var.get()
            if seg in self.segments and eq and cnt > 0:
                if eq not in self.segment_equipment[seg]:
                    self.segment_equipment[seg][eq] = 0
                self.segment_equipment[seg][eq] += cnt

    def analyze(self):
        self.collect_data_for_analysis()

        all_rules = [(name, src, dst, svc) for name, src, dst, svc in self.global_rules]
        for seg, fio, pos, target, svc in self.user_rules:
            all_rules.append((f"User:{fio}", seg, target, svc))

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

        main_report = generate_report(
            self.segments, self.subnets, self.global_rules, self.user_rules, self.segment_equipment, errors
        )
        risk_report = generate_risk_report(
            self.segments, self.global_rules, self.user_rules, self.segment_equipment
        )

        full_report = main_report + "\n\n" + risk_report
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, full_report)

        if errors:
            messagebox.showwarning("Внимание", f"Обнаружено ошибок: {len(errors)}. Отчёт содержит предупреждения.")

    def save_diagram(self):
        self.collect_data_for_analysis()
        try:
            if not self.segments:
                messagebox.showerror("Ошибка", "Нет сегментов для визуализации")
                return
            img_path = draw_and_save_network(
                self.segments, self.global_rules, self.user_rules, self.segment_equipment, self.root
            )
            if img_path:
                messagebox.showinfo("Успех", f"Схема сохранена:\n{img_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать схему:\n{str(e)}")

    def view_diagram(self):
        self.collect_data_for_analysis()
        if not self.segments:
            messagebox.showerror("Ошибка", "Нет сегментов для визуализации")
            return

        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_path = tmp.name

            import tkinter.filedialog
            original_asksave = tkinter.filedialog.asksaveasfilename
            tkinter.filedialog.asksaveasfilename = lambda **kw: temp_path

            try:
                img_path = draw_and_save_network(
                    self.segments,
                    self.global_rules,
                    self.user_rules,
                    self.segment_equipment,
                    self.root,
                    show_legend=True
                )
                if img_path and os.path.exists(img_path):
                    open_image_file(img_path)
                else:
                    messagebox.showwarning("Ошибка", "Не удалось создать схему")
            finally:
                tkinter.filedialog.asksaveasfilename = original_asksave

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить схему:\n{str(e)}")

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



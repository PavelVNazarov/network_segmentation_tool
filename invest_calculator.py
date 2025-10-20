import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class InvestmentCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Инвестиционный калькулятор сложного процента с пополнением")
        self.root.geometry("600x700")

        # Variables
        self.target_var = tk.StringVar(value="income")  # income, rate, capital, term, topup
        self.start_capital_var = tk.DoubleVar()
        self.term_var = tk.IntVar()
        self.term_unit_var = tk.StringVar(value="лет")
        self.rate_var = tk.DoubleVar()
        self.reinvest_var = tk.BooleanVar()
        self.topup_amount_var = tk.DoubleVar()
        self.topup_frequency_var = tk.StringVar(value="Раз в месяц")

        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Title
        title_label = ttk.Label(main_frame, text="Инвестиционный калькулятор", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Target calculation radio buttons
        target_frame = ttk.LabelFrame(main_frame, text="Вычислить", padding="10")
        target_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        ttk.Radiobutton(target_frame, text="Доход", variable=self.target_var, value="income").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(target_frame, text="Ставку", variable=self.target_var, value="rate").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(target_frame, text="Стартовый капитал", variable=self.target_var, value="capital").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(target_frame, text="Срок достижения цели", variable=self.target_var, value="term").grid(row=3, column=0, sticky="w")
        ttk.Radiobutton(target_frame, text="Размер пополнений", variable=self.target_var, value="topup").grid(row=4, column=0, sticky="w")

        # Start Capital
        ttk.Label(main_frame, text="Стартовый капитал:").grid(row=2, column=0, sticky="w", pady=5)
        start_capital_entry = ttk.Entry(main_frame, textvariable=self.start_capital_var, width=20)
        start_capital_entry.grid(row=2, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, text="₽").grid(row=2, column=2, sticky="w", padx=5)

        # Term
        ttk.Label(main_frame, text="Срок инвестирования:").grid(row=3, column=0, sticky="w", pady=5)
        term_entry = ttk.Entry(main_frame, textvariable=self.term_var, width=10)
        term_entry.grid(row=3, column=1, sticky="w", pady=5)
        term_unit_combo = ttk.Combobox(main_frame, textvariable=self.term_unit_var, values=["лет", "месяцев"], state="readonly", width=8)
        term_unit_combo.grid(row=3, column=2, sticky="w", padx=5)

        # Rate
        ttk.Label(main_frame, text="Ставка:").grid(row=4, column=0, sticky="w", pady=5)
        rate_entry = ttk.Entry(main_frame, textvariable=self.rate_var, width=20)
        rate_entry.grid(row=4, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, text="% годовых").grid(row=4, column=2, sticky="w", padx=5)

        # Reinvest
        ttk.Checkbutton(main_frame, text="Реинвестировать доход", variable=self.reinvest_var).grid(row=5, column=0, columnspan=3, sticky="w", pady=10)

        # Top-up
        ttk.Label(main_frame, text="Дополнительные вложения:").grid(row=6, column=0, sticky="w", pady=5)
        topup_entry = ttk.Entry(main_frame, textvariable=self.topup_amount_var, width=20)
        topup_entry.grid(row=6, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, text="₽").grid(row=6, column=2, sticky="w", padx=5)

        topup_freq_combo = ttk.Combobox(main_frame, textvariable=self.topup_frequency_var,
                                        values=["Раз в месяц", "Раз в 3 месяца", "Раз в полгода", "Раз в год"],
                                        state="readonly", width=15)
        topup_freq_combo.grid(row=7, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, text="Частота:").grid(row=7, column=0, sticky="w", pady=5)

        # Calculate button
        calc_button = ttk.Button(main_frame, text="РАССЧИТАТЬ", command=self.calculate)
        calc_button.grid(row=8, column=0, columnspan=3, pady=20)

        # Result panel
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="10")
        result_frame.grid(row=9, column=0, columnspan=3, sticky="ew", pady=10)

        self.result_text = tk.Text(result_frame, height=8, width=60, wrap="word", state="disabled", font=("Courier", 10))
        self.result_text.pack(fill="both", expand=True)

        # Save button
        save_button = ttk.Button(main_frame, text="Сохранить результат", command=self.save_result)
        save_button.grid(row=10, column=0, columnspan=3, pady=10)

    def calculate(self):
        try:
            start_capital = self.start_capital_var.get()
            term = self.term_var.get()
            term_unit = self.term_unit_var.get()
            rate = self.rate_var.get() / 100.0  # convert to decimal
            reinvest = self.reinvest_var.get()
            topup_amount = self.topup_amount_var.get()
            topup_freq_str = self.topup_frequency_var.get()

            if term <= 0:
                raise ValueError("Срок должен быть больше 0")
            if rate < 0:
                raise ValueError("Ставка не может быть отрицательной")
            if start_capital < 0:
                raise ValueError("Стартовый капитал не может быть отрицательным")
            if topup_amount < 0:
                raise ValueError("Пополнение не может быть отрицательным")

            # Convert term to months
            if term_unit == "лет":
                total_months = term * 12
            else:  # месяцев
                total_months = term

            # Determine top-up interval in months
            freq_map = {
                "Раз в месяц": 12,
                "Раз в 3 месяца": 4,
                "Раз в полгода": 2,
                "Раз в год": 1
            }
            topups_per_year = freq_map[topup_freq_str]
            topup_interval_months = 12 // topups_per_year

            # Calculate total number of top-ups
            num_topups = total_months // topup_interval_months

            if reinvest:
                # Сложный процент с ежемесячной капитализацией
                monthly_rate = rate / 12
                current_amount = start_capital
                for month in range(1, total_months + 1):
                    current_amount *= (1 + monthly_rate)
                    if topup_amount > 0 and month % topup_interval_months == 0:
                        current_amount += topup_amount
            else:
                # Простой процент: проценты только на стартовый капитал
                years = total_months / 12
                interest_on_capital = start_capital * rate * years
                total_topups = topup_amount * num_topups
                current_amount = start_capital + interest_on_capital + total_topups

            # Общая сумма вложений
            total_invested = start_capital + (topup_amount * num_topups)
            income = current_amount - total_invested

            # Format output
            result = f"Расчёт по цели: {self.get_target_name()}\n\n"
            result += f"Стартовый капитал: {start_capital:,.2f} ₽\n"
            result += f"Срок: {term} {term_unit}\n"
            result += f"Годовая ставка: {rate*100:.2f}%\n"
            result += f"Реинвестирование: {'Да' if reinvest else 'Нет'}\n"
            result += f"Пополнение: {topup_amount:,.2f} ₽ ({topup_freq_str})\n"
            result += "-" * 50 + "\n"
            result += f"Итоговая сумма: {current_amount:,.2f} ₽\n"
            result += f"Доход (прибыль): {income:,.2f} ₽\n"

            # Display in text widget
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def get_target_name(self):
        targets = {
            "income": "Доход",
            "rate": "Ставку",
            "capital": "Стартовый капитал",
            "term": "Срок достижения цели",
            "topup": "Размер пополнений"
        }
        return targets.get(self.target_var.get(), "Неизвестно")

    def save_result(self):
        result_content = self.result_text.get(1.0, tk.END).strip()
        if not result_content:
            messagebox.showwarning("Сохранение", "Нет данных для сохранения.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            title="Сохранить результат"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result_content)
                messagebox.showinfo("Успех", f"Результат сохранён в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InvestmentCalculator(root)
    root.mainloop()


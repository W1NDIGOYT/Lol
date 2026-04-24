import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from threading import Thread

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("650x600")
        self.root.resizable(True, True)
        
        # Конфигурация
        self.API_KEY = "ВАШ_API_КЛЮЧ"  # Замените на ваш ключ
        self.API_URL = f"https://v6.exchangerate-api.com/v6/{self.API_KEY}/latest/"
        self.HISTORY_FILE = "conversion_history.json"
        
        # Доступные валюты
        self.currencies = []
        self.exchange_rates = {}
        
        # Загрузка истории при запуске
        self.history = self.load_history()
        
        # Создание интерфейса
        self.setup_ui()
        
        # Загрузка списка валют
        self.load_currencies()
        
    def setup_ui(self):
        """Создание интерфейса приложения"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Конвертер валют", 
                                font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Фрейм для конвертации
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация", padding="10")
        convert_frame.grid(row=1, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        convert_frame.columnconfigure(1, weight=1)
        
        # Из валюты
        ttk.Label(convert_frame, text="Из:").grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        self.from_currency = ttk.Combobox(convert_frame, width=10)
        self.from_currency.grid(row=0, column=1, padx=(0, 10), sticky=tk.W)
        
        # В валюту
        ttk.Label(convert_frame, text="В:").grid(row=0, column=2, padx=(10, 10), sticky=tk.W)
        self.to_currency = ttk.Combobox(convert_frame, width=10)
        self.to_currency.grid(row=0, column=3, padx=(0, 10), sticky=tk.W)
        
        # Сумма
        ttk.Label(convert_frame, text="Сумма:").grid(row=1, column=0, padx=(0, 10), 
                                                     pady=10, sticky=tk.W)
        self.amount_entry = ttk.Entry(convert_frame, width=15)
        self.amount_entry.grid(row=1, column=1, padx=(0, 10), pady=10, sticky=tk.W)
        
        # Результат
        ttk.Label(convert_frame, text="Результат:").grid(row=1, column=2, padx=(10, 10), 
                                                         pady=10, sticky=tk.W)
        self.result_label = ttk.Label(convert_frame, text="0.00", font=("Arial", 12, "bold"))
        self.result_label.grid(row=1, column=3, padx=(0, 10), pady=10, sticky=tk.W)
        
        # Кнопка конвертации
        self.convert_btn = ttk.Button(convert_frame, text="Конвертировать", 
                                     command=self.convert_currency)
        self.convert_btn.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Фрейм для истории
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Таблица истории (Treeview)
        columns = ("Дата", "Сумма", "Из", "В", "Результат")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        
        # Настройка заголовков
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Кнопки управления историей
        btn_frame = ttk.Frame(history_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Очистить историю", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить курсы", command=self.refresh_rates).pack(side=tk.LEFT, padx=5)
        
        # Статус бар
        self.status_bar = ttk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Загрузка сохраненной истории в таблицу
        self.update_history_display()
    
    def load_currencies(self):
        """Загрузка списка доступных валют"""
        try:
            # Пробуем загрузить из кэша
            if os.path.exists("currencies.json"):
                with open("currencies.json", "r") as f:
                    data = json.load(f)
                    self.currencies = data.get("currencies", [])
                    self.from_currency['values'] = self.currencies
                    self.to_currency['values'] = self.currencies
                    if self.currencies:
                        self.from_currency.set("USD")
                        self.to_currency.set("EUR")
                        return
            
            # Если кэша нет, загружаем из API
            self.update_status("Загрузка списка валют...")
            response = requests.get(f"{self.API_URL}USD")
            if response.status_code == 200:
                data = response.json()
                self.currencies = list(data.get("conversion_rates", {}).keys())
                self.from_currency['values'] = self.currencies
                self.to_currency['values'] = self.currencies
                if self.currencies:
                    self.from_currency.set("USD")
                    self.to_currency.set("EUR")
                
                # Сохраняем в кэш
                with open("currencies.json", "w") as f:
                    json.dump({"currencies": self.currencies}, f)
                
                self.update_status("Готов к работе")
            else:
                self.update_status("Ошибка загрузки валют")
                self.use_fallback_currencies()
        except Exception as e:
            self.update_status(f"Ошибка: {str(e)}")
            self.use_fallback_currencies()
    
    def use_fallback_currencies(self):
        """Использование стандартного списка валют при ошибке"""
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "KZT", "UAH"]
        self.from_currency['values'] = self.currencies
        self.to_currency['values'] = self.currencies
        self.from_currency.set("USD")
        self.to_currency.set("EUR")
        self.update_status("Используются стандартные валюты")
    
    def convert_currency(self):
        """Конвертация валюты"""
        # Проверка ввода
        amount_str = self.amount_entry.get().strip()
        
        if not amount_str:
            messagebox.showerror("Ошибка", "Введите сумму для конвертации")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число")
            return
        
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        if not from_curr or not to_curr:
            messagebox.showerror("Ошибка", "Выберите валюты")
            return
        
        # Конвертация в отдельном потоке
        Thread(target=self.perform_conversion, args=(amount, from_curr, to_curr), daemon=True).start()
    
    def perform_conversion(self, amount, from_curr, to_curr):
        """Выполнение конвертации"""
        self.convert_btn.config(state="disabled")
        self.update_status("Получение курса валют...")
        
        try:
            # Получение курса
            response = requests.get(f"{self.API_URL}{from_curr}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success":
                    rates = data.get("conversion_rates", {})
                    rate = rates.get(to_curr)
                    
                    if rate:
                        result = amount * rate
                        
                        # Обновление интерфейса в главном потоке
                        self.root.after(0, lambda: self.update_result(result, amount, from_curr, to_curr, rate))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Курс для {to_curr} не найден"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", "Ошибка API"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка HTTP: {response.status_code}"))
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", "Превышено время ожидания"))
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Неизвестная ошибка: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.convert_btn.config(state="normal"))
    
    def update_result(self, result, amount, from_curr, to_curr, rate):
        """Обновление результата и сохранение в историю"""
        self.result_label.config(text=f"{result:.2f} {to_curr}")
        
        # Сохранение в историю
        history_entry = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": result,
            "rate": rate
        }
        
        self.history.append(history_entry)
        self.save_history()
        self.update_history_display()
        
        self.update_status(f"Конвертация выполнена: {amount} {from_curr} = {result:.2f} {to_curr}")
    
    def update_history_display(self):
        """Обновление отображения истории"""
        # Очистка таблицы
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Добавление записей
        for entry in reversed(self.history[-20:]):  # Показываем последние 20 записей
            self.history_tree.insert("", "end", values=(
                entry["datetime"],
                f"{entry['amount']:.2f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.2f}"
            ))
    
    def load_history(self):
        """Загрузка истории из JSON файла"""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю конвертаций?"):
            self.history = []
            self.save_history()
            self.update_history_display()
            self.update_status("История очищена")
    
    def refresh_rates(self):
        """Обновление курсов валют"""
        self.update_status("Обновление курсов...")
        # Просто перезагружаем список валют
        self.load_currencies()
        self.update_status("Курсы обновлены")
    
    def update_status(self, message):
        """Обновление статусной строки"""
        self.status_bar.config(text=message)

def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
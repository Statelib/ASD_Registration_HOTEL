# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from hotel import (
    HotelSystem,
    ROOM_TYPES,
)



class HotelApp:
    def __init__(self, root):
        self.root = root
        self.system = HotelSystem()      

        self.root.title("Регистрация постояльцев в гостинице ")
        self.root.geometry("1000x640")
        self.root.minsize(860, 560)

        self._setup_style()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

        # Первичное заполнение таблиц (пока пустые)
        self.refresh_guests()
        self.refresh_rooms()
        self.refresh_stays()

    #  Оформление
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", padding=5)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"))

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(10, 6))
        bar.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(bar, text="Гостиница", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Button(bar, text="Загрузить демо-данные",
                   command=self.load_demo).pack(side=tk.RIGHT)

    def _build_statusbar(self):
        self.status = tk.StringVar(value="Готово.")
        bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(bar, textvariable=self.status, anchor="w",
                  padding=(10, 4)).pack(fill=tk.X)

    def set_status(self, text):
        """Короткое сообщение в строке состояния внизу окна."""
        self.status.set(text)

    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.tab_guests = ttk.Frame(self.nb, padding=8)
        self.tab_rooms = ttk.Frame(self.nb, padding=8)
        self.tab_stays = ttk.Frame(self.nb, padding=8)

        self.nb.add(self.tab_guests, text="Постояльцы")
        self.nb.add(self.tab_rooms, text="Гостиничные номера")
        self.nb.add(self.tab_stays, text="Вселение / выселение")

        self._build_guests_tab()
        self._build_rooms_tab()
        self._build_stays_tab()

    #  Вспомогательная функция: подпись + поле ввода в сетке
    @staticmethod
    def _add_field(parent, label, row, width=28):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w",
                                           padx=(0, 8), pady=3)
        var = tk.StringVar()
        entry = ttk.Entry(parent, textvariable=var, width=width)
        entry.grid(row=row, column=1, sticky="w", pady=3)
        return var, entry

    #  ВКЛАДКА «ПОСТОЯЛЬЦЫ»
    def _build_guests_tab(self):
        tab = self.tab_guests

        # --- Форма регистрации ---
        form = ttk.LabelFrame(tab, text="Регистрация постояльца", padding=10)
        form.pack(side=tk.TOP, fill=tk.X)

        self.g_passport, _ = self._add_field(form, "Номер паспорта (NNNN-NNNNNN):", 0)
        self.g_name, _ = self._add_field(form, "ФИО:", 1, width=40)
        self.g_year, _ = self._add_field(form, "Год рождения:", 2, width=10)
        self.g_address, _ = self._add_field(form, "Адрес:", 3, width=40)
        self.g_purpose, _ = self._add_field(form, "Цель прибытия:", 4, width=40)

        ttk.Button(form, text="Зарегистрировать",
                   command=self.on_register_guest).grid(row=5, column=1,
                                                        sticky="w", pady=(8, 0))

        # --- Панель поиска ---
        search = ttk.LabelFrame(tab, text="Поиск", padding=10)
        search.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))

        ttk.Label(search, text="По паспорту:").grid(row=0, column=0, sticky="w")
        self.g_search_passport = tk.StringVar()
        ttk.Entry(search, textvariable=self.g_search_passport, width=18)\
            .grid(row=0, column=1, padx=4)
        ttk.Button(search, text="Найти",
                   command=self.on_search_guest_passport).grid(row=0, column=2, padx=2)

        ttk.Label(search, text="По ФИО:").grid(row=0, column=3, sticky="w", padx=(16, 0))
        self.g_search_name = tk.StringVar()
        ttk.Entry(search, textvariable=self.g_search_name, width=22)\
            .grid(row=0, column=4, padx=4)
        ttk.Button(search, text="Найти",
                   command=self.on_search_guest_name).grid(row=0, column=5, padx=2)

        ttk.Button(search, text="Показать всех",
                   command=self.refresh_guests).grid(row=0, column=6, padx=(16, 0))

        # --- Таблица постояльцев ---
        table_frame = ttk.Frame(tab)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(8, 0))

        cols = ("passport", "name", "year", "address", "purpose", "room")
        headers = ("Паспорт", "ФИО", "Год", "Адрес", "Цель прибытия", "Проживает в")
        widths = (110, 220, 55, 200, 160, 95)
        self.guests_tree = self._make_tree(table_frame, cols, headers, widths)

        # --- Кнопки действий ---
        actions = ttk.Frame(tab)
        actions.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))
        ttk.Button(actions, text="Удалить выбранного",
                   command=self.on_delete_guest).pack(side=tk.LEFT)
        ttk.Button(actions, text="Очистить всех",
                   command=self.on_clear_guests).pack(side=tk.LEFT, padx=6)

    #  ВКЛАДКА «ГОСТИНИЧНЫЕ НОМЕРА»
    def _build_rooms_tab(self):
        tab = self.tab_rooms

        form = ttk.LabelFrame(tab, text="Добавление гостиничного номера", padding=10)
        form.pack(side=tk.TOP, fill=tk.X)

        hint = "Номер (ANNN), A: Л-люкс, П-полулюкс, О-одноместный, М-многоместный:"
        self.r_number, _ = self._add_field(form, hint, 0, width=12)
        self.r_places, _ = self._add_field(form, "Количество мест:", 1, width=10)
        self.r_rooms, _ = self._add_field(form, "Количество комнат:", 2, width=10)

        ttk.Label(form, text="Наличие санузла:").grid(row=3, column=0, sticky="w",
                                                      padx=(0, 8), pady=3)
        self.r_bathroom = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, variable=self.r_bathroom).grid(row=3, column=1,
                                                             sticky="w")

        self.r_equipment, _ = self._add_field(form, "Оборудование:", 4, width=50)

        ttk.Button(form, text="Добавить номер",
                   command=self.on_add_room).grid(row=5, column=1, sticky="w",
                                                  pady=(8, 0))

        # --- Поиск ---
        search = ttk.LabelFrame(tab, text="Поиск", padding=10)
        search.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))

        ttk.Label(search, text="По номеру:").grid(row=0, column=0, sticky="w")
        self.r_search_number = tk.StringVar()
        ttk.Entry(search, textvariable=self.r_search_number, width=12)\
            .grid(row=0, column=1, padx=4)
        ttk.Button(search, text="Найти",
                   command=self.on_search_room_number).grid(row=0, column=2, padx=2)

        ttk.Label(search, text="По фрагменту оборудования:")\
            .grid(row=0, column=3, sticky="w", padx=(16, 0))
        self.r_search_equip = tk.StringVar()
        ttk.Entry(search, textvariable=self.r_search_equip, width=22)\
            .grid(row=0, column=4, padx=4)
        ttk.Button(search, text="Найти (Бойер–Мур)",
                   command=self.on_search_room_equip).grid(row=0, column=5, padx=2)

        ttk.Button(search, text="Показать все",
                   command=self.refresh_rooms).grid(row=0, column=6, padx=(16, 0))

        # --- Таблица номеров ---
        table_frame = ttk.Frame(tab)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(8, 0))

        cols = ("number", "type", "places", "rooms", "bath", "equip")
        headers = ("Номер", "Тип", "Мест", "Комнат", "Санузел", "Оборудование")
        widths = (80, 110, 60, 70, 80, 300)
        self.rooms_tree = self._make_tree(table_frame, cols, headers, widths)

        actions = ttk.Frame(tab)
        actions.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))
        ttk.Button(actions, text="Удалить выбранный",
                   command=self.on_delete_room).pack(side=tk.LEFT)
        ttk.Button(actions, text="Очистить все",
                   command=self.on_clear_rooms).pack(side=tk.LEFT, padx=6)

    #  ВКЛАДКА «ВСЕЛЕНИЕ / ВЫСЕЛЕНИЕ»
    def _build_stays_tab(self):
        tab = self.tab_stays

        form = ttk.LabelFrame(tab, text="Регистрация вселения", padding=10)
        form.pack(side=tk.TOP, fill=tk.X)

        self.s_passport, _ = self._add_field(form, "Номер паспорта:", 0, width=18)
        self.s_room, _ = self._add_field(form, "Номер гост. номера:", 1, width=12)
        self.s_date_in, _ = self._add_field(form, "Дата заселения:", 2, width=18)
        # Подставим сегодняшнюю дату по умолчанию для удобства
        self.s_date_in.set(datetime.date.today().isoformat())

        ttk.Button(form, text="Заселить",
                   command=self.on_check_in).grid(row=3, column=1, sticky="w",
                                                  pady=(8, 0))

        # --- Выселение выбранной записи ---
        out = ttk.LabelFrame(tab, text="Регистрация выселения", padding=10)
        out.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
        ttk.Label(out, text="Дата выселения:").grid(row=0, column=0, sticky="w")
        self.s_date_out = tk.StringVar(value=datetime.date.today().isoformat())
        ttk.Entry(out, textvariable=self.s_date_out, width=18)\
            .grid(row=0, column=1, padx=4)
        ttk.Button(out, text="Выселить выбранного",
                   command=self.on_check_out).grid(row=0, column=2, padx=6)
        ttk.Label(out, text="(сначала выберите строку проживающего в таблице)")\
            .grid(row=0, column=3, sticky="w", padx=(8, 0))

        # --- Таблица записей ---
        table_frame = ttk.Frame(tab)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(8, 0))

        cols = ("room", "passport", "in", "out", "status")
        headers = ("Номер комнаты", "Паспорт", "Заселение", "Выселение", "Статус")
        widths = (120, 130, 130, 130, 120)
        self.stays_tree = self._make_tree(table_frame, cols, headers, widths)

        ttk.Button(tab, text="Обновить список",
                   command=self.refresh_stays).pack(side=tk.TOP, anchor="w",
                                                    pady=(6, 0))

    #  Вспомогательная функция: создать Treeview со скроллбаром
    @staticmethod
    def _make_tree(parent, cols, headers, widths):
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        for c, h, w in zip(cols, headers, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    #  ОБНОВЛЕНИЕ ТАБЛИЦ
    def refresh_guests(self, guests=None):
        """Перерисовать таблицу постояльцев (по умолчанию — всех)."""
        tree = self.guests_tree
        tree.delete(*tree.get_children())
        if guests is None:
            guests = self.system.list_guests()
        for g in guests:
            # Текущий номер проживания берём через ядро системы
            _, room = self.system.find_guest_by_passport(g.passport)
            room = room if room else "—"
            tree.insert("", tk.END, iid=g.passport,
                        values=(g.passport, g.full_name, g.birth_year,
                                g.address, g.purpose, room))

    def refresh_rooms(self, rooms=None):
        """Перерисовать таблицу номеров (по умолчанию — прямой обход дерева)."""
        tree = self.rooms_tree
        tree.delete(*tree.get_children())
        if rooms is None:
            rooms = self.system.list_rooms()
        for r in rooms:
            tree.insert("", tk.END, iid=r.number,
                        values=(r.number, r.type_name(), r.places, r.rooms_count,
                                "есть" if r.has_bathroom else "нет", r.equipment))

    def refresh_stays(self):
        """Перерисовать таблицу вселений (список уже отсортирован по номеру)."""
        tree = self.stays_tree
        tree.delete(*tree.get_children())
        self._stay_rows = {}  # сопоставление iid -> объект Stay
        for i, s in enumerate(self.system.list_stays()):
            iid = "stay-%d" % i
            self._stay_rows[iid] = s
            status = "проживает" if s.check_out == "" else "выселен"
            tree.insert("", tk.END, iid=iid,
                        values=(s.room_number, s.passport, s.check_in,
                                s.check_out if s.check_out else "—", status))

    #  ОБРАБОТЧИКИ — ПОСТОЯЛЬЦЫ
    def on_register_guest(self):
        year_text = self.g_year.get().strip()
        if not year_text.lstrip("-").isdigit():
            messagebox.showwarning("Ошибка ввода", "Год рождения должен быть целым числом.")
            return
        ok, msg = self.system.register_guest(
            self.g_passport.get().strip(),
            self.g_name.get().strip(),
            int(year_text),
            self.g_address.get().strip(),
            self.g_purpose.get().strip(),
        )
        self.set_status(msg)
        if ok:
            # очистим поля формы и обновим таблицу
            for var in (self.g_passport, self.g_name, self.g_year,
                        self.g_address, self.g_purpose):
                var.set("")
            self.refresh_guests()
        else:
            messagebox.showwarning("Не удалось зарегистрировать", msg)

    def on_delete_guest(self):
        sel = self.guests_tree.selection()
        if not sel:
            messagebox.showinfo("Удаление", "Сначала выберите постояльца в таблице.")
            return
        passport = sel[0]
        if not messagebox.askyesno("Подтверждение",
                                   "Удалить постояльца %s?" % passport):
            return
        ok, msg = self.system.delete_guest(passport)
        self.set_status(msg)
        self.refresh_guests()
        self.refresh_stays()  # могли удалиться связанные записи о вселении

    def on_clear_guests(self):
        if not messagebox.askyesno("Подтверждение",
                                   "Очистить ВСЕ данные о постояльцах?"):
            return
        self.system.clear_guests()
        self.set_status("Данные о постояльцах очищены.")
        self.refresh_guests()

    def on_search_guest_passport(self):
        passport = self.g_search_passport.get().strip()
        guest, room = self.system.find_guest_by_passport(passport)
        if guest is None:
            self.set_status("Постоялец с паспортом %s не найден." % passport)
            self.refresh_guests([])
            messagebox.showinfo("Поиск", "Постоялец не найден.")
        else:
            self.refresh_guests([guest])
            place = room if room else "нигде не проживает"
            self.set_status("Найден: %s | проживает: %s" % (guest.full_name, place))

    def on_search_guest_name(self):
        frag = self.g_search_name.get().strip()
        if not frag:
            self.refresh_guests()
            return
        found = self.system.find_guests_by_name(frag)
        self.refresh_guests(found)
        self.set_status("Найдено постояльцев по ФИО «%s»: %d" % (frag, len(found)))

    #  ОБРАБОТЧИКИ — ГОСТИНИЧНЫЕ НОМЕРА
    def on_add_room(self):
        places_text = self.r_places.get().strip()
        rooms_text = self.r_rooms.get().strip()
        if not places_text.isdigit() or not rooms_text.isdigit():
            messagebox.showwarning("Ошибка ввода",
                                   "Количество мест и комнат — целые числа.")
            return
        ok, msg = self.system.add_room(
            self.r_number.get().strip(),
            int(places_text),
            int(rooms_text),
            self.r_bathroom.get(),
            self.r_equipment.get().strip(),
        )
        self.set_status(msg)
        if ok:
            for var in (self.r_number, self.r_places, self.r_rooms, self.r_equipment):
                var.set("")
            self.r_bathroom.set(True)
            self.refresh_rooms()
        else:
            messagebox.showwarning("Не удалось добавить", msg)

    def on_delete_room(self):
        sel = self.rooms_tree.selection()
        if not sel:
            messagebox.showinfo("Удаление", "Сначала выберите номер в таблице.")
            return
        number = sel[0]
        if not messagebox.askyesno("Подтверждение", "Удалить номер %s?" % number):
            return
        ok, msg = self.system.delete_room(number)
        self.set_status(msg)
        self.refresh_rooms()
        self.refresh_stays()

    def on_clear_rooms(self):
        if not messagebox.askyesno("Подтверждение",
                                   "Очистить ВСЕ данные о гостиничных номерах?"):
            return
        self.system.clear_rooms()
        self.set_status("Данные о гостиничных номерах очищены.")
        self.refresh_rooms()

    def on_search_room_number(self):
        number = self.r_search_number.get().strip()
        room = self.system.find_room(number)
        if room is None:
            self.refresh_rooms([])
            self.set_status("Номер %s не найден." % number)
            messagebox.showinfo("Поиск", "Гостиничный номер не найден.")
        else:
            self.refresh_rooms([room])
            self.set_status("Найден номер %s (%s)." % (room.number, room.type_name()))

    def on_search_room_equip(self):
        frag = self.r_search_equip.get().strip()
        if not frag:
            self.refresh_rooms()
            return
        # Внутри ядра: прямой обход АВЛ-дерева + поиск Бойера–Мура
        found = self.system.find_rooms_by_equipment(frag)
        self.refresh_rooms(found)
        self.set_status("Найдено номеров по фрагменту «%s»: %d" % (frag, len(found)))

    #  ОБРАБОТЧИКИ — ВСЕЛЕНИЕ / ВЫСЕЛЕНИЕ
    def on_check_in(self):
        ok, msg = self.system.check_in(
            self.s_passport.get().strip(),
            self.s_room.get().strip(),
            self.s_date_in.get().strip(),
        )
        self.set_status(msg)
        if ok:
            self.s_passport.set("")
            self.s_room.set("")
            self.refresh_stays()
            self.refresh_guests()
        else:
            messagebox.showwarning("Не удалось заселить", msg)

    def on_check_out(self):
        sel = self.stays_tree.selection()
        if not sel:
            messagebox.showinfo("Выселение",
                                "Сначала выберите проживающего в таблице.")
            return
        stay = self._stay_rows.get(sel[0])
        if stay is None:
            return
        if stay.check_out != "":
            messagebox.showinfo("Выселение", "Этот постоялец уже выселен.")
            return
        ok, msg = self.system.check_out(stay.passport, stay.room_number,
                                        self.s_date_out.get().strip())
        self.set_status(msg)
        if ok:
            self.refresh_stays()
            self.refresh_guests()
        else:
            messagebox.showwarning("Не удалось выселить", msg)

    #  ДЕМО-ДАННЫЕ
    def load_demo(self):
        s = self.system
        s.register_guest("1234-567890", "Иванов Иван Иванович", 1985,
                         "г. Москва, ул. Ленина, 1", "Туризм")
        s.register_guest("2345-678901", "Петров Пётр Петрович", 1990,
                         "г. Казань, ул. Мира, 5", "Командировка")
        s.register_guest("3456-789012", "Иванова Анна Сергеевна", 1995,
                         "г. Самара, ул. Садовая, 7", "Отдых")
        s.add_room("Л101", 2, 3, True, "Телевизор, кондиционер, мини-бар, сейф")
        s.add_room("О205", 1, 1, True, "Телевизор, кондиционер")
        s.add_room("М010", 4, 1, False, "Телевизор, холодильник")
        s.add_room("П150", 2, 2, True, "Телевизор, кондиционер, фен")
        s.check_in("1234-567890", "Л101", "2026-06-01")
        s.check_in("2345-678901", "М010", "2026-06-05")

        self.refresh_guests()
        self.refresh_rooms()
        self.refresh_stays()
        self.set_status("Демонстрационные данные загружены.")

#  ТОЧКА ВХОДА

def main():
    root = tk.Tk()
    app = HotelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

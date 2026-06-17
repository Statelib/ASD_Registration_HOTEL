# -*- coding: utf-8 -*-
"""
  ИНФОРМАЦИОННАЯ СИСТЕМА «РЕГИСТРАЦИЯ ПОСТОЯЛЬЦЕВ В ГОСТИНИЦЕ»
  * Хеш-таблица             — закрытое хеширование (открытая адресация)
                            с КВАДРАТИЧНЫМ опробованием. Ключ — номер паспорта.
                            Хранит данные о ПОСТОЯЛЬЦАХ.
  * АВЛ-дерево поиска      — упорядочено по номеру гостиничного номера.
                            Хранит данные о ГОСТИНИЧНЫХ НОМЕРАХ.
                            Обход дерева — ПРЯМОЙ
  * Линейный однонаправленный список — хранит записи о ВСЕЛЕНИИ/ВЫСЕЛЕНИИ,
                            упорядочен по номеру гостиничного номера.
                            Сортировка — методом ВКЛЮЧЕНИЯ 
  * Поиск подстроки        — алгоритм БОЙЕРА–МУРА (для поиска фрагмента
                            в строке «Оборудование»).
"""
#ВАЛИДАЦИЯ ВВОДИМЫХ ДАННЫХ
def is_digit_string(s):
    """Истина, если строка s не пуста и состоит только из цифр 0..9."""
    if len(s) == 0:
        return False
    for ch in s:
        if ch < '0' or ch > '9':
            return False
    return True


def is_valid_passport(s):
    """
    Проверка формата номера паспорта: «NNNN-NNNNNN».
    4 цифры, дефис, 6 цифр. Общая длина — 11 символов.
    """
    if len(s) != 11:
        return False
    if s[4] != '-':
        return False
    # символы 0..3 — цифры, символы 5..10 — цифры
    return is_digit_string(s[0:4]) and is_digit_string(s[5:11])


# Допустимые буквы — типы гостиничных номеров.
ROOM_TYPES = {
    'Л': 'Люкс',
    'П': 'Полулюкс',
    'О': 'Одноместный',
    'М': 'Многоместный',
}


def is_valid_room_number(s):
    """
    Проверка формата номера гостиничного номера: «ANNN».
    A — буква типа (Л/П/О/М), далее 3 цифры. Общая длина — 4 символа.
    """
    if len(s) != 4:
        return False
    if s[0] not in ROOM_TYPES:
        return False
    return is_digit_string(s[1:4])


#  РАЗДЕЛ 2.  КЛАССЫ-ЗАПИСИ (хранят содержательные данные)

class Guest:
    """Запись о постояльце."""
    def __init__(self, passport, full_name, birth_year, address, purpose):
        self.passport = passport        # номер паспорта (первичный ключ)
        self.full_name = full_name      # ФИО
        self.birth_year = birth_year    # год рождения (целое)
        self.address = address          # адрес
        self.purpose = purpose          # цель прибытия


class Room:
    """Запись о гостиничном номере."""
    def __init__(self, number, places, rooms_count, has_bathroom, equipment):
        self.number = number            # номер гостиничного номера (ключ АВЛ-дерева)
        self.places = places            # количество мест (целое)
        self.rooms_count = rooms_count  # количество комнат (целое)
        self.has_bathroom = has_bathroom  # наличие санузла (логическое)
        self.equipment = equipment      # оборудование (строка)

    def type_name(self):
        """Расшифровка типа номера по первой букве."""
        return ROOM_TYPES.get(self.number[0], 'Неизвестно')


class Stay:
    """Запись о вселении/выселении постояльца."""
    def __init__(self, passport, room_number, check_in, check_out):
        self.passport = passport          # номер паспорта постояльца
        self.room_number = room_number    # номер гостиничного номера (ключ сортировки)
        self.check_in = check_in          # дата заселения (строка)
        self.check_out = check_out        # дата выселения (строка; "" — ещё проживает)

#  ХЕШ-ТАБЛИЦА
#  Закрытое хеширование (открытая адресация) с КВАДРАТИЧНЫМ опробованием.

#  Идея закрытого хеширования: все элементы хранятся в самом массиве
#  фиксированного размера. При коллизии (нужная ячейка занята) мы ищем
#  следующую свободную ячейку по формуле опробования.
#
#  Квадратичное опробование: для ключа k проверяем ячейки
#       index(i) = ( h(k) + i*i ) mod m,    i = 0, 1, 2, 3, ...
#  где h(k) — хеш-функция, m — размер таблицы.
#
#  Чтобы квадратичное опробование гарантированно находило свободную ячейку,
#  размер таблицы m берут ПРОСТЫМ числом, а коэффициент заполнения держат < 0.5.
#  (Тогда первые (m+1)/2 проб дают различные ячейки.)
#
#  Удаление: физически удалить элемент нельзя — это разорвёт цепочку
#  опробований при поиске. Поэтому используется «ленивое» удаление: ячейка
#  помечается состоянием DELETED («удалена»), но поиск через неё продолжается.

class HashTable:
    # Состояния ячеек таблицы:
    EMPTY = 0      # ячейка никогда не использовалась
    OCCUPIED = 1   # ячейка занята действующим элементом
    DELETED = 2    # элемент удалён

    def __init__(self, capacity=11):
        # capacity — простое число (важно для квадратичного опробования)
        self.capacity = capacity
        self.size = 0                          # число занятых (OCCUPIED) ячеек
        self.keys = [None] * capacity          # массив ключей
        self.values = [None] * capacity        # массив значений (объектов Guest)
        self.states = [self.EMPTY] * capacity  # массив состояний ячеек

    # ----- Вспомогательные функции работы с простыми числами -----
    @staticmethod
    def _is_prime(n):
        """Проверка, является ли число n простым."""
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        d = 3
        while d * d <= n:
            if n % d == 0:
                return False
            d += 2
        return True

    @classmethod
    def _next_prime(cls, n):
        """Найти ближайшее простое число, не меньшее n."""
        while not cls._is_prime(n):
            n += 1
        return n

    #Хеш-функция
    def _hash(self, key):
        """
        Полиномиальная хеш-функция для строки (схема Горнера, основание 31).
        Возвращает индекс в диапазоне [0, capacity).
        """
        h = 0
        for ch in key:
            h = (h * 31 + ord(ch)) % self.capacity
        return h

    #Перехеширование (увеличение таблицы)
    def _rehash(self):
        """
        Увеличить таблицу (примерно в 2 раза до простого числа) и
        заново вставить все действующие элементы. Вызывается, когда
        коэффициент заполнения приближается к 0.5.
        """
        old_keys = self.keys
        old_values = self.values
        old_states = self.states

        new_capacity = self._next_prime(self.capacity * 2 + 1)
        self.capacity = new_capacity
        self.keys = [None] * new_capacity
        self.values = [None] * new_capacity
        self.states = [self.EMPTY] * new_capacity
        self.size = 0

        # Переносим только действующие (OCCUPIED) элементы.
        for j in range(len(old_keys)):
            if old_states[j] == self.OCCUPIED:
                self.insert(old_keys[j], old_values[j])

    # ----- Вставка -----
    def insert(self, key, value):
        """
        Вставить пару (ключ, значение). Если ключ уже существует —
        обновить значение. Возвращает True при добавлении нового элемента.
        """
        # Поддерживаем коэффициент заполнения < 0.5 (требование к
        # квадратичному опробованию). Если близко — перехешируем.
        if (self.size + 1) * 2 >= self.capacity:
            self._rehash()

        h = self._hash(key)
        first_deleted = -1   # запомним первую встреченную «удалённую» ячейку

        for i in range(self.capacity):
            idx = (h + i * i) % self.capacity
            state = self.states[idx]

            if state == self.EMPTY:
                # Дошли до пустой ячейки — значит, такого ключа в таблице нет.
                # Вставляем либо в первую «удалённую» ячейку (если была),
                # либо в эту пустую.
                target = first_deleted if first_deleted != -1 else idx
                self.keys[target] = key
                self.values[target] = value
                self.states[target] = self.OCCUPIED
                self.size += 1
                return True

            elif state == self.OCCUPIED:
                # Ключ уже есть — обновляем значение.
                if self.keys[idx] == key:
                    self.values[idx] = value
                    return False

            else:  # DELETED
                if first_deleted == -1:
                    first_deleted = idx

        # Если цикл завершился (теоретически почти невозможно при load<0.5),
        # но осталась «удалённая» ячейка — используем её.
        if first_deleted != -1:
            self.keys[first_deleted] = key
            self.values[first_deleted] = value
            self.states[first_deleted] = self.OCCUPIED
            self.size += 1
            return True

        # Таблица переполнена — перехешируем и повторяем.
        self._rehash()
        return self.insert(key, value)

    # ----- Поиск -----
    def search(self, key):
        """Вернуть значение по ключу или None, если ключ не найден."""
        h = self._hash(key)
        for i in range(self.capacity):
            idx = (h + i * i) % self.capacity
            state = self.states[idx]
            if state == self.EMPTY:
                # Пустая ячейка означает конец цепочки опробований — ключа нет.
                return None
            if state == self.OCCUPIED and self.keys[idx] == key:
                return self.values[idx]
            # Состояние DELETED — продолжаем поиск дальше.
        return None

    #Удаление
    def delete(self, key):
        """
        Удалить элемент по ключу («ленивое» удаление — ячейка помечается
        как DELETED). Возвращает True, если элемент был найден и удалён.
        """
        h = self._hash(key)
        for i in range(self.capacity):
            idx = (h + i * i) % self.capacity
            state = self.states[idx]
            if state == self.EMPTY:
                return False
            if state == self.OCCUPIED and self.keys[idx] == key:
                self.states[idx] = self.DELETED
                self.keys[idx] = None
                self.values[idx] = None
                self.size -= 1
                return True
        return False

    #Полный перебор
    def items(self):
        """Список всех пар (ключ, значение) действующих элементов."""
        result = []
        for j in range(self.capacity):
            if self.states[j] == self.OCCUPIED:
                result.append((self.keys[j], self.values[j]))
        return result

    def clear(self):
        """Полная очистка таблицы."""
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.states = [self.EMPTY] * self.capacity
        self.size = 0


#  АВЛ-ДЕРЕВО ПОИСКА
#  Сбалансированное двоичное дерево поиска. Ключ — номер гостиничного номера.
#  Обход — ПРЯМОЙ (preorder): корень -> левое поддерево -> правое поддерево.
#
#  АВЛ-дерево — двоичное дерево поиска, в котором для КАЖДОГО узла высоты
#  левого и правого поддеревьев отличаются не более чем на 1 (баланс-фактор
#  в {-1, 0, +1}). После вставки/удаления баланс восстанавливается
#  поворотами (малыми и большими).

class AVLNode:
    """Узел АВЛ-дерева."""
    def __init__(self, key, value):
        self.key = key          # ключ (номер гостиничного номера)
        self.value = value      # значение (объект Room)
        self.left = None        # левое поддерево
        self.right = None       # правое поддерево
        self.height = 1         # высота узла (лист = 1)


class AVLTree:
    def __init__(self):
        self.root = None

    #Служебные функции высоты/баланса
    def _height(self, node):
        return node.height if node else 0

    def _update_height(self, node):
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node):
        """Баланс-фактор = высота(левое) - высота(правое)."""
        return self._height(node.left) - self._height(node.right) if node else 0

    # ----- Повороты -----
    def _rotate_right(self, y):
        """Правый (малый) поворот вокруг узла y."""
        x = y.left
        t2 = x.right
        x.right = y
        y.left = t2
        self._update_height(y)
        self._update_height(x)
        return x   # новый корень поддерева

    def _rotate_left(self, x):
        """Левый (малый) поворот вокруг узла x."""
        y = x.right
        t2 = y.left
        y.left = x
        x.right = t2
        self._update_height(x)
        self._update_height(y)
        return y   # новый корень поддерева

    def _balance(self, node):
        """Восстановить баланс узла после вставки/удаления."""
        self._update_height(node)
        bf = self._balance_factor(node)

        # Левый перевес
        if bf > 1:
            if self._balance_factor(node.left) < 0:
                # Случай Лево-Право: сначала левый поворот левого потомка
                node.left = self._rotate_left(node.left)
            # Случай Лево-Лево: правый поворот
            return self._rotate_right(node)

        # Правый перевес
        if bf < -1:
            if self._balance_factor(node.right) > 0:
                # Случай Право-Лево: сначала правый поворот правого потомка
                node.right = self._rotate_right(node.right)
            # Случай Право-Право: левый поворот
            return self._rotate_left(node)

        return node  # дерево сбалансировано

    #Вставка
    def insert(self, key, value):
        """Вставить (или обновить) элемент. True — если добавлен новый."""
        inserted = [False]   # «обёртка», чтобы вернуть факт вставки из рекурсии
        self.root = self._insert(self.root, key, value, inserted)
        return inserted[0]

    def _insert(self, node, key, value, inserted):
        if node is None:
            inserted[0] = True
            return AVLNode(key, value)
        if key < node.key:
            node.left = self._insert(node.left, key, value, inserted)
        elif key > node.key:
            node.right = self._insert(node.right, key, value, inserted)
        else:
            node.value = value   # ключ уже есть — обновляем значение
            return node
        return self._balance(node)

    #Поиск
    def search(self, key):
        """Итеративный поиск значения по ключу. None — если не найдено."""
        node = self.root
        while node:
            if key == node.key:
                return node.value
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        return None

    #Удаление
    def _min_node(self, node):
        """Узел с минимальным ключом в поддереве (самый левый)."""
        while node.left:
            node = node.left
        return node

    def delete(self, key):
        """Удалить элемент по ключу. True — если был найден и удалён."""
        deleted = [False]
        self.root = self._delete(self.root, key, deleted)
        return deleted[0]

    def _delete(self, node, key, deleted):
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key, deleted)
        elif key > node.key:
            node.right = self._delete(node.right, key, deleted)
        else:
            deleted[0] = True
            # Узел найден. Три случая:
            if node.left is None:          # нет левого потомка
                return node.right
            elif node.right is None:       # нет правого потомка
                return node.left
            else:
                # Два потомка: заменяем узел его «преемником»
                # (минимальный ключ в правом поддереве), затем удаляем преемника.
                successor = self._min_node(node.right)
                node.key = successor.key
                node.value = successor.value
                node.right = self._delete(node.right, successor.key, [False])
        return self._balance(node)

    # ПРЯМОЙ обход (preorder): корень -> левое -> правое
    def preorder(self):
        """Вернуть список (ключ, значение) в порядке прямого обхода."""
        result = []
        self._preorder(self.root, result)
        return result

    def _preorder(self, node, result):
        if node:
            result.append((node.key, node.value))   # сначала КОРЕНЬ
            self._preorder(node.left, result)        # затем ЛЕВОЕ поддерево
            self._preorder(node.right, result)       # затем ПРАВОЕ поддерево

    def clear(self):
        self.root = None

    def is_empty(self):
        return self.root is None


#ЛИНЕЙНЫЙ ОДНОНАПРАВЛЕННЫЙ СПИСОК + СОРТИРОВКА ВКЛЮЧЕНИЕМ
#Хранит записи о вселении/выселении, упорядочен по номеру гост. номера.

class ListNode:
    """Узел односвязного списка (хранит ссылку только на СЛЕДУЮЩИЙ элемент)."""
    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None    # голова списка
        self.count = 0      # количество элементов

    def append(self, value):
        """Добавить элемент в конец списка (за O(n))."""
        new_node = ListNode(value)
        if self.head is None:
            self.head = new_node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node
        self.count += 1

    def insertion_sort(self, key_func):
        """
        СОРТИРОВКА ВКЛЮЧЕНИЕМ (insertion sort) для односвязного списка
        по возрастанию ключа key_func(value).

        формируем новый «отсортированный» список. Берём по одному
        узлу из исходного списка и ВКЛЮЧАЕМ (вставляем) его на правильное
        место в уже отсортированной части.
        """
        sorted_head = None      # голова отсортированной части
        cur = self.head
        while cur is not None:
            nxt = cur.next      # запомнить следующий узел до перецепления
            key = key_func(cur.value)

            # Вставка узла cur в отсортированный список:
            if sorted_head is None or key_func(sorted_head.value) >= key:
                # в начало отсортированной части
                cur.next = sorted_head
                sorted_head = cur
            else:
                # ищем позицию: первый узел, после которого ключ >= нашего
                p = sorted_head
                while p.next is not None and key_func(p.next.value) < key:
                    p = p.next
                cur.next = p.next
                p.next = cur

            cur = nxt
        self.head = sorted_head

    def find(self, predicate):
        """Первый элемент, удовлетворяющий условию predicate, или None."""
        cur = self.head
        while cur:
            if predicate(cur.value):
                return cur.value
            cur = cur.next
        return None

    def find_all(self, predicate):
        """Все элементы, удовлетворяющие условию predicate."""
        result = []
        cur = self.head
        while cur:
            if predicate(cur.value):
                result.append(cur.value)
            cur = cur.next
        return result

    def remove_all(self, predicate):
        """
        Удалить ВСЕ элементы, удовлетворяющие predicate.
        Возвращает количество удалённых элементов.
        """
        removed = 0
        # Удаление из начала, пока голова подходит под условие
        while self.head is not None and predicate(self.head.value):
            self.head = self.head.next
            self.count -= 1
            removed += 1
        # Удаление из середины/конца
        prev = self.head
        while prev is not None and prev.next is not None:
            if predicate(prev.next.value):
                prev.next = prev.next.next
                self.count -= 1
                removed += 1
            else:
                prev = prev.next
        return removed

    def to_list(self):
        """Преобразовать список в обычный массив (для перебора)."""
        result = []
        cur = self.head
        while cur:
            result.append(cur.value)
            cur = cur.next
        return result

    def clear(self):
        self.head = None
        self.count = 0


#  АЛГОРИТМ ПОИСКА ПОДСТРОКИ — БОЙЕРА–МУРА
#  Используется для поиска фрагмента в строке «Оборудование».
#
#  Алгоритм Бойера–Мура сравнивает образец (pattern) с текстом СПРАВА НАЛЕВО
#  и при несовпадении сдвигает образец вправо сразу на несколько позиций,
#  используя две эвристики:
#    1) «плохого символа» (bad character) — учитывает символ текста,
#       на котором произошло несовпадение;
#    2) «хорошего суффикса» (good suffix) — учитывает уже совпавший суффикс
#       образца.
#  Из двух предложенных сдвигов берётся максимальный.

def _bad_char_table(pattern):
    """
    Таблица «плохого символа»: для каждого символа образца — индекс его
    ПОСЛЕДНЕГО вхождения в образец. Реализована словарём (подходит для
    любых символов, в т.ч. кириллицы).
    """
    table = {}
    for i in range(len(pattern)):
        table[pattern[i]] = i
    return table


def _good_suffix_tables(pattern):
    """
    Предобработка эвристики «хорошего суффикса».
    Возвращает массив shift (сдвиги) длиной m+1.
    Классическая реализация в два прохода (strong good suffix).
    """
    m = len(pattern)
    shift = [0] * (m + 1)
    border = [0] * (m + 1)   # позиции границ (border positions)

    # Проход 1: случай, когда хороший суффикс встречается в образце
    i = m
    j = m + 1
    border[i] = j
    while i > 0:
        while j <= m and pattern[i - 1] != pattern[j - 1]:
            if shift[j] == 0:
                shift[j] = j - i
            j = border[j]
        i -= 1
        j -= 1
        border[i] = j

    #Проход 2: случай, когда в образце есть только ЧАСТЬ суффикса
    j = border[0]
    for i in range(m + 1):
        if shift[i] == 0:
            shift[i] = j
        if i == j:
            j = border[j]

    return shift


def boyer_moore_find_first(text, pattern):
    """
    Поиск ПЕРВОГО вхождения образца pattern в текст text алгоритмом
    Бойера–Мура. Возвращает индекс начала вхождения или -1.
    """
    n = len(text)
    m = len(pattern)
    if m == 0:
        return 0          # пустой образец считаем найденным в начале
    if m > n:
        return -1

    bad = _bad_char_table(pattern)
    good_shift = _good_suffix_tables(pattern)

    s = 0   # величина сдвига образца относительно текста
    while s <= n - m:
        j = m - 1
        # Сравниваем справа налево
        while j >= 0 and pattern[j] == text[s + j]:
            j -= 1

        if j < 0:
            return s      # полное совпадение — образец найден на позиции s
        else:
            # Сдвиг по «плохому символу»:
            last = bad.get(text[s + j], -1)
            bc_shift = j - last
            # Сдвиг по «хорошему суффиксу»:
            gs_shift = good_shift[j + 1]
            # Берём максимальный безопасный сдвиг (но не меньше 1)
            s += max(1, bc_shift, gs_shift)

    return -1


def boyer_moore_contains(text, pattern):
    """
    Содержит ли text подстроку pattern (поиск без учёта регистра).
    Используется при поиске номеров по фрагменту «Оборудования».
    """
    return boyer_moore_find_first(text.lower(), pattern.lower()) != -1


#ОСНОВНОЙ КЛАСС СИСТЕМЫ — связывает все структуры данных

class HotelSystem:
    def __init__(self):
        self.guests = HashTable()   # постояльцы (ключ — номер паспорта)
        self.rooms = AVLTree()      # гост. номера (ключ — номер номера)
        self.stays = LinkedList()   # вселения/выселения (по номеру номера)

    #ПОСТОЯЛЬЦЫ

    def register_guest(self, passport, full_name, birth_year, address, purpose):
        """Регистрация нового постояльца. (False, msg) при ошибке."""
        if not is_valid_passport(passport):
            return False, "Неверный формат номера паспорта (нужно NNNN-NNNNNN)."
        if self.guests.search(passport) is not None:
            return False, "Постоялец с таким номером паспорта уже зарегистрирован."
        guest = Guest(passport, full_name, birth_year, address, purpose)
        self.guests.insert(passport, guest)
        return True, "Постоялец зарегистрирован."

    def delete_guest(self, passport):
        """Удаление постояльца. Заодно удаляются его записи о вселении."""
        if self.guests.search(passport) is None:
            return False, "Постоялец не найден."
        self.guests.delete(passport)
        n = self.stays.remove_all(lambda st: st.passport == passport)
        return True, "Постоялец удалён. Удалено связанных записей о вселении: %d." % n

    def list_guests(self):
        """Все постояльцы."""
        return [v for _, v in self.guests.items()]

    def clear_guests(self):
        self.guests.clear()

    def find_guest_by_passport(self, passport):
        """
        Поиск постояльца по номеру паспорта.
        Возвращает (guest, room_number) — где room_number это номер,
        в котором постоялец проживает СЕЙЧАС (или None).
        """
        guest = self.guests.search(passport)
        if guest is None:
            return None, None
        active = self.stays.find(
            lambda st: st.passport == passport and st.check_out == ""
        )
        room_number = active.room_number if active else None
        return guest, room_number

    def find_guests_by_name(self, name_fragment):
        """
        Поиск постояльцев по ФИО (по вхождению фрагмента, без учёта регистра).
        Возвращает список постояльцев.
        """
        frag = name_fragment.lower()
        result = []
        for _, guest in self.guests.items():
            # Используем тот же алгоритм Бойера–Мура для поиска подстроки
            if boyer_moore_contains(guest.full_name, frag):
                result.append(guest)
        return result

    #ГОСТИНИЧНЫЕ НОМЕРА

    def add_room(self, number, places, rooms_count, has_bathroom, equipment):
        """Добавление гостиничного номера. (False, msg) при ошибке."""
        if not is_valid_room_number(number):
            return False, "Неверный формат номера (нужно ANNN, A in {Л,П,О,М})."
        if self.rooms.search(number) is not None:
            return False, "Гостиничный номер с таким номером уже существует."
        room = Room(number, places, rooms_count, has_bathroom, equipment)
        self.rooms.insert(number, room)
        return True, "Гостиничный номер добавлен."

    def delete_room(self, number):
        """Удаление номера. Заодно удаляются связанные записи о вселении."""
        if self.rooms.search(number) is None:
            return False, "Гостиничный номер не найден."
        self.rooms.delete(number)
        n = self.stays.remove_all(lambda st: st.room_number == number)
        return True, "Номер удалён. Удалено связанных записей о вселении: %d." % n

    def list_rooms(self):
        """Все номера — в порядке ПРЯМОГО обхода АВЛ-дерева."""
        return [v for _, v in self.rooms.preorder()]

    def clear_rooms(self):
        self.rooms.clear()

    def find_room(self, number):
        """Поиск гостиничного номера по его номеру."""
        return self.rooms.search(number)

    def find_rooms_by_equipment(self, fragment):
        """
        Поиск номеров по фрагменту «Оборудования».
        Реализация согласно заданию:
          1) систематический ПРЯМОЙ обход АВЛ-дерева;
          2) для каждого номера — поиск фрагмента в строке «Оборудование»
             алгоритмом БОЙЕРА–МУРА.
        """
        result = []
        for _, room in self.rooms.preorder():      # прямой обход дерева
            if boyer_moore_contains(room.equipment, fragment):  # Бойер–Мур
                result.append(room)
        return result

    #ВСЕЛЕНИЕ / ВЫСЕЛЕНИЕ

    def occupied_places(self, room_number):
        """Сколько мест в номере занято сейчас (активные вселения)."""
        active = self.stays.find_all(
            lambda st: st.room_number == room_number and st.check_out == ""
        )
        return len(active)

    def check_in(self, passport, room_number, date_in):
        """Регистрация вселения постояльца."""
        guest = self.guests.search(passport)
        if guest is None:
            return False, "Постоялец с таким паспортом не зарегистрирован."
        room = self.rooms.search(room_number)
        if room is None:
            return False, "Гостиничный номер не найден."

        # Постоялец не должен быть уже где-то заселён
        active = self.stays.find(
            lambda st: st.passport == passport and st.check_out == ""
        )
        if active is not None:
            return False, "Постоялец уже проживает в номере %s." % active.room_number

        # Проверка наличия свободных мест
        if self.occupied_places(room_number) >= room.places:
            return False, "В номере %s нет свободных мест." % room_number

        stay = Stay(passport, room_number, date_in, "")
        # Добавляем в список и пересортировываем ВКЛЮЧЕНИЕМ по номеру номера
        self.stays.append(stay)
        self.stays.insertion_sort(lambda st: st.room_number)
        return True, "Вселение зарегистрировано."

    def check_out(self, passport, room_number, date_out):
        """Регистрация выселения постояльца (проставляется дата выселения)."""
        stay = self.stays.find(
            lambda st: st.passport == passport
            and st.room_number == room_number
            and st.check_out == ""
        )
        if stay is None:
            return False, "Активная запись о вселении не найдена."
        stay.check_out = date_out
        return True, "Выселение зарегистрировано."

    def list_stays(self):
        """Все записи о вселении/выселении (список уже отсортирован)."""
        return self.stays.to_list()

#КОНСОЛЬНЫЙ ИНТЕРФЕЙС (ввод/вывод)

def input_line(prompt):
    """Ввод строки с обработкой конца файла (для тестов через stdin)."""
    try:
        return input(prompt)
    except EOFError:
        return "0"


def read_int(prompt):
    """Чтение целого числа с проверкой."""
    while True:
        s = input_line(prompt).strip()
        if s.lstrip('-').isdigit():
            return int(s)
        print("  ! Введите целое число.")


def read_bool(prompt):
    """Чтение логического значения (да/нет)."""
    while True:
        s = input_line(prompt).strip().lower()
        if s in ('да', 'д', 'yes', 'y', '1', '+'):
            return True
        if s in ('нет', 'н', 'no', 'n', '0', '-'):
            return False
        print("  ! Введите 'да' или 'нет'.")


def print_guest(g):
    room_info = ""
    print("  Паспорт:        %s" % g.passport)
    print("  ФИО:            %s" % g.full_name)
    print("  Год рождения:   %d" % g.birth_year)
    print("  Адрес:          %s" % g.address)
    print("  Цель прибытия:  %s" % g.purpose)


def print_room(r):
    print("  Номер:          %s (%s)" % (r.number, r.type_name()))
    print("  Кол-во мест:    %d" % r.places)
    print("  Кол-во комнат:  %d" % r.rooms_count)
    print("  Санузел:        %s" % ("есть" if r.has_bathroom else "нет"))
    print("  Оборудование:   %s" % r.equipment)


def print_stay(s):
    out = s.check_out if s.check_out else "— (проживает)"
    print("  Номер: %s | Паспорт: %s | Заселение: %s | Выселение: %s"
          % (s.room_number, s.passport, s.check_in, out))


def load_demo(system):
    """Загрузка демонстрационных данных для проверки."""
    system.register_guest("1234-567890", "Иванов Иван Иванович", 1985,
                          "г. Москва, ул. Ленина, 1", "Туризм")
    system.register_guest("2345-678901", "Петров Пётр Петрович", 1990,
                          "г. Казань, ул. Мира, 5", "Командировка")
    system.register_guest("3456-789012", "Иванова Анна Сергеевна", 1995,
                          "г. Самара, ул. Садовая, 7", "Отдых")

    system.add_room("Л101", 2, 3, True, "Телевизор, кондиционер, мини-бар, сейф")
    system.add_room("О205", 1, 1, True, "Телевизор, кондиционер")
    system.add_room("М010", 4, 1, False, "Телевизор, холодильник")
    system.add_room("П150", 2, 2, True, "Телевизор, кондиционер, фен")

    system.check_in("1234-567890", "Л101", "2026-06-01")
    system.check_in("2345-678901", "М010", "2026-06-05")
    print(">> Демонстрационные данные загружены.")


MENU = """
================ РЕГИСТРАЦИЯ ПОСТОЯЛЬЦЕВ В ГОСТИНИЦЕ ================
--- ПОСТОЯЛЬЦЫ ---
 1. Регистрация нового постояльца
 2. Удаление данных о постояльце
 3. Просмотр всех постояльцев
 4. Очистка данных о постояльцах
 5. Поиск постояльца по номеру паспорта
 6. Поиск постояльца по ФИО
--- ГОСТИНИЧНЫЕ НОМЕРА ---
 7. Добавление нового гостиничного номера
 8. Удаление гостиничного номера
 9. Просмотр всех гостиничных номеров
10. Очистка данных о гостиничных номерах
11. Поиск гостиничного номера по номеру
12. Поиск номера по фрагменту «Оборудования»
--- ВСЕЛЕНИЕ / ВЫСЕЛЕНИЕ ---
13. Регистрация вселения постояльца
14. Регистрация выселения постояльца
15. Просмотр записей о вселении/выселении
--- ПРОЧЕЕ ---
16. Загрузить демонстрационные данные
 0. Выход
==================================================================="""


def main():
    system = HotelSystem()

    while True:
        print(MENU)
        choice = input_line("Выберите пункт: ").strip()

        # ------------------------- ПОСТОЯЛЬЦЫ -------------------------
        if choice == "1":
            passport = input_line("Номер паспорта (NNNN-NNNNNN): ").strip()
            name = input_line("ФИО: ").strip()
            year = read_int("Год рождения: ")
            address = input_line("Адрес: ").strip()
            purpose = input_line("Цель прибытия: ").strip()
            ok, msg = system.register_guest(passport, name, year, address, purpose)
            print(">>", msg)

        elif choice == "2":
            passport = input_line("Номер паспорта удаляемого постояльца: ").strip()
            ok, msg = system.delete_guest(passport)
            print(">>", msg)

        elif choice == "3":
            guests = system.list_guests()
            if not guests:
                print(">> Постояльцев нет.")
            else:
                print(">> Зарегистрированные постояльцы (%d):" % len(guests))
                for g in guests:
                    print("-" * 40)
                    print_guest(g)

        elif choice == "4":
            system.clear_guests()
            print(">> Данные о постояльцах очищены.")

        elif choice == "5":
            passport = input_line("Номер паспорта для поиска: ").strip()
            guest, room_number = system.find_guest_by_passport(passport)
            if guest is None:
                print(">> Постоялец не найден.")
            else:
                print(">> Найден постоялец:")
                print_guest(guest)
                if room_number:
                    print("  Проживает в номере: %s" % room_number)
                else:
                    print("  В данный момент нигде не проживает.")

        elif choice == "6":
            frag = input_line("ФИО (или его часть) для поиска: ").strip()
            found = system.find_guests_by_name(frag)
            if not found:
                print(">> Постояльцы не найдены.")
            else:
                print(">> Найдено постояльцев: %d" % len(found))
                for g in found:
                    print("  Паспорт: %s | ФИО: %s" % (g.passport, g.full_name))

        # --------------------- ГОСТИНИЧНЫЕ НОМЕРА ---------------------
        elif choice == "7":
            print("Тип: Л-люкс, П-полулюкс, О-одноместный, М-многоместный")
            number = input_line("Номер (ANNN): ").strip()
            places = read_int("Количество мест: ")
            rooms_count = read_int("Количество комнат: ")
            has_bathroom = read_bool("Наличие санузла (да/нет): ")
            equipment = input_line("Оборудование: ").strip()
            ok, msg = system.add_room(number, places, rooms_count,
                                      has_bathroom, equipment)
            print(">>", msg)

        elif choice == "8":
            number = input_line("Номер удаляемого гост. номера: ").strip()
            ok, msg = system.delete_room(number)
            print(">>", msg)

        elif choice == "9":
            rooms = system.list_rooms()
            if not rooms:
                print(">> Гостиничных номеров нет.")
            else:
                print(">> Гостиничные номера (%d), прямой обход дерева:" % len(rooms))
                for r in rooms:
                    print("-" * 40)
                    print_room(r)

        elif choice == "10":
            system.clear_rooms()
            print(">> Данные о гостиничных номерах очищены.")

        elif choice == "11":
            number = input_line("Номер для поиска: ").strip()
            room = system.find_room(number)
            if room is None:
                print(">> Гостиничный номер не найден.")
            else:
                print(">> Найден гостиничный номер:")
                print_room(room)

        elif choice == "12":
            frag = input_line("Фрагмент «Оборудования»: ").strip()
            found = system.find_rooms_by_equipment(frag)
            if not found:
                print(">> Гостиничные номера не найдены.")
            else:
                print(">> Найдено номеров: %d" % len(found))
                for r in found:
                    print("  Номер: %s | Мест: %d | Комнат: %d | Оборудование: %s"
                          % (r.number, r.places, r.rooms_count, r.equipment))

        # ---------------------- ВСЕЛЕНИЕ / ВЫСЕЛЕНИЕ ------------------
        elif choice == "13":
            passport = input_line("Номер паспорта: ").strip()
            number = input_line("Номер гост. номера: ").strip()
            date_in = input_line("Дата заселения: ").strip()
            ok, msg = system.check_in(passport, number, date_in)
            print(">>", msg)

        elif choice == "14":
            passport = input_line("Номер паспорта: ").strip()
            number = input_line("Номер гост. номера: ").strip()
            date_out = input_line("Дата выселения: ").strip()
            ok, msg = system.check_out(passport, number, date_out)
            print(">>", msg)

        elif choice == "15":
            stays = system.list_stays()
            if not stays:
                print(">> Записей о вселении/выселении нет.")
            else:
                print(">> Записи (%d), упорядочены по номеру номера:" % len(stays))
                for s in stays:
                    print_stay(s)

        # ----------------------------- ПРОЧЕЕ ------------------------
        elif choice == "16":
            load_demo(system)

        elif choice == "0":
            print(">> Завершение работы.")
            break

        else:
            print(">> Неизвестный пункт меню.")


if __name__ == "__main__":
    main()

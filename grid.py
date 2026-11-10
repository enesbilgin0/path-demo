"""
grid.py
-------
Labirent ızgarasını (grid) temsil eden `Grid` sınıfı.

Grid, duvarları bir küme (set) içinde tutar; başlangıç ve hedef düğümlerinin
konumlarını saklar. Harita şablonları (preset engel senaryosu ve rastgele
labirent) burada üretilir ve üretilen her harita çözülebilir olacak şekilde
BFS ile doğrulanır.
"""

import random
from collections import deque

import config


class Grid:
    def __init__(self, rows=config.ROWS, cols=config.COLS):
        self.rows = rows
        self.cols = cols
        self.walls = set()                 # (satir, sutun) duvar hücreleri
        self.start = (rows // 2, 3)         # başlangıç düğümü
        self.goal = (rows // 2, cols - 4)   # hedef düğümü

    # ------------------------------------------------------------------ #
    # Temel sorgular
    # ------------------------------------------------------------------ #
    def in_bounds(self, cell):
        """Hücre grid sınırları içinde mi?"""
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_wall(self, cell):
        return cell in self.walls

    def passable(self, cell):
        """Hücre grid içinde ve duvar değilse geçilebilirdir."""
        return self.in_bounds(cell) and cell not in self.walls

    def neighbors(self, cell):
        """4 yönlü (yukarı/aşağı/sol/sağ) geçilebilir komşuları üretir."""
        r, c = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if self.passable(n):
                yield n

    # ------------------------------------------------------------------ #
    # Düzenleme
    # ------------------------------------------------------------------ #
    def add_wall(self, cell):
        """Başlangıç/hedef hariç verilen hücreye duvar ekler."""
        if self.in_bounds(cell) and cell != self.start and cell != self.goal:
            self.walls.add(cell)

    def remove_wall(self, cell):
        self.walls.discard(cell)

    def set_start(self, cell):
        if self.in_bounds(cell) and cell != self.goal and cell not in self.walls:
            self.start = cell

    def set_goal(self, cell):
        if self.in_bounds(cell) and cell != self.start and cell not in self.walls:
            self.goal = cell

    def clear_walls(self):
        self.walls.clear()

    def reset(self):
        """Haritayı tamamen başlangıç durumuna döndürür."""
        self.walls.clear()
        self.start = (self.rows // 2, 3)
        self.goal = (self.rows // 2, self.cols - 4)

    # ------------------------------------------------------------------ #
    # Çözülebilirlik kontrolü (hızlı BFS)
    # ------------------------------------------------------------------ #
    def has_path(self):
        """Başlangıçtan hedefe bir yol var mı? (hızlı BFS)"""
        if self.start in self.walls or self.goal in self.walls:
            return False
        frontier = deque([self.start])
        seen = {self.start}
        while frontier:
            cur = frontier.popleft()
            if cur == self.goal:
                return True
            for n in self.neighbors(cur):
                if n not in seen:
                    seen.add(n)
                    frontier.append(n)
        return False

    # ------------------------------------------------------------------ #
    # Harita şablonları
    # ------------------------------------------------------------------ #
    def preset_obstacles(self):
        """
        "8+ Engel Senaryosu": Başlangıç ve hedef arasına, ajanın etrafından
        dolaşmak zorunda kalacağı en az 8-10 adet AYRIK engel bloğu yerleştirir.
        Yerleşim çözülebilir kalacak biçimde elle tasarlanmıştır.
        """
        self.walls.clear()
        self.start = (self.rows // 2, 3)       # (12, 3)
        self.goal = (self.rows // 2, self.cols - 4)  # (12, 46)

        # Her blok (r0, c0, r1, c1) kapsayan dikdörtgen olarak tanımlanır.
        blocks = [
            (2, 9, 14, 9),     # 1: üst-sol dikey çubuk (altta geçiş bırakır)
            (10, 13, 24, 13),  # 2: dikey çubuk (üstte geçiş bırakır)
            (3, 17, 7, 20),    # 3: dikdörtgen blok (üst)
            (14, 17, 18, 20),  # 4: dikdörtgen blok (alt)
            (0, 24, 12, 24),   # 5: dikey çubuk (altta geçiş bırakır)
            (16, 27, 22, 30),  # 6: dikdörtgen blok (sağ-alt)
            (2, 30, 7, 33),    # 7: dikdörtgen blok (sağ-üst)
            (6, 36, 24, 36),   # 8: uzun dikey çubuk (üstte geçiş bırakır)
            (9, 40, 13, 43),   # 9: dikdörtgen blok (orta-sağ)
            (18, 42, 20, 45),  # 10: küçük blok (sağ-alt)
        ]
        for (r0, c0, r1, c1) in blocks:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    self.add_wall((r, c))

        # Güvenlik: tasarım çözülebilir olmalı; değilse 2. çubuğu biraz aç.
        if not self.has_path():
            for r in range(10, 13):
                self.remove_wall((r, 13))

    def random_maze(self, density=0.28):
        """
        "Rastgele Labirent": Rastgele engel dağılımı üretir ve üretilen
        haritanın ÇÖZÜLEBİLİR olduğunu BFS ile doğrular. Çözülemezse yoğunluğu
        azaltarak birkaç kez yeniden dener.
        """
        for _ in range(80):
            self.walls.clear()
            for r in range(self.rows):
                for c in range(self.cols):
                    cell = (r, c)
                    if cell == self.start or cell == self.goal:
                        continue
                    if random.random() < density:
                        self.walls.add(cell)
            # Başlangıç ve hedefin hemen çevresini biraz açarak nefes aldır.
            for cell in (self.start, self.goal):
                for n in ((cell[0] + d[0], cell[1] + d[1])
                          for d in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                    self.walls.discard(n)
            if self.has_path():
                return
            density = max(0.12, density - 0.03)
        # Son çare: duvarları temizle (her zaman çözülebilir).
        self.walls.clear()

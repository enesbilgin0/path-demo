"""
main.py
-------
"Labirentte Yol Bulan ve Dinamik Engellerden Kaçan Ajan"
(Hybrid Pathfinding & Dynamic Obstacle Avoidance Visualizer)

Çalıştırma:
    pip install -r requirements.txt
    python main.py

Kontroller
----------
Fare:
    Sol tık / sürükle : Duvar ekle
    Sağ tık / sürükle : Duvar sil
    Başlangıç/Hedef düğümünü tutup sürükleyerek taşı (ajan hareketsizken)

Klavye:
    1 : BFS çalıştır        2 : A* çalıştır        3 : Hibrit modu başlat/durdur
    C : Yolu temizle        R : Rastgele labirent  P : 8+ engel senaryosu
    Boşluk : Hibrit modu başlat/durdur
    + / -  : Ajan hızını artır / azalt       ESC : Çıkış

Modlar
------
* BFS   : Dalga yayılımını ve bulunan en kısa yolu animasyonla çizer.
* A*    : Manhattan sezgiseliyle yönlendirilmiş aramayı animasyonla çizer.
* Hibrit: BFS ile küresel (global) rota çıkarılır; ajan rota üzerinde ilerlerken
          önüne eklenen duvarları fark edince, bütün haritayı yeniden taramak
          yerine yerel bir A* (Local Repair) ile engelin etrafından dolaşan
          turuncu bir yama üretir ve yoluna devam eder.
"""

import time

import pygame

import config
import algorithms as algo
from grid import Grid
from ui import Button, draw_sidebar_bg, draw_telemetry

C = config.COLORS


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Labirent Ajanı — Hibrit Yol Bulma & Dinamik Engelden Kaçış")
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fontlar (Pygame yerleşik / sistem monospace — harici dosya yok)
        mono = "Menlo,Consolas,DejaVu Sans Mono,monospace"
        sans = "Helvetica Neue,Arial,DejaVu Sans,sans-serif"
        self.fonts = {
            "title": pygame.font.SysFont(sans, 22, bold=True),
            "sub":   pygame.font.SysFont(sans, 13),
            "btn":   pygame.font.SysFont(sans, 13, bold=True),
            "body":  pygame.font.SysFont(sans, 13, bold=True),
            "small": pygame.font.SysFont(mono, 12),
        }

        self.grid = Grid()

        # --- Çalışma durumu ---
        self.mode = "BFS"          # BFS | A* | HİBRİT
        self.phase = "idle"        # idle | searching | tracing | running | done | blocked
        self.status = "Hazır"
        self.status_ok = True
        self.speed = config.AGENT_SPEED_DEFAULT

        # BFS / A* animasyon durumu
        self.visited_order = []
        self.reveal_index = 0
        self.search_step = 4
        self.path = []
        self.path_index = 0

        # Hibrit durumu
        self.agent_index = 0
        self.repair_cells = set()
        self.escaped = 0
        self.repairs = 0
        self.move_accum = 0.0

        # Telemetri istatistikleri
        self.bfs_stats = None
        self.astar_stats = None

        # Fare sürükleme durumu
        self.drag = None  # 'add' | 'erase' | 'start' | 'goal'

        self.buttons = []
        self._build_buttons()

    # ================================================================== #
    # Buton yerleşimi
    # ================================================================== #
    def _build_buttons(self):
        x = config.SIDEBAR_X + 16
        w_full = config.SIDEBAR_WIDTH - 32
        y = config.GRID_ORIGIN[1] + 70
        h = 30
        gap = 7
        f = self.fonts["btn"]

        # Algoritma modları: 3 yan yana
        w3 = (w_full - 2 * gap) // 3
        self.buttons.append(Button((x, y, w3, h), "BFS", "bfs", f))
        self.buttons.append(Button((x + w3 + gap, y, w3, h), "A*", "astar", f))
        self.buttons.append(Button((x + 2 * (w3 + gap), y, w_full - 2 * (w3 + gap), h),
                                   "Hibrit", "hybrid", f))
        y += h + gap

        # Karşılaştırma (tam genişlik)
        self.buttons.append(Button((x, y, w_full, h), "BFS vs A* Karşılaştır", "compare", f))
        y += h + gap

        # Harita şablonları: 2x2
        w2 = (w_full - gap) // 2
        self.buttons.append(Button((x, y, w2, h), "8+ Engel Senaryosu", "preset", f))
        self.buttons.append(Button((x + w2 + gap, y, w_full - w2 - gap, h),
                                   "Rastgele Labirent", "random", f))
        y += h + gap
        self.buttons.append(Button((x, y, w2, h), "Yolu Temizle", "clearpath", f))
        self.buttons.append(Button((x + w2 + gap, y, w_full - w2 - gap, h),
                                   "Haritayı Sıfırla", "reset", f))
        y += h + gap

        self._telemetry_y = y + 4

    # ================================================================== #
    # Piksel <-> hücre dönüşümleri
    # ================================================================== #
    @staticmethod
    def cell_at_pixel(pos):
        x, y = pos
        ox, oy = config.GRID_ORIGIN
        if ox <= x < ox + config.GRID_WIDTH and oy <= y < oy + config.GRID_HEIGHT:
            c = (x - ox) // config.CELL_SIZE
            r = (y - oy) // config.CELL_SIZE
            return (int(r), int(c))
        return None

    @staticmethod
    def cell_rect(r, c):
        ox, oy = config.GRID_ORIGIN
        return pygame.Rect(ox + c * config.CELL_SIZE, oy + r * config.CELL_SIZE,
                          config.CELL_SIZE, config.CELL_SIZE)

    # ================================================================== #
    # Durum sıfırlama
    # ================================================================== #
    def reset_view(self):
        """Animasyon/yol katmanlarını temizler, duvarları korur, hibridi durdurur."""
        self.phase = "idle"
        self.visited_order = []
        self.reveal_index = 0
        self.path = []
        self.path_index = 0
        self.agent_index = 0
        self.repair_cells = set()
        self.escaped = 0
        self.repairs = 0
        self.move_accum = 0.0
        self.status = "Hazır"
        self.status_ok = True

    # ================================================================== #
    # Eylemler (buton / klavye)
    # ================================================================== #
    def do_action(self, action):
        if action == "bfs":
            self.start_search("BFS")
        elif action == "astar":
            self.start_search("A*")
        elif action == "hybrid":
            if self.phase == "running":
                self.phase = "idle"
                self.status = "Hibrit duraklatıldı"
            else:
                self.start_hybrid()
        elif action == "compare":
            self.run_compare()
        elif action == "preset":
            self.grid.preset_obstacles()
            self.reset_view()
            self.status = "8+ engel senaryosu yüklendi"
        elif action == "random":
            self.grid.random_maze()
            self.reset_view()
            self.status = "Rastgele labirent üretildi"
        elif action == "clearpath":
            self.reset_view()
            self.status = "Yol temizlendi"
        elif action == "reset":
            self.grid.reset()
            self.reset_view()
            self.bfs_stats = None
            self.astar_stats = None
            self.status = "Harita sıfırlandı"

    def start_search(self, mode):
        """BFS veya A* aramasını başlatır (animasyonlu)."""
        self.reset_view()
        self.mode = mode
        fn = algo.bfs if mode == "BFS" else algo.astar
        t0 = time.perf_counter()
        res = fn(self.grid, self.grid.start, self.grid.goal)
        ms = (time.perf_counter() - t0) * 1000.0

        stats = {"visited": res["visited_count"],
                 "length": len(res["path"]),
                 "ms": ms, "found": res["found"]}
        if mode == "BFS":
            self.bfs_stats = stats
        else:
            self.astar_stats = stats

        self.visited_order = res["visited_order"]
        self.path = res["path"]
        self.reveal_index = 0
        self.path_index = 0
        # Arama animasyonunu ~90 karede tamamlayacak adım büyüklüğü
        self.search_step = max(2, len(self.visited_order) // 90)
        self.phase = "searching"
        self.status_ok = res["found"]
        self.status = "Aranıyor..." if res["found"] else "Yol bulunamadı"

    def start_hybrid(self):
        """Hibrit modu başlatır: BFS ile global rota + dinamik yerel onarım."""
        self.reset_view()
        self.mode = "HİBRİT"
        t0 = time.perf_counter()
        res = algo.bfs(self.grid, self.grid.start, self.grid.goal)
        ms = (time.perf_counter() - t0) * 1000.0
        self.bfs_stats = {"visited": res["visited_count"], "length": len(res["path"]),
                          "ms": ms, "found": res["found"]}

        if not res["found"]:
            self.phase = "blocked"
            self.status_ok = False
            self.status = "Başlangıç rotası yok!"
            return

        self.path = res["path"]
        self.agent_index = 0
        self.phase = "running"
        self.move_accum = 0.0
        self.status = "Ajan hareket ediyor"
        self.status_ok = True

    def run_compare(self):
        """Mevcut harita üzerinde BFS ve A*'ı çalıştırıp metrikleri doldurur."""
        self.reset_view()
        for mode, fn in (("BFS", algo.bfs), ("A*", algo.astar)):
            t0 = time.perf_counter()
            res = fn(self.grid, self.grid.start, self.grid.goal)
            ms = (time.perf_counter() - t0) * 1000.0
            stats = {"visited": res["visited_count"], "length": len(res["path"]),
                     "ms": ms, "found": res["found"]}
            if mode == "BFS":
                self.bfs_stats = stats
            else:
                self.astar_stats = stats
        self.status = "BFS vs A* hesaplandı — panele bakın"
        self.status_ok = True

    # ================================================================== #
    # Hibrit ajan mantığı
    # ================================================================== #
    def hybrid_step(self):
        """Ajanın tek bir mantıksal adımı: engel kontrolü -> onarım ya da ilerleme."""
        if self.phase != "running":
            return
        cur = self.path[self.agent_index]
        if cur == self.grid.goal:
            self.phase = "done"
            self.status = "Hedefe ulaşıldı 🎉"
            return

        # Kalan rotada ileride duvar var mı?
        remaining = self.path[self.agent_index:]
        blocked_rel = None
        for i in range(1, len(remaining)):
            if remaining[i] in self.grid.walls:
                blocked_rel = i
                break

        if blocked_rel is not None:
            self._repair(remaining, blocked_rel)
            return

        # Engel yok: bir kare ilerle
        self.agent_index += 1
        if self.path[self.agent_index] == self.grid.goal:
            self.phase = "done"
            self.status = "Hedefe ulaşıldı 🎉"

    def _repair(self, remaining, b):
        """
        Yerel onarım (Local Repair):
        Engel kümesinin arkasındaki ilk açık ana-rota karesine kadar yerel A*
        çalıştırıp engelin etrafından dolaşan bir yama üretir. Mümkün değilse
        mevcut konumdan hedefe tam A* uygular.
        """
        cur = remaining[0]
        n = len(remaining)

        # Engel kümesini atla: arkadaki ilk geçilebilir ana-rota karesi
        j = b
        while j < n and remaining[j] in self.grid.walls:
            j += 1
        reconnect = remaining[j] if j < n else None

        # 1) Yerel yama denemesi
        if reconnect is not None:
            res = algo.astar(self.grid, cur, reconnect)
            if res["found"]:
                local = res["path"]              # cur ... reconnect
                tail = remaining[j + 1:]         # reconnect'ten sonrası
                self.path = self.path[:self.agent_index] + local + tail
                self.repair_cells.update(local)
                self.escaped += 1
                self.repairs += 1
                self.status = "Engelden kaçıldı (yerel onarım)"
                self.status_ok = True
                return

        # 2) Yerel yama yoksa: hedefe tam A*
        res = algo.astar(self.grid, cur, self.grid.goal)
        if res["found"]:
            self.path = self.path[:self.agent_index] + res["path"]
            self.repair_cells.update(res["path"])
            self.escaped += 1
            self.repairs += 1
            self.status = "Engelden kaçıldı (tam A*)"
            self.status_ok = True
        else:
            self.phase = "blocked"
            self.status = "Yol kapalı! Hedefe ulaşılamıyor."
            self.status_ok = False

    # ================================================================== #
    # Olay işleme
    # ================================================================== #
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False

        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.running = False
            elif e.key == pygame.K_1:
                self.do_action("bfs")
            elif e.key == pygame.K_2:
                self.do_action("astar")
            elif e.key in (pygame.K_3, pygame.K_SPACE):
                self.do_action("hybrid")
            elif e.key == pygame.K_c:
                self.do_action("clearpath")
            elif e.key == pygame.K_r:
                self.do_action("random")
            elif e.key == pygame.K_p:
                self.do_action("preset")
            elif e.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.speed = min(config.AGENT_SPEED_MAX, self.speed + 1)
            elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.speed = max(config.AGENT_SPEED_MIN, self.speed - 1)

        elif e.type == pygame.MOUSEBUTTONDOWN:
            # Önce butonlar
            for b in self.buttons:
                if b.hit(e.pos):
                    self.do_action(b.action)
                    return
            cell = self.cell_at_pixel(e.pos)
            if cell is None:
                return
            if cell == self.grid.start and self.phase != "running":
                self.drag = "start"
            elif cell == self.grid.goal and self.phase != "running":
                self.drag = "goal"
            elif e.button == 1:
                self.drag = "add"
                self._apply_drag(cell)
            elif e.button == 3:
                self.drag = "erase"
                self._apply_drag(cell)

        elif e.type == pygame.MOUSEBUTTONUP:
            self.drag = None

        elif e.type == pygame.MOUSEMOTION:
            if self.drag:
                cell = self.cell_at_pixel(e.pos)
                if cell is not None:
                    self._apply_drag(cell)

    def _apply_drag(self, cell):
        """Aktif sürükleme durumuna göre hücreyi günceller."""
        if self.drag == "add":
            # Ajanın bulunduğu kareye duvar koymayı engelle
            if self.phase == "running" and cell == self.path[self.agent_index]:
                return
            self.grid.add_wall(cell)
        elif self.drag == "erase":
            self.grid.remove_wall(cell)
        elif self.drag == "start":
            self.grid.set_start(cell)
        elif self.drag == "goal":
            self.grid.set_goal(cell)

    # ================================================================== #
    # Güncelleme (animasyon ilerletme)
    # ================================================================== #
    def update(self, dt):
        if self.phase == "searching":
            self.reveal_index += self.search_step
            if self.reveal_index >= len(self.visited_order):
                self.reveal_index = len(self.visited_order)
                if self.path:
                    self.phase = "tracing"
                    self.path_index = 0
                else:
                    self.phase = "done"

        elif self.phase == "tracing":
            self.path_index += max(1, len(self.path) // 60)
            if self.path_index >= len(self.path):
                self.path_index = len(self.path)
                self.phase = "done"
                self.status = "En kısa yol bulundu"

        elif self.phase == "running":
            interval = 1000.0 / self.speed  # ms / kare
            self.move_accum += dt
            # Bir karede birden çok adım birikmişse hepsini uygula
            steps = 0
            while self.move_accum >= interval and self.phase == "running" and steps < 100:
                self.move_accum -= interval
                self.hybrid_step()
                steps += 1

    # ================================================================== #
    # Çizim
    # ================================================================== #
    def draw(self):
        self.screen.fill(C["bg"])
        self._draw_grid()
        self._draw_overlays()
        self._draw_start_goal()
        self._draw_agent()
        self._draw_sidebar()
        pygame.display.flip()

    def _draw_grid(self):
        # Grid arka planını (çizgi rengi) doldur, sonra hücreleri 1px içeriden çiz
        area = pygame.Rect(config.GRID_ORIGIN[0], config.GRID_ORIGIN[1],
                          config.GRID_WIDTH, config.GRID_HEIGHT)
        pygame.draw.rect(self.screen, C["grid_line"], area)
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                rect = self.cell_rect(r, c).inflate(-1, -1)
                color = C["wall"] if (r, c) in self.grid.walls else C["empty"]
                pygame.draw.rect(self.screen, color, rect)

    def _fill_cell(self, cell, color):
        if cell == self.grid.start or cell == self.grid.goal:
            return
        pygame.draw.rect(self.screen, color, self.cell_rect(*cell).inflate(-1, -1))

    def _draw_overlays(self):
        if self.mode in ("BFS", "A*") and self.phase in ("searching", "tracing", "done"):
            revealed = self.visited_order[:self.reveal_index]
            revealed_set = set(revealed)

            # Taranan kareler
            for cell in revealed:
                self._fill_cell(cell, C["visited"])

            # Sınır (frontier): taranan kümenin geçilebilir komşu sınırı
            if self.phase == "searching":
                frontier = set()
                for cell in revealed:
                    for nb in self.grid.neighbors(cell):
                        if nb not in revealed_set:
                            frontier.add(nb)
                for cell in frontier:
                    self._fill_cell(cell, C["frontier"])

            # Bulunan yol (altın sarısı), adım adım
            if self.phase in ("tracing", "done"):
                for cell in self.path[:self.path_index]:
                    self._fill_cell(cell, C["path"])

        elif self.mode == "HİBRİT" and self.phase in ("running", "done", "blocked"):
            # Küresel rotanın kalan kısmı (altın), yerel onarım kareleri (turuncu)
            for idx in range(self.agent_index, len(self.path)):
                cell = self.path[idx]
                color = C["repair"] if cell in self.repair_cells else C["path"]
                self._fill_cell(cell, color)

    def _draw_start_goal(self):
        pygame.draw.rect(self.screen, C["start"],
                        self.cell_rect(*self.grid.start).inflate(-1, -1), border_radius=4)
        pygame.draw.rect(self.screen, C["goal"],
                        self.cell_rect(*self.grid.goal).inflate(-1, -1), border_radius=4)

    def _draw_agent(self):
        if self.mode != "HİBRİT" or self.phase not in ("running", "done", "blocked"):
            return
        if not self.path:
            return
        idx = min(self.agent_index, len(self.path) - 1)
        rect = self.cell_rect(*self.path[idx])
        center = rect.center
        radius = int(config.CELL_SIZE * 0.42)
        pygame.draw.circle(self.screen, C["agent_ring"], center, radius)
        pygame.draw.circle(self.screen, C["agent"], center, radius - 3)

    def _draw_sidebar(self):
        draw_sidebar_bg(self.screen)
        x = config.SIDEBAR_X + 16

        # Başlık
        self.screen.blit(self.fonts["title"].render("LABİRENT AJANI", True, C["text"]),
                        (x, config.GRID_ORIGIN[1] + 14))
        self.screen.blit(self.fonts["sub"].render("Hibrit Yol Bulma & Dinamik Kaçış",
                                                  True, C["text_dim"]),
                        (x, config.GRID_ORIGIN[1] + 42))

        # Buton aktiflik durumları
        for b in self.buttons:
            b.active = (
                (b.action == "bfs" and self.mode == "BFS") or
                (b.action == "astar" and self.mode == "A*") or
                (b.action == "hybrid" and self.mode == "HİBRİT")
            )
            b.draw(self.screen)

        data = {
            "mode": self.mode,
            "status": self.status,
            "status_ok": self.status_ok,
            "speed": self.speed,
            "bfs": self.bfs_stats,
            "astar": self.astar_stats,
            "escaped": self.escaped,
            "repairs": self.repairs,
        }
        draw_telemetry(self.screen, self.fonts, data, self._telemetry_y)

    # ================================================================== #
    # Ana döngü
    # ================================================================== #
    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(config.FPS)  # ms
            mouse = pygame.mouse.get_pos()
            for b in self.buttons:
                b.hover = b.hit(mouse)
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    App().run()

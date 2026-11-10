"""
ui.py
-----
Arayüz bileşenleri: tıklanabilir `Button` sınıfı ve yan paneldeki (sidebar)
canlı telemetri / karşılaştırma panelini çizen yardımcı fonksiyonlar.

Tüm çizimler Pygame'in yerleşik şekil ve font araçlarıyla yapılır; harici
font ya da görsel dosyasına bağımlılık yoktur.
"""

import pygame

import config

C = config.COLORS


class Button:
    """Basit, hover ve aktif durumlu yuvarlatılmış köşeli buton."""

    def __init__(self, rect, label, action, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action   # tıklanınca uygulamaya iletilecek eylem anahtarı
        self.font = font
        self.hover = False
        self.active = False    # seçili mod için vurgulu gösterim

    def draw(self, surf):
        bg = C["surface"]
        if self.active:
            bg = C["accent"]
        elif self.hover:
            bg = C["surface_hi"]
        pygame.draw.rect(surf, bg, self.rect, border_radius=6)

        txt_color = C["bg"] if self.active else C["text"]
        label = self.font.render(self.label, True, txt_color)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


def _swatch(surf, x, y, color, label, font):
    """Küçük renk kutusu + etiket (lejant için)."""
    pygame.draw.rect(surf, color, pygame.Rect(x, y + 2, 12, 12), border_radius=3)
    surf.blit(font.render(label, True, C["text_dim"]), (x + 18, y))


def draw_sidebar_bg(surf):
    """Yan panelin arka plan dikdörtgenini çizer."""
    panel = pygame.Rect(config.SIDEBAR_X, config.GRID_ORIGIN[1],
                        config.SIDEBAR_WIDTH, config.GRID_HEIGHT)
    pygame.draw.rect(surf, C["sidebar"], panel, border_radius=10)
    return panel


def draw_telemetry(surf, fonts, data, y):
    """
    Telemetri ve karşılaştırma metriklerini yan panele yazar.
    `data` sözlüğü uygulama tarafından doldurulur.
    `y` metnin başlayacağı dikey piksel konumudur.
    """
    x = config.SIDEBAR_X + 16
    body = fonts["body"]
    small = fonts["small"]
    line = 18

    def row(label, value, value_color=None):
        nonlocal y
        surf.blit(small.render(label, True, C["text_dim"]), (x, y))
        if value is not None:
            val = small.render(str(value), True, value_color or C["text"])
            surf.blit(val, (config.SIDEBAR_X + config.SIDEBAR_WIDTH - 16 - val.get_width(), y))
        y += line

    def header(text):
        nonlocal y
        y += 4
        surf.blit(body.render(text, True, C["accent"]), (x, y))
        y += line + 2

    # --- Durum ---
    header("DURUM")
    row("Seçili Mod", data["mode"])
    row("Ajan Durumu", data["status"],
        C["ok"] if data.get("status_ok", True) else C["warn"])
    row("Ajan Hızı", f"{data['speed']} kare/sn")

    # --- BFS ---
    header("BFS  (Breadth-First Search)")
    b = data.get("bfs")
    if b:
        row("Baktığı Kare", b["visited"])
        row("Yol Uzunluğu", b["length"])
        row("Süre", f"{b['ms']:.2f} ms")
    else:
        row("(henüz çalıştırılmadı)", None)

    # --- A* ---
    header("A*  (Manhattan sezgiseli)")
    a = data.get("astar")
    if a:
        row("Baktığı Kare", a["visited"])
        row("Yol Uzunluğu", a["length"])
        row("Süre", f"{a['ms']:.2f} ms")
    else:
        row("(henüz çalıştırılmadı)", None)

    # --- Verimlilik farkı ---
    header("KARŞILAŞTIRMA")
    if b and a and b["visited"] > 0:
        eff = (b["visited"] - a["visited"]) / b["visited"] * 100.0
        row("A* verimliliği", f"%{eff:.1f} daha az",
            C["ok"] if eff >= 0 else C["warn"])
    else:
        row("A* verimliliği", "—")

    # --- Hibrit ---
    header("HİBRİT DİNAMİK MOD")
    row("Kaçılan Engel", data.get("escaped", 0))
    row("Yerel Onarım (A*)", data.get("repairs", 0))

    # --- Lejant (renk anahtarı) ---
    y += 6
    pygame.draw.line(surf, C["divider"], (x, y),
                    (config.SIDEBAR_X + config.SIDEBAR_WIDTH - 16, y))
    y += 8
    col2 = x + 158
    _swatch(surf, x, y, C["start"], "Başlangıç", small)
    _swatch(surf, col2, y, C["goal"], "Hedef", small)
    y += line
    _swatch(surf, x, y, C["wall"], "Duvar", small)
    _swatch(surf, col2, y, C["visited"], "Taranan", small)
    y += line
    _swatch(surf, x, y, C["frontier"], "Sınır", small)
    _swatch(surf, col2, y, C["path"], "Yol", small)
    y += line
    _swatch(surf, x, y, C["repair"], "Onarım", small)
    _swatch(surf, col2, y, C["agent"], "Ajan", small)
    return y

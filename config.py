"""
config.py
---------
Projenin genel yapılandırması: grid boyutları, pencere ölçüleri ve
karanlık tema (dark mode) renk paleti burada tek yerden yönetilir.

Renkler Catppuccin Mocha paletinden esinlenmiştir.
"""


def _hex(h):
    """'#RRGGBB' biçimindeki bir metni (R, G, B) demetine çevirir."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# --- Grid (ızgara) boyutları ---
ROWS = 25          # satır sayısı
COLS = 50          # sütun sayısı
CELL_SIZE = 20     # her hücrenin piksel kenar uzunluğu

# --- Yerleşim (layout) ---
GRID_ORIGIN = (20, 20)                 # grid alanının sol-üst köşesi
GRID_WIDTH = COLS * CELL_SIZE          # 1000 px
GRID_HEIGHT = ROWS * CELL_SIZE         # 500 px

SIDEBAR_GAP = 20                       # grid ile yan panel arası boşluk
SIDEBAR_X = GRID_ORIGIN[0] + GRID_WIDTH + SIDEBAR_GAP
SIDEBAR_WIDTH = 340

WINDOW_WIDTH = SIDEBAR_X + SIDEBAR_WIDTH + 20   # 1400 px
WINDOW_HEIGHT = GRID_ORIGIN[1] * 2 + GRID_HEIGHT  # 540 px

FPS = 60

# --- Ajan hızı (saniyedeki kare/adım sayısı) ---
AGENT_SPEED_DEFAULT = 7
AGENT_SPEED_MIN = 1
AGENT_SPEED_MAX = 30

# --- Renk paleti (Dark Theme) ---
COLORS = {
    "bg":         _hex("#1E1E2E"),  # koyu antrasit arka plan
    "sidebar":    _hex("#181825"),  # yan panel (biraz daha koyu)
    "empty":      _hex("#2A2A3C"),  # boş hücre
    "grid_line":  _hex("#1E1E2E"),  # ince grid çizgileri (arka planla aynı -> yumuşak)
    "start":      _hex("#A6E3A1"),  # başlangıç - neon yeşil
    "goal":       _hex("#F38BA8"),  # hedef - mercan kırmızısı
    "wall":       _hex("#45475A"),  # duvar / engel
    "visited":    _hex("#74C7EC"),  # taranan (visited) kareler
    "visited_hi": _hex("#89DCEB"),  # taranan - açık ton
    "frontier":   _hex("#CBA6F7"),  # sınır (frontier) kareler
    "path":       _hex("#F9E2AF"),  # bulunan en kısa yol - altın sarısı
    "repair":     _hex("#FAB387"),  # dinamik yerel onarım yolu - turuncu
    "agent":      _hex("#F5F5F5"),  # ajan - parlak beyaz
    "agent_ring": _hex("#F9E2AF"),  # ajan dış halkası - sarı
    "text":       _hex("#CDD6F4"),  # birincil metin
    "text_dim":   _hex("#9399B2"),  # ikincil / soluk metin
    "surface":    _hex("#313244"),  # buton yüzeyi
    "surface_hi": _hex("#45475A"),  # buton hover
    "accent":     _hex("#89B4FA"),  # vurgu (mavi)
    "accent2":    _hex("#A6E3A1"),  # vurgu (yeşil)
    "divider":    _hex("#313244"),  # ayırıcı çizgi
    "ok":         _hex("#A6E3A1"),
    "warn":       _hex("#F38BA8"),
}

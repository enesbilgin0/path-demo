"""
algorithms.py
-------------
Yol bulma algoritmaları:

* `bfs`   : Breadth-First Search (genişlik öncelikli arama) — ağırlıksız
            gridde en kısa yolu garanti eder, ancak her yöne eşit yayılır.
* `astar` : A* (A-Yıldız) — Manhattan sezgiseli (heuristic) ile hedefe doğru
            yönlendirilmiş arama; genellikle BFS'den çok daha az kareye bakar.

Her iki fonksiyon da animasyon ve telemetri için ortak bir sözlük döndürür:
    {
        "path":          [...],   # başlangıçtan hedefe hücre listesi (yoksa [])
        "visited_order": [...],   # kareler tarandıkları SIRAYLA (animasyon için)
        "visited_count": int,     # bakılan (genişletilen) kare sayısı
        "found":         bool,    # hedefe ulaşıldı mı?
    }
"""

import heapq
from collections import deque


def manhattan(a, b):
    """İki hücre arası Manhattan mesafesi (A* sezgiseli)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(came_from, start, goal):
    """`came_from` zincirinden başlangıç -> hedef yolunu geri kurar."""
    if goal not in came_from:
        return []
    path = [goal]
    cur = goal
    while cur != start:
        cur = came_from[cur]
        path.append(cur)
    path.reverse()
    return path


def bfs(grid, start, goal):
    """Klasik BFS ile en kısa yolu bulur."""
    frontier = deque([start])
    came_from = {start: None}
    visited_order = []
    found = False

    while frontier:
        cur = frontier.popleft()
        visited_order.append(cur)
        if cur == goal:
            found = True
            break
        for n in grid.neighbors(cur):
            if n not in came_from:
                came_from[n] = cur
                frontier.append(n)

    path = _reconstruct(came_from, start, goal) if found else []
    return {
        "path": path,
        "visited_order": visited_order,
        "visited_count": len(visited_order),
        "found": found,
    }


def astar(grid, start, goal):
    """A* algoritması (Manhattan sezgiseli)."""
    counter = 0  # heap içinde eşit öncelikte kararlı sıralama için sayaç
    open_heap = [(manhattan(start, goal), 0, counter, start)]
    came_from = {start: None}
    g_score = {start: 0}
    visited_order = []
    closed = set()
    found = False

    while open_heap:
        _, _, _, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        visited_order.append(cur)
        if cur == goal:
            found = True
            break
        for n in grid.neighbors(cur):
            tentative = g_score[cur] + 1
            if n not in g_score or tentative < g_score[n]:
                g_score[n] = tentative
                came_from[n] = cur
                counter += 1
                f = tentative + manhattan(n, goal)
                heapq.heappush(open_heap, (f, tentative, counter, n))

    path = _reconstruct(came_from, start, goal) if found else []
    return {
        "path": path,
        "visited_order": visited_order,
        "visited_count": len(visited_order),
        "found": found,
    }

"""Visualizador de algoritmos de búsqueda ciega en un laberinto 5x5.

Ejecuta este archivo con: python3 CIEGA.PY
"""

import heapq
import random
import tkinter as tk
import webbrowser
from collections import deque
from tkinter import ttk
from pathlib import Path


ROWS = 5
COLUMNS = 5
START = (0, 0)
GOAL = (ROWS - 1, COLUMNS - 1)
CELL_SIZE = 74
MARGIN = 18

ALGORITHMS = (
    "Búsqueda en anchura (BFS)",
    "Búsqueda en profundidad (DFS)",
    "Búsqueda de costo uniforme",
    "Búsqueda bidireccional",
    "Búsqueda en profundidad limitada",
    "Profundización iterativa",
)

COLORS = {
    "background": "#f4f6f8",
    "wall": "#263238",
    "open": "#ffffff",
    "visited": "#b3e5fc",
    "path": "#a5d6a7",
    "start": "#2e7d32",
    "goal": "#c62828",
    "text": "#17212b",
    "muted": "#52616b",
}


def build_maze():
    """Genera un laberinto perfecto: todas las celdas quedan conectadas."""
    graph = {
        (row, column): []
        for row in range(ROWS)
        for column in range(COLUMNS)
    }
    visited = {START}
    stack = [START]

    while stack:
        current = stack[-1]
        row, column = current
        neighbors = [
            cell
            for cell in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            )
            if 0 <= cell[0] < ROWS
            and 0 <= cell[1] < COLUMNS
            and cell not in visited
        ]
        if not neighbors:
            stack.pop()
            continue

        neighbor = random.choice(neighbors)
        graph[current].append(neighbor)
        graph[neighbor].append(current)
        visited.add(neighbor)
        stack.append(neighbor)

    return graph


def restore_path(parent, goal):
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))


def breadth_first_search(graph):
    frontier = deque([START])
    parent = {START: None}
    events = []

    while frontier:
        current = frontier.popleft()
        events.append((current, len(frontier), "Expandiendo"))
        if current == GOAL:
            return events, restore_path(parent, GOAL)
        for neighbor in graph[current]:
            if neighbor not in parent:
                parent[neighbor] = current
                frontier.append(neighbor)

    return events, []


def depth_first_search(graph):
    frontier = [START]
    parent = {START: None}
    events = []

    while frontier:
        current = frontier.pop()
        events.append((current, len(frontier), "Expandiendo"))
        if current == GOAL:
            return events, restore_path(parent, GOAL)
        for neighbor in reversed(graph[current]):
            if neighbor not in parent:
                parent[neighbor] = current
                frontier.append(neighbor)

    return events, []


def uniform_cost_search(graph):
    frontier = [(0, 0, START)]
    parent = {START: None}
    best_cost = {START: 0}
    sequence = 0
    events = []

    while frontier:
        cost, _, current = heapq.heappop(frontier)
        if cost != best_cost[current]:
            continue
        events.append((current, len(frontier), "Expandiendo"))
        if current == GOAL:
            return events, restore_path(parent, GOAL)
        for neighbor in graph[current]:
            new_cost = cost + 1
            if new_cost < best_cost.get(neighbor, float("inf")):
                best_cost[neighbor] = new_cost
                parent[neighbor] = current
                sequence += 1
                heapq.heappush(frontier, (new_cost, sequence, neighbor))

    return events, []


def bidirectional_search(graph):
    start_frontier = deque([START])
    goal_frontier = deque([GOAL])
    start_parent = {START: None}
    goal_parent = {GOAL: None}
    events = []

    while start_frontier and goal_frontier:
        from_start = len(start_frontier) <= len(goal_frontier)
        frontier = start_frontier if from_start else goal_frontier
        own_parent = start_parent if from_start else goal_parent
        other_parent = goal_parent if from_start else start_parent
        layer_size = len(frontier)
        meeting = None

        for _ in range(layer_size):
            current = frontier.popleft()
            events.append(
                (
                    current,
                    len(start_frontier) + len(goal_frontier),
                    "Expandiendo desde inicio"
                    if from_start
                    else "Expandiendo desde meta",
                )
            )
            if current in other_parent:
                meeting = current
                break

            for neighbor in graph[current]:
                if neighbor in own_parent:
                    continue
                own_parent[neighbor] = current
                frontier.append(neighbor)
                if neighbor in other_parent:
                    meeting = neighbor
                    break
            if meeting is not None:
                break

        if meeting is not None:
            left = []
            current = meeting
            while current is not None:
                left.append(current)
                current = start_parent[current]
            left.reverse()

            right = []
            current = goal_parent[meeting]
            while current is not None:
                right.append(current)
                current = goal_parent[current]
            return events, left + right

    return events, []


def depth_limited_search(graph, limit):
    events = []

    def visit(current, depth, path):
        events.append((current, max(0, limit - depth), "Probando profundidad"))
        if current == GOAL:
            return list(path)
        if depth == limit:
            return None

        for neighbor in graph[current]:
            if neighbor not in path:
                path.append(neighbor)
                result = visit(neighbor, depth + 1, path)
                if result is not None:
                    return result
                path.pop()
        return None

    result = visit(START, 0, [START])
    return events, result or []


def iterative_deepening_search(graph):
    events = []
    for limit in range(ROWS * COLUMNS):
        result_events, path = depth_limited_search(graph, limit)
        events.extend(result_events)
        if path:
            return events, path
    return events, []


SEARCH_FUNCTIONS = {
    ALGORITHMS[0]: breadth_first_search,
    ALGORITHMS[1]: depth_first_search,
    ALGORITHMS[2]: uniform_cost_search,
    ALGORITHMS[3]: bidirectional_search,
    ALGORITHMS[4]: lambda graph: depth_limited_search(
        graph, ROWS * COLUMNS - 1
    ),
    ALGORITHMS[5]: iterative_deepening_search,
}


class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Búsqueda ciega — Laberinto 5x5")
        self.root.configure(bg=COLORS["background"])
        self.root.geometry("820x560")
        self.root.resizable(False, False)

        self.graph = build_maze()
        self.events = []
        self.path = []
        self.event_index = 0
        self.visited = set()
        self.path_cells = set()
        self.after_id = None
        self.paused = False

        self.algorithm = tk.StringVar(value=ALGORITHMS[0])
        self.status = tk.StringVar(
            value="Elige un algoritmo y presiona «Iniciar búsqueda»."
        )
        self.speed = tk.IntVar(value=350)
        self.speed_label = tk.StringVar(value="350 ms por paso")

        self._build_interface()
        self._draw_maze()

    def _build_interface(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TFrame",
            background=COLORS["background"],
        )
        style.configure(
            "TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("Helvetica", 10),
        )
        style.configure(
            "Title.TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("Helvetica", 18, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("Helvetica", 11, "bold"),
        )
        style.configure(
            "TButton",
            background="#e1e7eb",
            foreground=COLORS["text"],
            padding=6,
        )
        style.map(
            "TButton",
            background=[("active", "#cbd5dc"), ("disabled", "#e8ecef")],
            foreground=[("disabled", COLORS["muted"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["open"],
            background="#e1e7eb",
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
        )

        main = ttk.Frame(self.root, padding=18)
        main.grid(row=0, column=0, sticky="nsew")
        ttk.Label(
            main, text="Búsqueda ciega en un laberinto 5x5", style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        controls = ttk.Frame(main, padding=(0, 4, 18, 0))
        controls.grid(row=1, column=0, sticky="nw")
        ttk.Label(
            controls, text="Algoritmo de búsqueda", style="Section.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.algorithm_picker = ttk.Combobox(
            controls,
            textvariable=self.algorithm,
            values=ALGORITHMS,
            state="readonly",
            width=35,
        )
        self.algorithm_picker.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        self.start_button = ttk.Button(
            controls, text="Iniciar búsqueda", command=self.start_search
        )
        self.start_button.grid(row=2, column=0, sticky="ew", pady=3)
        self.pause_button = ttk.Button(
            controls,
            text="Pausar",
            command=self.toggle_pause,
            state="disabled",
        )
        self.pause_button.grid(row=3, column=0, sticky="ew", pady=3)
        ttk.Button(
            controls, text="Limpiar camino", command=self.clear_search
        ).grid(row=4, column=0, sticky="ew", pady=3)
        ttk.Button(
            controls, text="Generar nuevo laberinto", command=self.new_maze
        ).grid(row=5, column=0, sticky="ew", pady=3)

        ttk.Label(
            controls, text="Velocidad de animación", style="Section.TLabel"
        ).grid(row=6, column=0, sticky="w", pady=(18, 4))
        self.speed_scale = ttk.Scale(
            controls,
            from_=30,
            to=1000,
            orient="horizontal",
            command=self._update_speed,
        )
        self.speed_scale.set(self.speed.get())
        self.speed_scale.grid(row=7, column=0, sticky="ew")
        ttk.Label(controls, textvariable=self.speed_label).grid(
            row=8, column=0, sticky="w", pady=(2, 14)
        )

        ttk.Label(
            controls,
            textvariable=self.status,
            wraplength=270,
            justify="left",
        ).grid(row=9, column=0, sticky="w", pady=(4, 14))
        ttk.Label(
            controls,
            text="Celda azul: explorada\nCelda verde: camino encontrado",
            justify="left",
        ).grid(row=10, column=0, sticky="w")
        ttk.Label(
            controls,
            text="I: inicio    F: meta",
            foreground=COLORS["muted"],
        ).grid(row=11, column=0, sticky="w", pady=(6, 0))

        canvas_size = CELL_SIZE * COLUMNS + MARGIN * 2
        self.canvas = tk.Canvas(
            main,
            width=canvas_size,
            height=canvas_size,
            bg=COLORS["open"],
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=1, sticky="n")
        self.root.update_idletasks()

    def _update_speed(self, value):
        self.speed.set(int(float(value)))
        self.speed_label.set("{} ms por paso".format(self.speed.get()))

    def _cancel_animation(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _reset_search(self):
        self._cancel_animation()
        self.events = []
        self.path = []
        self.event_index = 0
        self.visited.clear()
        self.path_cells.clear()
        self.paused = False
        self.pause_button.configure(text="Pausar", state="disabled")
        self.start_button.configure(state="normal")
        self._draw_maze()

    def start_search(self):
        self._reset_search()
        search = SEARCH_FUNCTIONS[self.algorithm.get()]
        self.events, self.path = search(self.graph)
        if not self.path:
            self.status.set("No se encontró un camino hasta la meta.")
            return

        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.status.set("Preparando la búsqueda...")
        self._animate_next()

    def _animate_next(self):
        self.after_id = None
        if self.paused:
            return

        if self.event_index < len(self.events):
            cell, frontier_size, action = self.events[self.event_index]
            self.event_index += 1
            self.visited.add(cell)
            detail_label = (
                "Profundidad restante"
                if action == "Probando profundidad"
                else "Celdas pendientes"
            )
            self.status.set(
                "Paso {} de {}: {} la celda {}.\n"
                "{}: {}.".format(
                    self.event_index,
                    len(self.events),
                    action,
                    self._cell_name(cell),
                    detail_label,
                    frontier_size,
                )
            )
            self._draw_maze()
        elif self.path_cells != set(self.path):
            next_cell = self.path[len(self.path_cells)]
            self.path_cells.add(next_cell)
            self.status.set(
                "Camino encontrado: agregando {} ({} de {}).".format(
                    self._cell_name(next_cell),
                    len(self.path_cells),
                    len(self.path),
                )
            )
            self._draw_maze()
        else:
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled", text="Pausar")
            self.status.set(
                "¡Meta encontrada! {} pasos en el camino; "
                "{} expansiones.".format(
                    len(self.path) - 1, len(self.events)
                )
            )
            return

        self.after_id = self.root.after(self.speed.get(), self._animate_next)

    def toggle_pause(self):
        if not self.events:
            return
        self.paused = not self.paused
        if self.paused:
            self._cancel_animation()
            self.pause_button.configure(text="Reanudar")
            self.status.set("Búsqueda pausada. Presiona «Reanudar» para seguir.")
        else:
            self.pause_button.configure(text="Pausar")
            self._animate_next()

    def clear_search(self):
        self._reset_search()
        self.status.set("Camino y exploración limpiados.")

    def new_maze(self):
        self._reset_search()
        self.graph = build_maze()
        self.status.set("Nuevo laberinto generado. Elige un algoritmo.")
        self._draw_maze()

    @staticmethod
    def _cell_name(cell):
        return "fila {}, columna {}".format(cell[0] + 1, cell[1] + 1)

    def _draw_maze(self):
        self.canvas.delete("all")
        for row in range(ROWS):
            for column in range(COLUMNS):
                cell = (row, column)
                x1 = MARGIN + column * CELL_SIZE
                y1 = MARGIN + row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                fill = COLORS["open"]
                if cell in self.path_cells:
                    fill = COLORS["path"]
                elif cell in self.visited:
                    fill = COLORS["visited"]

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline=""
                )
                if column == 0:
                    self._draw_wall(x1, y1, x1, y2)
                if row == 0:
                    self._draw_wall(x1, y1, x2, y1)
                if (row, column + 1) not in self.graph[cell]:
                    self._draw_wall(x2, y1, x2, y2)
                if (row + 1, column) not in self.graph[cell]:
                    self._draw_wall(x1, y2, x2, y2)

                if cell == START or cell == GOAL:
                    label = "I" if cell == START else "F"
                    color = COLORS["start"] if cell == START else COLORS["goal"]
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=label,
                        fill=color,
                        font=("Helvetica", 20, "bold"),
                    )

    def _draw_wall(self, x1, y1, x2, y2):
        self.canvas.create_line(
            x1,
            y1,
            x2,
            y2,
            fill=COLORS["wall"],
            width=4,
            capstyle=tk.ROUND,
        )


def main():
    app_path = Path(__file__).with_name("CIEGA.html").resolve()
    if not app_path.is_file():
        raise FileNotFoundError("No se encontró la interfaz: {}".format(app_path))
    webbrowser.open(app_path.as_uri())


if __name__ == "__main__":
    main()
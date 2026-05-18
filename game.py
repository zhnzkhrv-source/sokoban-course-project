import pygame
from dataclasses import dataclass
from collections import deque
from typing import Optional, List, Tuple

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LIGHT_BROWN = (160, 100, 40)

WALL = '#'
FLOOR = ' '
GOAL = '.'


@dataclass(frozen=True)
class GameState:
    player: Tuple[int, int]
    boxes: frozenset


class SokobanGame:
    def __init__(self, level_file: str):
        self.walls = set()
        self.goals = set()
        self.width = 0
        self.height = 0
        self.player_pos = None
        self.boxes = set()

        self.history = []
        self.history_index = -1
        self.moves = 0
        self.pushes = 0

        self.load_level(level_file)
        self.save_state()

    def load_level(self, filename: str):
        self.walls.clear()
        self.goals.clear()
        self.boxes.clear()

        with open(filename, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return

        self.height = len(lines)
        self.width = max(len(line) for line in lines)

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == WALL:
                    self.walls.add((x, y))
                elif char == GOAL:
                    self.goals.add((x, y))
                elif char == '@':
                    self.player_pos = (x, y)
                elif char == '$':
                    self.boxes.add((x, y))
                elif char == '*':
                    self.boxes.add((x, y))
                    self.goals.add((x, y))
                elif char == '+':
                    self.player_pos = (x, y)
                    self.goals.add((x, y))

    def get_current_state(self) -> GameState:
        return GameState(self.player_pos, frozenset(self.boxes))

    def restore_state(self, state: GameState):
        self.player_pos = state.player
        self.boxes = set(state.boxes)

    def save_state(self):
        state = self.get_current_state()
        self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        self.history_index += 1

    def undo(self) -> bool:
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state(self.history[self.history_index])
            self.moves = max(0, self.moves - 1)
            return True
        return False

    def try_move(self, dx: int, dy: int) -> bool:
        if not self.player_pos:
            return False

        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy

        if new_x < 0 or new_x >= self.width or new_y < 0 or new_y >= self.height:
            return False

        self.save_state()

        if (new_x, new_y) in self.boxes:
            box_x, box_y = new_x + dx, new_y + dy

            if box_x < 0 or box_x >= self.width or box_y < 0 or box_y >= self.height:
                self.history.pop()
                self.history_index -= 1
                return False

            if (box_x, box_y) in self.walls or (box_x, box_y) in self.boxes:
                self.history.pop()
                self.history_index -= 1
                return False

            self.boxes.remove((new_x, new_y))
            self.boxes.add((box_x, box_y))
            self.player_pos = (new_x, new_y)
            self.moves += 1
            self.pushes += 1
            return True

        elif (new_x, new_y) not in self.walls:
            self.player_pos = (new_x, new_y)
            self.moves += 1
            return True

        self.history.pop()
        self.history_index -= 1
        return False

    def check_win(self) -> bool:
        return all(box in self.goals for box in self.boxes)

    def get_stats(self) -> dict:
        return {'moves': self.moves, 'pushes': self.pushes}

    def calculate_tile_size(self, screen_width, screen_height, ui_top=70, ui_bottom=90):
        available_height = screen_height - ui_top - ui_bottom
        available_width = screen_width

        if self.width <= 0 or self.height <= 0:
            return 32

        tile_by_width = available_width // self.width
        tile_by_height = available_height // self.height
        tile_size = min(tile_by_width, tile_by_height)
        return max(20, min(tile_size, 80))

    def draw(self, screen, font, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        if self.width == 0 or self.height == 0:
            return

        tile_size = self.calculate_tile_size(screen_width, screen_height)
        offset_y = 70
        offset_x = (screen_width - (self.width * tile_size)) // 2

        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    offset_x + x * tile_size,
                    offset_y + y * tile_size,
                    tile_size,
                    tile_size
                )

                pygame.draw.rect(screen, WHITE, rect)
                pygame.draw.rect(screen, GRAY, rect, 1)

                if (x, y) in self.walls:
                    pygame.draw.rect(screen, DARK_GRAY, rect)
                    pygame.draw.rect(screen, BLACK, rect, 2)

                if (x, y) in self.goals:
                    pygame.draw.circle(screen, RED, rect.center, tile_size // 4)
                    pygame.draw.circle(screen, YELLOW, rect.center, tile_size // 6)

                if (x, y) in self.boxes:
                    pygame.draw.rect(screen, BROWN, rect)
                    pygame.draw.rect(screen, BLACK, rect, 2)

                if self.player_pos == (x, y):
                    pygame.draw.circle(screen, BLUE, rect.center, tile_size // 3)
                    eye_size = max(2, tile_size // 8)
                    eye_offset = tile_size // 4
                    pygame.draw.circle(screen, WHITE, (rect.centerx - eye_offset, rect.centery - eye_offset), eye_size)
                    pygame.draw.circle(screen, WHITE, (rect.centerx + eye_offset, rect.centery - eye_offset), eye_size)
                    pygame.draw.circle(screen, BLACK, (rect.centerx - eye_offset, rect.centery - eye_offset),
                                       eye_size // 2)
                    pygame.draw.circle(screen, BLACK, (rect.centerx + eye_offset, rect.centery - eye_offset),
                                       eye_size // 2)

    # ========== ПРОСТОЙ BFS ДЛЯ МАЛЕНЬКИХ УРОВНЕЙ ==========

    def get_hint(self) -> Optional[Tuple[int, int]]:
        """Подсказка — первый шаг решения (только для маленьких уровней)"""
        # Если ящиков больше 3 — не ищем (долго)
        if len(self.boxes) > 3:
            return None  # Молча возвращаем None, без сообщений в терминал

        initial = GameState(self.player_pos, frozenset(self.boxes))

        if all(box in self.goals for box in initial.boxes):
            return None

        queue = deque([(initial, [])])
        visited = {initial}

        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        max_states = 20000
        iterations = 0

        while queue and iterations < max_states:
            iterations += 1
            state, path = queue.popleft()

            for dx, dy in directions:
                new_state = self._apply_move(state, dx, dy)

                if new_state and new_state not in visited:
                    new_path = path + [(dx, dy)]

                    if all(box in self.goals for box in new_state.boxes):
                        return new_path[0]  # Возвращаем первый ход

                    visited.add(new_state)
                    queue.append((new_state, new_path))

        return None  # Решение не найдено


    def _apply_move(self, state: GameState, dx: int, dy: int) -> Optional[GameState]:
        player = state.player
        boxes = set(state.boxes)
        new_x, new_y = player[0] + dx, player[1] + dy

        if new_x < 0 or new_x >= self.width or new_y < 0 or new_y >= self.height:
            return None

        if (new_x, new_y) in self.walls:
            return None

        if (new_x, new_y) in boxes:
            box_x, box_y = new_x + dx, new_y + dy

            if box_x < 0 or box_x >= self.width or box_y < 0 or box_y >= self.height:
                return None

            if (box_x, box_y) in self.walls or (box_x, box_y) in boxes:
                return None

            boxes.remove((new_x, new_y))
            boxes.add((box_x, box_y))

        return GameState((new_x, new_y), frozenset(boxes))
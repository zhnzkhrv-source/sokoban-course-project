import pygame
from dataclasses import dataclass
from collections import deque
from typing import Optional, List, Tuple
import os

WALL = '#'
FLOOR = ' '
PLAYER = '@'
BOX = '$'
GOAL = '.'
BOX_ON_GOAL = '*'
PLAYER_ON_GOAL = '+'


@dataclass(frozen=True)
class GameState:
    player: Tuple[int, int]
    boxes: frozenset
    moves: int = 0
    pushes: int = 0


class SokobanGame:
    def __init__(self, level_map):
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

        self.images = self.load_images()

        self.load_level(level_map)
        self.save_state()

    def load_images(self):
        images = {}
        img_dir = "images"
        if not os.path.exists(img_dir):
            return images

        for tex in ['wall', 'floor', 'player', 'box', 'goal', 'box_on_goal', 'player_on_goal']:
            filepath = os.path.join(img_dir, f"{tex}.png")
            if os.path.exists(filepath):
                try:
                    images[tex] = pygame.image.load(filepath).convert_alpha()
                except:
                    pass
        return images

    def load_level(self, level_map):
        self.walls.clear()
        self.goals.clear()
        self.boxes.clear()

        self.height = len(level_map)
        self.width = max(len(line) for line in level_map)

        for y, line in enumerate(level_map):
            for x, char in enumerate(line):
                if char == WALL:
                    self.walls.add((x, y))
                elif char == GOAL:
                    self.goals.add((x, y))
                elif char == PLAYER:
                    self.player_pos = (x, y)
                elif char == BOX:
                    self.boxes.add((x, y))
                elif char == BOX_ON_GOAL:
                    self.boxes.add((x, y))
                    self.goals.add((x, y))
                elif char == PLAYER_ON_GOAL:
                    self.player_pos = (x, y)
                    self.goals.add((x, y))

    def get_current_state(self) -> GameState:
        return GameState(self.player_pos, frozenset(self.boxes), self.moves, self.pushes)

    def restore_state(self, state: GameState):
        self.player_pos = state.player
        self.boxes = set(state.boxes)
        self.moves = state.moves
        self.pushes = state.pushes

    def save_state(self):
        state = self.get_current_state()
        # Обрезаем историю после текущего индекса
        self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        self.history_index += 1

    def undo(self) -> bool:
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state(self.history[self.history_index])
            return True
        return False

    def try_move(self, dx: int, dy: int) -> bool:
        if not self.player_pos:
            return False

        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy

        if new_x < 0 or new_x >= self.width or new_y < 0 or new_y >= self.height:
            return False

        if (new_x, new_y) in self.walls:
            return False

        # Движение с ящиком
        if (new_x, new_y) in self.boxes:
            box_x, box_y = new_x + dx, new_y + dy

            if box_x < 0 or box_x >= self.width or box_y < 0 or box_y >= self.height:
                return False

            if (box_x, box_y) in self.walls or (box_x, box_y) in self.boxes:
                return False

            # Все проверки пройдены — сохраняем состояние и двигаем
            self.save_state()
            self.boxes.remove((new_x, new_y))
            self.boxes.add((box_x, box_y))
            self.player_pos = (new_x, new_y)
            self.moves += 1
            self.pushes += 1
            return True

        # Обычное движение
        elif (new_x, new_y) not in self.walls and (new_x, new_y) not in self.boxes:
            self.save_state()
            self.player_pos = (new_x, new_y)
            self.moves += 1
            return True

        return False

    def check_win(self) -> bool:
        return all(box in self.goals for box in self.boxes)

    def get_stats(self) -> dict:
        return {'moves': self.moves, 'pushes': self.pushes}

    def calculate_tile_size(self, screen_width, screen_height, ui_top=70, ui_bottom=90):
        available_height = screen_height - ui_top - ui_bottom
        available_width = screen_width

        if self.width <= 0 or self.height <= 0:
            return 64

        tile_by_width = available_width // self.width
        tile_by_height = available_height // self.height
        tile_size = min(tile_by_width, tile_by_height)
        return max(48, min(tile_size, 80))

    def draw(self, screen, font, screen_width, screen_height):
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

                # Пол
                if 'floor' in self.images:
                    floor_img = pygame.transform.scale(self.images['floor'], (tile_size, tile_size))
                    screen.blit(floor_img, rect)
                else:
                    pygame.draw.rect(screen, (240, 240, 240), rect)
                    pygame.draw.rect(screen, (200, 200, 200), rect, 1)

                # Стена
                if (x, y) in self.walls:
                    if 'wall' in self.images:
                        wall_img = pygame.transform.scale(self.images['wall'], (tile_size, tile_size))
                        screen.blit(wall_img, rect)
                    else:
                        pygame.draw.rect(screen, (100, 100, 100), rect)
                        pygame.draw.rect(screen, (50, 50, 50), rect, 2)

                # Цель
                if (x, y) in self.goals:
                    if 'goal' in self.images:
                        goal_img = pygame.transform.scale(self.images['goal'], (tile_size, tile_size))
                        screen.blit(goal_img, rect)
                    else:
                        pygame.draw.circle(screen, (255, 100, 100), rect.center, tile_size // 4)

                # Ящик
                if (x, y) in self.boxes:
                    if (x, y) in self.goals and 'box_on_goal' in self.images:
                        box_img = pygame.transform.scale(self.images['box_on_goal'], (tile_size, tile_size))
                    elif 'box' in self.images:
                        box_img = pygame.transform.scale(self.images['box'], (tile_size, tile_size))
                    else:
                        pygame.draw.rect(screen, (139, 69, 19), rect)
                        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
                        box_img = None

                    if box_img:
                        screen.blit(box_img, rect)

                # Игрок (всегда поверх всего)
                if self.player_pos == (x, y):
                    if (x, y) in self.goals and 'player_on_goal' in self.images:
                        player_img = pygame.transform.scale(self.images['player_on_goal'], (tile_size, tile_size))
                    elif 'player' in self.images:
                        player_img = pygame.transform.scale(self.images['player'], (tile_size, tile_size))
                    else:
                        pygame.draw.circle(screen, (0, 0, 255), rect.center, tile_size // 3)
                        player_img = None

                    if player_img:
                        screen.blit(player_img, rect)
    def get_hint(self) -> Optional[Tuple[int, int]]:
        if len(self.boxes) > 3:
            return None

        initial = self.get_current_state()

        if self.check_win():
            return None

        from collections import deque
        queue = deque([(initial, [])])
        # visited хранит только (player, boxes) без moves/pushes
        visited = {(initial.player, initial.boxes)}
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        max_states = 20000
        iterations = 0

        while queue and iterations < max_states:
            iterations += 1
            state, path = queue.popleft()

            for dx, dy in directions:
                new_state = self._apply_move(state, dx, dy)
                key = (new_state.player, new_state.boxes) if new_state else None

                if new_state and key not in visited:
                    new_path = path + [(dx, dy)]

                    # Проверка победы
                    if all(box in self.goals for box in new_state.boxes):
                        return new_path[0]

                    visited.add(key)
                    queue.append((new_state, new_path))

        return None

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
            return GameState((new_x, new_y), frozenset(boxes), state.moves + 1, state.pushes + 1)

        return GameState((new_x, new_y), frozenset(boxes), state.moves + 1, state.pushes)
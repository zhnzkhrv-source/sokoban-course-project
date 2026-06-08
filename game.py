import pygame
from dataclasses import dataclass
from collections import deque
from typing import Optional, List, Tuple
import os
from constants import *


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
        self.texture_cache = {}

        # Анимация
        self.anim_progress = 1.0
        self.anim_start = None
        self.anim_target = None
        self.anim_box_start = None
        self.anim_box_target = None
        self.anim_box = None
        self.pending_move = None

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
                except pygame.error as e:
                    print(f"Ошибка загрузки {tex}.png: {e}")
        return images

    def get_scaled_texture(self, name, target_size):
        if name not in self.images:
            return None
        key = (name, target_size)
        if key not in self.texture_cache:
            self.texture_cache[key] = pygame.transform.scale(
                self.images[name], (target_size, target_size)
            )
        return self.texture_cache.get(key)

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

        self.anim_progress = 1.0
        self.anim_start = None
        self.anim_target = None
        self.anim_box_start = None
        self.anim_box_target = None
        self.anim_box = None
        self.pending_move = None

    def get_current_state(self) -> GameState:
        return GameState(self.player_pos, frozenset(self.boxes), self.moves, self.pushes)

    def restore_state(self, state: GameState):
        self.player_pos = state.player
        self.boxes = set(state.boxes)
        self.moves = state.moves
        self.pushes = state.pushes
        self.anim_progress = 1.0
        self.anim_start = None
        self.anim_target = None
        self.anim_box_start = None
        self.anim_box_target = None
        self.anim_box = None
        self.pending_move = None

    def save_state(self):
        state = self.get_current_state()
        self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        self.history_index += 1

    def undo(self) -> bool:
        if self.history_index > 0 and self.anim_progress >= 1.0:
            self.history_index -= 1
            self.restore_state(self.history[self.history_index])
            return True
        return False

    def try_move(self, dx: int, dy: int) -> bool:
        if not self.player_pos:
            return False

        if self.anim_progress < 1.0:
            return False

        x, y = self.player_pos
        new_x, new_y = x + dx, y + dy

        if new_x < 0 or new_x >= self.width or new_y < 0 or new_y >= self.height:
            return False

        if (new_x, new_y) in self.walls:
            return False

        if (new_x, new_y) in self.boxes:
            box_x, box_y = new_x + dx, new_y + dy

            if box_x < 0 or box_x >= self.width or box_y < 0 or box_y >= self.height:
                return False

            if (box_x, box_y) in self.walls or (box_x, box_y) in self.boxes:
                return False

            self.pending_move = (dx, dy, new_x, new_y, box_x, box_y)
            self.anim_progress = 0.0
            self.anim_start = (x, y)
            self.anim_target = (new_x, new_y)
            self.anim_box_start = (new_x, new_y)
            self.anim_box_target = (box_x, box_y)
            self.anim_box = (new_x, new_y)
            return True

        elif (new_x, new_y) not in self.walls and (new_x, new_y) not in self.boxes:
            self.pending_move = (dx, dy, new_x, new_y, None, None)
            self.anim_progress = 0.0
            self.anim_start = (x, y)
            self.anim_target = (new_x, new_y)
            self.anim_box_start = None
            self.anim_box_target = None
            self.anim_box = None
            return True

        return False

    def update_animation(self, dt):
        if self.anim_progress < 1.0:
            self.anim_progress += dt * 12.0
            if self.anim_progress >= 1.0:
                self.player_pos = self.anim_target
                if self.anim_box_start is not None and self.anim_box_target is not None:
                    self.boxes.remove(self.anim_box_start)
                    self.boxes.add(self.anim_box_target)

                self.save_state()

                if self.pending_move:
                    dx, dy, new_x, new_y, box_x, box_y = self.pending_move
                    self.moves += 1
                    if box_x is not None:
                        self.pushes += 1
                    self.pending_move = None

                self.anim_start = None
                self.anim_target = None
                self.anim_box_start = None
                self.anim_box_target = None
                self.anim_box = None
                self.anim_progress = 1.0

    def check_win(self) -> bool:
        return all(box in self.goals for box in self.boxes)

    def get_stats(self) -> dict:
        return {'moves': self.moves, 'pushes': self.pushes}

    def calculate_tile_size(self, screen_width, screen_height, ui_top=70, ui_bottom=90):
        available_height = screen_height - ui_top - ui_bottom
        available_width = screen_width

        if self.width <= 0 or self.height <= 0:
            return DEFAULT_TILE_SIZE

        tile_by_width = available_width // self.width
        tile_by_height = available_height // self.height
        tile_size = min(tile_by_width, tile_by_height)
        return max(MIN_TILE_SIZE, min(tile_size, MAX_TILE_SIZE))

    def get_animated_pos(self, start, target, progress):
        if start is None or target is None:
            return None
        x = start[0] + (target[0] - start[0]) * progress
        y = start[1] + (target[1] - start[1]) * progress
        return (x, y)

    def draw(self, screen, font, screen_width, screen_height):
        if self.width == 0 or self.height == 0:
            return

        tile_size = self.calculate_tile_size(screen_width, screen_height)
        offset_y = 70
        offset_x = (screen_width - (self.width * tile_size)) // 2

        if self.anim_progress < 1.0 and self.anim_start is not None:
            player_draw_pos = self.get_animated_pos(
                self.anim_start, self.anim_target, self.anim_progress
            )
            player_logic_pos = self.anim_start
        else:
            player_draw_pos = self.player_pos
            player_logic_pos = self.player_pos

        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    offset_x + x * tile_size,
                    offset_y + y * tile_size,
                    tile_size,
                    tile_size
                )

                floor_img = self.get_scaled_texture('floor', tile_size)
                if floor_img:
                    screen.blit(floor_img, rect)
                else:
                    pygame.draw.rect(screen, WHITE, rect)
                    pygame.draw.rect(screen, GRAY, rect, 1)

                if (x, y) in self.walls:
                    wall_img = self.get_scaled_texture('wall', tile_size)
                    if wall_img:
                        screen.blit(wall_img, rect)
                    else:
                        pygame.draw.rect(screen, DARK_GRAY, rect)
                        pygame.draw.rect(screen, BLACK, rect, 2)

                if (x, y) in self.goals:
                    goal_img = self.get_scaled_texture('goal', tile_size)
                    if goal_img:
                        screen.blit(goal_img, rect)
                    else:
                        pygame.draw.circle(screen, RED, rect.center, tile_size // 4)

                if (x, y) in self.boxes:
                    if self.anim_box is not None and (x, y) == self.anim_box and self.anim_progress < 1.0:
                        anim_box_pos = self.get_animated_pos(
                            self.anim_box_start, self.anim_box_target, self.anim_progress
                        )
                        if anim_box_pos:
                            anim_rect = pygame.Rect(
                                offset_x + anim_box_pos[0] * tile_size,
                                offset_y + anim_box_pos[1] * tile_size,
                                tile_size,
                                tile_size
                            )
                            if (x, y) in self.goals:
                                box_img = self.get_scaled_texture('box_on_goal', tile_size)
                            else:
                                box_img = self.get_scaled_texture('box', tile_size)
                            if box_img:
                                screen.blit(box_img, anim_rect)
                            else:
                                pygame.draw.rect(screen, BROWN, anim_rect)
                                pygame.draw.rect(screen, BLACK, anim_rect, 2)
                            continue

                    if (x, y) in self.goals:
                        box_img = self.get_scaled_texture('box_on_goal', tile_size)
                    else:
                        box_img = self.get_scaled_texture('box', tile_size)

                    if box_img:
                        screen.blit(box_img, rect)
                    else:
                        pygame.draw.rect(screen, BROWN, rect)
                        pygame.draw.rect(screen, BLACK, rect, 2)

        if player_draw_pos:
            px = player_draw_pos[0] - int(player_draw_pos[0])
            py = player_draw_pos[1] - int(player_draw_pos[1])
            player_rect = pygame.Rect(
                offset_x + (int(player_draw_pos[0]) + px) * tile_size,
                offset_y + (int(player_draw_pos[1]) + py) * tile_size,
                tile_size,
                tile_size
            )

            player_on_goal = (int(player_logic_pos[0]), int(player_logic_pos[1])) in self.goals
            if player_on_goal:
                player_img = self.get_scaled_texture('player_on_goal', tile_size)
            else:
                player_img = self.get_scaled_texture('player', tile_size)

            if player_img:
                screen.blit(player_img, player_rect)
            else:
                pygame.draw.circle(screen, BLUE, player_rect.center, tile_size // 3)

    def update(self, dt):
        self.update_animation(dt)

    def get_hint(self) -> Optional[Tuple[int, int]]:
        if len(self.boxes) > 3:
            return None

        initial = self.get_current_state()

        if self.check_win():
            return None

        queue = deque([(initial, [])])
        visited = {(initial.player, initial.boxes)}
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        max_states = 20000
        iterations = 0

        while queue and iterations < max_states:
            iterations += 1
            state, path = queue.popleft()

            for dx, dy in directions:
                new_state = self._apply_move(state, dx, dy)
                if new_state:
                    key = (new_state.player, new_state.boxes)
                    if key not in visited:
                        new_path = path + [(dx, dy)]

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
import pygame
import os
import time
from constants import *
from game import SokobanGame


class LevelEditor:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)

        self.tools = [
            {'key': '1', 'name': 'Стена', 'char': WALL, 'color': DARK_GRAY},
            {'key': '2', 'name': 'Игрок', 'char': PLAYER, 'color': BLUE},
            {'key': '3', 'name': 'Ящик', 'char': BOX, 'color': BROWN},
            {'key': '4', 'name': 'Цель', 'char': GOAL, 'color': RED},
            {'key': '5', 'name': 'Ластик', 'char': FLOOR, 'color': GRAY},
        ]
        self.current_tool = 0

        self.map_width = 14
        self.map_height = 11
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]
        self.goals = set()

        total_width = self.map_width * TILE_SIZE
        self.field_x = (SCREEN_WIDTH - TOOLBAR_WIDTH - total_width) // 2
        self.field_y = 50

        self.saved_levels = []
        self.selected_level_index = -1
        self.show_save_dialog = False
        self.filename_input = ""
        self.status_message = ""
        self.status_timer = 0
        self.button_rects = {}

        self.is_solvable = None
        self.solvability_message = ""
        self.solvability_timer = 0

        self.load_saved_levels_list()

    def load_saved_levels_list(self):
        self.saved_levels = []
        if os.path.exists("levels"):
            for f in os.listdir("levels"):
                if f.endswith(".txt") and not f.startswith("level"):
                    self.saved_levels.append(f)
        self.saved_levels.sort()

    def update_goals_set(self):
        self.goals.clear()
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.level[y][x] == GOAL or self.level[y][x] == BOX_ON_GOAL or self.level[y][x] == PLAYER_ON_GOAL:
                    self.goals.add((x, y))

    def is_deadlock_cell(self, x, y):
        self.update_goals_set()
        if (x, y) in self.goals or self.level[y][x] == GOAL:
            return False

        left_wall = x > 0 and self.level[y][x - 1] == WALL
        right_wall = x < self.map_width - 1 and self.level[y][x + 1] == WALL
        up_wall = y > 0 and self.level[y - 1][x] == WALL
        down_wall = y < self.map_height - 1 and self.level[y + 1][x] == WALL

        if (left_wall and up_wall) or (left_wall and down_wall) or (right_wall and up_wall) or (
                right_wall and down_wall):
            return True
        return False

    def draw_deadlock_overlay(self):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.set_alpha(100)
        s.fill(RED)

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.level[y][x] == BOX or self.level[y][x] == FLOOR or self.level[y][x] == ' ':
                    if self.is_deadlock_cell(x, y):
                        rect = pygame.Rect(
                            self.field_x + x * TILE_SIZE,
                            self.field_y + y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE
                        )
                        self.screen.blit(s, rect)

    def check_solvability(self):
        self.update_goals_set()
        temp_game = SokobanGame(self.level)

        if len(temp_game.boxes) > 5:
            self.solvability_message = "Ящиков >5"
            self.solvability_timer = 60
            return

        solution = temp_game.get_hint()

        if solution:
            self.is_solvable = True
            self.solvability_message = "РЕШАЕМ!"
        else:
            self.is_solvable = False
            self.solvability_message = "НЕРЕШАЕМ!"

        self.solvability_timer = 90

    def update_stats(self):
        self.box_count = sum(row.count(BOX) + row.count(BOX_ON_GOAL) for row in self.level)
        self.goal_count = sum(
            row.count(GOAL) + row.count(BOX_ON_GOAL) + row.count(PLAYER_ON_GOAL) for row in self.level)
        self.player_count = sum(row.count(PLAYER) + row.count(PLAYER_ON_GOAL) for row in self.level)
        self.is_valid = (self.box_count == self.goal_count and self.player_count == 1)

    def draw_tile(self, x, y, char):
        rect = pygame.Rect(self.field_x + x * TILE_SIZE, self.field_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

        if char == WALL:
            pygame.draw.rect(self.screen, DARK_GRAY, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
        elif char == FLOOR or char == ' ':
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
        elif char == PLAYER:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
            pygame.draw.circle(self.screen, BLUE, rect.center, TILE_SIZE // 3)
        elif char == BOX:
            pygame.draw.rect(self.screen, BROWN, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
        elif char == GOAL:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
            pygame.draw.circle(self.screen, RED, rect.center, TILE_SIZE // 4)
        else:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw(self):
        try:
            bg_editor = pygame.image.load("images/background.png").convert()
            bg_editor = pygame.transform.scale(bg_editor, self.screen.get_size())
            self.screen.blit(bg_editor, (0, 0))
        except:
            self.screen.fill((255, 230, 235))

        title = self.font.render("РЕДАКТОР УРОВНЕЙ", True, BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 5))

        field_rect = pygame.Rect(self.field_x - 3, self.field_y - 3, self.map_width * TILE_SIZE + 6,
                                 self.map_height * TILE_SIZE + 6)
        pygame.draw.rect(self.screen, BLUE, field_rect, 2)

        for y in range(self.map_height):
            for x in range(self.map_width):
                self.draw_tile(x, y, self.level[y][x])
                pygame.draw.rect(self.screen, GRAY,
                                 (self.field_x + x * TILE_SIZE, self.field_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)

        self.draw_deadlock_overlay()

        panel_x = SCREEN_WIDTH - TOOLBAR_WIDTH - 5
        panel_w = TOOLBAR_WIDTH

        pygame.draw.rect(self.screen, LIGHT_BLUE, (panel_x, 30, panel_w, SCREEN_HEIGHT - 40))
        pygame.draw.rect(self.screen, BLACK, (panel_x, 30, panel_w, SCREEN_HEIGHT - 40), 1)

        y = 45

        tools_title = self.small_font.render("ИНСТРУМЕНТЫ:", True, BLACK)
        self.screen.blit(tools_title, (panel_x + 10, y))
        y += 18

        for i, tool in enumerate(self.tools):
            btn_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, 24)
            if i == self.current_tool:
                pygame.draw.rect(self.screen, PINK, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 1)

            text = self.small_font.render(f"{tool['key']} - {tool['name']}", True, BLACK)
            self.screen.blit(text, (panel_x + 15, y + 4))

            self.button_rects[f"tool_{i}"] = btn_rect
            y += 28

        y += 5

        self.update_stats()
        stat_text = f"Ящ:{self.box_count} Цел:{self.goal_count} Игр:{self.player_count}"
        self.screen.blit(self.small_font.render(stat_text, True, BLACK), (panel_x + 10, y))
        y += 18

        if self.is_valid:
            self.screen.blit(self.small_font.render("ГОТОВО", True, GREEN), (panel_x + 10, y))
        else:
            self.screen.blit(self.small_font.render("НЕВЕРНО", True, RED), (panel_x + 10, y))
        y += 20

        btn_check = pygame.Rect(panel_x + 10, y, panel_w - 20, 28)
        pygame.draw.rect(self.screen, ORANGE, btn_check)
        pygame.draw.rect(self.screen, BLACK, btn_check, 1)
        self.screen.blit(self.small_font.render("ПРОВЕРИТЬ", True, BLACK), (btn_check.x + 50, btn_check.y + 6))
        self.button_rects["check"] = btn_check
        y += 35

        if self.solvability_timer > 0:
            msg_color = GREEN if "РЕШАЕМ" in self.solvability_message else RED
            msg_surface = self.small_font.render(self.solvability_message, True, msg_color)
            self.screen.blit(msg_surface, (panel_x + 10, y))
            self.solvability_timer -= 1
            y += 18

        y += 5

        list_title = self.small_font.render("МОИ УРОВНИ:", True, BLACK)
        self.screen.blit(list_title, (panel_x + 10, y))
        y += 18

        for i, name in enumerate(self.saved_levels[:4]):
            btn_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, 22)
            if i == self.selected_level_index:
                pygame.draw.rect(self.screen, YELLOW, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            text = self.small_font.render(name.replace(".txt", "")[:12], True, BLACK)
            self.screen.blit(text, (panel_x + 15, y + 4))
            self.button_rects[f"level_{i}"] = btn_rect
            y += 26

        y += 10

        btn_clear = pygame.Rect(panel_x + 10, y, panel_w - 20, 28)
        btn_save = pygame.Rect(panel_x + 10, y + 32, panel_w - 20, 28)
        btn_load = pygame.Rect(panel_x + 10, y + 64, panel_w - 20, 28)
        btn_back = pygame.Rect(panel_x + 10, y + 96, panel_w - 20, 28)

        pygame.draw.rect(self.screen, GREEN, btn_clear)
        pygame.draw.rect(self.screen, BLUE, btn_save)
        pygame.draw.rect(self.screen, ORANGE, btn_load)
        pygame.draw.rect(self.screen, RED, btn_back)

        pygame.draw.rect(self.screen, BLACK, btn_clear, 1)
        pygame.draw.rect(self.screen, BLACK, btn_save, 1)
        pygame.draw.rect(self.screen, BLACK, btn_load, 1)
        pygame.draw.rect(self.screen, BLACK, btn_back, 1)

        self.screen.blit(self.small_font.render("ОЧИСТИТЬ (C)", True, BLACK), (btn_clear.x + 45, btn_clear.y + 6))
        self.screen.blit(self.small_font.render("СОХРАНИТЬ (S)", True, BLACK), (btn_save.x + 40, btn_save.y + 6))
        self.screen.blit(self.small_font.render("ЗАГРУЗИТЬ (L)", True, BLACK), (btn_load.x + 40, btn_load.y + 6))
        self.screen.blit(self.small_font.render("НАЗАД (ESC)", True, BLACK), (btn_back.x + 40, btn_back.y + 6))

        self.button_rects["clear"] = btn_clear
        self.button_rects["save"] = btn_save
        self.button_rects["load"] = btn_load
        self.button_rects["back"] = btn_back

        if self.status_message and self.status_timer > 0:
            status_surface = self.small_font.render(self.status_message, True,
                                                    RED if "невалиден" in self.status_message else GREEN)
            self.screen.blit(status_surface, (panel_x + 10, SCREEN_HEIGHT - 25))
            self.status_timer -= 1

    def get_filename_dialog(self):
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 80, 300, 160)
        pygame.draw.rect(self.screen, WHITE, dialog_rect)
        pygame.draw.rect(self.screen, BLACK, dialog_rect, 2)

        label = self.font.render("Имя файла:", True, BLACK)
        self.screen.blit(label, (dialog_rect.x + 15, dialog_rect.y + 20))

        input_rect = pygame.Rect(dialog_rect.x + 15, dialog_rect.y + 55, 270, 35)
        pygame.draw.rect(self.screen, GRAY, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 1)

        text = self.font.render(self.filename_input + "█", True, BLACK)
        self.screen.blit(text, (input_rect.x + 8, input_rect.y + 8))

        ok_btn = pygame.Rect(dialog_rect.x + 50, dialog_rect.y + 110, 90, 35)
        cancel_btn = pygame.Rect(dialog_rect.x + 160, dialog_rect.y + 110, 90, 35)

        pygame.draw.rect(self.screen, GREEN, ok_btn)
        pygame.draw.rect(self.screen, RED, cancel_btn)
        pygame.draw.rect(self.screen, BLACK, ok_btn, 1)
        pygame.draw.rect(self.screen, BLACK, cancel_btn, 1)

        self.screen.blit(self.font.render("OK", True, BLACK), (ok_btn.x + 33, ok_btn.y + 8))
        self.screen.blit(self.font.render("ОТМЕНА", True, BLACK), (cancel_btn.x + 18, cancel_btn.y + 8))

        return ok_btn, cancel_btn

    def save_level(self, name):
        safe_name = os.path.basename(name)
        if not safe_name or safe_name.startswith('.'):
            self.status_message = "Недопустимое имя!"
            self.status_timer = 60
            return False

        while self.map_height > 0 and all(cell == ' ' for cell in self.level[-1]):
            self.level.pop()
            self.map_height -= 1

        if self.map_height > 0:
            while self.map_width > 0 and all(self.level[y][self.map_width - 1] == ' ' for y in range(self.map_height)):
                for y in range(self.map_height):
                    self.level[y].pop()
                self.map_width -= 1

        if self.map_height > 0:
            while self.map_width > 0 and all(self.level[y][0] == ' ' for y in range(self.map_height)):
                for y in range(self.map_height):
                    self.level[y].pop(0)
                self.map_width -= 1

        if not os.path.exists("levels"):
            os.makedirs("levels")

        filename = safe_name if safe_name.endswith(".txt") else safe_name + ".txt"
        filepath = os.path.join("levels", filename)

        with open(filepath, "w") as f:
            for y in range(self.map_height):
                row = ''.join(self.level[y]).rstrip()
                if row:
                    f.write(row + "\n")

        self.status_message = f"Сохранён: {filename}"
        self.status_timer = 60
        self.load_saved_levels_list()
        return True

    def load_level(self, filename):
        safe_name = os.path.basename(filename)
        filepath = os.path.join("levels", safe_name)
        if not os.path.exists(filepath):
            self.status_message = "Файл не найден!"
            self.status_timer = 60
            return False

        with open(filepath, "r") as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        self.map_height = len(lines)
        self.map_width = max(len(line) for line in lines) if lines else 14
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if x < self.map_width:
                    self.level[y][x] = char

        self.is_solvable = None
        self.solvability_message = ""
        self.solvability_timer = 0

        self.status_message = f"Загружен: {safe_name}"
        self.status_timer = 60
        return True

    def clear_level(self):
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]
        self.is_solvable = None
        self.solvability_message = ""
        self.solvability_timer = 0
        self.status_message = "Поле очищено"
        self.status_timer = 60

    def run(self):
        running = True

        while running:
            self.draw()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f or event.key == pygame.K_F11:
                        pass
                    if event.key == pygame.K_ESCAPE:
                        running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    for i, tool in enumerate(self.tools):
                        if event.unicode == tool['key']:
                            self.current_tool = i
                    if event.key == pygame.K_c:
                        self.clear_level()
                    if event.key == pygame.K_s:
                        self.show_save_dialog = True
                        self.filename_input = ""
                    if event.key == pygame.K_l:
                        if self.selected_level_index >= 0 and self.selected_level_index < len(self.saved_levels):
                            self.load_level(self.saved_levels[self.selected_level_index])
                        else:
                            self.status_message = "Выберите уровень!"
                            self.status_timer = 60

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()

                    if "clear" in self.button_rects and self.button_rects["clear"].collidepoint(x, y):
                        self.clear_level()
                    elif "save" in self.button_rects and self.button_rects["save"].collidepoint(x, y):
                        self.show_save_dialog = True
                        self.filename_input = ""
                    elif "load" in self.button_rects and self.button_rects["load"].collidepoint(x, y):
                        if self.selected_level_index >= 0 and self.selected_level_index < len(self.saved_levels):
                            self.load_level(self.saved_levels[self.selected_level_index])
                        else:
                            self.status_message = "Выберите уровень!"
                            self.status_timer = 60
                    elif "check" in self.button_rects and self.button_rects["check"].collidepoint(x, y):
                        self.update_stats()
                        if self.is_valid:
                            self.check_solvability()
                        else:
                            self.solvability_message = "НЕВЕРНО!"
                            self.solvability_timer = 60
                    elif "back" in self.button_rects and self.button_rects["back"].collidepoint(x, y):
                        running = False
                    else:
                        selected = False
                        for i in range(len(self.saved_levels)):
                            key = f"level_{i}"
                            if key in self.button_rects and self.button_rects[key].collidepoint(x, y):
                                self.selected_level_index = i
                                self.status_message = f"Выбран: {self.saved_levels[i]}"
                                self.status_timer = 30
                                selected = True
                                break

                        if not selected:
                            for i in range(len(self.tools)):
                                key = f"tool_{i}"
                                if key in self.button_rects and self.button_rects[key].collidepoint(x, y):
                                    self.current_tool = i
                                    break

                        field_rect = pygame.Rect(self.field_x, self.field_y, self.map_width * 35, self.map_height * 35)
                        if field_rect.collidepoint(x, y):
                            grid_x = (x - self.field_x) // 35
                            grid_y = (y - self.field_y) // 35
                            if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                                self.level[grid_y][grid_x] = self.tools[self.current_tool]['char']
                                self.is_solvable = None
                                self.solvability_message = ""
                                self.solvability_timer = 0

                elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                    x, y = pygame.mouse.get_pos()
                    field_rect = pygame.Rect(self.field_x, self.field_y, self.map_width * 35, self.map_height * 35)
                    if field_rect.collidepoint(x, y):
                        grid_x = (x - self.field_x) // 35
                        grid_y = (y - self.field_y) // 35
                        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                            self.level[grid_y][grid_x] = self.tools[self.current_tool]['char']
                            self.is_solvable = None
                            self.solvability_message = ""
                            self.solvability_timer = 0

            if self.show_save_dialog:
                ok_btn, cancel_btn = self.get_filename_dialog()
                pygame.display.flip()

                waiting = True
                while waiting:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            waiting = False
                            running = False
                        elif e.type == pygame.KEYDOWN:
                            if e.key == pygame.K_RETURN:
                                if self.filename_input.strip():
                                    self.save_level(self.filename_input.strip())
                                self.show_save_dialog = False
                                self.filename_input = ""
                                waiting = False
                            elif e.key == pygame.K_BACKSPACE:
                                self.filename_input = self.filename_input[:-1]
                            elif e.unicode.isprintable() and len(self.filename_input) < 20:
                                self.filename_input += e.unicode
                        elif e.type == pygame.MOUSEBUTTONDOWN:
                            if ok_btn.collidepoint(e.pos):
                                if self.filename_input.strip():
                                    self.save_level(self.filename_input.strip())
                                self.show_save_dialog = False
                                self.filename_input = ""
                                waiting = False
                            elif cancel_btn.collidepoint(e.pos):
                                self.show_save_dialog = False
                                self.filename_input = ""
                                waiting = False
                    self.draw()
                    ok_btn, cancel_btn = self.get_filename_dialog()
                    pygame.display.flip()
                    self.clock.tick(30)

            self.clock.tick(60)

        return "menu"
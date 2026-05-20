import pygame
import os
import subprocess
import sys

# Константы
TILE_SIZE = 30
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Цвета
WHITE = (255, 250, 240)
BLACK = (45, 45, 65)
GRAY = (200, 190, 190)
DARK_GRAY = (150, 140, 150)
BROWN = (180, 140, 110)
BLUE = (180, 160, 210)
RED = (210, 130, 140)
GREEN = (140, 200, 160)
YELLOW = (240, 210, 140)
PINK = (245, 220, 230)
LIGHT_BLUE = (200, 220, 240)
ORANGE = (255, 200, 150)

TOOLS = [
    {'key': '1', 'name': 'Стена', 'char': '#', 'color': DARK_GRAY},
    {'key': '2', 'name': 'Пол', 'char': ' ', 'color': WHITE},
    {'key': '3', 'name': 'Игрок', 'char': '@', 'color': BLUE},
    {'key': '4', 'name': 'Ящик', 'char': '$', 'color': BROWN},
    {'key': '5', 'name': 'Цель', 'char': '.', 'color': RED},
    {'key': '6', 'name': 'Ластик', 'char': ' ', 'color': GRAY},
]


class LevelEditor:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        self.title_font = pygame.font.Font(None, 24)

        self.current_tool = 1
        self.map_width = 12
        self.map_height = 10
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]

        self.saved_levels = []
        self.selected_level_index = -1
        self.show_name_input = False
        self.name_input_text = ""
        self.status_message = ""
        self.status_timer = 0

        self.load_saved_levels_list()
        self.update_stats()

    def load_saved_levels_list(self):
        self.saved_levels = []
        if os.path.exists("levels"):
            for f in os.listdir("levels"):
                if f.endswith(".txt") and not f.startswith("level"):
                    self.saved_levels.append(f)
        self.saved_levels.sort()

    def update_stats(self):
        self.box_count = sum(row.count('$') + row.count('*') for row in self.level)
        self.goal_count = sum(row.count('.') + row.count('*') + row.count('+') for row in self.level)
        self.player_count = sum(row.count('@') + row.count('+') for row in self.level)
        self.is_valid = (self.box_count == self.goal_count and self.player_count == 1)

    def draw_tile(self, x, y, char):
        rect = pygame.Rect(x * TILE_SIZE + 5, y * TILE_SIZE + 40, TILE_SIZE, TILE_SIZE)

        if char == '#':
            pygame.draw.rect(self.screen, DARK_GRAY, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
        elif char == ' ':
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
        elif char == '@':
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
            pygame.draw.circle(self.screen, BLUE, rect.center, TILE_SIZE // 3)
        elif char == '$':
            pygame.draw.rect(self.screen, BROWN, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
        elif char == '.':
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
            pygame.draw.circle(self.screen, RED, rect.center, TILE_SIZE // 4)
        elif char == '*':
            pygame.draw.rect(self.screen, BROWN, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)
            pygame.draw.circle(self.screen, GREEN, rect.center, TILE_SIZE // 4)
        else:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw(self):
        self.screen.fill(WHITE)

        title = self.title_font.render("РЕДАКТОР УРОВНЕЙ", True, BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 5))

        for y in range(self.map_height):
            for x in range(self.map_width):
                self.draw_tile(x, y, self.level[y][x])

        panel_x = self.map_width * TILE_SIZE + 10
        panel_w = SCREEN_WIDTH - panel_x - 5

        pygame.draw.rect(self.screen, LIGHT_BLUE, (panel_x, 40, panel_w, SCREEN_HEIGHT - 45))
        pygame.draw.rect(self.screen, BLACK, (panel_x, 40, panel_w, SCREEN_HEIGHT - 45), 1)

        y_offset = 50
        for i, tool in enumerate(TOOLS):
            btn_rect = pygame.Rect(panel_x + 5, y_offset, panel_w - 10, 28)
            if i == self.current_tool:
                pygame.draw.rect(self.screen, PINK, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 1)

            key_text = self.small_font.render(f"[{tool['key']}]", True, BLACK)
            self.screen.blit(key_text, (panel_x + 8, y_offset + 6))

            name_text = self.small_font.render(tool['name'], True, BLACK)
            self.screen.blit(name_text, (panel_x + 50, y_offset + 6))

            y_offset += 32

        y_offset += 5
        stat_title = self.small_font.render("ПРОВЕРКА", True, BLACK)
        self.screen.blit(stat_title, (panel_x + panel_w // 2 - stat_title.get_width() // 2, y_offset))
        y_offset += 18

        stats = [f"Ящики: {self.box_count}", f"Цели: {self.goal_count}", f"Игроки: {self.player_count}"]
        for s in stats:
            text = self.small_font.render(s, True, BLACK)
            self.screen.blit(text, (panel_x + 8, y_offset))
            y_offset += 16

        y_offset += 5
        if self.is_valid:
            valid_text = self.small_font.render("ГОТОВО!", True, GREEN)
        else:
            valid_text = self.small_font.render("НЕВЕРНО!", True, RED)
        self.screen.blit(valid_text, (panel_x + 8, y_offset))

        y_offset += 25
        buttons = [
            {"name": "НОВЫЙ", "y": y_offset, "color": GREEN, "action": "new"},
            {"name": "СОХР", "y": y_offset + 30, "color": BLUE, "action": "save"},
            {"name": "ЗАГР", "y": y_offset + 60, "color": ORANGE, "action": "load"},
            {"name": "НАЗАД", "y": y_offset + 90, "color": RED, "action": "back"},
        ]

        self.button_rects = {}
        for btn in buttons:
            btn_rect = pygame.Rect(panel_x + 5, btn["y"], panel_w - 10, 28)
            pygame.draw.rect(self.screen, btn["color"], btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            text = self.small_font.render(btn["name"], True, BLACK)
            self.screen.blit(text, (btn_rect.centerx - text.get_width() // 2, btn_rect.centery - 7))
            self.button_rects[btn["action"]] = btn_rect

        if self.saved_levels:
            y_offset += 130
            list_title = self.small_font.render("МОИ УРОВНИ:", True, BLACK)
            self.screen.blit(list_title, (panel_x + 8, y_offset))
            y_offset += 18

            for i, level_file in enumerate(self.saved_levels[:5]):
                level_rect = pygame.Rect(panel_x + 5, y_offset, panel_w - 10, 22)
                if i == self.selected_level_index:
                    pygame.draw.rect(self.screen, YELLOW, level_rect)
                pygame.draw.rect(self.screen, BLACK, level_rect, 1)
                name_text = self.small_font.render(level_file.replace(".txt", "")[:15], True, BLACK)
                self.screen.blit(name_text, (panel_x + 10, y_offset + 4))
                y_offset += 24
                self.button_rects[f"level_{i}"] = level_rect

        if self.status_message and self.status_timer > 0:
            status_surface = self.small_font.render(self.status_message, True,
                                                    GREEN if "сохранён" in self.status_message else RED)
            self.screen.blit(status_surface, (panel_x + 5, SCREEN_HEIGHT - 22))
            self.status_timer -= 1

    def draw_name_dialog(self):
        """Рисует диалог ввода имени и возвращает кнопки"""
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 70, 300, 140)
        pygame.draw.rect(self.screen, WHITE, dialog_rect)
        pygame.draw.rect(self.screen, BLACK, dialog_rect, 2)

        label = self.small_font.render("Имя уровня:", True, BLACK)
        self.screen.blit(label, (dialog_rect.x + 15, dialog_rect.y + 15))

        input_rect = pygame.Rect(dialog_rect.x + 15, dialog_rect.y + 45, 270, 30)
        pygame.draw.rect(self.screen, GRAY, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 1)

        text = self.small_font.render(self.name_input_text + "|", True, BLACK)
        self.screen.blit(text, (input_rect.x + 5, input_rect.y + 6))

        ok_btn = pygame.Rect(dialog_rect.x + 60, dialog_rect.y + 95, 70, 30)
        cancel_btn = pygame.Rect(dialog_rect.x + 170, dialog_rect.y + 95, 70, 30)
        pygame.draw.rect(self.screen, GREEN, ok_btn)
        pygame.draw.rect(self.screen, RED, cancel_btn)
        pygame.draw.rect(self.screen, BLACK, ok_btn, 1)
        pygame.draw.rect(self.screen, BLACK, cancel_btn, 1)

        self.screen.blit(self.small_font.render("OK", True, BLACK), (ok_btn.x + 25, ok_btn.y + 8))
        self.screen.blit(self.small_font.render("НЕТ", True, BLACK), (cancel_btn.x + 22, cancel_btn.y + 8))

        return ok_btn, cancel_btn

    def save_level(self, name):
        if not self.is_valid:
            self.status_message = "Уровень невалиден!"
            self.status_timer = 60
            return False

        if not os.path.exists("levels"):
            os.makedirs("levels")

        filename = name if name.endswith(".txt") else name + ".txt"
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
        filepath = os.path.join("levels", filename)
        if not os.path.exists(filepath):
            self.status_message = "Файл не найден!"
            self.status_timer = 60
            return False

        with open(filepath, "r") as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        self.map_height = len(lines)
        self.map_width = max(len(line) for line in lines) if lines else 12
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if x < self.map_width:
                    self.level[y][x] = char

        self.update_stats()
        self.status_message = f"Загружен: {filename}"
        self.status_timer = 60
        return True

    def clear_level(self):
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]
        self.update_stats()
        self.status_message = "Поле очищено"
        self.status_timer = 60

    def run(self):
        running = True

        while running:
            self.draw()
            pygame.display.flip()

            # ДИАЛОГ СОХРАНЕНИЯ
            if self.show_name_input:
                ok_btn, cancel_btn = self.draw_name_dialog()
                pygame.display.flip()

                waiting = True
                while waiting:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            running = False
                            waiting = False
                        elif e.type == pygame.KEYDOWN:
                            if e.key == pygame.K_RETURN:
                                if self.name_input_text.strip():
                                    self.save_level(self.name_input_text.strip())
                                self.show_name_input = False
                                self.name_input_text = ""
                                waiting = False
                            elif e.key == pygame.K_BACKSPACE:
                                self.name_input_text = self.name_input_text[:-1]
                            elif e.unicode.isprintable() and len(self.name_input_text) < 20:
                                self.name_input_text += e.unicode
                        elif e.type == pygame.MOUSEBUTTONDOWN:
                            x, y = e.pos
                            if ok_btn.collidepoint(x, y):
                                if self.name_input_text.strip():
                                    self.save_level(self.name_input_text.strip())
                                self.show_name_input = False
                                self.name_input_text = ""
                                waiting = False
                            elif cancel_btn.collidepoint(x, y):
                                self.show_name_input = False
                                self.name_input_text = ""
                                waiting = False
                    self.draw()
                    ok_btn, cancel_btn = self.draw_name_dialog()
                    pygame.display.flip()
                    self.clock.tick(30)
                continue

            # ОСНОВНЫЕ СОБЫТИЯ
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    for i, tool in enumerate(TOOLS):
                        if event.unicode == tool['key']:
                            self.current_tool = i

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    panel_x = self.map_width * TILE_SIZE + 10

                    if "new" in self.button_rects and self.button_rects["new"].collidepoint(x, y):
                        self.clear_level()
                    elif "save" in self.button_rects and self.button_rects["save"].collidepoint(x, y):
                        if self.is_valid:
                            self.show_name_input = True
                            self.name_input_text = ""
                        else:
                            self.status_message = "Уровень невалиден!"
                            self.status_timer = 60
                    elif "load" in self.button_rects and self.button_rects["load"].collidepoint(x, y):
                        if self.selected_level_index >= 0 and self.selected_level_index < len(self.saved_levels):
                            self.load_level(self.saved_levels[self.selected_level_index])
                    elif "back" in self.button_rects and self.button_rects["back"].collidepoint(x, y):
                        running = False
                    else:
                        for i in range(len(self.saved_levels)):
                            if f"level_{i}" in self.button_rects and self.button_rects[f"level_{i}"].collidepoint(x, y):
                                self.selected_level_index = i
                                self.status_message = f"Выбран: {self.saved_levels[i]}"
                                self.status_timer = 30

                        y_offset = 50
                        for i in range(len(TOOLS)):
                            btn_rect = pygame.Rect(panel_x + 5, y_offset + i * 32, SCREEN_WIDTH - panel_x - 15, 28)
                            if btn_rect.collidepoint(x, y):
                                self.current_tool = i

                        if 5 <= x < self.map_width * TILE_SIZE + 5 and 40 <= y < self.map_height * TILE_SIZE + 40:
                            grid_x = (x - 5) // TILE_SIZE
                            grid_y = (y - 40) // TILE_SIZE
                            if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                                self.level[grid_y][grid_x] = TOOLS[self.current_tool]['char']
                                self.update_stats()

                elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                    x, y = pygame.mouse.get_pos()
                    if 5 <= x < self.map_width * TILE_SIZE + 5 and 40 <= y < self.map_height * TILE_SIZE + 40:
                        grid_x = (x - 5) // TILE_SIZE
                        grid_y = (y - 40) // TILE_SIZE
                        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                            self.level[grid_y][grid_x] = TOOLS[self.current_tool]['char']
                            self.update_stats()

            self.clock.tick(60)

        return "menu"
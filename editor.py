import pygame
import os
from constants import TILE_SIZE, EDITOR_WIDTH, EDITOR_HEIGHT, TOOLBAR_WIDTH
from constants import WHITE, BLACK, GRAY, DARK_GRAY, BROWN, BLUE, RED, GREEN, YELLOW, PINK, LIGHT_BLUE, ORANGE
from constants import WALL, FLOOR, PLAYER, BOX, GOAL, BOX_ON_GOAL, PLAYER_ON_GOAL


class LevelEditor:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Инструменты: убрали "Пол", оставили только Ластик
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

        total_width = self.map_width * TILE_SIZE
        self.field_x = (EDITOR_WIDTH - TOOLBAR_WIDTH - total_width) // 2
        self.field_y = 80

        self.saved_levels = []
        self.selected_level_index = -1
        self.show_save_dialog = False
        self.filename_input = ""
        self.status_message = ""
        self.status_timer = 0
        self.button_rects = {}

        self.load_saved_levels_list()

    def load_saved_levels_list(self):
        self.saved_levels = []
        if os.path.exists("levels"):
            for f in os.listdir("levels"):
                if f.endswith(".txt") and not f.startswith("level"):
                    self.saved_levels.append(f)
        self.saved_levels.sort()

    def draw_tile(self, x, y, char):
        rect = pygame.Rect(self.field_x + x * TILE_SIZE, self.field_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

        if char == WALL:
            pygame.draw.rect(self.screen, DARK_GRAY, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
        elif char == FLOOR or char == ' ':
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
        elif char == PLAYER:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
            pygame.draw.circle(self.screen, BLUE, rect.center, TILE_SIZE // 3)
        elif char == BOX:
            pygame.draw.rect(self.screen, BROWN, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
        elif char == GOAL:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)
            pygame.draw.circle(self.screen, RED, rect.center, TILE_SIZE // 4)
        else:
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw(self):
        self.screen.fill(WHITE)

        title = self.font.render("РЕДАКТОР УРОВНЕЙ", True, BLUE)
        self.screen.blit(title, (EDITOR_WIDTH // 2 - title.get_width() // 2, 15))

        field_rect = pygame.Rect(self.field_x - 3, self.field_y - 3, self.map_width * TILE_SIZE + 6,
                                 self.map_height * TILE_SIZE + 6)
        pygame.draw.rect(self.screen, BLUE, field_rect, 2)

        for y in range(self.map_height):
            for x in range(self.map_width):
                self.draw_tile(x, y, self.level[y][x])
                pygame.draw.rect(self.screen, GRAY,
                                 (self.field_x + x * TILE_SIZE, self.field_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)

        panel_x = EDITOR_WIDTH - TOOLBAR_WIDTH - 15
        panel_w = TOOLBAR_WIDTH

        pygame.draw.rect(self.screen, LIGHT_BLUE, (panel_x, 50, panel_w, EDITOR_HEIGHT - 70))
        pygame.draw.rect(self.screen, BLACK, (panel_x, 50, panel_w, EDITOR_HEIGHT - 70), 2)

        y = 70

        list_title = self.font.render("Мои уровни:", True, BLACK)
        self.screen.blit(list_title, (panel_x + 15, y))
        y += 30

        for i, name in enumerate(self.saved_levels[:5]):
            btn_rect = pygame.Rect(panel_x + 15, y, panel_w - 30, 30)
            if i == self.selected_level_index:
                pygame.draw.rect(self.screen, YELLOW, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            text = self.small_font.render(name.replace(".txt", "")[:15], True, BLACK)
            self.screen.blit(text, (panel_x + 20, y + 7))
            self.button_rects[f"level_{i}"] = btn_rect
            y += 35

        y += 15

        tools_title = self.font.render("Инструменты:", True, BLACK)
        self.screen.blit(tools_title, (panel_x + 15, y))
        y += 30

        for i, tool in enumerate(self.tools):
            btn_rect = pygame.Rect(panel_x + 15, y, panel_w - 30, 38)
            if i == self.current_tool:
                pygame.draw.rect(self.screen, PINK, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 2)

            text = self.font.render(f"{tool['key']} - {tool['name']}", True, BLACK)
            self.screen.blit(text, (panel_x + 25, y + 10))

            self.button_rects[f"tool_{i}"] = btn_rect
            y += 45

        y += 15

        box_count = sum(row.count(BOX) + row.count(BOX_ON_GOAL) for row in self.level)
        goal_count = sum(row.count(GOAL) + row.count(BOX_ON_GOAL) + row.count(PLAYER_ON_GOAL) for row in self.level)
        player_count = sum(row.count(PLAYER) + row.count(PLAYER_ON_GOAL) for row in self.level)
        is_valid = (box_count == goal_count and player_count == 1)

        stat_text = f"Ящики:{box_count} Цели:{goal_count} Игрок:{player_count}"
        self.screen.blit(self.small_font.render(stat_text, True, BLACK), (panel_x + 15, y))
        y += 25

        if is_valid:
            self.screen.blit(self.font.render("ГОТОВО", True, GREEN), (panel_x + 15, y))
        else:
            self.screen.blit(self.font.render("НЕВЕРНО", True, RED), (panel_x + 15, y))

        y += 55

        btn_clear = pygame.Rect(panel_x + 15, y, panel_w - 30, 42)
        btn_save = pygame.Rect(panel_x + 15, y + 50, panel_w - 30, 42)
        btn_load = pygame.Rect(panel_x + 15, y + 100, panel_w - 30, 42)
        btn_back = pygame.Rect(panel_x + 15, y + 150, panel_w - 30, 42)

        pygame.draw.rect(self.screen, GREEN, btn_clear)
        pygame.draw.rect(self.screen, BLUE, btn_save)
        pygame.draw.rect(self.screen, ORANGE, btn_load)
        pygame.draw.rect(self.screen, RED, btn_back)

        pygame.draw.rect(self.screen, BLACK, btn_clear, 2)
        pygame.draw.rect(self.screen, BLACK, btn_save, 2)
        pygame.draw.rect(self.screen, BLACK, btn_load, 2)
        pygame.draw.rect(self.screen, BLACK, btn_back, 2)

        self.screen.blit(self.font.render("ОЧИСТИТЬ ВСЁ (C)", True, BLACK), (btn_clear.x + 40, btn_clear.y + 12))
        self.screen.blit(self.font.render("СОХРАНИТЬ (S)", True, BLACK), (btn_save.x + 55, btn_save.y + 12))
        self.screen.blit(self.font.render("ЗАГРУЗИТЬ (L)", True, BLACK), (btn_load.x + 55, btn_load.y + 12))
        self.screen.blit(self.font.render("НАЗАД (ESC)", True, BLACK), (btn_back.x + 65, btn_back.y + 12))

        self.button_rects["clear"] = btn_clear
        self.button_rects["save"] = btn_save
        self.button_rects["load"] = btn_load
        self.button_rects["back"] = btn_back

        if self.status_message and self.status_timer > 0:
            status_surface = self.small_font.render(self.status_message, True,
                                                    RED if "невалиден" in self.status_message else GREEN)
            self.screen.blit(status_surface, (panel_x + 15, EDITOR_HEIGHT - 45))
            self.status_timer -= 1

    def get_filename_dialog(self):
        dialog_rect = pygame.Rect(EDITOR_WIDTH // 2 - 200, EDITOR_HEIGHT // 2 - 100, 400, 200)
        pygame.draw.rect(self.screen, WHITE, dialog_rect)
        pygame.draw.rect(self.screen, BLACK, dialog_rect, 3)

        label = self.font.render("Имя файла:", True, BLACK)
        self.screen.blit(label, (dialog_rect.x + 20, dialog_rect.y + 30))

        input_rect = pygame.Rect(dialog_rect.x + 20, dialog_rect.y + 70, 360, 40)
        pygame.draw.rect(self.screen, GRAY, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)

        text = self.font.render(self.filename_input + "█", True, BLACK)
        self.screen.blit(text, (input_rect.x + 10, input_rect.y + 10))

        ok_btn = pygame.Rect(dialog_rect.x + 60, dialog_rect.y + 130, 120, 40)
        cancel_btn = pygame.Rect(dialog_rect.x + 220, dialog_rect.y + 130, 120, 40)

        pygame.draw.rect(self.screen, GREEN, ok_btn)
        pygame.draw.rect(self.screen, RED, cancel_btn)
        pygame.draw.rect(self.screen, BLACK, ok_btn, 2)
        pygame.draw.rect(self.screen, BLACK, cancel_btn, 2)

        self.screen.blit(self.font.render("ОК", True, BLACK), (ok_btn.x + 45, ok_btn.y + 10))
        self.screen.blit(self.font.render("ОТМЕНА", True, BLACK), (cancel_btn.x + 30, cancel_btn.y + 10))

        return ok_btn, cancel_btn

    def save_level(self, name):
        safe_name = os.path.basename(name)
        if not safe_name or safe_name.startswith('.'):
            self.status_message = "Недопустимое имя файла!"
            self.status_timer = 60
            return False

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

        self.status_message = f"Загружен: {safe_name}"
        self.status_timer = 60
        return True

    def clear_level(self):
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]
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
                            self.status_message = "Выберите уровень из списка!"
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
                            self.status_message = "Выберите уровень из списка!"
                            self.status_timer = 60
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

                        field_rect = pygame.Rect(self.field_x, self.field_y, self.map_width * TILE_SIZE,
                                                 self.map_height * TILE_SIZE)
                        if field_rect.collidepoint(x, y):
                            grid_x = (x - self.field_x) // TILE_SIZE
                            grid_y = (y - self.field_y) // TILE_SIZE
                            if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                                self.level[grid_y][grid_x] = self.tools[self.current_tool]['char']

                elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                    x, y = pygame.mouse.get_pos()
                    field_rect = pygame.Rect(self.field_x, self.field_y, self.map_width * TILE_SIZE,
                                             self.map_height * TILE_SIZE)
                    if field_rect.collidepoint(x, y):
                        grid_x = (x - self.field_x) // TILE_SIZE
                        grid_y = (y - self.field_y) // TILE_SIZE
                        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                            self.level[grid_y][grid_x] = self.tools[self.current_tool]['char']

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
                            elif e.unicode.isprintable() and len(self.filename_input) < 30:
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
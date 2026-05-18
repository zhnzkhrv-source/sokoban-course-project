import pygame
import os

TILE_SIZE = 50
EDITOR_WIDTH = 900
TOOLBAR_WIDTH = 300
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)

WALL = '#'
FLOOR = ' '
PLAYER = '@'
BOX = '$'
GOAL = '.'
BOX_ON_GOAL = '*'
PLAYER_ON_GOAL = '+'


class LevelEditor:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 36)

        self.tools = [
            {'key': '1', 'name': 'Стена', 'char': WALL, 'color': DARK_GRAY},
            {'key': '2', 'name': 'Пол', 'char': FLOOR, 'color': WHITE},
            {'key': '3', 'name': 'Игрок', 'char': PLAYER, 'color': BLUE},
            {'key': '4', 'name': 'Ящик', 'char': BOX, 'color': BROWN},
            {'key': '5', 'name': 'Цель', 'char': GOAL, 'color': RED},
            {'key': '6', 'name': 'Ящик на цели', 'char': BOX_ON_GOAL, 'color': GREEN},
            {'key': '7', 'name': 'Игрок на цели', 'char': PLAYER_ON_GOAL, 'color': ORANGE},
        ]
        self.current_tool = 0

        self.map_width = 20
        self.map_height = 15
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]

        self.show_save_dialog = False
        self.show_load_dialog = False
        self.filename_input = ""
        self.status_message = ""
        self.status_timer = 0

    def get_filename_input(self):
        """Ввод имени файла в pygame-окне"""
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)
        pygame.draw.rect(self.screen, WHITE, dialog_rect)
        pygame.draw.rect(self.screen, BLACK, dialog_rect, 3)

        label = self.font.render("Введите имя файла:", True, BLACK)
        self.screen.blit(label, (dialog_rect.x + 20, dialog_rect.y + 30))

        # Поле ввода
        input_rect = pygame.Rect(dialog_rect.x + 20, dialog_rect.y + 70, 360, 40)
        pygame.draw.rect(self.screen, GRAY, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)

        text = self.font.render(self.filename_input + "█", True, BLACK)
        self.screen.blit(text, (input_rect.x + 10, input_rect.y + 10))

        # Кнопки
        save_btn = pygame.Rect(dialog_rect.x + 50, dialog_rect.y + 130, 120, 40)
        cancel_btn = pygame.Rect(dialog_rect.x + 230, dialog_rect.y + 130, 120, 40)

        pygame.draw.rect(self.screen, GREEN, save_btn)
        pygame.draw.rect(self.screen, RED, cancel_btn)
        pygame.draw.rect(self.screen, BLACK, save_btn, 2)
        pygame.draw.rect(self.screen, BLACK, cancel_btn, 2)

        save_text = self.font.render("СОХРАНИТЬ", True, BLACK)
        cancel_text = self.font.render("ОТМЕНА", True, BLACK)

        self.screen.blit(save_text, (save_btn.x + 20, save_btn.y + 10))
        self.screen.blit(cancel_text, (cancel_btn.x + 30, cancel_btn.y + 10))

        return save_btn, cancel_btn

    def save_level(self):
        """Сохраняет уровень в файл"""
        if not self.filename_input:
            self.status_message = "Имя файла не может быть пустым"
            self.status_timer = 60
            return False

        if not os.path.exists("levels"):
            os.makedirs("levels")

        filename = self.filename_input
        if not filename.endswith(".txt"):
            filename += ".txt"

        # Убираем пустые строки и колонки
        while self.map_height > 0 and all(cell == ' ' for cell in self.level[-1]):
            self.level.pop()
            self.map_height -= 1

        while self.map_width > 0 and all(self.level[y][self.map_width - 1] == ' ' for y in range(self.map_height)):
            for y in range(self.map_height):
                self.level[y].pop()
            self.map_width -= 1

        filepath = os.path.join("levels", filename)
        with open(filepath, "w") as f:
            for y in range(self.map_height):
                line = ''.join(self.level[y][:self.map_width])
                f.write(line.rstrip() + "\n")

        self.status_message = f"Сохранено: {filename}"
        self.status_timer = 60
        return True

    def load_level(self):
        """Загружает уровень из файла"""
        if not self.filename_input:
            self.status_message = "Введите имя файла"
            self.status_timer = 60
            return False

        filename = self.filename_input
        if not filename.endswith(".txt"):
            filename += ".txt"

        filepath = os.path.join("levels", filename)
        if not os.path.exists(filepath):
            self.status_message = f"Файл не найден: {filename}"
            self.status_timer = 60
            return False

        with open(filepath, "r") as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        self.map_height = len(lines)
        self.map_width = max(len(line) for line in lines) if lines else 20
        self.level = [[' ' for _ in range(self.map_width)] for _ in range(self.map_height)]

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if x < self.map_width:
                    self.level[y][x] = char

        self.status_message = f"Загружено: {filename}"
        self.status_timer = 60
        return True

    def draw(self):
        self.screen.fill(WHITE)

        for y in range(self.map_height):
            for x in range(self.map_width):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                char = self.level[y][x]

                if char == WALL:
                    pygame.draw.rect(self.screen, DARK_GRAY, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 2)
                elif char == FLOOR or char == ' ':
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pygame.draw.rect(self.screen, GRAY, rect, 1)
                elif char == PLAYER:
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pygame.draw.circle(self.screen, BLUE, rect.center, TILE_SIZE // 3)
                elif char == BOX:
                    pygame.draw.rect(self.screen, BROWN, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 2)
                elif char == GOAL:
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pygame.draw.circle(self.screen, RED, rect.center, TILE_SIZE // 4)
                elif char == BOX_ON_GOAL:
                    pygame.draw.rect(self.screen, BROWN, rect)
                    pygame.draw.circle(self.screen, GREEN, rect.center, TILE_SIZE // 4)
                elif char == PLAYER_ON_GOAL:
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pygame.draw.circle(self.screen, BLUE, rect.center, TILE_SIZE // 3)
                    pygame.draw.circle(self.screen, RED, rect.center, TILE_SIZE // 4)
                else:
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pygame.draw.rect(self.screen, GRAY, rect, 1)

        # Сетка
        for x in range(self.map_width):
            for y in range(self.map_height):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, GRAY, rect, 1)

        # Тулбар
        toolbar_rect = pygame.Rect(EDITOR_WIDTH, 0, TOOLBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, LIGHT_BLUE, toolbar_rect)
        pygame.draw.rect(self.screen, BLACK, toolbar_rect, 3)

        title = self.big_font.render("ИНСТРУМЕНТЫ", True, BLACK)
        self.screen.blit(title, (EDITOR_WIDTH + 50, 20))

        y_offset = 80
        for i, tool in enumerate(self.tools):
            tool_rect = pygame.Rect(EDITOR_WIDTH + 20, y_offset, 260, 50)
            if i == self.current_tool:
                pygame.draw.rect(self.screen, YELLOW, tool_rect)
            pygame.draw.rect(self.screen, BLACK, tool_rect, 2)

            key_text = self.font.render(f"[{tool['key']}]", True, BLACK)
            self.screen.blit(key_text, (EDITOR_WIDTH + 30, y_offset + 15))

            name_text = self.font.render(tool['name'], True, BLACK)
            self.screen.blit(name_text, (EDITOR_WIDTH + 80, y_offset + 15))

            y_offset += 60

        # Кнопки
        save_btn = pygame.Rect(EDITOR_WIDTH + 50, SCREEN_HEIGHT - 200, 200, 50)
        load_btn = pygame.Rect(EDITOR_WIDTH + 50, SCREEN_HEIGHT - 130, 200, 50)
        back_btn = pygame.Rect(EDITOR_WIDTH + 50, SCREEN_HEIGHT - 60, 200, 50)

        pygame.draw.rect(self.screen, GREEN, save_btn)
        pygame.draw.rect(self.screen, ORANGE, load_btn)
        pygame.draw.rect(self.screen, RED, back_btn)
        pygame.draw.rect(self.screen, BLACK, save_btn, 2)
        pygame.draw.rect(self.screen, BLACK, load_btn, 2)
        pygame.draw.rect(self.screen, BLACK, back_btn, 2)

        self.screen.blit(self.font.render("СОХРАНИТЬ", True, BLACK), (save_btn.x + 50, save_btn.y + 15))
        self.screen.blit(self.font.render("ЗАГРУЗИТЬ", True, BLACK), (load_btn.x + 50, load_btn.y + 15))
        self.screen.blit(self.font.render("НАЗАД", True, BLACK), (back_btn.x + 60, back_btn.y + 15))

        box_count = sum(row.count(BOX) + row.count(BOX_ON_GOAL) for row in self.level)
        goal_count = sum(row.count(GOAL) + row.count(BOX_ON_GOAL) + row.count(PLAYER_ON_GOAL) for row in self.level)
        stats_color = BLACK if box_count == goal_count else RED
        stats_text = self.font.render(f"Ящики: {box_count} | Цели: {goal_count}", True, stats_color)
        self.screen.blit(stats_text, (EDITOR_WIDTH + 30, SCREEN_HEIGHT - 250))

        if self.status_message and self.status_timer > 0:
            status_surface = self.font.render(self.status_message, True,
                                              GREEN if "Сохранено" in self.status_message or "Загружено" in self.status_message else RED)
            self.screen.blit(status_surface, (EDITOR_WIDTH + 30, SCREEN_HEIGHT - 280))
            self.status_timer -= 1

        if self.show_save_dialog:
            save_btn, cancel_btn = self.get_filename_input()
            pygame.display.flip()

            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_RETURN:
                            if self.save_level():
                                self.show_save_dialog = False
                                self.filename_input = ""
                            waiting = False
                        elif e.key == pygame.K_BACKSPACE:
                            self.filename_input = self.filename_input[:-1]
                        elif e.unicode.isprintable():
                            self.filename_input += e.unicode
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        if save_btn.collidepoint(e.pos):
                            if self.save_level():
                                self.show_save_dialog = False
                                self.filename_input = ""
                            waiting = False
                        elif cancel_btn.collidepoint(e.pos):
                            self.show_save_dialog = False
                            self.filename_input = ""
                            waiting = False
                    elif e.type == pygame.QUIT:
                        waiting = False
                        return False
                self.draw()
                save_btn, cancel_btn = self.get_filename_input()
                pygame.display.flip()
                self.clock.tick(30)

        if self.show_load_dialog:
            save_btn, cancel_btn = self.get_filename_input()
            pygame.display.flip()

            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_RETURN:
                            if self.load_level():
                                self.show_load_dialog = False
                                self.filename_input = ""
                            waiting = False
                        elif e.key == pygame.K_BACKSPACE:
                            self.filename_input = self.filename_input[:-1]
                        elif e.unicode.isprintable():
                            self.filename_input += e.unicode
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        if save_btn.collidepoint(e.pos):
                            if self.load_level():
                                self.show_load_dialog = False
                                self.filename_input = ""
                            waiting = False
                        elif cancel_btn.collidepoint(e.pos):
                            self.show_load_dialog = False
                            self.filename_input = ""
                            waiting = False
                    elif e.type == pygame.QUIT:
                        waiting = False
                        return False
                self.draw()
                save_btn, cancel_btn = self.get_filename_input()
                pygame.display.flip()
                self.clock.tick(30)

        return save_btn, load_btn, back_btn

    def run(self):
        running = True
        while running:
            save_btn, load_btn, back_btn = self.draw()
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

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()

                    if x > EDITOR_WIDTH:
                        # Тулбар
                        for i in range(len(self.tools)):
                            btn_y = 80 + i * 60
                            if EDITOR_WIDTH + 20 < x < EDITOR_WIDTH + 280 and btn_y < y < btn_y + 50:
                                self.current_tool = i

                        if save_btn.collidepoint(x, y):
                            self.show_save_dialog = True
                            self.filename_input = ""
                        elif load_btn.collidepoint(x, y):
                            self.show_load_dialog = True
                            self.filename_input = ""
                        elif back_btn.collidepoint(x, y):
                            running = False
                    else:
                        grid_x = x // TILE_SIZE
                        grid_y = y // TILE_SIZE
                        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                            self.level[grid_y][grid_x] = self.tools[self.current_tool]['char']

                elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                    x, y = pygame.mouse.get_pos()
                    if x < EDITOR_WIDTH:
                        grid_x = x // TILE_SIZE
                        grid_y = y // TILE_SIZE
                        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                            self.level[grid_y][grid_x] = self.tools[self.current_tool]['char']

            self.clock.tick(60)

        return "menu"
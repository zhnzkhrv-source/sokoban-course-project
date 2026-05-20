import pygame
import sys
import os
import json
import re

# Цвета оформления
BG_COLOR = (255, 240, 245)
BTN_COLOR = (255, 182, 193)
TEXT_COLOR = (139, 0, 139)
BORDER_COLOR = (219, 112, 147)

# Дополнительные цвета
GREEN = (100, 200, 100)
YELLOW = (255, 220, 100)
RED = (220, 100, 100)


def extract_level_number(name):
    """Извлекает номер уровня из имени (level10 -> 10, Custom3 -> 3)"""
    numbers = re.findall(r'\d+', name)
    return int(numbers[0]) if numbers else 999


def load_all_levels_from_file(filename="levels.txt"):
    """Загружает стандартные уровни из levels.txt"""
    if not os.path.exists(filename):
        print(f"Ошибка: файл {filename} не найден!")
        return []

    with open(filename, 'r') as f:
        lines = f.readlines()

    levels = []
    current_level = []
    in_level = False

    for line in lines:
        line = line.rstrip('\n')

        if line.startswith('Level ') and line[6:].strip().isdigit():
            if current_level:
                levels.append(current_level)
                current_level = []
            in_level = True
            continue

        if not line.strip():
            continue

        if in_level and line.strip():
            current_level.append(line)

    if current_level:
        levels.append(current_level)

    print(f"Загружено {len(levels)} стандартных уровней")
    return levels


def load_custom_levels():
    """Загружает пользовательские уровни из папки levels/"""
    if not os.path.exists("levels"):
        os.makedirs("levels")
        return []

    custom_levels = []
    files = [f for f in os.listdir("levels") if f.endswith(".txt")]
    files.sort()

    for filename in files:
        filepath = os.path.join("levels", filename)
        with open(filepath, 'r') as f:
            lines = [line.rstrip() for line in f.readlines() if line.strip()]
            if lines:
                custom_levels.append(lines)
                print(f"Загружен пользовательский уровень: {filename}")

    return custom_levels


def load_progress(category="standard"):
    os.makedirs("saves", exist_ok=True)
    progress_file = f"saves/progress_{category}.json"
    if not os.path.exists(progress_file):
        return 0
    try:
        with open(progress_file, "r") as f:
            data = json.load(f)
            return data.get("current_level", 0)
    except:
        return 0


def save_progress(level_index, category="standard"):
    os.makedirs("saves", exist_ok=True)
    progress_file = f"saves/progress_{category}.json"
    with open(progress_file, "w") as f:
        json.dump({"current_level": level_index}, f)


def save_stats(level_name, moves, pushes, category="standard"):
    os.makedirs("saves", exist_ok=True)
    stats_file = f"saves/stats_{category}.json"

    stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r") as f:
                stats = json.load(f)
        except:
            pass

    if level_name in stats:
        old = stats[level_name]
        old['attempts'] = old.get('attempts', 0) + 1
        if moves < old.get('best_moves', 999999):
            old['best_moves'] = moves
        stats[level_name] = old
    else:
        stats[level_name] = {'best_moves': moves, 'attempts': 1}

    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)


def get_level_category(level_num):
    if level_num <= 5:
        return "ЛЁГКИЙ", GREEN
    elif level_num <= 10:
        return "СРЕДНИЙ", YELLOW
    else:
        return "СЛОЖНЫЙ", RED


class GameManager:
    def __init__(self):
        pygame.init()

        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        self.fullscreen = False
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Sokoban - Курсовая работа")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 72)
        self.state = "menu"
        self.running = True
        self.message = ""
        self.message_timer = 0

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

    def show_message(self, text, duration=60):
        self.message = text
        self.message_timer = duration

    def draw_message(self):
        if self.message and self.message_timer > 0:
            msg_surface = self.font.render(self.message, True, RED)
            self.screen.blit(msg_surface,
                             (self.screen_width // 2 - msg_surface.get_width() // 2, self.screen_height - 80))
            self.message_timer -= 1
        else:
            self.message = ""

    def show_menu(self):
        self.screen.fill(BG_COLOR)

        title = self.title_font.render("SOKOBAN", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))

        menu_items = [
            {"text": "ИГРАТЬ", "y": 200, "action": "playing"},
            {"text": "СОЗДАННЫЕ УРОВНИ", "y": 270, "action": "custom"},
            {"text": "РЕДАКТОР", "y": 340, "action": "editor"},
            {"text": "СТАТИСТИКА", "y": 410, "action": "stats"},
            {"text": "ВЫХОД", "y": 480, "action": "exit"},
        ]

        hint = self.small_font.render("F11 - полноэкранный режим", True, TEXT_COLOR)
        self.screen.blit(hint, (self.screen_width - hint.get_width() - 20, self.screen_height - 30))

        for item in menu_items:
            btn_rect = pygame.Rect(self.screen_width // 2 - 150, item["y"], 300, 50)
            color = BTN_COLOR if item["action"] != "exit" else (200, 100, 100)
            pygame.draw.rect(self.screen, color, btn_rect)
            pygame.draw.rect(self.screen, BORDER_COLOR, btn_rect, 3)
            text = self.font.render(item["text"], True, TEXT_COLOR)
            self.screen.blit(text, (btn_rect.centerx - text.get_width() // 2, btn_rect.centery - 10))

        self.draw_message()
        pygame.display.flip()

    def show_stats(self, category="standard"):
        self.screen.fill(BG_COLOR)

        category_names = {"standard": "СТАНДАРТНЫЕ УРОВНИ", "custom": "СОЗДАННЫЕ УРОВНИ"}
        title = self.font.render(f"СТАТИСТИКА - {category_names.get(category, '')}", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 30))

        stats_file = f"saves/stats_{category}.json"
        stats = {}
        if os.path.exists(stats_file):
            try:
                with open(stats_file, "r") as f:
                    stats = json.load(f)
            except:
                pass

        # Функция для извлечения номера уровня
        def level_number(name):
            import re
            numbers = re.findall(r'\d+', name)
            return int(numbers[0]) if numbers else 999

        y = 100
        if not stats:
            text = self.small_font.render("Нет статистики", True, TEXT_COLOR)
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 200))
        else:
            for level_name, data in sorted(stats.items(), key=lambda x: level_number(x[0])):
                text = self.small_font.render(
                    f"{level_name}: {data.get('best_moves', '-')} ходов, {data.get('attempts', 0)} попыток",
                    True, TEXT_COLOR
                )
                self.screen.blit(text, (50, y))
                y += 25
                if y > self.screen_height - 150:
                    break

        # ===== РАЗДВИНУТЫЕ КНОПКИ =====
        btn_width = 180
        btn_height = 40
        spacing = 20

        total_width = btn_width * 2 + spacing
        start_x = (self.screen_width - total_width) // 2

        std_rect = pygame.Rect(start_x, self.screen_height - 80, btn_width, btn_height)
        cust_rect = pygame.Rect(start_x + btn_width + spacing, self.screen_height - 80, btn_width, btn_height)
        back_rect = pygame.Rect(self.screen_width // 2 - 100, self.screen_height - 30, 200, btn_height)

        # Цвета кнопок
        if category == "standard":
            pygame.draw.rect(self.screen, GREEN, std_rect)
            pygame.draw.rect(self.screen, BTN_COLOR, cust_rect)
        else:
            pygame.draw.rect(self.screen, BTN_COLOR, std_rect)
            pygame.draw.rect(self.screen, GREEN, cust_rect)

        pygame.draw.rect(self.screen, BORDER_COLOR, std_rect, 2)
        pygame.draw.rect(self.screen, BORDER_COLOR, cust_rect, 2)
        pygame.draw.rect(self.screen, BORDER_COLOR, back_rect, 2)

        std_text = self.small_font.render("СТАНДАРТ", True, TEXT_COLOR)
        cust_text = self.small_font.render("СОЗДАННЫЕ", True, TEXT_COLOR)
        back_text = self.small_font.render("НАЗАД", True, TEXT_COLOR)

        self.screen.blit(std_text, (std_rect.centerx - std_text.get_width() // 2, std_rect.centery - 10))
        self.screen.blit(cust_text, (cust_rect.centerx - cust_text.get_width() // 2, cust_rect.centery - 10))
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - 10))

        self.draw_message()
        pygame.display.flip()
        return back_rect, std_rect, cust_rect

    def run_game(self, levels, category="standard", category_name=""):
        if not levels:
            self.show_message("Нет уровней!", 90)
            return "menu"

        current_level = load_progress(category)
        if current_level >= len(levels):
            current_level = 0

        from game import SokobanGame
        game = SokobanGame(levels[current_level])
        level_completed = False
        hint_move = None
        hint_status = ""

        # Проверка победы при загрузке
        if game.check_win():
            # Пауза 1.5 секунды, чтобы игрок увидел финальное положение
            pygame.time.wait(1500)

            level_completed = True
            level_name = f"Level{current_level + 1}" if category == "standard" else f"Custom{current_level + 1}"
            stats = game.get_stats()
            save_stats(level_name, stats['moves'], stats['pushes'], category)

            self.screen.fill(BG_COLOR)
            win_text = self.font.render("ПОБЕДА!", True, GREEN)
            self.screen.blit(win_text,
                             (self.screen_width // 2 - win_text.get_width() // 2, self.screen_height // 2 - 50))
            pygame.display.flip()
            pygame.time.wait(2000)  # 2 секунды показываем экран победы

            current_level += 1
            if current_level >= len(levels):
                final_text = self.font.render("ВСЕ УРОВНИ ПРОЙДЕНЫ!", True, GREEN)
                self.screen.blit(final_text,
                                 (self.screen_width // 2 - final_text.get_width() // 2, self.screen_height // 2))
                pygame.display.flip()
                pygame.time.wait(2000)
                return "menu"
            else:
                save_progress(current_level, category)
                game = SokobanGame(levels[current_level])
                level_completed = False
                hint_status = ""
                hint_move = None

        running = True
        while running:
            self.screen.fill(BG_COLOR)

            if not level_completed:
                game.draw(self.screen, self.font, self.screen_width, self.screen_height)

                level_num = current_level + 1
                if category == "standard":
                    level_display = f"Уровень {level_num}"
                    cat, cat_color = get_level_category(level_num)
                    cat_surface = self.small_font.render(cat, True, cat_color)
                    self.screen.blit(cat_surface, (10, 10))
                else:
                    level_display = f"Созданный уровень {level_num}"

                info = self.small_font.render(f"{level_display} | Ходы: {game.moves} | Толчки: {game.pushes}", True,
                                              TEXT_COLOR)
                self.screen.blit(info, (self.screen_width - info.get_width() - 10, 10))

                controls = self.small_font.render(
                    "Стрелки | U - отмена | R - рестарт | H - подсказка | F11 - полноэкранный | ESC - меню", True,
                    TEXT_COLOR)
                self.screen.blit(controls, (10, self.screen_height - 30))

                if hint_status == "found" and hint_move:
                    arrow = ""
                    if hint_move == (0, -1):
                        arrow = "↑ вверх"
                    elif hint_move == (0, 1):
                        arrow = "↓ вниз"
                    elif hint_move == (-1, 0):
                        arrow = "← влево"
                    elif hint_move == (1, 0):
                        arrow = "→ вправо"
                    hint_text = self.small_font.render(f"Подсказка: {arrow}", True, GREEN)
                    self.screen.blit(hint_text,
                                     (self.screen_width - hint_text.get_width() - 10, self.screen_height - 30))
                elif hint_status == "not_found":
                    hint_text = self.small_font.render("Подсказка: решения нет (слишком сложный уровень)", True, RED)
                    self.screen.blit(hint_text,
                                     (self.screen_width - hint_text.get_width() - 10, self.screen_height - 30))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_progress(current_level, category)
                    return "exit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()

                    if event.key == pygame.K_ESCAPE:
                        save_progress(current_level, category)
                        return "menu"

                    if not level_completed:
                        if event.key == pygame.K_UP:
                            game.try_move(0, -1)
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_DOWN:
                            game.try_move(0, 1)
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_LEFT:
                            game.try_move(-1, 0)
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_RIGHT:
                            game.try_move(1, 0)
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_u:
                            game.undo()
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_r:
                            game = SokobanGame(levels[current_level])
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_h:
                            if len(game.boxes) > 3:
                                hint_status = "not_found"
                                hint_move = None
                            else:
                                hint_move = game.get_hint()
                                hint_status = "found" if hint_move else "not_found"

                        if game.check_win():
                            # Пауза 0.8 секунды перед экраном победы
                            pygame.time.wait(500)

                            level_completed = True
                            level_name = f"Level{current_level + 1}" if category == "standard" else f"Custom{current_level + 1}"
                            stats = game.get_stats()
                            save_stats(level_name, stats['moves'], stats['pushes'], category)

                            self.screen.fill(BG_COLOR)
                            win_text = self.font.render("ПОБЕДА!", True, GREEN)
                            self.screen.blit(win_text, (self.screen_width // 2 - win_text.get_width() // 2,
                                                        self.screen_height // 2 - 50))
                            pygame.display.flip()
                            pygame.time.wait(1500)

                            current_level += 1
                            if current_level >= len(levels):
                                final_text = self.font.render("ВСЕ УРОВНИ ПРОЙДЕНЫ!", True, GREEN)
                                self.screen.blit(final_text, (self.screen_width // 2 - final_text.get_width() // 2,
                                                              self.screen_height // 2))
                                pygame.display.flip()
                                pygame.time.wait(2000)
                                return "menu"
                            else:
                                save_progress(current_level, category)
                                game = SokobanGame(levels[current_level])
                                level_completed = False
                                hint_status = ""
                                hint_move = None

            self.draw_message()
            pygame.display.flip()
            self.clock.tick(60)

        return "menu"

    def run_editor(self):
        from editor import LevelEditor
        editor = LevelEditor(self.screen)
        return editor.run()

    def run(self):
        standard_levels = load_all_levels_from_file("levels.txt")

        while self.running:
            if self.state == "menu":
                self.show_menu()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = pygame.mouse.get_pos()
                        if pygame.Rect(self.screen_width // 2 - 150, 200, 300, 50).collidepoint(x, y):
                            if standard_levels:
                                self.state = "playing"
                            else:
                                self.show_message("Нет стандартных уровней! Добавьте levels.txt", 90)
                        elif pygame.Rect(self.screen_width // 2 - 150, 270, 300, 50).collidepoint(x, y):
                            self.state = "custom"
                        elif pygame.Rect(self.screen_width // 2 - 150, 340, 300, 50).collidepoint(x, y):
                            self.state = "editor"
                        elif pygame.Rect(self.screen_width // 2 - 150, 410, 300, 50).collidepoint(x, y):
                            self.state = "stats"
                        elif pygame.Rect(self.screen_width // 2 - 150, 480, 300, 50).collidepoint(x, y):
                            self.running = False

            elif self.state == "playing":
                result = self.run_game(standard_levels, category="standard", category_name="СТАНДАРТНЫЕ")
                self.state = result if result else "menu"

            elif self.state == "custom":
                custom_levels = load_custom_levels()
                if not custom_levels:
                    self.show_message("Нет созданных уровней! Создайте их в редакторе", 90)
                    self.state = "menu"
                else:
                    result = self.run_game(custom_levels, category="custom", category_name="СОЗДАННЫЕ")
                    self.state = result if result else "menu"

            elif self.state == "editor":
                result = self.run_editor()
                self.state = result if result else "menu"

            elif self.state == "stats":
                category = "standard"
                in_stats = True
                while in_stats:
                    back_rect, std_rect, cust_rect = self.show_stats(category)
                    pygame.display.flip()

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            in_stats = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                in_stats = False
                            if event.key == pygame.K_F11:
                                self.toggle_fullscreen()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            x, y = pygame.mouse.get_pos()
                            if back_rect.collidepoint(x, y):
                                in_stats = False
                            elif std_rect.collidepoint(x, y):
                                category = "standard"
                            elif cust_rect.collidepoint(x, y):
                                category = "custom"
                    pygame.time.wait(50)
                self.state = "menu"

            pygame.time.wait(50)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    manager = GameManager()
    manager.run()
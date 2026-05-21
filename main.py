import pygame
import sys
import os
import json
import re
import time
from constants import *


def extract_level_number(name): # извлекает номер уровня из имени файла для сортировки
    numbers = re.findall(r'\d+', name)
    return int(numbers[0]) if numbers else 999


def load_all_levels_from_file(filename="levels.txt"): # загружает все стандартные уровни из одного файла levels.txt
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


def load_custom_levels(): # загружает пользовательские уровни из папки levels
    if not os.path.exists("levels"):
        os.makedirs("levels")
        return []

    custom_levels = []
    files = [f for f in os.listdir("levels") if f.endswith(".txt")]
    files.sort()

    for filename in files:
        filepath = os.path.join("levels", filename)
        try:
            with open(filepath, 'r') as f:
                lines = [line.rstrip() for line in f.readlines() if line.strip()]
                if lines:
                    custom_levels.append(lines)
                    print(f"Загружен пользовательский уровень: {filename}")
        except (OSError, IOError) as e:
            print(f"Ошибка загрузки {filename}: {e}")

    return custom_levels


def load_progress(category="standard"):  # загружает сохраненный прогресс (номер текущего уровня) для указанной категории
    os.makedirs("saves", exist_ok=True)
    progress_file = f"saves/progress_{category}.json"
    if not os.path.exists(progress_file):
        return 0
    try:
        with open(progress_file, "r") as f:
            data = json.load(f)
            return data.get("current_level", 0)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Ошибка загрузки прогресса: {e}")
        return 0


def save_progress(level_index, category="standard"): # сохраняет текущий номер уровня в файл прогресса указанной категории
    os.makedirs("saves", exist_ok=True)
    progress_file = f"saves/progress_{category}.json"
    with open(progress_file, "w") as f:
        json.dump({"current_level": level_index}, f)


def save_stats(level_name, moves, pushes, elapsed_time, category="standard"): # сохраняет/обновляет статистику прохождения уровня (лучш кол-во ходов, кол-во толчков, время и кол-во попыток)
    os.makedirs("saves", exist_ok=True)
    stats_file = f"saves/stats_{category}.json"

    stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r") as f:
                stats = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Ошибка загрузки статистики: {e}")

    if level_name in stats:
        old = stats[level_name]
        old['attempts'] = old.get('attempts', 0) + 1
        if moves < old.get('best_moves', 999999):
            old['best_moves'] = moves
        if pushes < old.get('best_pushes', 999999):
            old['best_pushes'] = pushes
        if elapsed_time < old.get('best_time', 999999):
            old['best_time'] = elapsed_time
        stats[level_name] = old
    else:
        stats[level_name] = {
            'best_moves': moves,
            'best_pushes': pushes,
            'best_time': elapsed_time,
            'attempts': 1
        }

    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)


def format_time(seconds): # форматирует время в мм:сс
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def get_level_category(level_num): # определяет сложность уровня по номеру и возвращает название + цвет для отображения в интерфейсе
    if level_num <= 5:
        return "ЛЁГКИЙ", CAT_EASY
    elif level_num <= 10:
        return "СРЕДНИЙ", CAT_MEDIUM
    else:
        return "СЛОЖНЫЙ", CAT_HARD


class GameManager: # инициализация главного менеджера игры - создает окно, настраивает pygame
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

    def toggle_fullscreen(self): # переключает режим окна между оконным и полноэкранным
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

    def show_message(self, text, duration=60): # показывает временное сообщение на экране
        self.message = text
        self.message_timer = duration

    def draw_message(self): # отрисовывает временное сообщение внизу экрана и управляет его таймером
        if self.message and self.message_timer > 0:
            msg_surface = self.font.render(self.message, True, RED)
            self.screen.blit(msg_surface,
                             (self.screen_width // 2 - msg_surface.get_width() // 2, self.screen_height - 80))
            self.message_timer -= 1
        else:
            self.message = ""

    def show_menu(self): # главное меню с кнопками
        self.screen.fill(BG_COLOR)

        title = self.title_font.render("SOKOBAN", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))

        menu_items = [
            {"text": "ИГРАТЬ", "y": 180, "action": "playing"},
            {"text": "СОЗДАННЫЕ УРОВНИ", "y": 250, "action": "custom"},
            {"text": "ВЫБРАТЬ УРОВЕНЬ", "y": 320, "action": "select"},
            {"text": "РЕДАКТОР", "y": 390, "action": "editor"},
            {"text": "СТАТИСТИКА", "y": 460, "action": "stats"},
            {"text": "ВЫХОД", "y": 530, "action": "exit"},
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
            self.button_rects = getattr(self, 'button_rects', {})
            self.button_rects[item["action"]] = btn_rect

        self.draw_message()
        pygame.display.flip()

    def show_level_select(self): # экран выбора стандартных уровней (1-15)
        self.screen.fill(BG_COLOR)
        title = self.font.render("ВЫБОР УРОВНЯ", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 30))

        levels = load_all_levels_from_file("levels.txt")
        if not levels:
            self.show_message("Нет уровней!")
            return "menu"

        cols = 3
        rows = 5
        btn_w = 150
        btn_h = 50
        spacing_x = 40
        spacing_y = 20

        total_width = cols * btn_w + (cols - 1) * spacing_x
        start_x = (self.screen_width - total_width) // 2
        start_y = 150

        self.level_buttons = []
        for i in range(len(levels)):
            row = i // cols
            col = i % cols
            x = start_x + col * (btn_w + spacing_x)
            y = start_y + row * (btn_h + spacing_y)
            rect = pygame.Rect(x, y, btn_w, btn_h)

            pygame.draw.rect(self.screen, BTN_COLOR, rect)
            pygame.draw.rect(self.screen, BORDER_COLOR, rect, 2)
            text = self.small_font.render(f"Уровень {i + 1}", True, TEXT_COLOR)
            self.screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - 10))
            self.level_buttons.append((rect, i))

        back_rect = pygame.Rect(self.screen_width // 2 - 100, self.screen_height - 80, 200, 50)
        pygame.draw.rect(self.screen, RED, back_rect)
        pygame.draw.rect(self.screen, BLACK, back_rect, 2)
        back_text = self.font.render("НАЗАД", True, WHITE)
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - 10))

        self.draw_message()
        pygame.display.flip()
        return back_rect

    def show_custom_levels_select(self): # экран выбора пользовательских уровней, созданных в редакторе
        self.screen.fill(BG_COLOR)
        title = self.font.render("ВЫБОР СОЗДАННОГО УРОВНЯ", True, TEXT_COLOR)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 30))

        custom_levels = load_custom_levels()
        if not custom_levels:
            self.show_message("Нет созданных уровней! Создайте их в редакторе", 90)
            return None, None

        # Получаем список имён файлов
        files = [f for f in os.listdir("levels") if f.endswith(".txt") and not f.startswith("level")]
        files.sort()

        progress = {}
        progress_file = "saves/custom_progress.json"
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    progress = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Ошибка загрузки прогресса: {e}")

        cols = 2
        btn_w = 300
        btn_h = 50
        spacing_x = 40
        spacing_y = 20

        total_width = cols * btn_w + (cols - 1) * spacing_x
        start_x = (self.screen_width - total_width) // 2
        start_y = 150

        level_buttons = []
        for i, level_map in enumerate(custom_levels):
            row = i // cols
            col = i % cols
            x = start_x + col * (btn_w + spacing_x)
            y = start_y + row * (btn_h + spacing_y)
            rect = pygame.Rect(x, y, btn_w, btn_h)

            # ПОКАЗЫВАЕМ РЕАЛЬНОЕ ИМЯ ФАЙЛА
            display_name = files[i].replace(".txt", "") if i < len(files) else f"Уровень {i + 1}"
            is_completed = progress.get(display_name, False)

            if is_completed:
                pygame.draw.rect(self.screen, GREEN, rect)
            else:
                pygame.draw.rect(self.screen, BTN_COLOR, rect)
            pygame.draw.rect(self.screen, BORDER_COLOR, rect, 2)

            text = self.small_font.render(display_name, True, TEXT_COLOR)
            self.screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - 10))

            if is_completed:
                check_text = self.small_font.render("✓", True, TEXT_COLOR)
                self.screen.blit(check_text, (rect.x + 15, rect.centery - 10))

            level_buttons.append((rect, i, display_name))

        back_rect = pygame.Rect(self.screen_width // 2 - 100, self.screen_height - 80, 200, 50)
        pygame.draw.rect(self.screen, RED, back_rect)
        pygame.draw.rect(self.screen, BLACK, back_rect, 2)
        back_text = self.font.render("НАЗАД", True, WHITE)
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - 10))

        self.draw_message()
        pygame.display.flip()
        return level_buttons, back_rect

    def show_stats(self, category="standard"): # статистика прохождения для выбранной категории (стандартные или созданные уровни)
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
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Ошибка загрузки статистики: {e}")

        y = 100
        if not stats:
            text = self.small_font.render("Нет статистики", True, TEXT_COLOR)
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 200))
        else:
            for level_name, data in sorted(stats.items(), key=lambda x: extract_level_number(x[0])):
                best_pushes = data.get('best_pushes', '-')
                best_time = data.get('best_time', '-')
                if best_time != '-':
                    best_time = format_time(best_time)
                text = self.small_font.render(
                    f"{level_name}: {data.get('best_moves', '-')} ходов, {best_pushes} толчков, время: {best_time}, {data.get('attempts', 0)} попыток",
                    True, TEXT_COLOR
                )
                self.screen.blit(text, (50, y))
                y += 25
                if y > self.screen_height - 150:
                    break

        btn_width = 180
        btn_height = 40
        spacing = 20

        total_width = btn_width * 2 + spacing
        start_x = (self.screen_width - total_width) // 2

        std_rect = pygame.Rect(start_x, self.screen_height - 80, btn_width, btn_height)
        cust_rect = pygame.Rect(start_x + btn_width + spacing, self.screen_height - 80, btn_width, btn_height)
        back_rect = pygame.Rect(self.screen_width // 2 - 100, self.screen_height - 30, 200, btn_height)

        if category == "standard":
            pygame.draw.rect(self.screen, CAT_EASY, std_rect)
            pygame.draw.rect(self.screen, BTN_COLOR, cust_rect)
        else:
            pygame.draw.rect(self.screen, BTN_COLOR, std_rect)
            pygame.draw.rect(self.screen, CAT_EASY, cust_rect)

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

    def run_game(self, levels, category="standard", category_name="", start_level=-1): # главный игровой цикл - обрабатывает ввод, анимацию, проверку победы, переход между уровнями
        if not levels:
            self.show_message("Нет уровней!", 90)
            return "menu"

        if start_level >= 0 and start_level < len(levels):
            current_level = start_level
        else:
            current_level = load_progress(category)
            if current_level >= len(levels):
                current_level = 0

        from game import SokobanGame
        game = SokobanGame(levels[current_level])
        level_completed = False
        hint_move = None
        hint_status = ""
        win_shown = False
        win_time = 0
        level_start_time = time.time()

        running = True
        while running:
            dt = self.clock.get_time() / 1000.0
            game.update(dt)

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

                elapsed = int(time.time() - level_start_time)
                time_display = format_time(elapsed)

                info = self.small_font.render(
                    f"{level_display} | Ходы: {game.moves} | Толчки: {game.pushes} | Время: {time_display}", True,
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

                    if not level_completed and not win_shown:
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
                            level_start_time = time.time()
                            hint_status = ""
                            hint_move = None
                        elif event.key == pygame.K_h:
                            if len(game.boxes) > 3:
                                hint_status = "not_found"
                                hint_move = None
                            else:
                                hint_move = game.get_hint()
                                hint_status = "found" if hint_move else "not_found"

                        if game.check_win() and not win_shown:
                            win_shown = True
                            win_time = pygame.time.get_ticks()

                            level_name = f"Level{current_level + 1}" if category == "standard" else f"Уровень {current_level + 1}"
                            stats = game.get_stats()
                            elapsed = int(time.time() - level_start_time)
                            save_stats(level_name, stats['moves'], stats['pushes'], elapsed, category)

                            if category == "custom":
                                progress_file = "saves/custom_progress.json"
                                progress = {}
                                if os.path.exists(progress_file):
                                    try:
                                        with open(progress_file, "r") as f:
                                            progress = json.load(f)
                                    except (json.JSONDecodeError, OSError) as e:
                                        print(f"Ошибка загрузки прогресса: {e}")
                                progress[level_name] = True
                                with open(progress_file, "w") as f:
                                    json.dump(progress, f, indent=2)

                            win_rect = pygame.Rect(
                                self.screen_width // 2 - 200,
                                self.screen_height // 2 - 100,
                                400,
                                200
                            )

                            pygame.draw.rect(self.screen, BG_COLOR, win_rect)
                            pygame.draw.rect(self.screen, BORDER_COLOR, win_rect, 4)
                            pygame.draw.rect(self.screen, BTN_COLOR, win_rect.inflate(-8, -8))

                            win_text = self.font.render("ПОБЕДА!", True, TEXT_COLOR)
                            self.screen.blit(win_text, (win_rect.centerx - win_text.get_width() // 2, win_rect.y + 30))

                            moves_text = self.small_font.render(f"Ходов: {stats['moves']}", True, TEXT_COLOR)
                            pushes_text = self.small_font.render(f"Толчков: {stats['pushes']}", True, TEXT_COLOR)
                            time_text = self.small_font.render(f"Время: {format_time(elapsed)}", True, TEXT_COLOR)
                            self.screen.blit(moves_text, (win_rect.x + 50, win_rect.y + 80))
                            self.screen.blit(pushes_text, (win_rect.x + 50, win_rect.y + 110))
                            self.screen.blit(time_text, (win_rect.x + 50, win_rect.y + 140))

                            continue_text = self.small_font.render("Нажми любую клавишу...", True, GRAY)
                            self.screen.blit(continue_text,
                                             (win_rect.centerx - continue_text.get_width() // 2, win_rect.y + 170))

                            pygame.display.flip()

            if win_shown and not level_completed:
                if pygame.time.get_ticks() - win_time > 2000:
                    level_completed = True
                    current_level += 1
                    if current_level >= len(levels):
                        complete_rect = pygame.Rect(
                            self.screen_width // 2 - 250,
                            self.screen_height // 2 - 100,
                            500,
                            200
                        )

                        pygame.draw.rect(self.screen, BG_COLOR, complete_rect)
                        pygame.draw.rect(self.screen, BORDER_COLOR, complete_rect, 4)
                        pygame.draw.rect(self.screen, CAT_EASY, complete_rect.inflate(-8, -8))

                        complete_text = self.font.render("ВСЕ УРОВНИ ПРОЙДЕНЫ!", True, TEXT_COLOR)
                        self.screen.blit(complete_text,
                                         (complete_rect.centerx - complete_text.get_width() // 2, complete_rect.y + 50))

                        congrats_text = self.small_font.render("Поздравляем! Вы прошли все уровни.", True, TEXT_COLOR)
                        self.screen.blit(congrats_text, (complete_rect.centerx - congrats_text.get_width() // 2,
                                                         complete_rect.y + 110))

                        exit_text = self.small_font.render("Нажмите любую клавишу для выхода...", True, GRAY)
                        self.screen.blit(exit_text,
                                         (complete_rect.centerx - exit_text.get_width() // 2, complete_rect.y + 150))

                        pygame.display.flip()

                        waiting = True
                        while waiting:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    waiting = False
                                    self.running = False
                                if event.type == pygame.KEYDOWN:
                                    waiting = False
                            self.clock.tick(30)

                        return "menu"
                    else:
                        save_progress(current_level, category)
                        game = SokobanGame(levels[current_level])
                        level_start_time = time.time()
                        level_completed = False
                        win_shown = False
                        hint_status = ""
                        hint_move = None

            self.draw_message()
            pygame.display.flip()
            self.clock.tick(60)

        return "menu"

    def run_editor(self): # запускает редактор уровней из главного экрана
        from editor import LevelEditor
        editor = LevelEditor(self.screen)
        return editor.run()

    def run(self): # управление переключением между экранами приложения
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
                        if hasattr(self, 'button_rects'):
                            if self.button_rects.get("playing", pygame.Rect(0, 0, 0, 0)).collidepoint(x, y):
                                if standard_levels:
                                    self.state = "playing"
                                else:
                                    self.show_message("Нет стандартных уровней! Добавьте levels.txt", 90)
                            elif self.button_rects.get("custom", pygame.Rect(0, 0, 0, 0)).collidepoint(x, y):
                                self.state = "custom_select"
                            elif self.button_rects.get("select", pygame.Rect(0, 0, 0, 0)).collidepoint(x, y):
                                self.state = "select"
                            elif self.button_rects.get("editor", pygame.Rect(0, 0, 0, 0)).collidepoint(x, y):
                                self.state = "editor"
                            elif self.button_rects.get("stats", pygame.Rect(0, 0, 0, 0)).collidepoint(x, y):
                                self.state = "stats"
                            elif self.button_rects.get("exit", pygame.Rect(0, 0, 0, 0)).collidepoint(x, y):
                                self.running = False

            elif self.state == "playing":
                result = self.run_game(standard_levels, category="standard", category_name="СТАНДАРТНЫЕ")
                self.state = result if result else "menu"

            elif self.state == "custom_select":
                level_buttons, back_rect = self.show_custom_levels_select()
                if level_buttons is None:
                    self.state = "menu"
                else:
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.running = False
                                waiting = False
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_F11:
                                    self.toggle_fullscreen()
                                if event.key == pygame.K_ESCAPE:
                                    waiting = False
                                    self.state = "menu"
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                x, y = pygame.mouse.get_pos()
                                if back_rect.collidepoint(x, y):
                                    waiting = False
                                    self.state = "menu"
                                else:
                                    for rect, level_idx, level_name in level_buttons:
                                        if rect.collidepoint(x, y):
                                            custom_levels = load_custom_levels()
                                            result = self.run_game(
                                                [custom_levels[level_idx]],
                                                category="custom",
                                                category_name="СОЗДАННЫЕ",
                                                start_level=0
                                            )
                                            waiting = False
                                            self.state = "menu"
                                            break
                        self.clock.tick(60)

            elif self.state == "select":
                back_rect = self.show_level_select()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = pygame.mouse.get_pos()
                        for rect, level_idx in self.level_buttons:
                            if rect.collidepoint(x, y):
                                result = self.run_game(standard_levels, category="standard", start_level=level_idx)
                                self.state = result if result else "select"
                                break
                        if back_rect.collidepoint(x, y):
                            self.state = "menu"

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
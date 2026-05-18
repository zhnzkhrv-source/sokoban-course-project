import pygame
import sys
import os
import json
from game import SokobanGame, SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, GREEN, GRAY, YELLOW, BLUE, RED

DARK_GRAY = (100, 100, 100)


def load_levels_list():
    levels_dir = "levels"
    if not os.path.exists(levels_dir):
        os.makedirs(levels_dir)

    levels = []
    if os.path.exists(levels_dir):
        for file in sorted(os.listdir(levels_dir)):
            if file.endswith(".txt"):
                levels.append(os.path.join(levels_dir, file))
    return levels


def load_progress():
    os.makedirs("saves", exist_ok=True)
    progress_file = "saves/progress.json"
    if not os.path.exists(progress_file):
        return 0
    try:
        with open(progress_file, "r") as f:
            data = json.load(f)
            return data.get("current_level", 0)
    except:
        return 0


def save_progress(level_index):
    os.makedirs("saves", exist_ok=True)
    with open("saves/progress.json", "w") as f:
        json.dump({"current_level": level_index}, f)


def save_stats(level_name, moves, pushes):
    os.makedirs("saves", exist_ok=True)
    stats_file = "saves/stats.json"

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
        if pushes < old.get('best_pushes', 999999):
            old['best_pushes'] = pushes
        stats[level_name] = old
    else:
        stats[level_name] = {
            'best_moves': moves,
            'best_pushes': pushes,
            'attempts': 1
        }

    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)


class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Sokoban - Курсовая работа")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        self.state = "menu"

    def show_menu(self):
        self.screen.fill(WHITE)

        title = pygame.font.Font(None, 72).render("SOKOBAN", True, BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        menu_items = [
            {"text": "▶ ИГРАТЬ", "y": 280, "action": "playing"},
            {"text": "✎ РЕДАКТОР", "y": 360, "action": "editor"},
            {"text": "📊 СТАТИСТИКА", "y": 440, "action": "stats"},
            {"text": "✖ ВЫХОД", "y": 520, "action": "exit"}
        ]

        for item in menu_items:
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, item["y"], 300, 50)
            pygame.draw.rect(self.screen, BLUE if item["action"] == "playing" else GRAY, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 2)
            text = self.font.render(item["text"], True, WHITE if item["action"] == "playing" else BLACK)
            self.screen.blit(text, (btn_rect.centerx - text.get_width() // 2, btn_rect.centery - 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                for item in menu_items:
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, item["y"], 300, 50)
                    if btn_rect.collidepoint(x, y):
                        return item["action"]
        return None

    def show_stats(self):
        self.screen.fill(WHITE)

        title = self.font.render("СТАТИСТИКА", True, BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        stats = {}
        if os.path.exists("saves/stats.json"):
            try:
                with open("saves/stats.json", "r") as f:
                    stats = json.load(f)
            except:
                pass

        y = 100
        if not stats:
            text = self.small_font.render("Нет статистики", True, BLACK)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200))
        else:
            for level_name, data in sorted(stats.items()):
                text = self.small_font.render(
                    f"{level_name}: {data.get('best_moves', '-')} ходов, {data.get('attempts', 0)} попыток",
                    True, BLACK
                )
                self.screen.blit(text, (50, y))
                y += 30

        back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
        pygame.draw.rect(self.screen, GRAY, back_rect)
        pygame.draw.rect(self.screen, BLACK, back_rect, 2)
        back_text = self.font.render("НАЗАД", True, BLACK)
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    return "menu"
        return None

    def run_game(self):
        levels = load_levels_list()
        if not levels:
            print("Нет уровней")
            return "menu"

        current_level = load_progress()
        if current_level >= len(levels):
            current_level = 0

        game = SokobanGame(levels[current_level])
        level_completed = False
        hint_move = None

        running = True
        while running:
            self.screen.fill(WHITE)

            if not level_completed:
                game.draw(self.screen, self.font, SCREEN_WIDTH, SCREEN_HEIGHT)

                level_name = os.path.basename(levels[current_level]).replace(".txt", "")
                info = self.small_font.render(f"Уровень: {level_name} | Ходы: {game.moves} | Толчки: {game.pushes}",
                                              True, BLACK)
                self.screen.blit(info, (10, 10))

                controls = self.small_font.render(
                    "Стрелки - движение | U - отмена | R - рестарт | H - подсказка | ESC - меню", True, DARK_GRAY)
                self.screen.blit(controls, (10, SCREEN_HEIGHT - 30))

                if hint_move:
                    arrow = ""
                    if hint_move == (0, -1):
                        arrow = "↑ (вверх)"
                    elif hint_move == (0, 1):
                        arrow = "↓ (вниз)"
                    elif hint_move == (-1, 0):
                        arrow = "← (влево)"
                    elif hint_move == (1, 0):
                        arrow = "→ (вправо)"
                    hint_text = self.small_font.render(f"Подсказка: нажми {arrow}", True, GREEN)
                    self.screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 10, SCREEN_HEIGHT - 30))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        save_progress(current_level)
                        return "menu"

                    elif not level_completed:
                        if event.key == pygame.K_UP:
                            game.try_move(0, -1)
                            hint_move = None
                        elif event.key == pygame.K_DOWN:
                            game.try_move(0, 1)
                            hint_move = None
                        elif event.key == pygame.K_LEFT:
                            game.try_move(-1, 0)
                            hint_move = None
                        elif event.key == pygame.K_RIGHT:
                            game.try_move(1, 0)
                            hint_move = None
                        elif event.key == pygame.K_u:
                            game.undo()
                            hint_move = None
                        elif event.key == pygame.K_r:
                            game = SokobanGame(levels[current_level])
                            hint_move = None
                        elif event.key == pygame.K_h:
                            hint_move = game.get_hint()

                        if game.check_win():
                            level_completed = True
                            level_name = os.path.basename(levels[current_level]).replace(".txt", "")
                            stats = game.get_stats()
                            save_stats(level_name, stats['moves'], stats['pushes'])

                            self.screen.fill(WHITE)
                            win_text = self.font.render("ПОБЕДА!", True, GREEN)
                            self.screen.blit(win_text,
                                             (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
                            pygame.display.flip()
                            pygame.time.wait(1500)

                            current_level += 1
                            if current_level >= len(levels):
                                final_text = self.font.render("ВСЕ УРОВНИ ПРОЙДЕНЫ!", True, GREEN)
                                self.screen.blit(final_text,
                                                 (SCREEN_WIDTH // 2 - final_text.get_width() // 2, SCREEN_HEIGHT // 2))
                                pygame.display.flip()
                                pygame.time.wait(2000)
                                return "menu"
                            else:
                                save_progress(current_level)
                                game = SokobanGame(levels[current_level])
                                level_completed = False
                                hint_move = None

            self.clock.tick(60)

    def run_editor(self):
        from editor import LevelEditor
        editor = LevelEditor(self.screen)
        return editor.run()

    def run(self):
        while True:
            if self.state == "menu":
                result = self.show_menu()
                if result == "exit":
                    break
                elif result:
                    self.state = result

            elif self.state == "playing":
                result = self.run_game()
                self.state = result if result else "menu"

            elif self.state == "editor":
                result = self.run_editor()
                self.state = result if result else "menu"

            elif self.state == "stats":
                result = self.show_stats()
                self.state = result if result else "menu"

            pygame.time.wait(50)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    manager = GameManager()
    manager.run()
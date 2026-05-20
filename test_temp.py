import pygame
import sys
import os
from game import SokobanGame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 250, 240)


def main():
    if len(sys.argv) > 1:
        level_file = sys.argv[1]
    else:
        print("Нет файла для тестирования")
        return

    if not os.path.exists(level_file):
        print(f"Файл не найден: {level_file}")
        return

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ТЕСТИРОВАНИЕ УРОВНЯ - нажми ESC для выхода")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)

    game = SokobanGame(level_file)

    running = True
    while running:
        screen.fill(WHITE)
        game.draw(screen, font, SCREEN_WIDTH, SCREEN_HEIGHT)

        info = font.render("ТЕСТИРОВАНИЕ - ESC для выхода", True, (45, 45, 65))
        screen.blit(info, (10, 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    game.try_move(0, -1)
                elif event.key == pygame.K_DOWN:
                    game.try_move(0, 1)
                elif event.key == pygame.K_LEFT:
                    game.try_move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.try_move(1, 0)
                elif event.key == pygame.K_u:
                    game.undo()
                elif event.key == pygame.K_r:
                    game = SokobanGame(level_file)

                if game.check_win():
                    print("ПОБЕДА! Уровень пройден")
                    screen.fill(WHITE)
                    win_text = font.render("ПОБЕДА! Нажмите любую клавишу", True, (140, 200, 160))
                    screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2))
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    running = False

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
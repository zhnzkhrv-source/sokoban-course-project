# constants.py
# Общие константы для всего проекта

import pygame

# Размеры окна
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Размеры редактора
EDITOR_WIDTH = 1100
EDITOR_HEIGHT = 750
TOOLBAR_WIDTH = 280
TILE_SIZE = 50  # <--- ДОБАВЬ ЭТУ СТРОКУ

# Тайлы (символы для уровней)
WALL = '#'
FLOOR = ' '
PLAYER = '@'
BOX = '$'
GOAL = '.'
BOX_ON_GOAL = '*'
PLAYER_ON_GOAL = '+'

# Цвета (пастельные)
BG_COLOR = (255, 240, 245)        # Lavender Blush
BTN_COLOR = (255, 182, 193)       # Light Pink
TEXT_COLOR = (139, 0, 139)        # Dark Magenta
BORDER_COLOR = (219, 112, 147)    # Pale Violet Red

# Дополнительные цвета
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

# Цвета категорий
CAT_EASY = GREEN
CAT_MEDIUM = YELLOW
CAT_HARD = RED

# Размер клетки (минимальный и максимальный)
MIN_TILE_SIZE = 48
MAX_TILE_SIZE = 80
DEFAULT_TILE_SIZE = 64
"""
Игра «Изгиб Питона» (классическая змейка на pygame).

Запуск:
    python3 the_snake.py

Описание:
- Змейка двигается по полю, разделённому на клетки GRID_SIZE x GRID_SIZE.
- Если ест яблоко — растёт.
- Если врезается в саму себя — сбрасывается.
- Если выходит за край — появляется с другой стороны.
"""

from __future__ import annotations

import pygame
from random import randint
from typing import List, Tuple, Optional

# ------------------------
# Константы игрового поля
# ------------------------

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

GRID_SIZE = 20  # одна клетка сетки = 20х20 пикселей
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE    # 32 клетки по горизонтали
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE  # 24 клетки по вертикали

# Направления движения змейки (dx, dy) в клетках
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Цвета (RGB)
BOARD_BACKGROUND_COLOR = (0, 0, 0)        # фон поля — чёрный
BORDER_COLOR = (93, 216, 228)             # цвет линий сетки
APPLE_COLOR = (255, 0, 0)                 # красный цвет яблока
SNAKE_COLOR = (0, 255, 0)                 # зелёный цвет змейки

# Скорость игры (кол-во шагов/кадров в секунду)
SPEED = 20


class GameObject:
    """
    Базовый класс для любого объекта на поле (змейка, яблоко и т.д.).

    Атрибуты
    --------
    position : Tuple[int, int]
        Текущая позиция объекта на поле, в ПИКСЕЛЯХ (левый верхний угол клетки).
    body_color : Tuple[int, int, int]
        Цвет отрисовки объекта в формате RGB.
    """

    def __init__(self, position: Tuple[int, int], body_color: Tuple[int, int, int]) -> None:
        """
        Инициализирует объект с позицией и цветом.

        Parameters
        ----------
        position : Tuple[int, int]
            Начальные координаты объекта (x, y) в пикселях.
        body_color : Tuple[int, int, int]
            Цвет объекта.
        """
        self.position = position
        self.body_color = body_color

    def draw(self, surface: pygame.Surface) -> None:
        """
        Отрисовка объекта.
        Должна быть переопределена в дочернем классе.
        """
        raise NotImplementedError("Метод draw() должен быть реализован в наследнике.")


class Apple(GameObject):
    """
    Класс яблока.

    Яблоко — это квадрат размером в одну клетку GRID_SIZE x GRID_SIZE.
    После съедения змейкой яблоко появляется в новой случайной клетке.
    """

    def __init__(self) -> None:
        """
        Создаёт яблоко со случайной позицией и фиксированным красным цветом.
        """
        super().__init__(position=(0, 0), body_color=APPLE_COLOR)
        self.randomize_position()

    def randomize_position(self) -> None:
        """
        Устанавливает яблоко в случайную клетку поля.
        """
        grid_x = randint(0, GRID_WIDTH - 1)
        grid_y = randint(0, GRID_HEIGHT - 1)
        self.position = (grid_x * GRID_SIZE, grid_y * GRID_SIZE)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Рисует яблоко как красный квадрат.
        """
        rect = pygame.Rect(
            self.position[0],
            self.position[1],
            GRID_SIZE,
            GRID_SIZE,
        )
        pygame.draw.rect(surface, self.body_color, rect)


class Snake(GameObject):
    """
    Класс змейки.

    Змейка хранится как список координат сегментов (в пикселях).
    Первый элемент списка — это голова.

    Атрибуты
    --------
    length : int
        Текущая длина змейки (сколько сегментов у неё должно быть).
    positions : List[Tuple[int, int]]
        Список координат сегментов змейки (голова = positions[0]).
    direction : Tuple[int, int]
        Текущее направление движения (dx, dy).
    next_direction : Optional[Tuple[int, int]]
        Направление, выбранное игроком, которое применится на следующем шаге.
    """

    def __init__(self) -> None:
        """
        Создаёт змейку в центре экрана.
        По умолчанию длина = 1, направление = вправо.
        """
        # Ставим голову примерно по центру экрана (по сетке)
        start_x = (SCREEN_WIDTH // 2 // GRID_SIZE) * GRID_SIZE
        start_y = (SCREEN_HEIGHT // 2 // GRID_SIZE) * GRID_SIZE

        super().__init__(position=(start_x, start_y), body_color=SNAKE_COLOR)

        self.length: int = 1
        self.positions: List[Tuple[int, int]] = [self.position]
        self.direction: Tuple[int, int] = RIGHT
        self.next_direction: Optional[Tuple[int, int]] = None

    def get_head_position(self) -> Tuple[int, int]:
        """
        Возвращает координаты головы змейки.
        """
        return self.positions[0]

    def update_direction(self) -> None:
        """
        Применяет направление, запрошенное игроком (next_direction),
        если оно не является разворотом на 180 градусов.
        """
        if self.next_direction is None:
            return

        new_dx, new_dy = self.next_direction
        cur_dx, cur_dy = self.direction

        # запрещаем мгновенно поехать назад в саму себя
        if (new_dx, new_dy) == (-cur_dx, -cur_dy):
            # просто игнорируем это направление
            self.next_direction = None
            return

        self.direction = (new_dx, new_dy)
        self.next_direction = None

    def move(self) -> None:
        """
        Двигает змейку на одну клетку вперёд.

        Логика:
        1. считаем новую позицию головы из текущей головы + direction
        2. делаем "телепорт через край" (выходишь слева — появляешься справа)
        3. вставляем новую голову в начало self.positions
        4. если длина списка стала > self.length, удаляем хвост
        """
        head_x, head_y = self.get_head_position()
        dx, dy = self.direction

        new_x = head_x + dx * GRID_SIZE
        new_y = head_y + dy * GRID_SIZE

        # выход за поле -> появление с другой стороны
        if new_x < 0:
            new_x = SCREEN_WIDTH - GRID_SIZE
        elif new_x >= SCREEN_WIDTH:
            new_x = 0

        if new_y < 0:
            new_y = SCREEN_HEIGHT - GRID_SIZE
        elif new_y >= SCREEN_HEIGHT:
            new_y = 0

        new_head = (new_x, new_y)

        # добавляем новую голову в начало
        self.positions.insert(0, new_head)

        # если не выросли - убираем хвост
        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(
        self,
        surface: pygame.Surface,
        background_surface: pygame.Surface,
    ) -> None:
        """
        Рисует фон, потом змейку, потом сетку.

        Пояснение:
        - Мы сначала закрашиваем весь экран в цвет поля (background_surface),
          чтобы "стереть след".
        - Потом рисуем каждый сегмент змейки.
        - Потом рисуем линии сетки (чисто косметика).
        """
        # фон (стереть предыдущий кадр)
        surface.blit(background_surface, (0, 0))

        # тело змейки
        for segment in self.positions:
            rect = pygame.Rect(segment[0], segment[1], GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, self.body_color, rect)

        # сетка для удобства и красоты
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(surface, BORDER_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(surface, BORDER_COLOR, (0, y), (SCREEN_WIDTH, y))

    def reset(self) -> None:
        """
        Сбрасывает змейку в исходное состояние,
        если она врезалась сама в себя.
        """
        start_x = (SCREEN_WIDTH // 2 // GRID_SIZE) * GRID_SIZE
        start_y = (SCREEN_HEIGHT // 2 // GRID_SIZE) * GRID_SIZE

        self.length = 1
        self.positions = [(start_x, start_y)]
        self.direction = RIGHT
        self.next_direction = None


def handle_keys(snake: Snake) -> None:
    """
    Обрабатывает события Pygame:
    - закрытие окна;
    - нажатия клавиш для смены направления.

    Управление: стрелки или WASD.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                snake.next_direction = UP
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                snake.next_direction = DOWN
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                snake.next_direction = LEFT
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                snake.next_direction = RIGHT


def main() -> None:
    """
    Главная функция игры:
    - инициализирует Pygame,
    - создаёт объекты змейки и яблока,
    - запускает бесконечный игровой цикл.
    """
    pygame.init()

    # создаём окно
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    pygame.display.set_caption("Изгиб Питона")

    clock = pygame.time.Clock()

    # фон экрана (просто однотонная поверхность)
    background = pygame.Surface(screen.get_size()).convert()
    background.fill(BOARD_BACKGROUND_COLOR)

    # игровые объекты
    snake = Snake()
    apple = Apple()

    # игровой цикл
    while True:
        # 1. обработаем ввод пользователя
        handle_keys(snake)

        # 2. обновим направление змейки
        snake.update_direction()

        # 3. сдвинем змейку
        snake.move()

        # 4. проверим, съела ли змейка яблоко
        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position()

        # 5. проверим, не укусила ли себя
        head = snake.get_head_position()
        if head in snake.positions[1:]:
            snake.reset()
            apple.randomize_position()

        # 6. нарисуем фон + змейку + яблоко
        snake.draw(screen, background)
        apple.draw(screen)

        # 7. обновим экран
        pygame.display.update()

        # 8. ограничим скорость игры
        clock.tick(SPEED)


if __name__ == "__main__":
    main()

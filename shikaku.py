#!/usr/bin/env python3
from __future__ import annotations
import pygame
from typing import Optional
from random import randrange


CELL_SIZE = 25
GRID_SIZE = 5
GRID_COLOR = (0, 0, 0)
GRID_DRAWING_POS = (0, 0)
BACKGROUND_COLOR = (255, 255, 255)
RECT_COLOR = (0, 0, 0)
RECT_THICKNESS = 3
FONT_SIZE = 30


class Point:
    def __init__(self, *args):
        if len(args) == 1:
            # Not checking if iterable is bad practice, I know
            self.x = args[0][0]
            self.y = args[0][1]
        elif len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        else:
            raise TypeError("Point takes either iterable or two integers")

    def __eq__(self, other: Point):
        return self.x == other.x and self.y == other.y

class Rect:
    def __init__(self, a: Point, b: Point):
        self.init(a, b)

    def init(self, a: Point, b: Point):
        left = min(a.x, b.x)
        right = max(a.x, b.x)
        bottom = max(a.y, b.y)
        top = min(a.y, b.y)

        self.top_left = Point(left, top)
        self.bottom_right = Point(right, bottom)

        self.width = (self.bottom_right.x - self.top_left.x + 1)
        self.height = (self.bottom_right.y - self.top_left.y + 1)
        self.area = self.width * self.height

    def set_bottom_right(self, new_bottom_right: Point):
        self.init(self.top_left, new_bottom_right)

    def set_top_left(self, new_top_left: Point):
        self.init(new_top_left, self.bottom_right)

    def intersects(self, other: Rect):
        return (self.top_left.x <= other.bottom_right.x and self.bottom_right.x >= other.top_left.x)\
                and (self.top_left.y <= other.bottom_right.y and self.bottom_right.y >= other.top_left.y)

    def contains_point(self, other: Point):
        return (self.top_left.x <= other.x <= self.bottom_right.x) \
            and (self.top_left.y <= other.y <= self.bottom_right.y)

    def draw(self, screen, offset=[0, 0]):
        pygame.draw.rect(screen, RECT_COLOR,
            [self.top_left.x * CELL_SIZE + offset[0], self.top_left.y * CELL_SIZE + offset[1],
            self.width * CELL_SIZE + 1, self.height * CELL_SIZE + 1], RECT_THICKNESS)

class NumberRenderer:
    def __init__(self, font_name: str, font_size: int, color: tuple[int, int, int], font_path: Optional[str] = None):
        if font_path:
            self.name = ""
            self.font_obj = pygame.font.Font(font_path, font_size)
        else:
            self.name = font_name
            self.font_obj = pygame.font.SysFont(font_name, font_size)
        self.size = font_size
        self.color = color
        # Store already rendered numbers
        self.render_cache: dict[int, pygame.surface.Surface] = {}

    def get(self, number: int) -> pygame.surface.Surface:
        """Return a Surface with the rendered bitmap of the given number.

        If possible, already cached results will be used."""
        if not number in self.render_cache:
            self.render_cache[number] = self._render(number)
        return self.render_cache[number]

    def _render(self, number: int) -> pygame.surface.Surface:
        return self.font_obj.render(str(number), True, self.color)

class Game:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.total_size = grid_size * CELL_SIZE
        self.grid = empty_square_grid(grid_size)
        self.rects: list[Rect] = []
        self.numbers = self.generate_numbers()
        # TODO: Choose a font
        self.number_renderer = NumberRenderer("sans", FONT_SIZE, GRID_COLOR)

    def generate_numbers(self):
        total_area = self.grid_size * self.grid_size
        n_occupied = 0
        occupied = empty_square_grid(self.grid_size)
        numbers = empty_square_grid(self.grid_size)
        rects: list[Rect] = []

        while n_occupied < total_area:
            # Choose a random unoccupied cell
            n = randrange(total_area - n_occupied)
            for y, row in enumerate(occupied):
                for x, cell in enumerate(row):
                    if cell:
                        continue
                    if not n:
                        # One corner of the rectangle
                        A = [x, y]
                        # Determine available space left and right of A
                        _x = x
                        while True:
                            if _x < 0 or occupied[y][_x]:
                                space_left = (x - _x) - 1
                                break
                            _x -= 1
                        _x = x
                        while True:
                            if _x >= self.grid_size or occupied[y][_x]:
                                space_right = (_x - x) - 1
                                break
                            _x += 1
                        # Choose x-coordinate of B
                        B_x = A[0] - space_left + randrange(space_left + space_right + 1)
                        # Determine available space above and below
                        _y = y
                        while True:
                            if _y < 0 or any([occupied[_y][_x] for _x in range(min(A[0], B_x), max(A[0], B_x) + 1)]):
                                space_above = (y - _y) - 1
                                break
                            _y -= 1
                        _y = y
                        while True:
                            if _y >= self.grid_size or any([occupied[_y][_x] for _x in range(min(A[0], B_x), max(A[0], B_x) + 1)]):
                                space_below = (_y - y) - 1
                                break
                            _y += 1
                        B_y = A[1] - space_above + randrange(space_above + space_below + 1)
                        B = [B_x, B_y]
                        # Habemus rectiangulum!
                        rect = [min(A[0], B[0]),
                                min(A[1], B[1]),
                                max(A[0], B[0]) - min(A[0], B[0]) + 1,
                                max(A[1], B[1]) - min(A[1], B[1]) + 1]
                        # Mark area covered by rectangle as occupied
                        for _x in range(rect[0], rect[0] + rect[2]):
                            for _y in range(rect[1], rect[1] + rect[3]):
                                occupied[_y][_x] = 1
                        # Add area to total number of occupied cells
                        n_occupied += rect[2] * rect[3]
                        rects.append(Rect(Point(A), Point(B)))
                    n -= 1

        # Eliminate 1x1 rectangles
        i = 0
        while i < len(rects):
            if rects[i].width == rects[i].height == 1:
                # Find adjacent rect and merge
                for j, other in enumerate(rects):
                    if other.height == 1 and other.top_left.y == rects[i].top_left.y:
                        if other.top_left.x == rects[i].top_left.x + 1:
                            rects[j] = Rect(Point(other.top_left.x - 1, other.top_left.y),
                                other.bottom_right)
                            break
                        elif other.bottom_right.x == rects[i].top_left.x - 1:
                            rects[j] = Rect(other.top_left,
                                Point(other.bottom_right.x + 1, other.bottom_right.y))
                            break
                    if other.width == 1 and other.top_left.x == rects[i].top_left.x:
                        if other.top_left.y == rects[i].top_left.y + 1:
                            rects[j] = Rect(Point(other.top_left.x, other.top_left.y - 1),
                                other.bottom_right)
                            break
                        elif other.bottom_right.y == rects[i].bottom_right.y - 1:
                            rects[j] = Rect(other.top_left,
                                Point(other.bottom_right.x, other.bottom_right.y + 1))
                            break
                else:
                    # TODO: Solve this by retrying
                    raise Exception("Failed to generate puzzle, retrying.")
                rects.pop(i)

            else:
                i += 1


        for rect in rects:
            numbers[rect.top_left.y + randrange(rect.height)][rect.top_left.x + randrange(rect.width)] = rect.area
        return numbers

    def draw(self, screen: pygame.surface.Surface, pos=[0, 0]):
        # Draw grid
        for i in range(1, self.grid_size):
            pygame.draw.line(screen, GRID_COLOR, (pos[0] + i * CELL_SIZE, pos[1]),
                (pos[0] + i * CELL_SIZE, pos[1] + self.total_size), 1)
        for i in range(1, self.grid_size):
            pygame.draw.line(screen, GRID_COLOR, (pos[0], pos[1] + i * CELL_SIZE),
                (pos[0] + self.total_size, pos[1] + i * CELL_SIZE), 1)

        # Draw rectangles
        for rect in self.rects:
            rect.draw(screen, GRID_DRAWING_POS)

        # Draw numbers
        for y, row in enumerate(self.numbers):
            for x, number in enumerate(row):
                if number:
                    rendered = self.number_renderer.get(number)
                    offset = [int((CELL_SIZE - rendered.get_size()[0]) / 2),
                        int((CELL_SIZE - rendered.get_size()[1]) / 2)]
                    # TODO: Properly center
                    screen.blit(rendered, [x * CELL_SIZE + offset[0], y * CELL_SIZE + offset[1]])

    def add_rect(self, new: Rect):
        # Check if rect contained in grid
        if 0 <= new.top_left.x < self.grid_size and \
            0 <= new.bottom_right.x < self.grid_size and \
            0 <= new.top_left.y < self.grid_size and \
            0 <= new.bottom_right.y < self.grid_size:
            # Remove existing rects that intersect with the new one
            self.rects = [rect for rect in self.rects if not rect.intersects(new)]
            self.rects.append(new)

    def delete_intersecting(self, point: Point):
        # Delete all rects that contain a given point
        self.rects = [rect for rect in self.rects if not rect.contains_point(point)]

    def verify(self):
        covered = empty_square_grid(self.grid_size)
        for rect in self.rects:
            contains_number = False
            for x in range(rect.top_left.x, rect.bottom_right.x + 1):
                for y in range(rect.top_left.y, rect.bottom_right.y + 1):
                    if self.numbers[y][x]:
                        if contains_number or not rect.area == self.numbers[y][x]:
                            return False
                        contains_number = True
                    if covered[x][y]:
                        # Overlap
                        return False
                    covered[x][y] = 1
            if not contains_number:
                return False

        return all([all([cell for cell in row]) for row in covered])

def empty_square_grid(size):
    return [[0 for _ in range(size)] for _ in range(size)]

def pos_to_cell(pos, grid_pos):
    return (int((pos[0] - grid_pos[0]) / CELL_SIZE), int((pos[1] - grid_pos[1]) / CELL_SIZE))

def main():
    pygame.font.init()

    game = Game(GRID_SIZE)
    screen = pygame.display.set_mode([game.total_size, game.total_size])

    input_rect: Optional[Rect] = None
    start_cell: Optional[Point] = None
    mouse_cell: Optional[Point] = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    start_cell = Point(pos_to_cell(event.pos, GRID_DRAWING_POS))
                elif event.button == 3: # Right click
                    input_rect = None
                    start_cell = None
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: # Left click
                    if not start_cell or not mouse_cell:
                        # This happens if RMB is released before LMB is released
                        continue
                    if start_cell == mouse_cell:
                        # If the cursor wasn't moved, delete rect under cursor
                        assert start_cell
                        game.delete_intersecting(start_cell)
                    else:
                        # Place input rect onto grid
                        assert input_rect
                        game.add_rect(input_rect)
                        if game.verify():
                            game = Game(GRID_SIZE)
                    input_rect = None
                    start_cell = None

        if start_cell:
            mouse_cell = Point(pos_to_cell(pygame.mouse.get_pos(), GRID_DRAWING_POS))
            input_rect = Rect(start_cell, mouse_cell)

        screen.fill(BACKGROUND_COLOR)
        game.draw(screen, GRID_DRAWING_POS)
        if input_rect:
            input_rect.draw(screen, GRID_DRAWING_POS)
        pygame.display.flip() 

if __name__ == "__main__":
    main()

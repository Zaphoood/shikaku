#!/usr/bin/env python3
from __future__ import annotations

import os
from contextlib import suppress

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from random import randrange
from typing import Optional

import pygame
from screeninfo import get_monitors


def calc_cell_size(grid_size, cell_base_size) -> int:
    monitor = get_monitors()[0]
    screen_scale = 10
    if monitor.width_mm:
        screen_scale = monitor.width / monitor.width_mm
    cell_size = cell_base_size * screen_scale
    # If too small, scale up
    if cell_size * grid_size < monitor.height * MIN_SCREEN_PERC:
        cell_size = (monitor.height * MIN_SCREEN_PERC) / grid_size
    # If too large, scale down
    if cell_size * grid_size > monitor.height * MAX_SCREEN_PERC:
        cell_size = (monitor.height * MAX_SCREEN_PERC) / grid_size

    return round(cell_size)

GRID_SIZE = 8
CELL_BASE_SIZE = 10
MIN_SCREEN_PERC = 0.25
MAX_SCREEN_PERC = 0.75
CELL_SIZE = calc_cell_size(GRID_SIZE, CELL_BASE_SIZE)
GRID_SUBSECTIONS = 2
GRID_COLOR = (0, 0, 0)
GRID_DRAWING_POS = (0, 0)
BACKGROUND_COLOR = (255, 255, 255)
RECT_COLOR = (0, 0, 0)
RECT_COLOR_INVALID = (255, 100, 100)
RECT_COLOR_FLOATING = (100, 100, 100)
RECT_THICKNESS = 3
DASHED_LINE_THICKNESS = 1
DASHED_LINE_INTERVAL = 6
DASHED_LINE_LENGTH = 3
FONT = "ubuntumono"
BASE_FONT_SIZE = 45
FONT_SIZE = int(min(BASE_FONT_SIZE, CELL_SIZE * 0.85))
FRAMERATE = 60


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

    def __eq__(self, other: Point) -> bool:
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"<Point: x={self.x}, y={self.y}>"

class Rect:
    def __init__(self, a: Point, b: Point, color: tuple[int, int, int] = RECT_COLOR):
        self.init(a, b)
        self.color = color

    def init(self, a: Point, b: Point) -> None:
        left = min(a.x, b.x)
        right = max(a.x, b.x)
        bottom = max(a.y, b.y)
        top = min(a.y, b.y)

        self.top_left = Point(left, top)
        self.bottom_right = Point(right, bottom)

        self.width = (self.bottom_right.x - self.top_left.x + 1)
        self.height = (self.bottom_right.y - self.top_left.y + 1)
        self.area = self.width * self.height

    def set_bottom_right(self, new_bottom_right: Point) -> None:
        self.init(self.top_left, new_bottom_right)

    def set_top_left(self, new_top_left: Point) -> None:
        self.init(new_top_left, self.bottom_right)

    def intersects(self, other: Rect) -> bool:
        return (self.top_left.x <= other.bottom_right.x and self.bottom_right.x >= other.top_left.x)\
                and (self.top_left.y <= other.bottom_right.y and self.bottom_right.y >= other.top_left.y)

    def contains_point(self, other: Point) -> bool:
        return (self.top_left.x <= other.x <= self.bottom_right.x) \
            and (self.top_left.y <= other.y <= self.bottom_right.y)

    def draw(self, screen, offset=[0, 0]) -> None:
        # Fix bug with rects changing size when going (partially) off-screen
        # TODO: Fix off-by-one error with rect drawing
        pygame.draw.rect(screen, self.color,
            [int(self.top_left.x * CELL_SIZE + offset[0] - RECT_THICKNESS / 2),
             int(self.top_left.y * CELL_SIZE + offset[1] - RECT_THICKNESS / 2),
             int(self.width * CELL_SIZE + RECT_THICKNESS),
             int(self.height * CELL_SIZE + RECT_THICKNESS)],
            RECT_THICKNESS)

    def draw_floating(self, screen, offset=[0, 0]) -> None:
        """Draw rect using dashed lines"""
        for x in range(self.top_left.x * CELL_SIZE - 1, (self.bottom_right.x + 1) * CELL_SIZE, DASHED_LINE_INTERVAL):
            pygame.draw.line(screen, RECT_COLOR_FLOATING,
                    [offset[0] + x, offset[1] + self.top_left.y * CELL_SIZE - 1],
                    [min(offset[0] + x + DASHED_LINE_LENGTH, (self.bottom_right.x + 1) * CELL_SIZE),
                        offset[1] + self.top_left.y * CELL_SIZE - 1],
                    width = DASHED_LINE_THICKNESS)
            pygame.draw.line(screen, RECT_COLOR_FLOATING,
                    [offset[0] + x, offset[1] + (self.bottom_right.y + 1) * CELL_SIZE - 1],
                    [min(offset[0] + x + DASHED_LINE_LENGTH, (self.bottom_right.x + 1) * CELL_SIZE),
                        offset[1] + (self.bottom_right.y + 1) * CELL_SIZE - 1],
                    width = DASHED_LINE_THICKNESS)
        for y in range(self.top_left.y * CELL_SIZE - 1, (self.bottom_right.y + 1) * CELL_SIZE, DASHED_LINE_INTERVAL):
            pygame.draw.line(screen, RECT_COLOR_FLOATING,
                    [offset[0] + self.top_left.x * CELL_SIZE - 1, offset[1] + y],
                    [offset[0] + self.top_left.x * CELL_SIZE - 1,
                        min(offset[1] + y + DASHED_LINE_LENGTH, (self.bottom_right.y + 1) * CELL_SIZE)],
                    width = DASHED_LINE_THICKNESS)
            pygame.draw.line(screen, RECT_COLOR_FLOATING,
                    [offset[0] + (self.bottom_right.x + 1) * CELL_SIZE - 1, offset[1] + y],
                    [offset[0] + (self.bottom_right.x + 1) * CELL_SIZE - 1,
                        min(offset[1] + y + DASHED_LINE_LENGTH, (self.bottom_right.y + 1) * CELL_SIZE)],
                    width = DASHED_LINE_THICKNESS)

    def verify(self, numbers: list[list[int]]) -> bool:
        contains_number = False
        for x in range(self.top_left.x, self.bottom_right.x + 1):
            for y in range(self.top_left.y, self.bottom_right.y + 1):
                if numbers[y][x]:
                    if contains_number or not self.area == numbers[y][x]:
                        self.color = RECT_COLOR_INVALID
                        return False
                    contains_number = True
        if not contains_number:
            self.color = RECT_COLOR_INVALID
            return False
        return True

class NumberRenderer:
    def __init__(self, font_name: str, font_size: int, color: tuple[int, int, int], font_path: Optional[str] = None):
        if font_path:
            self.name = ""
            self.font_obj = pygame.font.Font(font_path, font_size)
        else:
            if not font_name in pygame.font.get_fonts():
                print(f"Font not available: '{font_name}'. Using fallback.")
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
        self.rects: list[Rect] = []
        # Store for each cell wether it is covered by a rectangle
        self.covered = empty_square_grid(grid_size)
        self.numbers = self.generate_numbers()
        self.number_renderer = NumberRenderer(FONT, FONT_SIZE, GRID_COLOR)

    def generate_numbers(self) -> list[list[int]]:
        total_area = self.grid_size * self.grid_size

        # TODO: Limit maximum rect area to be certain fraction of grid
        while True:
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
                            rect = Rect(Point(A), Point(B))
                            # Mark area covered by rectangle as occupied
                            for _x in range(rect.top_left.x, rect.bottom_right.x + 1):
                                for _y in range(rect.top_left.y, rect.bottom_right.y + 1):
                                    occupied[_y][_x] = 1
                            # Add area to total number of occupied cells
                            n_occupied += rect.width * rect.height
                            rects.append(rect)
                        n -= 1

            # Eliminate 1x1 rectangles
            success = True
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
                        success = False
                    rects.pop(i)
                else:
                    i += 1
            if success:
                break

        for rect in rects:
            numbers[rect.top_left.y + randrange(rect.height)][rect.top_left.x + randrange(rect.width)] = rect.area
        return numbers

    def draw(self, screen: pygame.surface.Surface, pos=[0, 0]) -> None:
        # Draw grid
        for x in range(1, self.grid_size * GRID_SUBSECTIONS):
            for y in range(1, self.grid_size * GRID_SUBSECTIONS):
                if (not x % GRID_SUBSECTIONS) and (not y % GRID_SUBSECTIONS):
                    pygame.draw.rect(screen, GRID_COLOR,
                        [int(pos[0] + (x / GRID_SUBSECTIONS) * CELL_SIZE - RECT_THICKNESS / 2),
                         int(pos[0] + (y / GRID_SUBSECTIONS) * CELL_SIZE - RECT_THICKNESS / 2),
                         RECT_THICKNESS,
                         RECT_THICKNESS], 0)
                elif (not x % GRID_SUBSECTIONS) or (not y % GRID_SUBSECTIONS):
                    screen.set_at([int(pos[0] + (x / GRID_SUBSECTIONS) * CELL_SIZE), int(pos[0] + (y / GRID_SUBSECTIONS) * CELL_SIZE)],
                        GRID_COLOR)

        # Draw rectangles
        for rect in self.rects:
            rect.draw(screen, pos)

        # Draw numbers
        for y, row in enumerate(self.numbers):
            for x, number in enumerate(row):
                if number:
                    rendered = self.number_renderer.get(number)
                    offset = [int((CELL_SIZE - rendered.get_size()[0]) / 2),
                        int((CELL_SIZE - rendered.get_size()[1]) / 2)]
                    screen.blit(rendered, [pos[0] + x * CELL_SIZE + offset[0], pos[1] + y * CELL_SIZE + offset[1]])

    def add_rect(self, new: Rect) -> None:
        # Check if rect contained in grid
        if not (0 <= new.top_left.x < self.grid_size and \
            0 <= new.bottom_right.x < self.grid_size and \
            0 <= new.top_left.y < self.grid_size and \
            0 <= new.bottom_right.y < self.grid_size):
            return
        # Remove existing rects that intersect with the new one
        intersecting = [i for i, rect in enumerate(self.rects) if rect.intersects(new)]
        self.delete_rects_by_indices(intersecting)
        self.rects.append(new)
        # Set cells as covered
        for y in range(new.top_left.y, new.bottom_right.y + 1):
            for x in range(new.top_left.x, new.bottom_right.x + 1):
                self.covered[y][x] = 1

        # Add implicitly created rects (rectangle-shaped, uncovered areas enclosed by
        # other rectangles that contain exactly one number)

        # Find uncovered cells that are horiz. or vert. adjacent to just created rectangle
        uncovered_neighbours: list[Point] = []
        def is_covered(p: Point) -> bool:
            if not (0 <= p.x < self.grid_size and 0 <= p.y < self.grid_size):
                return True
            return bool(self.covered[p.y][p.x])
        def add_if_uncovered(p: Point) -> None:
            if not is_covered(p):
                uncovered_neighbours.append(p)
        def get_adjacent(p: Point) -> list[Point]:
            return [Point(p.x + 1, p.y), Point(p.x - 1, p.y),
                    Point(p.x, p.y + 1), Point(p.x, p.y - 1)]
        def continuous_uncovered(p: Point) -> list[Point]:
            if is_covered(p):
                return []
            # If we visited two numbers, we can abort
            visited_number = False
            found = []
            queue = [p]
            while queue:
                current = queue.pop()
                found.append(current)
                if self.numbers[current.y][current.x]:
                    if visited_number:
                        return []
                    else:
                        visited_number = True
                queue.extend([p for p in get_adjacent(current) if (not is_covered(p) and not p in found and not p in queue)])
            if visited_number:
                return found
            else:
                return []

        for x in range(new.top_left.x, new.bottom_right.x + 1):
            add_if_uncovered(Point(x, new.top_left.y - 1))
            add_if_uncovered(Point(x, new.bottom_right.y + 1))
        for y in range(new.top_left.y, new.bottom_right.y + 1):
            add_if_uncovered(Point(new.top_left.x - 1, y))
            add_if_uncovered(Point(new.bottom_right.x + 1, y))
        # Group continuous uncovered areas and check if they are rectangles
        implicit_rects = []
        while uncovered_neighbours:
            cont_u = continuous_uncovered(uncovered_neighbours.pop())
            # Get bounding rect of continuous area
            min_x = min_y = self.grid_size
            max_x = max_y = 0
            for cell in cont_u:
                min_x = min(min_x, cell.x)
                max_x = max(max_x, cell.x)
                min_y = min(min_y, cell.y)
                max_y = max(max_y, cell.y)
                with suppress(ValueError): # contextlib.suppress
                    uncovered_neighbours.remove(cell)
            # Check if continuous area is equal to it's bounding rect
            # If their areas differ, it's not a rect
            if (max_x - min_x + 1) * (max_y - min_y + 1) != len(cont_u):
                continue
            # Check if all cells of continuous area are inside rect
            if not all([min_x <= cell.x <= max_x and min_y <= cell.y <= max_y for cell in cont_u]):
                continue
            # TODO: Should implicit rects only be added if they are correct?
            implicit_rects.append(Rect(Point(min_x, min_y), Point(max_x, max_y)))

        self.rects.extend(implicit_rects)

    def delete_intersecting(self, point: Point) -> None:
        """Delete all rects that contain a given Point"""
        self.delete_rects_by_indices([i for i, rect in enumerate(self.rects) if rect.contains_point(point)])

    def delete_rects_by_indices(self, indices: list[int]) -> None:
        deleted = [self.rects[i] for i in indices]
        self.rects = [rect for i, rect in enumerate(self.rects) if i not in indices]
        for rect in deleted:
            for y in range(rect.top_left.y, rect.bottom_right.y + 1):
                for x in range(rect.top_left.x, rect.bottom_right.x + 1):
                    self.covered[y][x] = 0

    def verify(self) -> bool:
        return all([rect.verify(self.numbers) for rect in self.rects]) and sum([rect.area for rect in self.rects]) == self.grid_size * self.grid_size

def empty_square_grid(size) -> list[list[int]]:
    return [[0 for _ in range(size)] for _ in range(size)]

def pos_to_cell(pos, grid_pos) -> tuple[int, int]:
    return (int((pos[0] - grid_pos[0]) / CELL_SIZE), int((pos[1] - grid_pos[1]) / CELL_SIZE))


def main():
    pygame.font.init()

    game = Game(GRID_SIZE)
    screen = pygame.display.set_mode([game.total_size + GRID_DRAWING_POS[0] * 2,
        game.total_size + GRID_DRAWING_POS[1] * 2])

    input_rect: Optional[Rect] = None
    start_cell: Optional[Point] = None
    mouse_cell: Optional[Point] = None

    running = True
    clock = pygame.time.Clock()
    while running:
        clock.tick(FRAMERATE)
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
            input_rect.draw_floating(screen, GRID_DRAWING_POS)
        pygame.display.flip() 

if __name__ == "__main__":
    main()

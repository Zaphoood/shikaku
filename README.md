# Shikaku

A fun and challenging puzzle game. My implementation was inspired by [this](https://www.puzzle-shikaku.com/) website.

## Rules

You have to divide the grid into rectangular pieces such that each piece contains exactly one number, and that number is equal the area of the rectangle. ([Source](https://www.puzzle-shikaku.com/))

## Setup

You will need Python 3.10, as well as the pygame library. To install pygame, run
```
python -m pip install pygame
```

## Usage

To start the game, run `python shikaku.py`.

Create new rectangles by clicking and dragging the mouse, delete rectangles simply by clicking them.

Alternatively, use the arrow keys to navigate: Press <kbd>Space</kbd> to start creating
a rectangle, resize using the arrow keys and press <kbd>Space</kbd> again to confirm.
To delete a rectangle under the cursor, press <kbd>D</kbd>.
While resizing, use <kbd>Ctrl+&lt;Arrow Key&gt;</kbd> to auto-fill.

Have fun!

## Example

This is what a solved game might look like:

<p align="center">
  <br>
  <img src="./examples/solved.png" width="50%"/>
</p>

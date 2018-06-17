"""Display chess board."""

import sys
import os
import pygame
from chess import ChessBoard, IllegalMove


class ChessDisplay():
    """Display chess board."""

    def __init__(self):
        """Init."""
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.width = 800
        self.height = 800

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Schroedinger Chess Game")

        self.load_images()

        self.selectedBox = None  # The box which has been clicked on

    def update(self, cb):
        """
        Update the graphical interface to match the given ChessBoard item.

        Handles piece selection and move attempts.
        :param cb: A ChessBoard object
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            # We check for a mouse click
            if event.type == pygame.MOUSEBUTTONUP:
                # A left click triggers the move, other clicks cancel it
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    box = ((8 * mouse[0]) // self.width), ((8 * mouse[1]) // self.height)
                    if self.selectedBox is None:  # If no box is selected
                        if cb.grid[box[0]][7 - box[1]] is not None:  # If we are targeting a non-empty box
                            self.selectedBox = box
                    else:  # if another box has already been selected, we try a move from the old box to the new box
                        try:
                            cb.move(self.selectedBox[0], 7 -
                                    self.selectedBox[1], box[0], 7 - box[1])
                            self.selectedBox = None
                        except IllegalMove as e:
                            # TODO: Make IllegalMove appear visually
                            print(e)
                            self.selectedBox = None
                else:
                    self.selectedBox = None

        # Now we display the board and the various pieces
        self.screen.blit(self.board, (0, 0))
        for y in range(8):
            for x in range(8):
                piece = cb.grid[x][y]
                if piece is not None:
                    # TODO: Manage the case where a piece has several natures
                    n = piece.possible_natures[0]
                    if n is None:
                        n = "P"
                    picture = self.pieces_pictures[piece.color_name.lower() + n]
                    self.screen.blit(picture, ((x * self.width) // 8, ((7 - y) * self.height) // 8))
        if self.selectedBox is not None:
            x = (self.selectedBox[0] * self.width) // 8
            y = (self.selectedBox[1] * self.height) // 8
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0, 0), [
                             x, y, self.width // 8, self.height // 8], 5)

        pygame.display.flip()

    def load_images(self):
        """Retrieve images from memory."""
        pieces_names = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]
        self.pieces_pictures = {}
        for name in pieces_names:
            self.pieces_pictures[name] = pygame.transform.scale(pygame.image.load(
                "img/" + name + ".png"), (self.width // 8, self.height // 8))
        self.board = pygame.transform.scale(pygame.image.load(
            "img/board.png"), (self.width, self.height))

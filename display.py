"""Display chess board."""

import sys
import os
import pygame

from chess import ChessPiece, ChessBoard, IllegalMove


class ChessDisplay():
    """Display chess board."""

    def __init__(self, gameEngine):
        """Init."""
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.width = 800
        self.height = 800

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Schroedinger Chess Game")

        self.state = "MENU"

        self.load_images()

        self.gameEngine = gameEngine

        self.selectedBox = None  # The box which has been clicked on


    def setTwoPlayersOnOneBoardMode(self):
        if self.state == "MENU":
            self.state = "PLAYING"
            self.gameEngine.setTwoPlayersOnOneBoardMode()
            self.drawBoard()


    def setOnePlayerOnNetworkMode(self):
        if self.state == "MENU":
            self.state = "PLAYING"
            self.gameEngine.setOnePlayerOnNetworkMode()
            self.drawBoard()


    def drawBoard(self):
        self.screen.blit(self.board, (0, 0))
        for y in range(8):
            for x in range(8):
                piece = self.gameEngine.getPiece(x,y)
                if piece is not None:
                    # TODO: Manage the case where a piece has several natures
                    n = piece.possible_natures[0]
                    if n is None:
                        n = "P"
                    picture = self.pieces_pictures[piece.color_name.lower() + n]
                    self.screen.blit(picture, ((x * self.width) // 8, ((7 - y) * self.height) // 8))

        pygame.display.flip()

    def undrawSelectedBox(self):
        if self.selectedBox is not None:
            self.drawBoard()
            pygame.display.flip()

    def drawSelectedBox(self):
        if self.selectedBox is not None:
            x = (self.selectedBox[0] * self.width) // 8
            y = (self.selectedBox[1] * self.height) // 8
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0, 0), [
                x, y, self.width // 8, self.height // 8], 5)
            pygame.display.flip()

    def update(self):
        if self.state == "MENU":
            self.updateMenu()
        elif self.state == "PLAYING":
            self.updateBoard()
        else:
            pass

    def updateMenu(self):
        self.setTwoPlayersOnOneBoardMode()

    def updateBoard(self):
        """
        Update the graphical interface to match the given ChessBoard item.

        Handles piece selection and move attempts.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.gameEngine.stop()

            # We check for a mouse click
            if event.type == pygame.MOUSEBUTTONUP:
                # A left click triggers the move, other clicks cancel it
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    box = ((8 * mouse[0]) // self.width), ((8 * mouse[1]) // self.height)
                    if self.selectedBox is None:  # If no box is selected
                            self.selectedBox = box
                            self.drawSelectedBox()
                    else:  # if another box has already been selected, we try a move from the old box to the new box
                        try:
                            self.gameEngine.move(self.selectedBox[0], 7 - self.selectedBox[1], box[0], 7 - box[1])
                            self.undrawSelectedBox()
                            self.selectedBox = None
                        except IllegalMove:
                            # TODO: Make IllegalMove appear visually
                            self.undrawSelectedBox()
                            self.selectedBox = None
                else:
                    self.undrawSelectedBox()
                    self.selectedBox = None

        if self.selectedBox is not None:
            self.drawSelectedBox()

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


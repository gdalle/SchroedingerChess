"""Display chess board."""

import sys
import os
import pygame

from chess import ChessPiece, ChessBoard, IllegalMove


class ChessDisplay():
    """Display of the chess board."""

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
        """ Sets the game engine on the two-players-on-one-board mode."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.gameEngine.setTwoPlayersOnOneBoardMode()
            self.gameEngine.makeDisplayDrawBoard()


    def setOnePlayerOnNetworkMode(self):
        """ Sets the game engine on the one-player on network mode."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.gameEngine.setOnePlayerOnNetworkMode()
            self.gameEngine.makeDisplayDrawBoard()


    def drawBoard(self, lightBoard):
        """
        Draws the board.
        :param lightBoard: The light board to draw. :see LightBoard
        """
        self.screen.blit(self.board, (0, 0))
        for y in range(8):
            for x in range(8):
                piece = lightBoard.getPiece(x, y)
                if piece is not None:
                    picture = self.pieces_pictures[piece[1] + piece[0]]
                    self.screen.blit(picture, ((x * self.width) // 8, ((7 - y) * self.height) // 8))
        pygame.display.flip()

    def undrawSelectedBox(self):
        """
        Undraws the selected box.
        """
        if self.selectedBox is not None:
            self.gameEngine.makeDisplayDrawBoard()

    def drawSelectedBox(self, natures): #TODO draw superposition of symbols
        """
        Draws the selected box.
        :param natures: List of the possible natures of the piece.
        """
        if self.selectedBox is not None:
            x = (self.selectedBox[0] * self.width) // 8
            y = (self.selectedBox[1] * self.height) // 8
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0, 0), [
                x, y, self.width // 8, self.height // 8], 5)
            pygame.display.flip()


    def drawChecks(self, check_positions): #TODO implement
        """
        Draws the checks created by the last move.
        :param check_positions: List of the check positions.
        """
        for pos in check_positions:
            x = pos[0]
            y = pos[0]

    def drawCheckMates(self, checkmates_positions):
        """
        Draws the checkmates created by the last move.
        :param checkmates_positions: List of the checkmate positions.
        """
        for pos in checkmates_positions:
            x = pos[0]
            y = pos[0]

    def handleIllegalMove(self, reason):
        """
        Handles illegal moves.
        :param reason: TOD0
        """
        #TODO see what to do see handleIllegalMove in GameEngine
        raise NotImplementedError


    def update(self):
        """ Updates the frame."""
        if self.state == "MENU":
            self.updateMenu()
        elif self.state == "PLAYING":
            self.updateBoard()
        elif self.state == "WAITING":
            pass
        else:
            pass

    def updateMenu(self):
        #TODO implement a menu
        #for now directly switches to two-players-on-one-board mode.
        self.setTwoPlayersOnOneBoardMode()

    def updateBoard(self):
        """
        Handles piece selection and move attempts.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.gameEngine.stop()

            # We check for a mouse click
            elif event.type == pygame.MOUSEBUTTONUP:
                # A left click triggers the move, other clicks cancel it
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    box = ((8 * mouse[0]) // self.width), ((8 * mouse[1]) // self.height)
                    if self.selectedBox is None:  # If no box is selected
                            self.selectedBox = box
                            self.gameEngine.selectBox(self.selectedBox[0], 7 - self.selectedBox[1])
                    else:  # if another box has already been selected, we try a move from the old box to the new box
                        self.gameEngine.move(self.selectedBox[0], 7 - self.selectedBox[1], box[0], 7 - box[1])
                        self.undrawSelectedBox()
                        self.selectedBox = None
                        self.state = "WAITNG"
                else:
                    self.undrawSelectedBox()
                    self.selectedBox = None

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


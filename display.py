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
        self.total_height = 900

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.total_height))
        pygame.display.set_caption("Schroedinger Chess Game")

        self.state = "MENU"

        self.load_images()

        self.gameEngine = gameEngine

        self.selectedBox = None  # The box which has been clicked on

        self.flip = False # Should the ChessBoard be upside down

        self.check_positions = [[False for i in range(8)] for j in range(8)]
        self.checkmate_positions = [[False for i in range(8)] for j in range(8)]

        self.currentMessage = ""


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


    def drawBoard(self, lightBoard, exceptBox=None):
        """
        Draws the board.
        :param lightBoard: The light board to draw. :see LightBoard
        :param exceptBox: A box which has to bet let empty whatever it contains
        """
        self.screen.blit(self.boardFlip if self.flip else self.board, (0, 0))
        for y in range(8):
            for x in range(8):
                if self.check_positions[x][y]:
                    pygame.draw.rect(self.screen, pygame.Color(150, 0, 0, 255), [
                        (x * self.width) // 8, (self.flipY(y) * self.height) // 8,
                        self.width // 8, self.height // 8], 5)

                if self.checkmate_positions[x][y]:
                    pygame.draw.rect(self.screen, pygame.Color(255, 0, 0, 255), [
                        (x * self.width) // 8, (self.flipY(y) * self.height) // 8,
                        self.width // 8, self.height // 8], 5)

                if exceptBox is not None and exceptBox[0]==x and exceptBox[1]==self.flipY(y):
                    continue

                piece = lightBoard.getPiece(x, y)
                if piece is not None:
                    picture = self.pieces_pictures[piece[1] + piece[0]]
                    self.screen.blit(picture, ((x * self.width) // 8, (self.flipY(y) * self.height) // 8))
        pygame.display.flip()

    def undrawSelectedBox(self):
        """
        Undraws the selected box.
        """
        if self.selectedBox is not None:
            self.gameEngine.makeDisplayDrawBoard()

    def drawSelectedBox(self, natures):
        """
        Draws the selected box.
        :param natures: List of the possible natures of the piece.
        """
        if self.selectedBox is not None:
            x = (self.selectedBox[0] * self.width) // 8
            y = (self.selectedBox[1] * self.height) // 8
            piece = self.gameEngine.lightBoard.getPiece(self.selectedBox[0], self.flipY(self.selectedBox[1]))
            if piece is not None:
                color = piece[1]
                if len(natures) == 1:
                    self.gameEngine.makeDisplayDrawBoard()
                else:
                    self.gameEngine.makeDisplayDrawBoard(exceptBox=self.selectedBox)
                    if len(natures) == 5:
                        for i in range(len(natures)):
                            xp = x + ((2*i)%3)*self.width // 24
                            yp = y + ((2*i)//3)*self.height // 24
                            picture = self.pieces_pictures[color + natures[i] + "xs"]
                            self.screen.blit(picture, (xp, yp))
                    else:
                        for i in range(len(natures)):
                            xp = x + (i%2)*self.width // 16
                            yp = y + (i//2)*self.height // 16
                            picture = self.pieces_pictures[color + natures[i] + "s"]
                            self.screen.blit(picture, (xp, yp))
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0, 0), [
                x, y, self.width // 8, self.height // 8], 5)

            pygame.display.flip()


    def drawChecks(self, check_positions):
        """
        Draws the checks created by the last move.
        :param check_positions: List of the check positions.
        """
        self.check_positions = [[False for i in range(8)] for j in range(8)]
        for pos in check_positions:
            self.check_positions[pos[0]][pos[1]] = True
        self.gameEngine.makeDisplayDrawBoard()

    def drawCheckMates(self, checkmate_positions):
        """
        Draws the checkmates created by the last move.
        :param checkmates_positions: List of the checkmate positions.
        """
        self.checkmate_positions = [[False for i in range(8)] for j in range(8)]
        for pos in checkmate_positions:
            self.checkmate_positions[pos[0]][pos[1]] = True
        self.gameEngine.makeDisplayDrawBoard()

    def handleIllegalMove(self, reason):
        """
        Handles illegal moves.
        :param reason: TOD0
        """
        self.currentMessage = reason
        self.updateMessage()


    def update(self):
        """ Updates the frame."""
        if self.state == "MENU":
            self.updateMenu()
        elif self.state == "PLAYING":
            self.updateBoard()
            self.updateMessage()
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
                self.currentMessage = ""
                self.updateMessage()
                # A left click triggers the move, other clicks cancel it
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    box = ((8 * mouse[0]) // self.width), ((8 * mouse[1]) // self.height)
                    if box[0] < 8 and box[1] < 8:
                        if self.selectedBox is None:  # If no box is selected
                                self.selectedBox = box
                                self.gameEngine.selectBox(self.selectedBox[0], self.flipY(self.selectedBox[1]))
                        else:  # if another box has already been selected, we try a move from the old box to the new box
                            self.gameEngine.move(self.selectedBox[0], self.flipY(self.selectedBox[1]), box[0], self.flipY(box[1]))
                            self.undrawSelectedBox()
                            self.selectedBox = None
                            self.state = "WAITNG"
                    else:
                        self.undrawSelectedBox()
                        self.selectedBox = None
                else:
                    self.undrawSelectedBox()
                    self.selectedBox = None

        pygame.display.flip()

    def updateMessage(self):
        font = pygame.font.SysFont("Lato Heavy", 30)
        text = font.render(self.currentMessage, True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.width // 2, (self.total_height+self.height+5) // 2))
        pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [
            0, self.height, self.width, self.total_height-self.height
        ])
        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
            0, self.height, self.width, 5
        ])
        self.screen.blit(text, text_rect)
        # print(pygame.font.get_fonts())

    def load_images(self):
        """Retrieve images from memory."""
        pieces_names = ["bB", "bK", "bN", "bP", "bQ", "bR", "bE", "wB", "wK", "wN", "wP", "wQ", "wR", "wE"]
        self.pieces_pictures = {}
        for name in pieces_names:
            self.pieces_pictures[name] = pygame.transform.scale(pygame.image.load(
                "img/" + name + ".png"), (self.width // 8, self.height // 8))
            self.pieces_pictures[name+"s"] = pygame.transform.scale(self.pieces_pictures[name],
                (self.width // 16, self.height // 16)) # small icons for multiple display
            self.pieces_pictures[name+"xs"] = pygame.transform.scale(self.pieces_pictures[name],
                (self.width // 24, self.height // 24))
        self.board = pygame.transform.scale(pygame.image.load(
            "img/board.png"), (self.width, self.height)) # smaller icons for multiple display
        self.boardFlip = pygame.transform.flip(self.board, False, True)

    def flipDisplay(self, newState):
        """
        Set the display orientation
        :param newState: Is True if and only if the display has to be upside down (Black in the lower part)
        """
        self.flip = newState
        self.gameEngine.makeDisplayDrawBoard()

    def flipY(self, y):
        """
        Flip the y coordinate depending on the flip parameter
        """
        return y if self.flip else 7-y

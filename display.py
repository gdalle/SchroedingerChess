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
        self.width = 600
        self.height = 600
        self.pane_width = 300
        self.total_width = self.width + self.pane_width
        self.total_height = self.height

        pygame.init()
        # self.screen = pygame.display.set_mode((self.total_width, self.total_height), pygame.RESIZABLE)
        self.screen = pygame.display.set_mode((self.total_width, self.total_height))
        pygame.display.set_caption("Schroedinger Chess Game")

        self.state = "MENU"

        self.menuState = "START" # The menu has different states
        self.menuSelection = "NONE" # The item currently being selected in the menu

        self.load_images()

        self.gameEngine = gameEngine

        self.selectedBox = None  # The box which has been clicked on

        self.flip = False # Should the ChessBoard be upside down

        self.check_positions = [[False for i in range(8)] for j in range(8)]
        self.checkmate_positions = [[False for i in range(8)] for j in range(8)]

        self.message_history = []
        self.maximum_messages = 9
        self.current_first_message = 0
        self.message_font = pygame.font.SysFont("Arial", 13)
        self.addMessage("Please select a game mode")

        self.drawMenu()
        self.drawPane()

    def setTwoPlayersOnOneBoardMode(self):
        """ Sets the game engine on the two-players-on-one-board mode."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.gameEngine.makeDisplayDrawBoard()
            self.gameEngine.setTwoPlayersOnOneBoardMode()
            self.addMessage("Started local game")


    def setOnePlayerOnNetworkMode(self):
        """ Sets the game engine on the one-player on network mode."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.gameEngine.makeDisplayDrawBoard()
            self.gameEngine.setOnePlayerOnNetworkMode()
            self.addMessage("Started online game")


    def drawBoard(self, lightBoard):
        """
        Draws the board.
        :param lightBoard: The light board to draw. :see LightBoard
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

                if self.selectedBox is not None and self.selectedBox[0]==x and self.selectedBox[1]==self.flipY(y):
                    continue

                piece = lightBoard.getPiece(x, y)
                if piece is not None:
                    color = piece[0]
                    natures = piece[1]
                    if color==0:
                        picture_name = "w"
                    else:
                        picture_name = "b"
                    if (len(natures) > 1):
                        picture_name += "E"
                    else:
                        picture_name += natures[0]
                    picture = self.pieces_pictures[picture_name]
                    self.screen.blit(picture, ((x * self.width) // 8, (self.flipY(y) * self.height) // 8))
        self.drawSelectedBox()
        pygame.display.flip()

    def undrawSelectedBox(self):
        """
        Undraws the selected box.
        """
        if self.selectedBox is not None:
            self.gameEngine.makeDisplayDrawBoard()

    def drawSelectedBox(self):
        """
        Draws the selected box.
        """
        if self.selectedBox is not None:
            x = (self.selectedBox[0] * self.width) // 8
            y = (self.selectedBox[1] * self.height) // 8
            piece = self.gameEngine.lightBoard.getPiece(self.selectedBox[0], self.flipY(self.selectedBox[1]))
            if piece is not None:
                if piece[0] == 0:
                    color = "w"
                else:
                    color = "b"
                natures = piece[1]
                if len(natures) == 1:
                    picture = self.pieces_pictures[color + natures[0]]
                    self.screen.blit(picture, (x, y))
                else:
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
                x, y, self.width // 8, self.height // 8], int(0.00625*self.width))


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
        self.addMessage(reason)
        self.updatePane()


    def update(self):
        """ Updates the frame."""
        # for event in pygame.event.get(pygame.VIDEORESIZE):
        #     self.total_width = event.w
        #     self.total_height = event.h
        #     self.height = min(event.w, event.h-100)
        #     self.width = self.height
        #     self.load_images()
        #     self.gameEngine.makeDisplayDrawBoard()
        all_events = pygame.event.get()
        dispatched_events = self.dispatch_events(all_events)
        if self.state == "MENU":
            self.updateMenu(dispatched_events["board"])
            self.updatePane(dispatched_events["pane"])
        elif self.state == "PLAYING":
            self.updateBoard(dispatched_events["board"])
            self.updatePane(dispatched_events["pane"])
        else:
            pass

    def updateMenu(self, events):
        """
        Updates the start menu.
        """
        if self.menuState == "START":
            # Reference coordinates
            w = int(0.6375*self.width)
            h = int(0.1875*self.height)
            abs_w = int(0.1875*self.width)
            abs_h = int(0.21875*self.height)
            abs_h2 = int(0.59375*self.height)

            changeState = False
            for event in events:
                if event.type == pygame.QUIT:
                    self.gameEngine.stop()

                if event.type == pygame.MOUSEMOTION:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w+w and mouse[1] > abs_h and mouse[1] < abs_h+h:
                        if self.menuSelection != "LOCAL" and self.menuSelection != "LOCAL_DOWN":
                            changeState = True
                            self.menuSelection = "LOCAL"
                    elif mouse[0] > abs_w and mouse[0] < abs_w+w and mouse[1] > abs_h2 and mouse[1] < abs_h2+h:
                        if self.menuSelection != "ONLINE" and self.menuSelection != "ONLINE_DOWN":
                            changeState = True
                            self.menuSelection = "ONLINE"
                    else:
                        if self.menuSelection != "NONE":
                            changeState = True
                            self.menuSelection = "NONE"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button <= 3:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w+w and mouse[1] > abs_h and mouse[1] < abs_h+h:
                        if self.menuSelection != "LOCAL_DOWN":
                            changeState = True
                            self.menuSelection = "LOCAL_DOWN"
                    if mouse[0] > abs_w and mouse[0] < abs_w+w and mouse[1] > abs_h2 and mouse[1] < abs_h2+h:
                        if self.menuSelection != "ONLINE_DOWN":
                            changeState = True
                            self.menuSelection = "ONLINE_DOWN"

                if event.type == pygame.MOUSEBUTTONUP and event.button <= 3:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w+w and mouse[1] > abs_h and mouse[1] < abs_h+h:
                        if self.menuSelection == "LOCAL_DOWN":
                            self.menuSelection = "NONE"
                            self.setTwoPlayersOnOneBoardMode()
                            return
                    if mouse[0] > abs_w and mouse[0] < abs_w+w and mouse[1] > abs_h2 and mouse[1] < abs_h2+h:
                        if self.menuSelection == "ONLINE_DOWN":
                            self.addMessage("The online mode is not supported yet.")
                            changeState = True
                            self.menuSelection = "ONLINE"

            if changeState:
                fontTitle = pygame.font.Font("fonts/CFRemingtonTypewriter-Regul.ttf", 60)
                if self.menuSelection == "LOCAL":
                    pygame.draw.rect(self.screen, pygame.Color(170, 170, 170), [abs_w, abs_h, w, h])
                    local = fontTitle.render("Local game", True, (0, 0, 0))
                    local_rect = local.get_rect(center=(self.width // 2, (0.3125*self.height)))
                    self.screen.blit(local, local_rect)
                elif self.menuSelection == "LOCAL_DOWN":
                    pygame.draw.rect(self.screen, pygame.Color(140, 140, 140), [abs_w, abs_h, w, h])
                    local = fontTitle.render("Local game", True, (0, 0, 0))
                    local_rect = local.get_rect(center=(self.width // 2, (0.3125*self.height)))
                    self.screen.blit(local, local_rect)
                elif self.menuSelection == "ONLINE":
                    pygame.draw.rect(self.screen, pygame.Color(170, 170, 170), [abs_w, abs_h2, w, h])
                    online = fontTitle.render("Online game", True, (0, 0, 0))
                    online_rect = online.get_rect(center=(self.width // 2, (0.6875*self.height)))
                    self.screen.blit(online, online_rect)
                elif self.menuSelection == "ONLINE_DOWN":
                    pygame.draw.rect(self.screen, pygame.Color(140, 140, 140), [abs_w, abs_h2, w, h])
                    online = fontTitle.render("Online game", True, (0, 0, 0))
                    online_rect = online.get_rect(center=(self.width // 2, (0.6875*self.height)))
                    self.screen.blit(online, online_rect)
                else:
                    self.drawMenu()
                pygame.display.flip()

    def updateBoard(self, events):
        """
        Handles piece selection and move attempts.
        """
        for event in events:
            if event.type == pygame.QUIT:
                self.gameEngine.stop()

            # We check for a mouse click
            elif event.type == pygame.MOUSEBUTTONUP:
                # A left click triggers the move, other clicks cancel it
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    box = ((8 * mouse[0]) // self.width), ((8 * mouse[1]) // self.height)
                    if box[0] < 8 and box[1] < 8:
                        if self.selectedBox is None:  # If no box is selected
                                self.selectedBox = box
                        else:  # if another box has already been selected, we try a move from the old box to the new box
                            x1, y1, x2, y2 = self.selectedBox[0], self.flipY(self.selectedBox[1]), box[0], self.flipY(box[1])
                            self.gameEngine.move(x1, y1, x2, y2)
                            self.selectedBox = None
                    else:
                        self.selectedBox = None
                else:
                    self.selectedBox = None

                self.gameEngine.makeDisplayDrawBoard()

        pygame.display.flip()

    def updatePane(self, events):
        """
        Update the right hand side plane
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if event.button == 4 and mouse[1] < self.height // 4:
                    self.current_first_message = max(0, self.current_first_message-1)
                    self.drawPane()
                if event.button == 5 and mouse[1] < self.height // 4:
                    self.current_first_message = min(max(0, len(self.message_history)-self.maximum_messages), self.current_first_message+1)
                    self.drawPane()

    def drawMenu(self):
        """
        Draws the start menu.
        """
        self.screen.blit(self.board, (0, 0))
        fontTitle = pygame.font.Font("fonts/CFRemingtonTypewriter-Regul.ttf", 60)
        if self.menuState == "START":
            # When multiplied by 800 we get integer numbers
            w = int(0.6375*self.width)
            h = int(0.1875*self.height)
            abs_w = int(0.1875*self.width)
            abs_h = int(0.21875*self.height)
            abs_h2 = int(0.59375*self.height)
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [abs_w-5, abs_h-5, w+10, h+10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w, abs_h, w, h])
            local = fontTitle.render("Local game", True, (0, 0, 0))
            local_rect = local.get_rect(center=(self.width // 2, (0.3125*self.height)))
            self.screen.blit(local, local_rect)

            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [abs_w-5, abs_h2-5, w+10, h+10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w, abs_h2, w, h])
            online = fontTitle.render("Online game", True, (0, 0, 0))
            online_rect = online.get_rect(center=(self.width // 2, (0.6875*self.height)))
            self.screen.blit(online, online_rect)
        # TODO: implement the other states of the menu -> see with gameEngine
        pygame.display.flip()

    def drawPane(self):
        pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [
            self.width, 0, self.total_width, self.total_height
        ])
        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [self.width, 0, 5, self.height])
        pygame.draw.rect(self.screen, pygame.Color(230, 230, 230), [self.width+15, 10, self.pane_width-30, self.height//4-4])
        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [self.width+15, 10, self.pane_width-30, self.height//4-4], 2)
        selected_messages = self.message_history[self.current_first_message:self.current_first_message+self.maximum_messages]
        for i, message in enumerate(selected_messages):
            local = self.message_font.render(message, True, (0, 0, 0))
            self.screen.blit(local, (self.width+20, 15+i*15))
        pygame.display.flip()

    def load_images(self):
        """Retrieve images from memory."""
        pieces_names = ["bB", "bK", "bN", "bP", "bQ", "bR", "bE", "wB", "wK", "wN", "wP", "wQ", "wR", "wE"]
        self.pieces_pictures = {}
        for name in pieces_names:
            self.pieces_pictures[name] = pygame.transform.smoothscale(pygame.image.load(
                "img/" + name + ".png"), (self.width // 8, self.height // 8))
            self.pieces_pictures[name+"s"] = pygame.transform.smoothscale(self.pieces_pictures[name],
                (self.width // 16, self.height // 16)) # small icons for multiple display
            self.pieces_pictures[name+"xs"] = pygame.transform.smoothscale(self.pieces_pictures[name],
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
        :param y: The y coordinate
        """
        return y if self.flip else 7-y

    def dispatch_events(self, events):
        """
        Dispatch the events to the board and the right hand side pane
        :param events: Array of events produced by pygame.events.get()
        """
        dict = {"board": [], "pane": []}
        for event in events:
            # The board only cares about the click and mouse motion events occuring on the left side of the display
            if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN]:
                mouse = event.pos
                if mouse[0] < self.width:
                    dict["board"].append(event)
                else:
                    dict["pane"].append(event)
            else:
                dict["pane"].append(event)
        return dict

    def addMessage(self, message):
        """
        Split the incoming text message according to the screen size and add it to the message history
        :param message: A string message
        """
        length = 0
        i0 = 0
        message = "> " + message
        for i, c in enumerate(message):
            length += self.message_font.metrics(c)[0][4] # The advance of each letter
            if length > self.pane_width-50:
                length = 0
                self.message_history.append(message[i0:i])
                i0 = i
        if i0 != len(message)-1:
            self.message_history.append(message[i0:])

        self.current_first_message = max(0, len(self.message_history)-self.maximum_messages) # Scroll to the end of the messages
        self.drawPane()

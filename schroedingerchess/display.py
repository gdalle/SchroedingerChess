"""Display chess board."""

import sys
import os
import pygame

from chess import ChessPiece, ChessBoard, IllegalMove


class InputBox():

    def __init__(self, x, y, w, h, text=''):
        self.COLOR_INACTIVE = (230, 230, 230)
        self.COLOR_ACTIVE = (255, 255, 255)
        self.FONT = pygame.font.SysFont("Arial", 20)
        self.rect = pygame.Rect(x, y, w, h)
        self.color = self.COLOR_INACTIVE
        self.text = text
        self.txt_surface = self.FONT.render(text, True, (0, 0, 0))
        self.active = False
        self.has_change = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.COLOR_ACTIVE if self.active else self.COLOR_INACTIVE
            self.has_change = True
        if event.type == pygame.KEYDOWN:
            if self.active:
                # if event.key == pygame.K_RETURN:
                #     self.text = ''
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = self.FONT.render(self.text, True, (0, 0, 0))
                self.has_change = True

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))


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
        self.mode = "NONE"

        self.menuState = "START"  # The menu has different states
        self.menuSelection = "NONE"  # The item currently being selected in the menu

        self.load_images()

        self.gameEngine = gameEngine

        self.selectedBox = None  # The box which has been clicked on
        self.last_move = (-1,-1,-1,-1) # x1, y1, x2, y2 coordinates

        self.flip = False  # Should the ChessBoard be upside down

        self.check_positions = [[False for i in range(8)] for j in range(8)]
        self.checkmate_positions = [[False for i in range(8)] for j in range(8)]

        self.white_dead = []
        self.black_dead = []
        self.dead_font = pygame.font.SysFont("Arial", 18)

        self.message_history = []
        self.maximum_messages = 6
        self.current_first_message = 0
        self.message_font = pygame.font.SysFont("Arial", 13)

        self.pane_buttons_font = pygame.font.SysFont("Arial", 20)
        self.automoveSelection = "NONE"
        self.finishSelection = "NONE"

        self.name = InputBox(int(0.458 * self.width), int(0.6875 *
                                                          self.height) - 40, int(self.width / 3), 32, text="lao")
        self.address = InputBox(int(0.458 * self.width), int(0.6875 *
                                                             self.height) + 10, int(self.width / 3), 32, text="127.0.0.1:6000")
        self.input_boxes = [self.name, self.address]
        self.clock = pygame.time.Clock()
        self.selected_color = "W"

        self.addMessage("Please select a game mode")

        self.drawMenu()
        self.drawPane()

    def setMenuMode(self):
        if self.state == "PLAYING":
            self.state = "MENU"
            self.drawMenu()

    def setTwoPlayersOnOneBoardMode(self):
        """ Sets the game engine on the two-players-on-one-board mode."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.mode = "LOCAL"
            self.gameEngine.setTwoPlayersOnOneBoardMode()
            self.gameEngine.makeDisplayDrawBoard()
            self.addMessage("Started local game")

    def setOnePlayerOnNetworkMode(self, name, address, color):
        """ Sets the game engine on the one-player on network mode."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.mode = "ONLINE"
            self.gameEngine.setOnePlayerOnNetworkMode(name, address, color)
            self.gameEngine.makeDisplayDrawBoard()

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

                if self.last_move[0] >= 0: # If turn > 0
                    x1, y1, x2, y2 = self.last_move
                    pygame.draw.rect(self.screen, pygame.Color(0, 100, 0, 255), [
                        (x1 * self.width) // 8, (self.flipY(y1) * self.height) // 8,
                        self.width // 8, self.height // 8], 3)
                    pygame.draw.rect(self.screen, pygame.Color(0, 180, 0, 255), [
                        (x2 * self.width) // 8, (self.flipY(y2) * self.height) // 8,
                        self.width // 8, self.height // 8], 3)

                piece = lightBoard.getPiece(x, y)
                if piece is not None:
                    isSelection = self.selectedBox is not None and self.selectedBox[0] == x and self.selectedBox[1] == self.flipY(y)
                    self.draw_piece(color=piece["color"],
                                    natures=piece["natures"],
                                    x=(x * self.width) // 8,
                                    y=(self.flipY(y) * self.height) // 8,
                                    size=self.height // 8,
                                    extended=isSelection)
                    if isSelection:
                        pygame.draw.rect(self.screen, pygame.Color(0,0,0), [
                            (x * self.width) // 8,
                            (self.flipY(y) * self.height) // 8,
                            self.width // 8, self.height // 8
                        ], int(0.00625 * self.width))

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
        :param reason: Reason of the illegal move
        """
        self.addMessage(reason)
        self.updatePane()

    def setLastMove(self, x1, y1, x2, y2):
        self.last_move = (x1, y1, x2, y2)

    def update(self):
        """ Updates the frame."""
        events = pygame.event.get()
        if self.state == "MENU":
            self.updateMenu(events)
            self.updatePane(events)
        elif self.state == "PLAYING":
            self.updateBoard(events)
            self.updatePane(events)
        else:
            pass

    def updateMenu(self, events):
        """
        Updates the start menu.
        """
        changeState = False
        if self.menuState == "START":
            # Reference coordinates
            w = int(0.6375 * self.width)
            h = int(0.1875 * self.height)
            abs_w = int(0.1875 * self.width)
            abs_h = int(0.21875 * self.height)
            abs_h2 = int(0.59375 * self.height)

            for event in events:
                if event.type == pygame.QUIT:
                    self.gameEngine.stop()

                if event.type == pygame.MOUSEMOTION:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.menuSelection != "LOCAL" and self.menuSelection != "LOCAL_DOWN":
                            changeState = True
                            self.menuSelection = "LOCAL"
                    elif mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h2 and mouse[1] < abs_h2 + h:
                        if self.menuSelection != "ONLINE" and self.menuSelection != "ONLINE_DOWN":
                            changeState = True
                            self.menuSelection = "ONLINE"
                    else:
                        if self.menuSelection != "NONE":
                            changeState = True
                            self.menuSelection = "NONE"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button <= 3:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.menuSelection != "LOCAL_DOWN":
                            changeState = True
                            self.menuSelection = "LOCAL_DOWN"
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h2 and mouse[1] < abs_h2 + h:
                        if self.menuSelection != "ONLINE_DOWN":
                            changeState = True
                            self.menuSelection = "ONLINE_DOWN"

                if event.type == pygame.MOUSEBUTTONUP and event.button <= 3:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.menuSelection == "LOCAL_DOWN":
                            self.menuSelection = "NONE"
                            self.setTwoPlayersOnOneBoardMode()
                            return
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h2 and mouse[1] < abs_h2 + h:
                        if self.menuSelection == "ONLINE_DOWN":
                            self.menuSelection = "NONE"
                            self.menuState = "ONLINE"
                            self.drawMenu()

        if self.menuState == "ONLINE":
            for event in events:
                if event.type == pygame.QUIT:
                    done = True
                for box in self.input_boxes:
                    box.handle_event(event)

            changeState = False
            for box in self.input_boxes:
                box.update()
                if box.has_change:
                    box.has_change = False
                    changeState = True

            if changeState:
                self.drawMenu()

            # Reference coordinates
            w = int(0.6375 * self.width)
            h = int(0.1875 * self.height)
            h2 = int(0.2675 * self.height)
            abs_w = int(0.1875 * self.width)
            abs_h = int(0.21875 * self.height)
            abs_h2 = int(0.52 * self.height)
            w3 = int(0.4 * self.width)
            h3 = int(0.12 * self.height)
            abs_w3 = int(0.3 * self.width)
            abs_h3 = int(0.82 * self.height)

            for event in events:
                if event.type == pygame.QUIT:
                    self.gameEngine.stop()

                if event.type == pygame.MOUSEMOTION:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.menuSelection != "LOCAL" and self.menuSelection != "LOCAL_DOWN":
                            changeState = True
                            self.menuSelection = "LOCAL"
                    elif mouse[0] > abs_w3 and mouse[0] < abs_w3 + w3 and mouse[1] > abs_h3 and mouse[1] < abs_h3 + h3:
                        if self.menuSelection != "CONNECT" and self.menuSelection != "CONNECT_DOWN":
                            changeState = True
                            self.menuSelection = "CONNECT"
                    else:
                        if self.menuSelection != "NONE":
                            changeState = True
                            self.menuSelection = "NONE"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button <= 3:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.menuSelection != "LOCAL_DOWN":
                            changeState = True
                            self.menuSelection = "LOCAL_DOWN"
                    elif mouse[0] > abs_w3 and mouse[0] < abs_w3 + w3 and mouse[1] > abs_h3 and mouse[1] < abs_h3 + h3:
                        if self.menuSelection != "CONNECT_DOWN":
                            changeState = True
                            self.menuSelection = "CONNECT_DOWN"

                if event.type == pygame.MOUSEBUTTONUP and event.button <= 3:
                    mouse = event.pos
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.menuSelection == "LOCAL_DOWN":
                            self.menuSelection = "NONE"
                            self.setTwoPlayersOnOneBoardMode()
                            return
                    elif mouse[0] > int(0.458 * self.width) and mouse[0] < int(0.458 * self.width) + self.width // 16 + 6 and mouse[1] > int(0.61 * self.height) - 45 - 3 and mouse[1] < int(0.61 * self.height) + self.width // 16 + 6:
                        if self.menuSelection != "SELECT_WHITE":
                            changeState = True
                            self.menuSelection = "SELECT_WHITE"
                            self.selected_color = "W"
                    elif mouse[0] > int(0.55 * self.width) and mouse[0] < int(0.55 * self.width) + self.width // 16 + 6 and mouse[1] > int(0.61 * self.height) - 45 - 3 and mouse[1] < int(0.61 * self.height) - 45 - 3 + self.width // 16 + 6:
                        if self.menuSelection != "SELECT_BLACK":
                            changeState = True
                            self.menuSelection = "SELECT_BLACK"
                            self.selected_color = "B"
                    elif mouse[0] > abs_w3 and mouse[0] < abs_w3 + w3 and mouse[1] > abs_h3 and mouse[1] < abs_h3 + h3:
                        if self.menuSelection == "CONNECT_DOWN":
                            check_IP_port = self.check_address_format(self.address.text)
                            if not check_IP_port:
                                changeState = True
                                self.menuSelection = "CONNECT"
                                self.addMessage(
                                    "Please enter a valid [IP]:[port] (example :    \"127.0.0.1:8006\")")
                            elif len(self.name.text) == 0:
                                changeState = True
                                self.menuSelection = "CONNECT"
                                self.addMessage("Please enter a player name")
                            else:
                                c = 0 if self.selected_color == "W" else 1
                                self.setOnePlayerOnNetworkMode(self.name.text, self.address.text, c)
                                return

        if changeState:
            fontTitleS = pygame.font.Font("fonts/CFRemingtonTypewriter-Regul.ttf", 40)
            fontTitle = pygame.font.Font("fonts/CFRemingtonTypewriter-Regul.ttf", 60)
            if self.menuSelection == "LOCAL":
                pygame.draw.rect(self.screen, pygame.Color(170, 170, 170), [abs_w, abs_h, w, h])
                local = fontTitle.render("Local game", True, (0, 0, 0))
                local_rect = local.get_rect(center=(self.width // 2, (0.3125 * self.height)))
                self.screen.blit(local, local_rect)
            elif self.menuSelection == "LOCAL_DOWN":
                pygame.draw.rect(self.screen, pygame.Color(140, 140, 140), [abs_w, abs_h, w, h])
                local = fontTitle.render("Local game", True, (0, 0, 0))
                local_rect = local.get_rect(center=(self.width // 2, (0.3125 * self.height)))
                self.screen.blit(local, local_rect)
            elif self.menuSelection == "ONLINE":
                pygame.draw.rect(self.screen, pygame.Color(170, 170, 170), [abs_w, abs_h2, w, h])
                online = fontTitle.render("Online game", True, (0, 0, 0))
                online_rect = online.get_rect(center=(self.width // 2, (0.6875 * self.height)))
                self.screen.blit(online, online_rect)
            elif self.menuSelection == "ONLINE_DOWN":
                pygame.draw.rect(self.screen, pygame.Color(140, 140, 140), [abs_w, abs_h2, w, h])
                online = fontTitle.render("Online game", True, (0, 0, 0))
                online_rect = online.get_rect(center=(self.width // 2, (0.6875 * self.height)))
                self.screen.blit(online, online_rect)
            elif self.menuSelection == "CONNECT":
                pygame.draw.rect(self.screen, pygame.Color(170, 170, 170), [abs_w3, abs_h3, w3, h3])
                connect = fontTitleS.render("Connect", True, (0, 0, 0))
                connect_rect = connect.get_rect(center=(abs_w3 + 0.5 * w3, abs_h3 + 0.5 * h3))
                self.screen.blit(connect, connect_rect)
            elif self.menuSelection == "CONNECT_DOWN":
                pygame.draw.rect(self.screen, pygame.Color(140, 140, 140), [abs_w3, abs_h3, w3, h3])
                connect = fontTitleS.render("Connect", True, (0, 0, 0))
                connect_rect = connect.get_rect(center=(abs_w3 + 0.5 * w3, abs_h3 + 0.5 * h3))
                self.screen.blit(connect, connect_rect)
            elif self.menuSelection == "SELECT_BLACK":
                pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [int(
                    0.458 * self.width), int(0.61 * self.height) - 45 - 3, self.width // 16 + 6, self.width // 16 + 6], 2)
                pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [int(
                    0.55 * self.width), int(0.61 * self.height) - 45 - 3, self.width // 16 + 6, self.width // 16 + 6], 2)
            elif self.menuSelection == "SELECT_WHITE":
                pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [int(
                    0.458 * self.width), int(0.61 * self.height) - 45 - 3, self.width // 16 + 6, self.width // 16 + 6], 2)
                pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [int(
                    0.55 * self.width), int(0.61 * self.height) - 45 - 3, self.width // 16 + 6, self.width // 16 + 6], 2)

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
                            x1, y1, x2, y2 = self.selectedBox[0], self.flipY(
                                self.selectedBox[1]), box[0], self.flipY(box[1])
                            self.gameEngine.move(x1, y1, x2, y2)
                            self.selectedBox = None
                    else:
                        self.selectedBox = None
                else:
                    self.selectedBox = None
                self.gameEngine.makeDisplayDrawBoard()

        pygame.display.flip()

    def updatePane(self, events=[]):
        """
        Update the right hand side pane
        """

        # Automove click bounding box
        w = int((0.6375) * self.width)
        h = int(0.1875 * self.height)
        abs_w = int(self.width + 15)
        abs_h = int(0.21875 * self.height)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if event.button == 4 and mouse[0] > self.width and mouse[1] < self.height // 4:
                    self.current_first_message = max(0, self.current_first_message - 1)
                if event.button == 5 and mouse[0] > self.width and mouse[1] < self.height // 4:
                    self.current_first_message = min(
                        max(0, len(self.message_history) - self.maximum_messages), self.current_first_message + 1)
                # Auto_move and game finish click
                if self.state == "PLAYING":
                    w = int(0.42 * self.pane_width)
                    h = int(0.12 * self.height)
                    abs_w = int(self.width + 15)
                    abs_h = int(0.195 * self.height)
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        self.automoveSelection = "DOWN"

                    abs_w = int(self.width + 0.5 * self.pane_width + 10)
                    abs_h = int(0.195 * self.height)
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        self.finishSelection = "DOWN"

            if self.state == "PLAYING":
                w = int(0.42 * self.pane_width)
                h = int(0.12 * self.height)

                # Auto_move and game finish hover
                if event.type == pygame.MOUSEMOTION:
                    mouse = event.pos

                    abs_w = int(self.width + 15)
                    abs_h = int(0.195 * self.height)
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.automoveSelection != "HOVER" and self.automoveSelection != "DOWN":
                            self.automoveSelection = "HOVER"
                    else:
                        if self.automoveSelection != "NONE":
                            self.automoveSelection = "NONE"

                    abs_w = int(self.width + 0.5 * self.pane_width + 10)
                    abs_h = int(0.195 * self.height)
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.finishSelection != "HOVER" and self.finishSelection != "DOWN":
                            self.finishSelection = "HOVER"
                    else:
                        if self.finishSelection != "NONE":
                            self.finishSelection = "NONE"

                # Auto_move button release
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse = event.pos

                    abs_w = int(self.width + 15)
                    abs_h = int(0.195 * self.height)
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.automoveSelection == "DOWN":
                            if self.mode == "LOCAL":
                                x1, y1, x2, y2 = self.gameEngine.autoMove()
                                self.gameEngine.move(x1, y1, x2, y2)
                                self.gameEngine.makeDisplayDrawBoard()
                            else: # Online mode
                                self.gameEngine.autoMove()
                                # self.addMessage("Auto-move is not available online")
                            self.automoveSelection = "HOVER"

                    abs_w = int(self.width + 0.5 * self.pane_width + 10)
                    abs_h = int(0.195 * self.height)
                    if mouse[0] > abs_w and mouse[0] < abs_w + w and mouse[1] > abs_h and mouse[1] < abs_h + h:
                        if self.finishSelection == "DOWN":
                            self.gameEngine.checkEnd()
                            self.finishSelection = "HOVER"

        self.white_dead = self.gameEngine.lightBoard.getDeadPieces(0)
        self.black_dead = self.gameEngine.lightBoard.getDeadPieces(1)
        self.drawPane()

    def drawMenu(self):
        """
        Draws the start menu.
        """
        self.screen.blit(self.board, (0, 0))
        fontTitle = pygame.font.Font("fonts/CFRemingtonTypewriter-Regul.ttf", 60)
        fontTitleS = pygame.font.Font("fonts/CFRemingtonTypewriter-Regul.ttf", 40)
        fontText = pygame.font.SysFont("Arial", 18)
        if self.menuState == "START":
            # When multiplied by 800 we get integer numbers
            w = int(0.6375 * self.width)
            h = int(0.1875 * self.height)
            abs_w = int(0.1875 * self.width)
            abs_h = int(0.21875 * self.height)
            abs_h2 = int(0.59375 * self.height)
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
                             abs_w - 5, abs_h - 5, w + 10, h + 10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w, abs_h, w, h])
            local = fontTitle.render("Local game", True, (0, 0, 0))
            local_rect = local.get_rect(center=(self.width // 2, (0.3125 * self.height)))
            self.screen.blit(local, local_rect)

            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
                             abs_w - 5, abs_h2 - 5, w + 10, h + 10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w, abs_h2, w, h])
            online = fontTitle.render("Online game", True, (0, 0, 0))
            online_rect = online.get_rect(center=(self.width // 2, (0.6875 * self.height)))
            self.screen.blit(online, online_rect)

        if self.menuState == "ONLINE":
            w = int(0.6375 * self.width)
            h = int(0.1875 * self.height)
            h2 = int(0.2675 * self.height)
            abs_w = int(0.1875 * self.width)
            abs_h = int(0.21875 * self.height)
            abs_h2 = int(0.52 * self.height)
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
                             abs_w - 5, abs_h - 5, w + 10, h + 10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w, abs_h, w, h])
            local = fontTitle.render("Local game", True, (0, 0, 0))
            local_rect = local.get_rect(center=(self.width // 2, (0.3125 * self.height)))
            self.screen.blit(local, local_rect)

            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
                             abs_w - 5, abs_h2 - 5, w + 10, h2 + 10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w, abs_h2, w, h2])
            color = fontText.render("Color", True, (0, 0, 0))
            self.screen.blit(color, (int(0.2 * self.width), int(0.61 * self.height) - 40))
            player = fontText.render("Player name", True, (0, 0, 0))
            self.screen.blit(player, (int(0.2 * self.width), int(0.697 * self.height) - 40))
            address = fontText.render("[Server IP]:[port]", True, (0, 0, 0))
            self.screen.blit(address, (int(0.2 * self.width), int(0.78 * self.height) - 40))
            for box in self.input_boxes:
                box.draw(self.screen)

            self.draw_piece(0, ["E"],
                int(0.458 * self.width) + 3, int(0.61 * self.height) - 45,
                self.width // 16, extended=False)
            self.draw_piece(1, ["E"],
                int(0.55 * self.width) + 3, int(0.61 * self.height) - 45,
                self.width // 16, extended=False)
            if self.selected_color == "W":
                pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [int(
                    0.458 * self.width), int(0.61 * self.height) - 45 - 3, self.width // 16 + 6, self.width // 16 + 6], 2)
            else:
                pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [int(
                    0.55 * self.width), int(0.61 * self.height) - 45 - 3, self.width // 16 + 6, self.width // 16 + 6], 2)

            w3 = int(0.4 * self.width)
            h3 = int(0.12 * self.height)
            abs_w3 = int(0.3 * self.width)
            abs_h3 = int(0.82 * self.height)
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
                             abs_w3 - 5, abs_h3 - 5, w3 + 10, h3 + 10])
            pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [abs_w3, abs_h3, w3, h3])
            connect = fontTitleS.render("Connect", True, (0, 0, 0))
            connect_rect = connect.get_rect(center=(abs_w3 + 0.5 * w3, abs_h3 + 0.5 * h3))
            self.screen.blit(connect, connect_rect)

            pygame.display.flip()
            self.clock.tick(30)

        pygame.display.flip()

    def drawPane(self):
        pygame.draw.rect(self.screen, pygame.Color(200, 200, 200), [
            self.width, 0, self.total_width, self.total_height
        ])
        # Messages
        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [self.width, 0, 5, self.height])
        pygame.draw.rect(self.screen, pygame.Color(230, 230, 230), [
                         self.width + 15, 10, self.pane_width - 30, self.height // 6])
        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [
                         self.width + 15, 10, self.pane_width - 30, self.height // 6], 2)
        selected_messages = self.message_history[self.current_first_message:
                                                 self.current_first_message + self.maximum_messages]
        for i, message in enumerate(selected_messages):
            local = self.message_font.render(message, True, (0, 0, 0))
            self.screen.blit(local, (self.width + 20, 15 + i * 15))

        # Auto-move button and finish test
        if self.state == "PLAYING":
            w = int(0.42 * self.pane_width)
            h = int(0.12 * self.height)
            abs_w = int(self.width + 15)
            abs_h = int(0.195 * self.height)
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [abs_w, abs_h, w, h])
            if self.automoveSelection == "NONE":
                color = pygame.Color(220, 220, 220)
            elif self.automoveSelection == "HOVER":
                color = pygame.Color(170, 170, 170)
            elif self.automoveSelection == "DOWN":
                color = pygame.Color(140, 140, 140)
            pygame.draw.rect(self.screen, color, [abs_w+2, abs_h+2, w-4, h-4])
            auto_move = self.pane_buttons_font.render("Auto-move", True, (0, 0, 0))
            self.screen.blit(auto_move, (abs_w + 0.13*w, abs_h + 0.35*h))

            w = int(0.42 * self.pane_width)
            h = int(0.12 * self.height)
            abs_w = int(self.width + 0.5 * self.pane_width + 10)
            abs_h = int(0.195 * self.height)
            pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), [abs_w, abs_h, w, h])
            if self.finishSelection == "NONE":
                color = pygame.Color(220, 220, 220)
            elif self.finishSelection == "HOVER":
                color = pygame.Color(170, 170, 170)
            elif self.finishSelection == "DOWN":
                color = pygame.Color(140, 140, 140)
            pygame.draw.rect(self.screen, color, [abs_w+2, abs_h+2, w-4, h-4])
            has_game = self.pane_buttons_font.render("Has game", True, (0, 0, 0))
            ended = self.pane_buttons_font.render("ended ?", True, (0, 0, 0))
            self.screen.blit(has_game, (abs_w + 0.15*w, abs_h + 0.15*h))
            self.screen.blit(ended, (abs_w + 0.25*w, abs_h + 0.55*h))

        # Dead pieces
        text_white = self.dead_font.render("White losses", True, (0, 0, 0))
        text_black = self.dead_font.render("Black losses", True, (0, 0, 0))
        self.screen.blit(text_white, (self.width + 20, 1.5 * self.height // 4 - 30))
        self.screen.blit(text_black, (self.width + 20, 2.75 * self.height // 4 - 30))

        for i, p in enumerate(self.white_dead):
            self.draw_piece(color=0, natures =p["natures"],
                            x=self.width + 20 + i % 5 * (self.width//12),
                            y=1.5*self.height // 4 + i // 5 * (self.width//12),
                            size=self.width//12)
        for i, p in enumerate(self.black_dead):
            self.draw_piece(color=1, natures =p["natures"],
                            x=self.width + 20 + i % 5 * (self.width//12),
                            y=2.75*self.height // 4 + i // 5 * (self.width//12),
                            size=self.width//12)

        pygame.display.flip()

    def load_images(self):
        """Retrieve images from memory."""
        pieces_names = ["bB", "bK", "bN", "bP", "bQ", "bR",
                        "bE", "wB", "wK", "wN", "wP", "wQ", "wR", "wE"]
        self.pieces_pictures = {}
        for name in pieces_names:
            self.pieces_pictures[name] = pygame.transform.smoothscale(pygame.image.load(
                "img/" + name + ".png"), (self.width // 8, self.height // 8))
        self.board = pygame.transform.scale(pygame.image.load(
            "img/board.png"), (self.width, self.height))  # smaller icons for multiple display
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
        return y if self.flip else 7 - y

    def addMessage(self, message):
        """
        Split the incoming text message according to the screen size and add it to the message history
        :param message: A string message
        """
        length = 0
        i0 = 0
        message = "> " + message
        for i, c in enumerate(message):
            length += self.message_font.metrics(c)[0][4]  # The advance of each letter
            if length > self.pane_width - 50:
                length = 0
                self.message_history.append(message[i0:i])
                i0 = i
        if i0 != len(message) - 1:
            self.message_history.append(message[i0:])

        # Scroll to the end of the messages
        self.current_first_message = max(0, len(self.message_history) - self.maximum_messages)
        self.drawPane()

    def check_address_format(self, s):
        t = s.split(":")
        if len(t) != 2:
            return False
        ip = t[0]
        port = t[1]
        numbers = ip.split(".")
        if len(numbers) != 4:
            return False
        for n in numbers:
            if not n.isdigit():
                return False
            if int(n) > 1000:
                return False
        if not port.isdigit():
            return False
        if int(port) > 65535:
            return False
        return True

    def draw_piece(self, color, natures, x, y, size, extended=False):
        """x, y are in pixels"""
        if extended:
            if color == 0:
                color = "w"
            else:
                color = "b"
            if len(natures) == 1:
                picture = self.pieces_pictures[color + natures[0]]
                self.screen.blit(picture, (x, y))
            else:
                if len(natures) == 5:
                    for i in range(len(natures)):
                        xp = x + ((2 * i) % 3) * self.width // 24
                        yp = y + ((2 * i) // 3) * self.height // 24
                        picture = pygame.transform.smoothscale(
                                    self.pieces_pictures[color + natures[i]],
                                    (size//3, size//3))
                        self.screen.blit(picture, (xp, yp))
                else:
                    for i in range(len(natures)):
                        xp = x + (i % 2) * self.width // 16
                        yp = y + (i // 2) * self.height // 16
                        picture = pygame.transform.smoothscale(
                                    self.pieces_pictures[color + natures[i]],
                                    (size//2, size//2))
                        self.screen.blit(picture, (xp, yp))
        else:
            if color == 0:
                picture_name = "w"
            else:
                picture_name = "b"
            if (len(natures) > 1):
                picture_name += "E"
            else:
                picture_name += natures[0]
            picture = pygame.transform.smoothscale(
                        self.pieces_pictures[picture_name],
                        (size, size))
            self.screen.blit(picture, (x, y))

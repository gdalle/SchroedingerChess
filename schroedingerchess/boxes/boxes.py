import pygame
import math

from twisted.internet.task import LoopingCall

from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

import json

class BoxesGameClientProtocol(Protocol):

    """ Class which handles the communication protocol between the game client and the game server."""

    def __init__(self, recv):
        """
        Constructor.
        :param recv: Client to bind to the protocol
        """
        self.recv = recv # reference to the client
        self.recv.protocol = self # set a reference to the protocol in the client
        self.state = "GET_GAME_INFO" # set the protocol to its initial state


    def dataReceived(self, data):

        """
        Handles the reception of data from the server.
        :param data: A byte representing a JSON-encoded object (default encoding UTF-8)
        """
        msg = json.loads(data.decode())
        if self.state == "GET_GAME_INFO":
            self.handle_GAME_INFO(msg)
        elif self.state == "WAITING_PLAYER_1":
            self.handle_WAITING_PLAYER_1(msg)
        elif self.state == "PLAYING":
            self.handle_PLAYING(msg)
        else:
            pass

    def connectionLost(self, reason):
        """
        Handles the connection lost with the server.
        :param reason: Reason of the disconnection
        """
        self.recv.terminated = True # the client should terminate
        self.recv.protocol = None # erase all external references to the protocol

    def handle_GAME_INFO(self, msg):
        """
        Handles a message setting up the game information.
        :param msg: A dictionary representing a game information setup message.
        """
        self.recv.setGameInfo(msg) # use the dict to set attributes
        if self.recv.player == 0: # determines player attributes (turn and colors)
            self.recv.turn = True
            self.recv.marker = self.recv.greenplayer
            self.recv.othermarker = self.recv.blueplayer
        else:
            self.recv.turn = False
            self.recv.marker = self.recv.blueplayer
            self.recv.othermarker = self.recv.greenplayer

        if self.recv.ready:
            self.state = "PLAYING" # if the game is ready go to the PLAYING state
        else:
            self.state = "WAITING_PLAYER_1" # if the server is waiting for the second player, go the the WAITING_PLAYER_1 state
            self.recv.turn = None

    def handle_WAITING_PLAYER_1(self, msg):
        """
        Handles the reception of the readiness message.
        :param msg: A dictionary representing a readiness message
        """
        self.handle_GAME_INFO(msg)
        if self.recv.player == 0:
            self.recv.turn = True
        else:
            self.recv.turn = False


    def handle_PLAYING(self, msgs):
        """
        Handles the reception of messages from the server when the game is playing.
        :param msgs: A list of dictionaries representing messages
        """
        hasTurn = False # flag to determine who has the hand after the messages
        for msg in msgs:
            if msg["action"] == "place-line": # place a new line
                hasTurn = not(hasTurn) and self.recv.player != msg["player"]
                if msg["is_horizontal"]:
                    self.recv.boardh[msg["ypos"]][msg["xpos"]] = True
                else:
                    self.recv.boardv[msg["ypos"]][msg["xpos"]] = True
            elif msg["action"] == "fill-box": # fill a new box
                hasTurn = self.recv.player == msg["player"]
                self.recv.owner[msg["xpos"]][msg["ypos"]] = msg["player"]
                self.recv.placeSound.play()
                if msg["player"] == self.recv.player:
                    self.recv.me += 1
                else:
                    self.recv.otherplayer += 1
            elif msg["action"] == "illegal-move": # do nothing as the action was illegal
                hasTurn = self.recv.player == msg["player"]
            else:
                pass
        self.recv.turn = hasTurn # set the hand to the correct player


class BoxesGameClient():

    """ Game client."""

    def __init__(self):
        """
        Constructor.
        """

        #initialize pygame
        pygame.init()
        pygame.font.init()
        width, height = 389, 489

        #initialize the screen
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Boxes")

        #initialize pygame clock
        self.clock=pygame.time.Clock()

        # initialize the graphics
        self.initGraphics()

        # initialize the sounds
        self.initSound()

        #initialize game data
        self.boardh = [[False for x in range(6)] for y in range(7)] # horizontal lines
        self.boardv = [[False for x in range(7)] for y in range(6)] # vertical lines
        self.owner = [[None for x in range(6)] for y in range(6)] # boxes
        self.player = None # player number
        self.turn = None # flag to tell who has the hand
        self.me = 0 # score of the player
        self.otherplayer = 0 # score of the other player
        self.didiwin = False # flag indicating if the player has won
        self.terminated = False # flag indicating if the game should end

        # initialize protocol
        self.protocol = None # reference to the communication protocol with the server

    def setGameInfo(self, dict):
        """
        Sets the attributes of the client using the dictionary.
        :param dict: Dictionary of attributes
        """
        for key in dict:
            setattr(self, key, dict[key])

    def update(self):

        """
        Updates the GUI.
        """

        #clear the screen
        self.screen.fill(0)

        #draw the board
        self.drawBoard()

        #draw the head-up display
        self.drawHUD()

        #draw the owner map
        self.drawOwnermap()

        for event in pygame.event.get():
            #quit if the quit button was pressed
            if event.type == pygame.QUIT:
                self.mainLoopStop() # stop the main loop (update loop)
                reactor.stop() # stop the twisted reactor
                pygame.quit() # deactivate pygame
                return

        if (self.me + self.otherplayer == 36) or self.terminated: # won / game over / disconnected case
            self.didiwin = True if self.me > self.otherplayer else False
            self.finished()


        # get the mouse coordinates
        mouse = pygame.mouse.get_pos()

        # get position on the grid
        xpos = int(math.ceil((mouse[0] - 32) / 64.0))
        ypos = int(math.ceil((mouse[1] - 32) / 64.0))

        # determine if the hovered line is horizontal
        is_horizontal = abs(mouse[1] - ypos * 64) < abs(mouse[0] - xpos * 64)

        # 4
        ypos = ypos - 1 if mouse[1] - ypos * 64 < 0 and not is_horizontal else ypos
        xpos = xpos - 1 if mouse[0] - xpos * 64 < 0 and is_horizontal else xpos

        # 5
        board = self.boardh if is_horizontal else self.boardv
        isoutofbounds = False

        # 6
        try:
            if not board[ypos][xpos]: self.screen.blit(self.hoverlineh if is_horizontal else self.hoverlinev,
                                                       [xpos * 64 + 5 if is_horizontal else xpos * 64,
                                                        ypos * 64 if is_horizontal else ypos * 64 + 5])
        except:
            isoutofbounds = True
            pass
        if not isoutofbounds:
            alreadyplaced = board[ypos][xpos]
        else:
            alreadyplaced = False

        if pygame.mouse.get_pressed()[0] and self.turn and not alreadyplaced and not isoutofbounds:
            self.turn = None # nobody has the hand for now
            # send the action to the server
            msg = {"action": "place", "xpos": xpos, "ypos": ypos, "is_horizontal": is_horizontal}
            self.sendMessage(msg)

        #update the screen
        pygame.display.flip()

    def initGraphics(self):
        """
        Loads the graphical components.
        """
        self.normallinev = pygame.image.load("normalline.png")
        self.normallineh = pygame.transform.rotate(pygame.image.load("normalline.png"), -90)
        self.bar_donev = pygame.image.load("bar_done.png")
        self.bar_doneh = pygame.transform.rotate(pygame.image.load("bar_done.png"), -90)
        self.hoverlinev = pygame.image.load("hoverline.png")
        self.hoverlineh = pygame.transform.rotate(pygame.image.load("hoverline.png"), -90)
        self.separators = pygame.image.load("separators.png")
        self.redindicator = pygame.image.load("redindicator.png")
        self.greenindicator = pygame.image.load("greenindicator.png")
        self.greenplayer = pygame.image.load("greenplayer.png")
        self.blueplayer = pygame.image.load("blueplayer.png")
        self.winningscreen = pygame.image.load("youwin.png")
        self.gameover = pygame.image.load("gameover.png")
        self.score_panel = pygame.image.load("score_panel.png")

    def initSound(self):
        pygame.mixer.music.load("music.wav")
        self.winSound = pygame.mixer.Sound('win.wav')
        self.loseSound = pygame.mixer.Sound('lose.wav')
        self.placeSound = pygame.mixer.Sound('place.wav')
        pygame.mixer.music.play()

    def drawBoard(self):
        """
        Draws the board (lines and separators)
        """
        for x in range(6):
            for y in range(7):
                if not self.boardh[y][x]:
                    self.screen.blit(self.normallineh, [(x) * 64 + 5, (y) * 64])
                else:
                    self.screen.blit(self.bar_doneh, [(x) * 64 + 5, (y) * 64])
        for x in range(7):
            for y in range(6):
                if not self.boardv[y][x]:
                    self.screen.blit(self.normallinev, [(x) * 64, (y) * 64 + 5])
                else:
                    self.screen.blit(self.bar_donev, [(x) * 64, (y) * 64 + 5])

        # draw separators
        for x in range(7):
            for y in range(7):
                self.screen.blit(self.separators, [x * 64, y * 64])

    def drawHUD(self):
        """
        Draws the head-up display.
        """

        # draw the background for the bottom:
        self.screen.blit(self.score_panel, [0, 389])
        # create font
        myfont = pygame.font.SysFont(None, 32)

        # create text surface
        label = myfont.render("Your Turn:", 1, (255, 255, 255))

        # draw surface
        self.screen.blit(label, (10, 400))

        self.screen.blit(self.greenindicator if self.turn else self.redindicator, (130, 395))

        # same thing here
        myfont64 = pygame.font.SysFont(None, 64)
        myfont20 = pygame.font.SysFont(None, 20)

        scoreme = myfont64.render(str(self.me), 1, (255, 255, 255))
        scoreother = myfont64.render(str(self.otherplayer), 1, (255, 255, 255))
        scoretextme = myfont20.render("You", 1, (255, 255, 255))
        scoretextother = myfont20.render("Other Player", 1, (255, 255, 255))

        self.screen.blit(scoretextme, (10, 425))
        self.screen.blit(scoreme, (10, 435))
        self.screen.blit(scoretextother, (280, 425))
        self.screen.blit(scoreother, (340, 435))

    def drawOwnermap(self):
        """
        Draws the owner map.
        """
        for x in range(6):
            for y in range(6):
                if self.owner[x][y] != None :
                    if self.owner[x][y] == self.player:
                        self.screen.blit(self.marker, (x * 64 + 5, y * 64 + 5))
                    else:
                        self.screen.blit(self.othermarker, (x * 64 + 5, y * 64 + 5))

    def finished(self):
        """
        Draws the finish screen.
        """
        self.screen.blit(self.gameover if not self.didiwin else self.winningscreen, (0, 0))
        if self.didiwin:
            self.winSound.play()
        else:
            self.loseSound.play()
        pygame.display.flip()


    def sendMessage(self, msg):
        """
        Sends a message to the server using the protocol.
        :param msg: A dictionary representing a message.
        """
        if self.protocol is not None:
            self.protocol.transport.write(json.dumps(msg).encode())

if __name__ == '__main__':

    address = input("Address of Server: ")
    if not address:
        host, port = "localhost", 6000
    else:
        host, port = address.split(":")

    c = BoxesGameClient() # creates the client

    point = TCP4ClientEndpoint(reactor, host, int(port)) # connection point
    d = connectProtocol(point, BoxesGameClientProtocol(c)) # create the communication protocol and connect it
    lc = LoopingCall(c.update) # looping call to update frames
    setattr(c, 'mainLoopStop', lc.stop) # looping call interruptor
    lc.start(1/60) # start the update loop (60 fps)
    reactor.run() # start the reactor



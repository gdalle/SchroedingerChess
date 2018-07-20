from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

import json

class BoxesGameServerProtocol(Protocol):

    """ Class to handles the communication protocol with a game client."""
    def connectionMade(self):

        """
        Sends the game information when a new client is connected.
        """
        msg = {}

        self.gameid = self.factory.currentIndex
        msg["gameid"] = self.gameid # gameid associated to the new client

        if self.factory.waitingGame == None: # if no game is waiting
            self.factory.waitingGame = Game(self, self.factory.currentIndex) # create a new game
            self.player = 0 # the connected client will be player 1
            msg["player"] = self.player
            msg["ready"] = False # the game is waiting for a second player
            self.state = "WAITING" # the communication protocol is in the waiting state
        else: # a game is waiting for the second player
            self.factory.waitingGame.player1 = self # set the second player
            self.factory.waitingGame.player0.notifyReady() # notify the first player that the game is ready
            self.factory.waitingGame.ready = True # set the game to be ready
            self.factory.games.append(self.factory.waitingGame) # append the game to the list of games
            self.factory.waitingGame = None # flush the game just pushed in the list of games
            self.factory.currentIndex += 1 # increment the game index
            self.player = 1 # the connected player will be player 2
            msg["player"] = self.player
            msg["ready"] = True
            self.state = "PLAYING" # the communication protocol is in the playing state

        self.transport.write(json.dumps(msg).encode()) # send the message to the client

    def sendMessage(self, msg):
        """
        Sends a message to the client.
        :param msg: A dictionary representing a message.
        """
        self.transport.write(json.dumps(msg).encode())

    def notifyReady(self):
        """
        Notifies the client that the game is ready.
        """
        self.state = "PLAYING"
        msg = {"ready" : True}
        self.sendMessage(msg)

    def dataReceived(self, data):
        """
        Handles the reception of data by the server
        :param data: A byte representing a JSON-encoded object (default encoding UTF-8)
        """
        msg = json.loads(data.decode())
        if self.state == "PLAYING":
            self.handle_PLAYING(msg)
        elif self.state == "WAITING":
            self.handle_WAITING(msg)

    def handle_WAITING(self, msg):
        """
        Handles the reception of data when in waiting state. All instructions are illegal.
        :param msg: A dictionary representing a message.
        """
        msg = {"action": "illegal-move", "player": self.player}
        self.sendMessage(msg)

    def handle_PLAYING(self, msg):
        """
        Handles the reception of data when in playing state. All instructions are illegal.
        :param msg: A dictionary representing a message.
        """
        game = self.factory.games[self.gameid] # get the game corresponding to the id
        if msg["action"] == "place":
            # try to place the new line and get the messages to send back
            msgs = game.placeLine(msg["is_horizontal"], msg["xpos"], msg["ypos"], self.player, [])
            game.player0.sendMessage(msgs) # send the messages to player 1
            game.player1.sendMessage(msgs) # send the messages to player 2

    def connectionLost(self, reason):
        """
        Handles the connection lost with the client.
        :param reason: Reason of the disconnection
        """
        if self.state == "PLAYING":
            game = self.factory.games[self.gameid]
            if game is not None:
                game.player0.transport.loseConnection()
                game.player1.transport.loseConnection()
                self.factory.games[self.gameid] = None
        elif self.state == "WAITING":
            self.factory.waitingGame = None


class BoxesGameServer(Factory):

    """
    Game server.
    """

    # This will be used by the default buildProtocol to create new protocols:
    protocol = BoxesGameServerProtocol

    def __init__(self):
        """
        Constructor.
        """
        self.games = [] # list of games
        self.waitingGame = None # game waiting for player 2
        self.currentIndex = 0 # number of games ever launched


class Game:
    """
    Class to represent a game instance.
    """
    def __init__(self, player0, currentIndex):
        # whose turn (1 or 0)
        self.turn = 0
        #owner map
        self.owner=[[None for x in range(6)] for y in range(6)]
        # Seven lines in each direction to make a six by six grid.
        self.boardh = [[False for x in range(6)] for y in range(7)]
        self.boardv = [[False for x in range(7)] for y in range(6)]
        #initialize the players including the one who started the game
        self.player0=player0
        self.player1=None
        self.ready = False
        #gameid of game
        self.gameid=currentIndex

        self.scores = (0, 0)

    def placeLine(self, is_h, x, y, num, msgs):
        """
        Try to place a new line on the board.
        :param is_h: Flag indicating if the line is horizontal.
        :param x: Horizontal coordinate of the line.
        :param y: Vertical coordinate of the line.
        :param num: Number of the player.
        :param msgs: List of messages to send back.
        :return: List of messages to send back.
        """
        # make sure it's their turn
        if num == self.turn:
            self.turn = 0 if self.turn else 1
            # place line in game
            if is_h:
                self.boardh[y][x] = True
            else:
                self.boardv[y][x] = True
            msgs.append({"action": "place-line", "is_horizontal": is_h, "xpos": x, "ypos": y, "player" : num})
            self.detectBox(is_h, x, y, num, msgs) # detect if new boxes were captured
        else:
            msgs.append({"action" : "illegal-move", "player" : num})

        return msgs

    def detectBox(self, is_h, x, y, num, msgs):
        boxes = []
        if is_h:
            try:
                if self.boardh[y-1][x] and self.boardv[y-1][x] and self.boardv[y-1][x+1]:
                    boxes.append((x, y - 1))
            except:
                pass
            try:
                if self.boardh[y+1][x] and self.boardv[y][x] and self.boardv[y][x+1]:
                    boxes.append( (x, y))
            except:
                pass
        else:
            try:
                if self.boardv[y][x-1] and self.boardh[y][x-1] and self.boardh[y+1][x-1]:
                    boxes.append( (x-1, y))
            except:
                pass
            try:
                if self.boardv[y][x+1] and self.boardh[y][x] and self.boardh[y+1][x]:
                    boxes.append( (x, y))
            except:
                pass

        for box in boxes:
            if self.owner[box[0]][box[1]] == None:
                self.turn = num
                self.owner[box[0]][box[1]] = num
                msgs.append({"action" : "fill-box", "player" : num, "xpos" : box[0], "ypos" : box[1]})


if __name__ == '__main__':

    address = input("Host:Port (localhost:6000): ")
    if not address:
        host, port = "localhost", 6000
    else:
        host, port = address.split(":")

    endpoint = TCP4ServerEndpoint(reactor, int(port))
    endpoint.listen(BoxesGameServer())
    reactor.run()
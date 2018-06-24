from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

import json

class ChessServerProtocol(Protocol):

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


class ChessServer(Factory):

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


if __name__ == '__main__':

    address = input("Host:Port (localhost:6000): ")
    if not address:
        host, port = "localhost", 6000
    else:
        host, port = address.split(":")

    endpoint = TCP4ServerEndpoint(reactor, int(port))
    endpoint.listen(ChessServer())
    reactor.run()
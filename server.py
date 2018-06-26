from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

from chess import ChessBoard, LightBoard, IllegalMove

import json

class ChessServerProtocol(Protocol):

    """ Class to handles the communication protocol with a game client."""
    def connectionMade(self):

        """
        Sends the game information when a new client is connected.
        """
        msg = {"type" : "init"}

        self.gameid = self.factory.currentIndex
        msg["gameid"] = self.gameid # gameid associated to the new client

        if self.factory.waitingGame == None: # if no game is waiting
            self.factory.waitingGame = Game(self, self.factory.currentIndex) # create a new game
            self.color = 0 # the connected client will be the whites
            msg["color"] = self.color
            msg["ready"] = False # the game is waiting for a second player
            self.state = "WAITING" # the communication protocol is in the waiting state
        else: # a game is waiting for the blacks
            self.factory.waitingGame.black = self # set the second player
            self.factory.waitingGame.player0.notifyReady() # notify the first player that the game is ready
            self.factory.waitingGame.ready = True # set the game to be ready
            self.factory.games.append(self.factory.waitingGame) # append the game to the list of games
            self.factory.waitingGame = None # flush the game just pushed in the list of games
            self.factory.currentIndex += 1 # increment the game index
            self.color = 1 # the connected player will be player 2
            msg["color"] = self.player
            msg["ready"] = True
            self.state = "PLAYING" # the communication protocol is in the playing state

        self.transport.write(json.dumps(msg).encode()) # send the message to the client

    def notifyReady(self):
        """
        Notifies the client that the game is ready.
        """
        self.state = "PLAYING"
        msg = {"type" : "ready" , "status" : True}
        self.sendMessage(msg)

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
        msg = {"type": "illegal-move", "description" : "waiting for second player"}
        self.sendMessage(msg)

    def handle_PLAYING(self, msg):
        """
        Handles the reception of data when in playing state. All instructions are illegal.
        :param msg: A dictionary representing a message.
        """
        game = self.factory.games[self.gameid] # get the game corresponding to the id
        if msg["type"] == "move":
            try:
                game.move()
                game.sendMessageToAll(game.lightBoard.wrapUp())
            except IllegalMove as e:
                msg = {"type" : "illegal-move", "description" : str(e)}
            finally:



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
    def __init__(self, white, currentIndex):
        self.turn = 0
        self.white=white
        self.black=None
        self.ready = False
        self.gameid=currentIndex
        self.chessBoard = ChessBoard() 
        self.lightBoard = LightBoard()

    def move(self, x1, y1, x2, y2, color):
        piece = self.chessBoard[x1][y1]
        if piece is not None and piece.color is not color:
            raise IllegalMove("Trying to move a place that does not belong to the player.")
        self.chessBoard.move(x1, y1, x2, y2)
        self.lightBoard.move(x1, y1, x2, y2)
        self.updateLightBoardTask()
    
    def updateLightBoardTask(self):
        for x in range(8):
                for y in range(8):
                    piece = self.chessBoard.grid[x][y]
                    if piece is not None:
                        natures = self.chessBoard.all_legal_natures(piece)
                        color = piece.color
                        self.lightBoard.setPiece(x, y , color, natures)
        self.sendMessage(self.lightBoard.wrapUp())

    def updateLightBoard(self):
        """ Schedules an update board task. """
        reactor.callLater(0, self.updateLightBoardTask)

    def sendMessageToAll(self, msg):
        self.white.sendMessage(msg)
        self.black.sendMessage(msg)

    def sendMessageTo(self, msg, color)
        if color == 0:
            self.white.sendMessage(msg)
        elif color == 1:
            self.black.sendMessage(msg)
        else:
            pass



if __name__ == '__main__':

    address = input("Host:Port (localhost:6000): ")
    if not address:
        host, port = "localhost", 6000
    else:
        host, port = address.split(":")

    endpoint = TCP4ServerEndpoint(reactor, int(port))
    endpoint.listen(ChessServer())
    reactor.run()
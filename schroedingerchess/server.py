from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

from chess import ChessBoard, LightBoard, IllegalMove

import json


class ChessServerProtocol(Protocol):
    """ Class to handles the communication protocol with a game client."""

    def __init__(self):
        self.player_id = None
        self.game_id = None
        self.game = None
        self.color = None

    def connectionMade(self):
        """
        Sends the game information when a new client is connected.
        """
        self.status = "GREETING"

        msg = {"type": "greetings"}

        msg["player_id"] = player_id

        msg["greetings"] = "looking forward hearing from you"

        player_id = self.factory.addWaitingPlayer(self)

        self.sendMessage(msg)

        # self.game_id = self.factory.currentIndex
        # msg["game_id"] = self.game_id # game_id associated to the new client

        # if self.factory.waitingGame == None: # if no game is waiting
        #     self.factory.waitingGame = Game(self, self.factory.currentIndex) # create a new game
        #     self.color = 0 # the connected client will be the whites
        #     msg["color"] = self.color
        #     self.game = self.factory.waitingGame
        # else: # a game is waiting for the blacks
        #     self.factory.waitingGame.black = self # set the second player
        #     self.factory.waitingGame.player0.notifyReady() # notify the first player that the game is ready
        #     self.factory.waitingGame.ready = True # set the game to be ready
        #     self.game = self.factory.waitingGame
        #     self.factory.games.append(self.factory.waitingGame) # append the game to the list of games
        #     self.factory.waitingGame = None # flush the game just pushed in the list of games
        #     self.factory.currentIndex += 1 # increment the game index
        #     self.color = 1 # the connected player will be player 2
        #     msg["color"] = self.player

        # self.sendMessage(msg, self.color)
        # if self.game.ready
        #     msg_for_both = {"type" : "ready", "status" : True}
        #     self.sendMessageToAll(msg_for_both)
        # else:
        #     msg = {"type" : "ready", "status" : False}
        #     self.sendMessage(msg, self.color)

        self.status = "WAITING_FOR_GREETINGS"

    # def notifyReady(self):
    #     """
    #     Notifies the client that the game is ready.
    #     """
    #     self.state = "PLAYING"
    #     msg = {"type" : "ready" , "status" : True}
    #     self.sendMessage(msg)

    def sendMessage(self, msg):
        """
        Sends a message to the client.
        :param msg: A dictionary representing a message.
        """
        self.transport.write(json.dumps(msg).encode())

    def sendMessageToAll(self, msg):
        """
        Sends a message to the client and the other player's client.
        :param msg: A dictionary representing a message.
        """
        if self.game is not None:
            self.game.sendMessageToAll(self)
        else:
            raise RuntimeError("trying to send a message when the game is not created / over")

    def sendMessageToOther(self, msg):
        """
        Sends a message to the client and the other player's client.
        :param msg: A dictionary representing a message.
        """
        if self.game is not None:
            self.game.sendMessageTo(msg, 0 if self.color else 1)
        else:
            raise RuntimeError("trying to send a message when the game is not created / over")

    def dataReceived(self, data):
        """
        Handles the reception of data by the server
        :param data: A byte representing a JSON-encoded object (default encoding UTF-8)
        """
        msg = json.loads(data.decode())
        if self.state == "GREETING":
            raise RuntimeError("Should no happen.")
        elif self.state == "WAITING_FOR_GREETINGS":
            if msg["type"] == "greetings":
                self.handleGreetings[msg]
        elif self.state == "PLAYING":
            if msg["type"] == "move":
                self.handleMove(msg)
            elif msg["type"] == "chat":
                self.sendMessageToOther({"type": "chat", "content": msg["content"]})
        else:
            self.refuseMessage(msg)

    def handleGreetings(self, msg):
        self.color = msg["color"]
        self.factory.assignColor(self.player_id, self.color)
        # if self.

    def refuseMessage(self, msg):
        """
        Handles the reception of messages when waiting for second player. All instructions are illegal.
        :param msg: A dictionary representing a message.
        """
        self.sendMessage({"type": "illegal-request", "request": msg})

    def handleMove(self, msg):
        try:
            player = msg["color"]
            x1, y1, x2, y2 = msg["description"]
            game.move(x1, y1, x2, y2, player)
        except IllegalMove as e:
            msg = {"type": "illegal-move", "description": str(e)}

    def connectionLost(self, reason):
        """
        Handles the connection lost with the client.
        :param reason: Reason of the disconnection
        """
        pass
        # TODO


class ChessServer(Factory):

    """
    Game server.
    """

    # This will be used by the default buildProtocol to create new protocols:
    protocol = ChessServerProtocol

    def __init__(self):
        """
        Constructor.
        """
        self.games = []  # list of games
        self.waitingBlackPlayers = ([], {})  # waiting white players
        self.waitingWhitePlayers = ([], {})  # waiting black players
        self.waitingPlayers = {}  # list of waiting players
        self.currentIndex = 0  # number of games ever launched
        self.playerIndex = 0  # number of players ever connected

    def addWaitingPlayer(self, client):
        self.waitingPlayers[self.playerIndex] = client
        self.playerIndex += 1
        return self.playerIndex - 1

    def assignColor(self, player_id, color):
        client = self.waitingPlayers.pop(player_id)
        if color == 0:
            self.waitingWhitePlayers[0].append(player_id)
            self.waitingWhitePlayers[1][player_id] = client
        elif color == 1:
            self.waitingBlackPlayers[0].append(player_id)
            self.waitingBlackPlayers[1][player_id] = client
        else:
            if len(self.waitingBlackPlayers) < len(self.waitingWhitePlayers):
                self.waitingWhitePlayers[0].append(player_id)
                self.waitingBlackPlayers[1][player_id] = client
            else:
                self.waitingWhitePlayers[0].append(player_id)
                self.waitingWhitePlayers[1][player_id] = client
        self.tryToMatchPlayers()

    def tryToMatchPlayers(self):
        if len(self.waitingBlackPlayers[0]) >= 1 and len(self.waitingWhitePlayers[0] >= 1):
            whites_id = self.waitingWhitePlayers[0].pop(0)
            blacks_id = self.waitingBlackPlayers[0].pop(0)
            whites_client = self.waitingWhitePlayers[1].pop(whites_id)
            blacks_client = self.waitingBlackPlayers[1].pop(blacks_id)
            game = Game(whites_client, blacks_client, self.currentIndex)
            self.gameIndex += 1


class Game:
    """
    Class to represent a game instance.
    """

    def __init__(self, whites, blacks, currentIndex):
        self.game_id = currentIndex
        self.turn = 0
        self.white = whites
        self.white.game_id = self.game_id
        self.white.game = self
        self.black = blacks
        self.black.game_id = self.game_id
        self.black.game = self
        self.chessBoard = ChessBoard()
        self.lightBoard = LightBoard()
        self.notifyReady()
        self.ready = True

    def notifyReady(self):
        self.sendMessageToAll({"type": "status", "status": "ready"})
        self.ready = True

    def move(self, x1, y1, x2, y2, color):
        piece = self.chessBoard[x1][y1]
        if piece is not None and piece.color is not color:
            raise IllegalMove("Trying to move a place that does not belong to the player.")
        self.chessBoard.move(x1, y1, x2, y2)
        self.lightBoard.move(x1, y1, x2, y2)
        self.updateLightBoardTask()

    def updateLightBoardTask(self):
        for i, piece in enumerate(self.chessBoard.pieces):
            if piece is not None:
                natures = self.chessBoard.all_legal_natures(piece)
                color = piece.color
                position = piece.position
                self.lightBoard.setPiece(i, color, position, natures)
        self.sendMessage(self.lightBoard.wrapUp())

    def updateLightBoard(self):
        """ Schedules an update board task. """
        reactor.callLater(0, self.updateLightBoardTask)

    def sendMessageToAll(self, msg):
        self.white.sendMessage(msg)
        self.black.sendMessage(msg)

    def sendMessageTo(self, msg, color):
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

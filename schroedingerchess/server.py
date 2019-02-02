from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.defer import inlineCallbacks, Deferred

from chess import ChessBoard, LightBoard, IllegalMove

import json
import time


class ChessServerProtocol(Protocol):
    """
    Class to handles the communication protocol with a game client.
    """

    def __init__(self):
        self.player_id = None
        self.game_id = None
        self.game = None
        self.color = None

    def connectionMade(self):
        """
        Sends the game information when a new client is connected.
        """
        self.state = "GREETING"

        self.player_id = self.factory.addWaitingPlayer(self)

        msg = {"type": "greetings"}
        msg["player_id"] = self.player_id
        msg["greetings"] = "looking forward hearing from you"
        self.sendMessage(msg)

        self.state = "WAITING_FOR_GREETINGS"

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
            self.game.sendMessageToAll(msg)
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
        # msg = json.loads(data.decode())
        messages = self.split_messages(data)
        update = False

        for msg_json in messages:
            msg = json.loads(msg_json)

            if self.state == "GREETING":
                raise RuntimeError("Should no happen.")
            elif self.state == "WAITING_FOR_GREETINGS":
                if msg["type"] == "player-info":
                    self.handleGreetings(msg)
            elif self.state == "PLAYING":
                if msg["type"] == "move":
                    self.handleMove(msg)
                if msg["type"] == "automove":
                    self.handleMove(msg, auto=True)
                elif msg["type"] == "chat":
                    self.sendMessageToOther({"type": "chat", "content": msg["content"]})
                elif msg["type"] == "endgame":
                    self.handleEndGame(msg["color"])
            else:
                self.refuseMessage(msg)
            # TODO : reduce lightboard update delay

    def handleGreetings(self, msg):
        self.color = msg["color"]
        self.factory.assignColor(self.player_id, self.color)

    def refuseMessage(self, msg):
        """
        Handles the reception of messages when waiting for second player. All instructions are illegal.
        :param msg: A dictionary representing a message.
        """
        self.sendMessage({"type": "illegal-request", "request": msg})

    def handleMove(self, msg, auto=False):
        try:
            player = msg["color"]
            if auto:
                move = self.game.autoMove()
            else:
                move = msg["description"]
            x1, y1, x2, y2 = [int(x) for x in move]
            self.game.move(x1, y1, x2, y2, player)
            msg = {"type": "move", "description": (x1, y1, x2, y2)}
            self.sendMessageToAll(msg)
            self.game.updateLightBoard()
        except IllegalMove as e:
            msg = {"type": "illegal-move", "description": str(e)}
            self.sendMessage(msg)

    def handleEndGame(self, color):
        if self.game is not None:
            reactor.callLater(0, self.game.checkEnd, color)

    def connectionLost(self, reason):
        """
        Handles the connection lost with the client (executes automatically).
        :param reason: Reason of the disconnection
        """
        if self.game is None:
            self.factory.removePlayerFromWaitingList(self.player_id)
        else:
            # Disconnect other player and remove the game
            self.sendMessageToOther({"type": "chat", "content": "Other player disconnected"})
            time.sleep(0.5)
            self.game.disconnectPlayers()
            self.factory.removeGame(self.game_id)

    def disconnect(self):
        """ Disconnect current player / protocol """
        self.transport.loseConnection()

    def split_messages(self, data):
        messages = []
        split = data.decode().split("}{")
        if len(split) == 1:
            return split
        for i, sp in enumerate(split):
            m = sp
            if i > 0:
                m = "{" + m
            if i < len(split)-1:
                m = m + "}"
            messages.append(m)
        return messages


class ChessServer(Factory):
    """
    Game server : produces a new ChessServerProtocol each time a client arrives
    """

    # This will be used by the default buildProtocol to create new protocols:
    protocol = ChessServerProtocol

    def __init__(self):
        """
        Constructor.
        """
        self.games = {}  # list of games
        self.waitingBlackPlayers = ([], {})  # waiting white players
        self.waitingWhitePlayers = ([], {})  # waiting black players
        self.waitingPlayers = {}  # list of waiting players
        self.gameIndex = 0  # total number of games ever launched
        self.playerIndex = 0  # total number of players ever connected

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
        while len(self.waitingBlackPlayers[0]) >= 1 and len(self.waitingWhitePlayers[0]) >= 1:
            whites_id = self.waitingWhitePlayers[0].pop(0)
            blacks_id = self.waitingBlackPlayers[0].pop(0)
            whites_client = self.waitingWhitePlayers[1].pop(whites_id)
            blacks_client = self.waitingBlackPlayers[1].pop(blacks_id)
            game = Game(whites_client, blacks_client, self.gameIndex)
            self.games[self.gameIndex] = game
            self.gameIndex += 1

    def removePlayerFromWaitingList(self, player_id):
        if player_id in self.waitingPlayers:
            del self.waitingPlayers[player_id]
        elif player_id in self.waitingWhitePlayers[0]:
            self.waitingWhitePlayers[0].remove(player_id)
            del self.waitingWhitePlayers[1][player_id]
        elif player_id in self.waitingBlackPlayers[0]:
            self.waitingBlackPlayers[0].remove(player_id)
            del self.waitingBlackPlayers[1][player_id]

    def removeGame(self, game_id):
        try:
            del self.games[game_id]
        except KeyError:
            # The other player already deleted the game
            pass


class Game:
    """
    Class to represent a game instance.
    """

    def __init__(self, whites, blacks, gameIndex):
        self.game_id = gameIndex
        self.validMovesCounter = 0
        self.white = whites
        self.white.game_id = self.game_id
        self.white.game = self
        self.black = blacks
        self.black.game_id = self.game_id
        self.black.game = self
        self.chessBoard = ChessBoard()
        self.lightBoard = LightBoard()
        self.notifyReady()

    def notifyReady(self):
        self.sendMessageToAll({"type": "status", "status": "ready"})
        self.white.state = "PLAYING"
        self.black.state = "PLAYING"

    def move(self, x1, y1, x2, y2, color):
        piece = self.chessBoard.grid[x1][y1]
        if piece is not None and piece.color is not color:
            raise IllegalMove("Trying to move a place that does not belong to the player.")
        self.chessBoard.move(x1, y1, x2, y2)
        self.lightBoard.move(x1, y1, x2, y2)
        self.validMovesCounter += 1

    def autoMove(self):
        return self.chessBoard.auto_move()

    def checkEnd(self, color):
        outcome = self.chessBoard.end_game()
        msg = {"type": "chat", "content": outcome}
        self.sendMessageTo(msg, color)

    def updateLightBoardTask(self):
        for col in [0, 1]:
            for i, piece in enumerate(self.chessBoard.pieces[col]):
                if piece is not None:
                    color = piece.color
                    position = piece.position
                    natures = self.chessBoard.all_legal_natures(piece)
                    pieceIndex = i + col * 24
                    self.lightBoard.setPiece(pieceIndex, color, position, natures)
        msg = {"type": "lightboard", "description": self.lightBoard.wrapUp()}
        self.sendMessageToAll(msg)

    def updateLightBoard(self):
        """ Schedules an update board task. """
        reactor.callLater(0.5, self.updateLightBoardTask)

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

    def disconnectPlayers(self):
        self.white.disconnect()
        self.black.disconnect()


if __name__ == '__main__':

    address = input("Host:Port (localhost:6000): ")
    if not address:
        host, port = "localhost", 6000
    else:
        host, port = address.split(":")

    endpoint = TCP4ServerEndpoint(reactor, int(port))
    endpoint.listen(ChessServer())
    reactor.run()

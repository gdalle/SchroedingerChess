from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet import reactor
from twisted.python import log

from display import ChessDisplay

from chess import ChessBoard, IllegalMove, LightBoard

from client import ChessClientProtocol

from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

import time

FRAME_PER_SECOND = 10
CONNECTION_WAITING_TIME = 10  # seconds


class GameEngine():
    # TODO fix JSON encore / decode error
    def start(self):
        """ Starts the game engine. Create the window and initiate the reaction loop."""
        self.lightBoard = LightBoard()
        self.display = ChessDisplay(self)
        self.loopingCall = LoopingCall(self.display.update)
        self.loopingCall.start(1 / FRAME_PER_SECOND).addErrback(log.err)
        reactor.run()

    def startFromEngine(self, engine):
        """ Starts the game engine. Create the window and initiate the reaction loop."""
        self.lightBoard = LightBoard()
        self.display = engine.display
        self.loopingCall = engine.loopingCall
        self.resume()

    def stop(self):
        """ Stops the game engine."""
        # self.loopingCall.stop() # causing an unhandled error and don't seem necessary
        # self.display = None
        reactor.stop()

    def suspend(self):
        """ Suspends the reaction loop of the window."""
        self.loopingCall.stop()

    def resume(self):
        """ Resumes the reaction loop of the window."""
        self.loopingCall.start(1 / FRAME_PER_SECOND).addErrback(log.err)

    def setTwoPlayersOnOneBoardMode(self):
        """ Sets the engine on the two-players-on-one-board mode."""
        self.suspend()
        self.display.gameEngine = TwoPlayersOnOneBoard(self)
        self.display.gameEngine.resume()

    def setOnePlayerOnNetworkMode(self, name, address, color):
        """ Sets the engine on the one-player-on-network mode."""
        self.suspend()
        self.display.gameEngine = OnePlayerOnNetwork(self, name, address, color)
        self.display.gameEngine.resume()

    def moveTask(self, x1, y1, x2, y2):
        """ Task to perform when the display detects a move."""
        raise NotImplementedError

    def move(self, x1, y1, x2, y2):
        """ Schedules a move task. """
        reactor.callLater(0, self.moveTask, x1, y1, x2, y2)

    def checkEndTask(self):
        """ Task to perform to check whether the game has ended."""
        raise NotImplementedError

    def checkEnd(self):
        """ Schedules an end check """
        reactor.callLater(0, self.checkEndTask)

    def handleIllegalMove(self, reason):
        """ Handles an illegal move."""
        self.display.handleIllegalMove(reason)

    def makeDisplayDrawBoard(self):
        """ Makes the display redraw the board."""
        self.display.drawBoard(self.lightBoard)

    def makeDisplayDrawChecks(self, check_positions):
        self.display.drawChecks(check_positions)

    def makeDisplayDrawChecksMates(self, checkmate_positions):
        self.display.drawCheckMates(checkmate_positions)


class TwoPlayersOnOneBoard(GameEngine):

    def __init__(self, gameEngine):
        """
        Constructor.
        :param gameEngine: The initial game engine.
        """
        self.chessBoard = ChessBoard()
        self.lightBoard = gameEngine.lightBoard
        self.display = gameEngine.display
        self.loopingCall = gameEngine.loopingCall
        self.validMovesCounter = 0

    @inlineCallbacks
    def updateLightBoard(self):
        nb = self.validMovesCounter
        for col in [0, 1]:
            for i, piece in enumerate(self.chessBoard.pieces[col]):
                if nb == self.validMovesCounter:
                    self.updateDeferred = Deferred()
                    self.updateDeferred.addCallback(self.chessBoard.all_legal_natures)
                    self.updateDeferred.addErrback(log.err)  # DEBUG
                    reactor.callLater(0, self.updateDeferred.callback, piece)
                    natures = yield self.updateDeferred
                    if nb == self.validMovesCounter:
                        color = piece.color
                        position = piece.position
                        pieceIndex = i + col * 24
                        self.lightBoard.setPiece(pieceIndex, color, position, natures)
                        if (piece.position is not None) and (piece.position is not False):
                            self.makeDisplayDrawBoard()
                        elif (piece.position is False):
                            self.display.updatePane()

    def moveTask(self, mov):
        x1, y1, x2, y2 = mov[0], mov[1], mov[2], mov[3]
        try:
            self.chessBoard.move(x1, y1, x2, y2, disp=False)
            self.lightBoard.move(x1, y1, x2, y2)
            color = "Whites" if (self.validMovesCounter % 2 == 0) else "Blacks"
            self.display.addMessage(color + " move from ({},{}) to ({},{})".format(x1, y1, x2, y2))
            self.validMovesCounter += 1
            self.display.setLastMove(x1, y1, x2, y2)
            self.makeDisplayDrawBoard()
            self.updateLightBoard()
        except IllegalMove as e:
            self.handleIllegalMove(str(e))

    def move(self, x1, y1, x2, y2):
        d = Deferred()
        d.addCallback(self.moveTask).addErrback(log.err)  # DEBUG
        reactor.callLater(0, d.callback, (x1, y1, x2, y2))

    def autoMove(self):
        return self.chessBoard.auto_move()

    def checkEndTask(self):
        outcome = self.chessBoard.end_game()
        self.addMessage(outcome)


class OnePlayerOnNetwork(GameEngine):

    def __init__(self, gameEngine, name, address=None, color=0):
        # raise NotImplementedError("Server not yet implemented")
        if not address:
            host, port = "localhost", 6000
        else:
            host, port = address.split(":")

        self.name = name
        self.color = color
        self.turn = -1 # 0 = White is playing, 1 = Black is playing
        self.lightBoard = gameEngine.lightBoard
        self.display = gameEngine.display
        if self.color == 1: # 1 = black
            self.display.flipDisplay(True)

        self.loopingCall = gameEngine.loopingCall
        self.protocol = ChessClientProtocol(self)

        point = TCP4ClientEndpoint(reactor, host, int(port))  # connection point
        try:
            attempt = connectProtocol(point, self.protocol)
            attempt.addErrback(self.connectionFailed)
            attempt.addTimeout(CONNECTION_WAITING_TIME, reactor,
                               onTimeoutCancel=self.connectionFailed)
            self.display.addMessage("Connecting to remote server...")
        except:
            self.connectionFailed()

    def handleInit(self):
        self.display.addMessage("Connection established.")
        self.display.addMessage("Waiting for an opponent...")

    def handleReady(self):
        self.display.addMessage("Found an opponent. White begins...")
        self.turn = 0

    def moveTask(self, x1, y1, x2, y2):
        if self.turn != self.color:
            self.display.addMessage("Trying to move out of turn")
        else:
            msg = {"type": "move", "color": self.color, "description": (x1, y1, x2, y2)}
            self.protocol.sendMessage(msg)

    def autoMove(self):
        reactor.callLater(0, self.autoMoveTask)

    def autoMoveTask(self):
        if self.turn != self.color:
            self.display.addMessage("Trying to move out of turn")
        else:
            msg = {"type": "automove", "color": self.color}
            self.protocol.sendMessage(msg)

    def checkEndTask(self):
        if self.turn == -1:
            self.addMessage("The game has not started yet")
        else:
            msg = {"type": "endgame", "color": self.color}
            self.protocol.sendMessage(msg)

    def handleMove(self, description):
        """ Executes a move received from the server """
        self.turn = (self.turn + 1) % 2
        x1, y1, x2, y2 = description
        self.lightBoard.move(x1, y1, x2, y2)
        color = "Whites" if (self.turn == 0) else "Blacks"
        self.display.addMessage(color+" move from ({},{}) to ({},{})".format(x1, y1, x2, y2))
        self.display.setLastMove(x1, y1, x2, y2)
        self.makeDisplayDrawBoard()
        # print("cb.move({},{},{},{})".format(x1, y1, x2, y2))

    def handleUpdateBoard(self, description):
        self.lightBoard.unwrap(description)
        self.makeDisplayDrawBoard()

    def handleChecks(self, description):
        self.makeDisplayDrawChecks(description)

    def handleCheckMates(self, description):
        self.makeDisplayDrawCheckMates(description)

    def connectionFailed(self, *kwargs):
        self.display.setMenuMode()
        self.display.addMessage("The server could not be reached.")

    def handleDisconnection(self, description):
        # if self.display is None:
            # return
        self.display.addMessage("Disconnected from server")
        self.display.addMessage(description.__str__())
        self.suspend()
        self.display.gameEngine = GameEngine()
        self.display.gameEngine.startFromEngine(self)
        self.display.setMenuMode()
        # raise NotImplementedError
        # TODO implement disconnection screen
        # reactor.stop()

from twisted.internet.task import LoopingCall

from twisted.internet import reactor

from twisted.python import log

from display import ChessDisplay

from chess import ChessBoard, IllegalMove, LightBoard

from client import ChessClientProtocol

from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

FRAME_PER_SECOND = 60
CONNECTION_WAITING_TIME = 10 # seconds

class GameEngine():

    def start(self):
        """ Starts the game engine. Create the window and initiate the reaction loop."""
        self.display = ChessDisplay(self)
        self.lightBoard = LightBoard()
        self.loopingCall = LoopingCall(self.display.update)
        self.loopingCall.start(1/FRAME_PER_SECOND).addErrback(log.err)
        reactor.run()

    def stop(self):
        """ Stops the game engine."""
        self.loopingCall.stop()
        self.display = None
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

    def setOnePlayerOnNetworkMode(self):
        """ Sets the engine on the one-player-on-network mode."""
        self.suspend()
        self.display.gameEngine = OnePlayerOnNetwork(self)
        self.display.gameEngine.resume()

    def moveTask(self, x1, y1, x2, y2):
        """ Task to perform when the display detects a move."""
        raise NotImplementedError

    def selectBoxTask(self, x, y):
        """ Task to perform when the display detects a box selection."""
        raise NotImplementedError

    def selectBox(self, x, y):
        """ Schedules a box selection task."""
        reactor.callLater(0, self.selectBoxTask, x, y)

    def move(self, x1, y1, x2, y2):
        """ Schedules a move task. """
        """ Tries to move the piece from position (x1, x2) to position (x2, y2)."""
        reactor.callLater(0, self.moveTask, x1, y1, x2, y2)

    def handleIllegalMove(self, reason):
        """ Handles an illegal move."""
        print(reason)
        # self.display.handleIllegalMove(reason) #TODO see the implementation of this method in ChessDisplay

    def makeDisplayDrawBoard(self):
        """ Makes the display redraw the board."""
        self.display.drawBoard(self.lightBoard)

    def makeDisplayDrawSelectedCell(self, natures):
        """ Makes the display draw the selected box."""
        self.display.drawSelectedBox(natures)

    def makeDisplayDrawChecks(self, check_positions):
        self.display.drawChecks(check_positions)

    def makeDisplayDrawChecks(self, checkmate_positions):
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

    def moveTask(self, x1, y1, x2, y2):
        try:
            self.chessBoard.move(x1, y1, x2, y2)
            # TODO recover list of checks created by the move
            # TODO recover checkmates
            self.lightBoard.move(x1, y1, x2, y2)
            self.makeDisplayDrawBoard()
        except IllegalMove as e:
            self.handleIllegalMove(str(e))
        finally:
            self.display.state = "PLAYING"

    def selectBoxTask(self, x, y): # TODO enable computation of possible natures
        piece = self.chessBoard.grid[x][y]
        natures = []
        # if piece is not None:
        #    natures = self.chessBoard.legal_natures_for(piece)
        self.display.drawSelectedBox(natures)



class OnePlayerOnNetwork(GameEngine):

    def __init__(self, gameEngine):
        raise NotImplementedError("Server not yet implemented")
        self.name = input("Player name: ")
        address = input("Address of Server: ")
        if not address:
            host, port = "localhost", 6000
        else:
            host, port = address.split(":")

        self.lightBoard = gameEngine.lightBoard
        self.display = gameEngine.display
        self.loopingCall = gameEngine.loopingCall
        self.protocol = ChessClientProtocol()

        point = TCP4ClientEndpoint(reactor, host, int(port))  # connection point
        try:
            attempt = connectProtocol(point, self.protocol)
            attempt.addTimeout(CONNECTION_WAITING_TIME, reactor)
        except:
            self.connectionFailed()

        def moveTask(self, x1, y1, x2, y2):
            msg = {"type" : "move", "player" : self.color, "description" : (x1, y1, x2, y2)}
            self.protocol.sendMessage(msg)

        def selectBoxTask(self, x, y):
            msg = {"type": "box-selection", "player": self.color, "description": (x, y)}
            self.protocol.sendMessage(msg)

        def handleMove(self, description):
            self.lightBoard.move(description[0], description[1], description[2], description[3])
            self.makeDisplayDrawBoard()
            self.display.state = "PLAYING"

        def handleChecks(self, description):
            self.makeDisplayDrawChecks(description)

        def handleCheckMates(self, description):
            self.makeDisplayDrawCheckMates(description)

        def handleDisconnection(self, description):
            raise NotImplementedError
            # TODO implement disconnection screen


















from twisted.internet.task import LoopingCall

from twisted.internet import reactor

from twisted.python import log

from display import ChessDisplay

from chess import ChessBoard, IllegalMove, LightBoard

from client import ChessClientProtocol

from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

FRAME_PER_SECOND = 10
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

    def updateLightBoardTask(self, x1, y1, x2, y2):
        """ Task to perform to update the display."""
        raise NotImplementedError

    def move(self, x1, y1, x2, y2):
        """ Schedules a move task. """
        reactor.callLater(0, self.moveTask, x1, y1, x2, y2)

    def updateLightBoard(self):
        """ Schedules an update board task. """
        reactor.callLater(0, self.updateLightBoardTask, x1, y1, x2, y2)

    def handleIllegalMove(self, reason):
        """ Handles an illegal move."""
        self.display.handleIllegalMove(reason) #TODO see the implementation of this method in ChessDisplay

    def makeDisplayDrawBoard(self, exceptBox=None):
        """ Makes the display redraw the board."""
        self.display.drawBoard(self.lightBoard, exceptBox=exceptBox)

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

    def updateLightBoardTask():
        for x in range(8):
                for y in range(8):
                    piece = self.chessBoard.grid[x][y]
                    if piece is not None:
                        natures = self.chessBoard.all_legal_natures(piece)
                        color = piece.color
                        self.lightBoard.setPiece(x, y , color, natures)
        self.makeDisplayDrawBoard()

    def moveTask(self, x1, y1, x2, y2):
        try:
            self.chessBoard.move(x1, y1, x2, y2)
            # TODO recover list of checks created by the move
            # TODO recover checkmates
            self.lightBoard.move(x1, y1, x2, y2)
            self.makeDisplayDrawBoard()
            print("cb.move({},{},{},{})".format(x1,y1,x2,y2))
        except IllegalMove as e:
            self.handleIllegalMove(str(e))
        finally:
            self.display.state = "PLAYING"



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
        self.protocol = ChessClientProtocol(self)

        point = TCP4ClientEndpoint(reactor, host, int(port))  # connection point
        try:
            attempt = connectProtocol(point, self.protocol)
            attempt.addTimeout(CONNECTION_WAITING_TIME, reactor)
        except:
            self.connectionFailed()

        def handleInit(self, description):
            self.color = description["color"]
            if self.color == "black":
                self.display.flipDisplay(True)
            self.display.state = "PLAYING"

        def moveTask(self, x1, y1, x2, y2):
            msg = {"type" : "move", "player" : self.color, "description" : (x1, y1, x2, y2)}
            self.protocol.sendMessage(msg)

        def handleMove(self, description):
            move = description["move"]
            x1 = move[0]
            y1 = move[1]
            x2 = move[2]
            y2 = move[3]
            self.lightBoard.move(x1, y1, x2, y2)
            natures = description["natures"]
            self.makeDisplayDrawBoard()
            self.display.state = "PLAYING"
            if len(natures) == 1:
                self.lightBoard.setPiece(x2, y2, natures[0])
            else:
                self.lightBoard.setPiece(x2, y2, "E")
            # self.display.flipDisplay(not(self.display.flip))
            self.makeDisplayDrawBoard()
            print("cb.move({},{},{},{})".format(x1,y1,x2,y2))

        def handleChecks(self, description):
            self.makeDisplayDrawChecks(description)

        def handleCheckMates(self, description):
            self.makeDisplayDrawCheckMates(description)

        def connectionFailed(self):
            raise NotImplementedError
            # TODO implement disconnection screen

        def handleDisconnection(self, description):
            raise NotImplementedError
            # TODO implement disconnection screen

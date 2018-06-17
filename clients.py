from twisted.internet.task import LoopingCall

from twisted.internet import reactor

from twisted.python import log

from display import ChessDisplay

from chess import ChessBoard, IllegalMove


class GameEngine():

    def __init__(self):
        self.display = ChessDisplay(self)
        self.loopingCall = LoopingCall(self.display.update)


    def start(self):
        self.loopingCall.start(1/60).addErrback(log.err)
        reactor.run()

    def stop(self):
        self.loopingCall.stop()
        self.display = None
        reactor.stop()

    def suspend(self):
        self.loopingCall.stop()

    def resume(self):
        self.loopingCall.start(1 / 60).addErrback(log.err)

    def setTwoPlayersOnOneBoardMode(self):
        self.suspend()
        self.display.gameEngine = TwoPlayersOnOneBoard(self)
        self.display.gameEngine.resume()

    def setOnePlayerOnNetworkMode(self):
        self.suspend()
        self.display.gameEngine = OnePlayerOnNetwork(self)
        self.display.gameEngine.resume()


class TwoPlayersOnOneBoard(GameEngine):

    def __init__(self, gameEngine):
        self.chessBoard = ChessBoard()
        self.display = gameEngine.display
        self.loopingCall = gameEngine.loopingCall

    def move(self, x1, x2, y1, y2):
        self.chessBoard.move(x1, x2, y1, y2)
        self.display.drawBoard()

    def isEmpty(self, x, y):
        return self.getPiece(x, y) is not None


    def getPossibleNatures(self, box):
        raise NotImplementedError

    def getPiece(self, x, y):
        return self.chessBoard.grid[x][y]

    def makeDisplayDrawBoard(self):
        self.display.drawBoard()


class OnePlayerOnNetwork(GameEngine):

    def __init__(self, gameEngine):
        raise NotImplementedError
        self.display = gameEngine.display
        self.loopingCall = gameEngine.loopingCall



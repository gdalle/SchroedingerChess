from chess import *
from display import *

# cb = ChessBoard.create_standard_board()
cb = ChessBoard()
window = ChessDisplay()
while True:
    window.update(cb)

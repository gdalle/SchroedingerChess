import pytest
from chess import *

# Format : input ChessBoard, move to perform, error message expected ("" = valid move)
test_moves_input = [
    (ChessBoard(), [0,0,1,2], ""),
]

@pytest.mark.parametrize("cb, move, result_msg", test_moves_input)
def test_moves(cb, move, result_msg):
    msg = ""
    try:
        cb.move(move[0], move[1], move[2], move[3])
    except IllegalMove as e:
        msg = str(e)
    assert msg == result_msg

# @pytest.mark.parametrize("cb, move, result_msg", test_moves_input)
# def test_natures()

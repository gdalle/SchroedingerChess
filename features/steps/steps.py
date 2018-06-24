from behave import *
from chess import *

@given("I have a standard Schroedinger ChessBoard")
def standard_chessboard(context):
    context.cb = ChessBoard()
    context.black_pawn = 6

@when("I move piece ({a:d},{b:d}) to ({c:d},{d:d})")
def move(context, a, b, c, d):
    try:
        context.cb.move(a, b, c, d)
        context.move_result = ""
    except IllegalMove as e:
        context.move_result = str(e)

@then("the move should be accepted")
def move_accepted(context):
    assert context.move_result == ""

@then("the move should be rejected")
def move_rejected(context):
    assert context.move_result != ""

@then("there should be an error : {error}")
def move_error(context, error):
    assert context.move_result == error

@then("the piece ({a:d},{b:d}) should have nature {n}")
def has_nature(context, a, b, n):
    piece = context.cb.grid[a][b]
    assert piece is not None
    natures = context.cb.all_legal_natures(piece)
    assert n in natures

@then("the piece ({a:d},{b:d}) should not have nature {n}")
def has_nature(context, a, b, n):
    piece = context.cb.grid[a][b]
    assert piece is not None
    natures = context.cb.all_legal_natures(piece)
    assert not (n in natures)

@when("Blacks move their left pawn")
def move_black_pawn(context):
    assert context.black_pawn > 0
    move(context, 0, context.black_pawn, 0, context.black_pawn-1)
    context.black_pawn = context.black_pawn - 1

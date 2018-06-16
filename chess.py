"""First test for chess implementation."""


import numpy as np


class IllegalMove(Exception):
    """Illegal move."""

    pass


class ChessPiece():
    """Chess piece manipulation."""

    def __init__(self, c=None, i=None, n=None, b=None, x=None, y=None):
        """Initialize color, number, nature, position."""
        self.color = c
        if c == 0:
            self.color_name = "W"
        elif c == 1:
            self.color_name = "B"
        if n == "P":
            self.color_name = self.color_name.lower()
        self.number = i
        if n is None:
            self.natures = ["K", "Q", "R", "B", "N"]
        else:
            self.natures = [n]
        self.board = b
        self.x = x
        self.y = y
        self.has_moved = False

    def __str__(self):
        """Display color and number."""
        return (
            self.color_name +
            str(self.number) +
            " " * (2 - len(str(self.number)))
        )


class ChessBoard():
    """Chess board manipulation."""

    def __init__(self):
        """Initialize the grid with pieces."""
        self.time = 0
        self.moves = []
        self.grid = [[None for y in range(8)] for x in range(8)]
        for x in range(8):
            self.grid[x][0] = ChessPiece(
                c=0, i=x, n=None,
                b=self, x=x, y=0
            )
            self.grid[x][1] = ChessPiece(
                c=0, i=8 + x, n="P",
                b=self, x=x, y=1
            )
            self.grid[x][6] = ChessPiece(
                c=1, i=8 + x, n="P",
                b=self, x=x, y=6
            )
            self.grid[x][7] = ChessPiece(
                c=1, i=x, n=None,
                b=self, x=x, y=7
            )

    def __str__(self):
        """Display the board in ASCII art."""
        s = ""
        for y in reversed(range(8)):
            for x in range(8):
                piece = self.grid[x][y]
                if piece is not None:
                    s += piece.__str__()
                else:
                    s += "-- "
                s += " "
            s += "\n"
        return s

    def on_board(self, x1, y1):
        """Check if a square is part of the board."""
        return x1 >= 0 and x1 < 8 and y1 >= 0 and y1 < 8

    def triable_move(b, x1, y1, x2, y2, n):
        """
        Decide if a move belongs to the abilities of a piece nature.

        Special case for pawns where it depends upon the target and their
        previous moves.
        """
        h = x2 - x1
        v = y2 - y1
        if n == "K":
            return abs(h) <= 1 and abs(v) <= 1
        elif n == "Q":
            return (
                abs(h) == 0 or
                abs(v) == 0 or
                abs(h) == abs(v)
            )
        elif n == "R":
            return (
                abs(h) == 0 or
                abs(v) == 0
            )
        elif n == "B":
            return abs(h) == abs(v)
        elif n == "N":
            return (
                (abs(h) == 2 and abs(v) == 1) or
                (abs(h) == 1 and abs(v) == 2)
            )
        elif n == "P":
            pawn = b.grid[x1][y1]
            pawn_dir = +1 if pawn.color == 0 else -1
            target_piece = b.grid[x2][y2]
            if target_piece is None:
                return (
                    (h == 0 and v == pawn_dir) or
                    (h == 0 and v == 2 * pawn_dir and not pawn.has_moved)
                )
            else:
                return (abs(h) == 1 and v == pawn_dir)

    def free_trajectory(self, x1, y1, x2, y2):
        """Decide if a move is prevented by other pieces in the way."""
        h = x2 - x1
        v = y2 - y1
        # Knight move
        if (
            (abs(h) == 2 and abs(v) == 1) or
            (abs(h) == 1 and abs(v) == 2)
        ):
            return True
        # Other move
        dir_h = np.sign(h)
        dir_v = np.sign(v)
        # Vertical move
        if h == 0:
            x_steps = [x1] * abs(v)
            y_steps = range(y1, y2, dir_v)
        # Horizontal move
        elif v == 0:
            x_steps = range(x1, x2, dir_h)
            y_steps = [y1] * abs(h)
        # Diagonal move
        elif abs(h) == abs(v):
            x_steps = range(x1, x2, dir_h)
            y_steps = range(y1, y2, dir_v)
        # Check all squares between 1 and 2 (strictly)
        for (x, y) in zip(x_steps[1:], y_steps[1:]):
            if self.grid[x][y] is not None:
                return False

        return True

    def update_nature(self, piece, x1, y1, x2, y2):
        """Update nature of the piece that just moved."""
        new_natures = []
        for n in piece.natures:
            if self.triable_move(x1, y1, x2, y2, n):
                new_natures.append(n)
        piece.natures = new_natures

    def move(self, x1, y1, x2, y2):
        """Perform a move."""
        # Check obvious failures
        if not self.on_board(x1, y1) or not self.on_board(x2, y2):
            raise IllegalMove("Trying to move outside of the board")
        piece = self.grid[x1][y1]
        target_piece = self.grid[x2][y2]
        if piece is None:
            raise IllegalMove("Trying to move the void")
        if self.time % 2 != piece.color:
            raise IllegalMove(
                "Trying to move out of turn"
            )
        if (
            target_piece is not None and
            target_piece.color == piece.color
        ):
            raise IllegalMove("Trying to eat a friend")
        # Check semi-obvious failures
        if not self.free_trajectory(x1, y1, x2, y2):
            raise IllegalMove("Trying to jump when you shouldn't")
        if not np.any([
                self.triable_move(x1, y1, x2, y2, n) for n in piece.natures]):
            raise IllegalMove(
                "Trying to move a piece in ways " +
                "inconsistent with its nature"
            )
        # Check quantum failures
        # ...
        # Perform move
        self.grid[x2][y2] = piece
        self.grid[x1][y1] = None
        piece.x = x2
        piece.y = y2
        piece.has_moved = True
        self.update_nature(piece, x1, y1, x2, y2)
        # Update other stuff
        self.time += 1
        self.moves.append((x1, y1, x2, y2))


cb = ChessBoard()
print(cb)
cb.move(0, 0, 1, 2)
print(cb)
cb.grid[1][2].natures

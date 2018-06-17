"""First test for chess implementation."""


import numpy as np
import pulp


class IllegalMove(Exception):
    """Illegal move."""

    pass


class ChessPiece():
    """Chess piece manipulation."""

    all_natures = ["K", "Q", "R", "B", "N", "P"]

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
            self.possible_natures = ["K", "Q", "R", "B", "N"]
        else:
            self.possible_natures = [n]
        self.nature_guess = self.initial_nature_guess()
        self.board = b
        self.x = x
        self.y = y
        self.has_moved = False
        self.is_dead = False

    def __str__(self, guess=False):
        """Display color and number or nature guess."""
        if not guess:
            return (
                self.color_name +
                str(self.number) +
                " " * (2 - len(str(self.number)))
            )
        elif guess:
            return (
                self.color_name.lower() +
                self.nature_guess + " "
            )

    def initial_nature_guess(self):
        """Define standard initial configuration."""
        if self.number >= 8:
            return "P"
        elif self.number in [0, 7]:
            return "R"
        elif self.number in [1, 6]:
            return "N"
        elif self.number in [2, 5]:
            return "B"
        elif self.number == 3:
            return "Q"
        elif self.number == 4:
            return "K"


class ChessBoard():
    """Chess board manipulation."""

    def __init__(self):
        """Initialize the board."""
        # Grid with pieces
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

        # Colorized lists of pieces
        white_pieces = [
            self.grid[x][0] for x in range(8)
        ] + [
            self.grid[x][1] for x in range(8)
        ]
        black_pieces = [
            self.grid[x][7] for x in range(8)
        ] + [
            self.grid[x][6] for x in range(8)
        ]
        self.pieces = [white_pieces, black_pieces]

        # Game history
        self.time = 0
        self.moves = []
        self.nature_eliminations = []
        self.positions = [self.compute_position()]
        self.attacks = [self.compute_attack()]

    def __str__(self, guess=False):
        """Display the board in ASCII art."""
        s = "\n"
        for y in reversed(range(8)):
            s += str(y) + "  "
            for x in range(8):
                piece = self.grid[x][y]
                if piece is not None:
                    s += piece.__str__(guess=guess)
                else:
                    s += "-- "
                s += " "
            s += "\n"
        s += "   "
        for x in range(8):
            s += str(x) + "   "
        s += "\n"
        return s

    def on_board(self, x1, y1):
        """Check if a square is part of the board."""
        return x1 >= 0 and x1 < 8 and y1 >= 0 and y1 < 8

    def get_square(self, x, y):
        """Get square number from coordinates."""
        return 8 * x + y

    def get_coord(self, s):
        """Get coordinates from square number."""
        return (s // 8, s % 8)

    def compute_position(self):
        """Encode position as a binary table."""
        position = np.zeros((64, 2, 16))
        for s in range(64):
            for c in range(2):
                for i in range(16):
                    piece = self.pieces[c][i]
                    if s == self.get_square(piece.x, piece.y):
                        position[s, c, i] = 1
        return position

    def compute_attack(self):
        """Encode attack as a binary table."""
        attack = np.zeros((64, 2, 16, 6))
        for s in range(64):
            xs, ys = self.get_coord(s)
            for c in range(2):
                for i in range(16):
                    piece = self.pieces[c][i]
                    for n in piece.all_natures:
                        n_ind = piece.all_natures.index(n)
                        if (
                            self.feasible_move(piece.x, piece.y, xs, ys, n) and
                            self.free_trajectory(piece.x, piece.y, xs, ys)
                        ):
                            attack[s, c, i, n_ind] = 1
        return attack

    def display_guess(self):
        """Display a possible guess."""
        print(self.__str__(guess=True))

    def feasible_move(self, x1, y1, x2, y2, n):
        """
        Decide if a move belongs to the abilities of a piece nature.

        Special case for pawns where it depends upon the target and their
        previous moves.
        """
        h = x2 - x1
        v = y2 - y1
        if n == "K":
            return abs(h) == 1 and abs(v) == 1
        elif n == "Q":
            return (
                (abs(h) == 0 and abs(h) >= 1) or
                (abs(v) == 0 and abs(h) >= 1) or
                (abs(h) == abs(v) and abs(h) >= 1)
            )
        elif n == "R":
            return (
                (abs(h) == 0 and abs(h) >= 1) or
                (abs(v) == 0 and abs(h) >= 1)
            )
        elif n == "B":
            return (abs(h) == abs(v) and abs(h) >= 1)
        elif n == "N":
            return (
                (abs(h) == 2 and abs(v) == 1) or
                (abs(h) == 1 and abs(v) == 2)
            )
        elif n == "P":
            pawn = self.grid[x1][y1]
            pawn_dir = +1 if pawn.color == 0 else -1
            target_piece = self.grid[x2][y2]
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

    def forbidden_natures(self, piece, x1, y1, x2, y2):
        """Update nature of the piece that just moved."""
        new_forbidden_natures = []
        for n in piece.possible_natures:
            if not self.feasible_move(x1, y1, x2, y2, n):
                new_forbidden_natures.append(n)
        return (piece.color, piece.number, new_forbidden_natures)

    def quantum_check(self):
        """Perform consistency check with MIP."""
        colors = list(range(2))
        piece_numbers = list(range(16))
        major_numbers = list(range(8))
        pawn_numbers = list(range(8, 16))
        natures = ["K", "Q", "R", "B", "N", "P"]
        max_quant = {
            "K": 1,
            "Q": 1,
            "R": 2,
            "B": 2,
            "N": 2,
            "P": 8
        }

        variables = [
            (c, i, n)
            for c in colors
            for i in piece_numbers
            for n in natures
        ]

        x = pulp.LpVariable.dicts(
            name="x",
            indexs=variables,
            lowBound=0,
            upBound=1,
            cat="Integer"
        )

        problem = pulp.LpProblem("chess", 1)

        problem += 1

        for c in colors:
            for i in piece_numbers:
                problem += (
                    sum([x[(c, i, n)] for n in natures]) == 1,
                    "One nature " + str((c, i))
                )

        for c in colors:
            for i in major_numbers:
                problem += (
                    x[(c, i, "P")] == 0,
                    "Not pawn " + str((c, i))
                )
            for i in pawn_numbers:
                problem += (
                    x[(c, i, "P")] == 1,
                    "Pawn " + str((c, i))
                )

        for c in colors:
            problem += (
                sum([x[(c, i, "K")] for i in piece_numbers]) >= 1,
                "Always one king " + str(c)
            )
            for n in natures:
                problem += (
                    sum([x[(c, i, n)] for i in piece_numbers]) <= max_quant[n],
                    "Right quantity " + str((c, n))
                )

        T = self.time

        for t in range(T):
            nature_elimination = self.nature_eliminations[t]
            c, i = nature_elimination[0], nature_elimination[1]
            new_impossible_natures = nature_elimination[2]
            for n in new_impossible_natures:
                problem += (
                    x[(c, i, n)] == 0,
                    "Impossible nature " + str((t, c, i, n))
                )

        for t in range(1, T+1):
            for s in range(64):
                cur_c = t % 2
                prev_c = 1 - cur_c
                dangers = sum([
                    self.attacks[t][s][cur_c][i][n_ind] * x[(cur_c, i, n)]
                    for i in piece_numbers
                    for n_ind, n in enumerate(natures)
                ])
                king = sum([
                    self.positions[t][s][prev_c][i] * x[(prev_c, i, "K")]
                    for i in piece_numbers
                ])
                problem += (
                    dangers <= 16 * (1-king),
                    "No king left in check " + str((t, c, s))
                )

        status = problem.solve()
        return problem, status

    def parse_variable(self, var):
        """Parse pulp variable name."""
        s = var.name.split("_")
        c = int(s[1][1])
        i = int(s[2][0]) if len(s[2]) == 2 else int(s[2][:2])
        n = s[3][1]
        return c, i, n

    def update_guess(self, problem):
        """Update guess with MIP solution."""
        for v in problem.variables():
            if v.varValue is not None and v.varValue == 1:
                c, i, n = self.parse_variable(v)
                self.pieces[c][i].nature_guess = n

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
        if not np.any([
                self.feasible_move(x1, y1, x2, y2, n)
                for n in piece.possible_natures
        ]):
            raise IllegalMove(
                "Trying to move a piece in ways " +
                "inconsistent with its nature(s)"
            )
        if not self.free_trajectory(x1, y1, x2, y2):
            raise IllegalMove("Trying to jump when you shouldn't")
        # Augment history
        self.time += 1
        self.moves.append((x1, y1, x2, y2))
        new_forbidden_natures = self.forbidden_natures(piece, x1, y1, x2, y2)
        self.nature_eliminations.append(new_forbidden_natures)
        self.positions.append(self.compute_position())
        self.attacks.append(self.compute_attack())
        # Check quantum failures (requires history with last move)
        problem, status = self.quantum_check()
        if status != 1:
            # Reverse last move
            self.time -= 1
            self.moves.pop()
            self.nature_eliminations.pop()
            self.positions.pop()
            self.attacks.pop()
        else:
            # Perform move
            self.grid[x2][y2] = piece
            self.grid[x1][y1] = None
            piece.x = x2
            piece.y = y2
            piece.has_moved = True
            piece.possible_natures = [
                n for n in piece.possible_natures
                if n not in new_forbidden_natures
            ]
            if target_piece is not None:
                target_piece.is_dead = True
            self.update_guess(problem)

    def create_standard_board():
        """Define standard board for test purposes."""
        cb = ChessBoard()
        cols = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for x in range(8):
            cb.grid[x][0] = ChessPiece(
                c=0, i=x, n=cols[x],
                b=cb, x=x, y=0
            )
            cb.grid[x][1] = ChessPiece(
                c=0, i=8 + x, n="P",
                b=cb, x=x, y=1
            )
            cb.grid[x][6] = ChessPiece(
                c=1, i=8 + x, n="P",
                b=cb, x=x, y=6
            )
            cb.grid[x][7] = ChessPiece(
                c=1, i=x, n=cols[x],
                b=cb, x=x, y=7
            )
        return cb


if __name__ == "__main__":
    cb = ChessBoard()
    cb.display_guess()
    cb.move(0, 0, 1, 2)
    cb.display_guess()
    cb.move(2, 6, 2, 4)
    cb.display_guess()

"""First test for chess implementation."""


import numpy as np
import pulp
from collections import defaultdict

colors = list(range(2))
piece_numbers = list(range(16))
major_piece_numbers = list(range(8))
pawn_numbers = list(range(8, 16))
promoted_numbers = list(range(16, 24))

all_natures = ["K", "Q", "R", "B", "N", "P"]
major_piece_natures = ["K", "Q", "R", "B", "N"]

max_quantity = {
    "K": 1,
    "Q": 1,
    "R": 2,
    "B": 2,
    "N": 2
}


class IllegalMove(Exception):
    """Illegal move."""

    pass


class ChessPiece():
    """Chess piece manipulation."""

    def __init__(self, c, i, n, b=None):
        """Initialize color, number, nature, position."""
        self.color = c
        self.color_name = "W" if c == 0 else "B"
        self.number = i
        if n is None:
            self.possible_natures = ["K", "Q", "R", "B", "N"]
        else:
            self.possible_natures = [n]
        self.legal_natures = self.possible_natures
        self.forbidden_natures = []
        self.nature_guess = self.initial_nature_guess()
        self.board = b

    def __str__(self, guess=False, natures=False):
        """Display color and number or nature guess."""
        if "P" in self.possible_natures:
            color_name = self.color_name.lower()
        else:
            color_name = self.color_name
        if not guess and not natures:
            return (
                color_name +
                str(self.number) +
                " " * (2 - len(str(self.number)))
            )
        elif guess:
            return (
                color_name +
                self.nature_guess + " "
            )
        elif natures:
            return (
                color_name +
                str(len(self.board.all_legal_natures(self))) + " "
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
        # Colorized lists of pieces
        white_pieces = [
            ChessPiece(c=0, i=i, n=None, b=self)
            for i in major_piece_numbers
        ] + [
            ChessPiece(c=0, i=i, n="P", b=self)
            for i in pawn_numbers
        ] + [
            ChessPiece(c=0, i=i, n=None, b=self)
            for i in promoted_numbers
        ]

        black_pieces = [
            ChessPiece(c=1, i=i, n=None, b=self)
            for i in major_piece_numbers
        ] + [
            ChessPiece(c=1, i=i, n="P", b=self)
            for i in pawn_numbers
        ] + [
            ChessPiece(c=1, i=i, n=None, b=self)
            for i in promoted_numbers
        ]

        self.pieces = [white_pieces, black_pieces]

        # Grid with pieces
        self.grid = [[None for y in range(8)] for x in range(8)]
        for x in range(8):
            self.grid[x][0] = self.pieces[0][x]
            self.grid[x][1] = self.pieces[0][x + 8]
            self.grid[x][7] = self.pieces[1][x]
            self.grid[x][6] = self.pieces[1][x + 8]

        # Game history
        self.time = 0
        self.moves = []
        self.nature_eliminations = []
        self.positions = [self.compute_position()]
        self.attacks = [self.compute_attack()]
        self.pieces_alive = [[16, 16]]

    def __str__(self, guess=False, natures=False):
        """Display the board in ASCII art."""
        s = "At time " + str(self.time) + ":\n"
        s += "\n"
        for y in reversed(range(8)):
            s += str(y) + "  "
            for x in range(8):
                square_color = (x + y) % 2
                piece = self.grid[x][y]
                if piece is not None:
                    s += piece.__str__(guess=guess, natures=natures)
                else:
                    if square_color == 0:
                        s += "-- "
                    else:
                        s += "-- "
                s += " "
            s += "\n"
        s += "   "
        for x in range(8):
            s += str(x) + "   "
        s += "\n"
        return s

    def display_guess(self):
        """Display a possible guess."""
        print(self.__str__(guess=True))

    def display_natures(self):
        """Display the number of legal natures."""
        print(self.__str__(natures=True))

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

    def on_board(self, x1, y1):
        """Check if a square is part of the board."""
        return x1 >= 0 and x1 < 8 and y1 >= 0 and y1 < 8

    def get_square(self, x, y):
        """Get square number from coordinates."""
        return 8 * x + y

    def get_coord(self, s):
        """Get coordinates from square number."""
        return (s // 8, s % 8)

    def pawn_could_reach(self, x1, y1, x2, y2, c):
        """Check whether a pawn on (x1, y1) can go to (x2, y2)."""
        h = x2 - x1
        v = y2 - y1
        pawn_dir = 1 if c == 0 else -1
        has_not_moved = (
            (c == 0 and y1 == 1) or
            (c == 1 and y1 == 6)
        )
        return (
            (h == 0 and v == pawn_dir) or
            (h == 0 and v == 2 * pawn_dir and has_not_moved)
        )

    def pawn_could_take(self, x1, y1, x2, y2, c):
        """Check whether a pawn on (x1, y1) threatens (x2, y2)."""
        h = x2 - x1
        v = y2 - y1
        pawn_dir = 1 if c == 0 else -1
        return (abs(h) == 1 and v == pawn_dir)

    def move_exists(self, x1, y1, x2, y2):
        """Verify that a move exists in chess."""
        h = x2 - x1
        v = y2 - y1
        ah = abs(h)
        av = abs(v)
        M = max(ah, av)
        m = min(ah, av)
        d = abs(ah - av)
        if m > 0 and d > 1:
            return False
        elif m > 0 and d == 1:
            return M == 2 and m == 1
        elif m == M == 0:
            return False
        else:
            return True

    def possible_move(self, x1, y1, x2, y2, n, c):
        """
        Decide if a move belongs to the abilities of a piece nature.

        Special case for pawns where it depends upon
        the color, target and the previous moves.
        """
        h = x2 - x1
        v = y2 - y1
        if n == "K":
            return (
                abs(h) <= 1 and
                abs(v) <= 1 and
                (h, v) != (0, 0)
            )
        elif n == "Q":
            return (
                (abs(h) == 0 and abs(v) >= 1) or
                (abs(v) == 0 and abs(h) >= 1) or
                (abs(h) == abs(v) and abs(h) >= 1)
            )
        elif n == "R":
            return (
                (abs(h) == 0 and abs(v) >= 1) or
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
            target_piece = self.grid[x2][y2]
            if target_piece is None:
                return self.pawn_could_reach(x1, y1, x2, y2, c)
            elif target_piece.color == 1 - c:
                return self.pawn_could_take(x1, y1, x2, y2, c)
            else:
                return False

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

    def nature_elimination(self, piece, x1, y1, x2, y2):
        """Find which natures got impossible for the piece that just moved."""
        move_forbidden_natures = []
        for n in piece.possible_natures:
            if not self.possible_move(x1, y1, x2, y2, n, piece.color):
                move_forbidden_natures.append(n)
        return (piece.color, piece.number, move_forbidden_natures)

    def compute_position(self):
        """Encode position as a binary table."""
        position = np.zeros((64, 2, 24))
        for x in range(8):
            for y in range(8):
                piece = self.grid[x][y]
                if piece is None:
                    continue
                s = self.get_square(x, y)
                c, i = piece.color, piece.number
                position[(s, c, i)] = 1
        return position

    def compute_attack(self):
        """Encode attack as a binary table."""
        attack = np.zeros((64, 2, 24, 5))
        cur_c = self.time % 2
        for x in range(8):
            for y in range(8):
                piece = self.grid[x][y]
                if piece is None:
                    continue
                c, i = piece.color, piece.number
                if c != cur_c:
                    continue
                if (
                    i in major_piece_numbers or
                    i in promoted_numbers
                ):
                    for s in range(64):
                        xs, ys = self.get_coord(s)
                        for n in piece.possible_natures:
                            n_ind = all_natures.index(n)
                            if (
                                self.move_exists(x, y, xs, ys)
                                and
                                self.free_trajectory(x, y, xs, ys)
                                and
                                self.possible_move(x, y, xs, ys, n, c)
                            ):
                                attack[s, c, i, n_ind] = 1
                elif i in pawn_numbers:
                    for s in range(64):
                        xs, ys = self.get_coord(s)
                        if self.pawn_could_take(x, y, xs, ys, c):
                            attack[s, c, i, -1] = 1
        return attack

    def quantum_explanation(self, check=None):
        """
        Perform consistency check with MIP.

        Returns the solved linear problem.
        """
        major_piece_variables = [
            (c, i, n)
            for c in colors
            for i in major_piece_numbers + promoted_numbers
            for n in major_piece_natures
        ]

        z = pulp.LpVariable.dicts(
            name="z",
            indexs=major_piece_variables,
            lowBound=0,
            upBound=1,
            cat="Integer"
        )

        problem = pulp.LpProblem("chess", 1)

        problem += 1

        for c in colors:
            for i in major_piece_numbers + promoted_numbers:

                problem += (
                    sum([z[(c, i, n)] for n in major_piece_natures]) == 1,
                    "One nature " + str((c, i))
                )

        for c in colors:
            for n in major_piece_natures:
                if n == "K":
                    problem += (
                        sum([z[(c, i, "K")] for i in major_piece_numbers]) == 1,
                        "Always one king " + str(c)
                    )

                else:
                    problem += (
                        sum(
                            [z[(c, i, n)] for i in major_piece_numbers]
                        ) <= max_quantity[n],
                        "Maximum quantity " + str((c, n))
                    )

        for c in colors:
            problem += (
                sum([z[(c, i, "B")] for i in [1, 3, 5, 7]]) == 1,
                "One " + str(c) + "-square bishop " + str(c)
            )
            problem += (
                sum([z[(c, i, "B")] for i in [0, 2, 4, 6]]) == 1,
                "One " + str(1 - c) + "-square bishop " + str(c)
            )

        for c in colors:
            for i in major_piece_numbers + promoted_numbers:
                piece = self.pieces[c][i]
                for n in piece.forbidden_natures:
                    problem += (
                        z[(c, i, n)] == 0,
                        "Forbidden nature " + str((c, i, n))
                    )

        T = self.time

        for t in range(T):
            c, i, move_forbidden_natures = self.nature_eliminations[t]
            if i in major_piece_numbers + promoted_numbers:
                for n in move_forbidden_natures:
                    problem += (
                        z[(c, i, n)] == 0,
                        "Move-forbidden nature " + str((t, c, i, n))
                    )

        for t in range(1, T + 1):
            cur_c = t % 2
            prev_c = 1 - cur_c
            for s in range(64):

                if self.attacks[t][s, cur_c, :, :].sum() < 0.5:
                    continue
                if self.positions[t][s, prev_c, major_piece_numbers].sum() < 0.5:
                    continue

                dangers = sum([
                    self.attacks[t][s, cur_c, i, n_ind] * z[(cur_c, i, n)]
                    for i in major_piece_numbers + promoted_numbers
                    for (n_ind, n) in enumerate(major_piece_natures)
                    if self.attacks[t][s, cur_c, i, n_ind] > 0.5
                ]) + sum([
                    self.attacks[t][s, cur_c, i, -1]
                    for i in pawn_numbers
                ])

                king = sum([
                    self.positions[t][s, prev_c, i] * z[(prev_c, i, "K")]
                    for i in major_piece_numbers
                    if self.positions[t][s, prev_c, i] > 0.5
                ])

                max_dangers_king = self.pieces_alive[t - 1][cur_c]

                problem += (
                    max_dangers_king * (1 - king) >= dangers,
                    "No king left in check " + str((t, prev_c, s))
                )

        cur_c = T % 2
        prev_c = 1 - cur_c

        for s in range(64):

            current_dangers = sum([
                self.attacks[T][s, prev_c, i, n_ind] * z[(prev_c, i, n)]
                for i in major_piece_numbers + promoted_numbers
                for (n_ind, n) in enumerate(major_piece_natures)
                if self.attacks[T][s, prev_c, i, n_ind] > 0.5
            ]) + sum([
                self.attacks[T][s, prev_c, i, -1]
                for i in pawn_numbers
            ])

            current_king = sum([
                self.positions[T][s, cur_c, i] * z[(cur_c, i, "K")]
                for i in major_piece_numbers
                if self.positions[T][s, cur_c, i] > 0.5
            ])

            if check == True:

                problem += (
                    king >= dangers,
                    "Current king in check " + str((T, cur_c))
                )

            elif check == False:

                problem += (
                    16 * (1 - current_king) >= current_dangers,
                    "Current king not in check " + str((T, cur_c))
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

    def trivial_test_move(self, x1, y1, x2, y2):
        """Check obvious failures."""
        if not self.on_board(x1, y1) or not self.on_board(x2, y2):
            error = "Trying to move outside of the board"
            return error
        piece = self.grid[x1][y1]
        target_piece = self.grid[x2][y2]
        if piece is None:
            error = "Trying to move the void"
            return error
        cur_c = piece.color
        if self.time % 2 != cur_c:
            error = "Trying to move out of turn"
            return error
        if (
            target_piece is not None and
            target_piece.color == cur_c
        ):
            error = "Trying to eat a friend"
            return error
        if not self.move_exists(x1, y1, x2, y2):
            error = "Trying to perform a move that doesn't exist in chess"
            return error
        if not self.free_trajectory(x1, y1, x2, y2):
            error = "Trying to move through other pieces"
            return error
        if "P" in piece.possible_natures:
            if not (
                (
                    target_piece is None and
                    self.pawn_could_reach(x1, y1, x2, y2, cur_c)
                ) or (
                    target_piece is not None and
                    self.pawn_could_take(x1, y1, x2, y2, cur_c)
                )
            ):
                error = "Trying to perform an illegal pawn move"
                return error
        else:
            if not np.any([
                self.possible_move(x1, y1, x2, y2, n, cur_c)
                for n in piece.possible_natures
            ]):
                error = (
                    "Trying to move a piece in a way inconsistent " +
                    "with one of its previous moves or preset " +
                    "possible natures"
                )
                return error
        return None

    def add_move_to_history(self, x1, y1, x2, y2, piece, target_piece):
        """Add move to history (temporarily or not)."""
        cur_c, i = piece.color, piece.number
        self.time += 1
        self.moves.append((x1, y1, x2, y2))
        self.nature_eliminations.append(
            self.nature_elimination(piece, x1, y1, x2, y2))
        self.grid[x2][y2] = piece
        if (
            ((y2 == 7 and cur_c == 0) or (y2 == 0 and cur_c == 1))
            and
            "P" in piece.possible_natures
        ):
            self.grid[x2][y2] = self.pieces[cur_c][i + 8]
        self.grid[x1][y1] = None
        alive = self.pieces_alive[-1][:]
        if target_piece is not None:
            alive[target_piece.color] -= 1
        self.pieces_alive.append(alive)
        self.positions.append(self.compute_position())
        self.attacks.append(self.compute_attack())

    def delete_move_from_history(self, x1, y1, x2, y2, piece, target_piece):
        """Reverse the last move."""
        self.time -= 1
        self.moves.pop()
        self.nature_eliminations.pop()
        self.grid[x2][y2] = target_piece
        self.grid[x1][y1] = piece
        self.pieces_alive.pop()
        self.positions.pop()
        self.attacks.pop()

    def test_move(self, x1, y1, x2, y2, full_result=False):
        """
        Test whether a move is possible.

        Raise IllegalMove exceptions detailing the various move invalidities.
        """
        error = self.trivial_test_move(x1, y1, x2, y2)
        if error is not None:
            raise IllegalMove(error)

        piece = self.grid[x1][y1]
        target_piece = self.grid[x2][y2]

        self.add_move_to_history(x1, y1, x2, y2, piece, target_piece)

        # Check quantum failures (requires history with last move)
        problem, status = self.quantum_explanation()

        self.delete_move_from_history(x1, y1, x2, y2, piece, target_piece)

        if status == -1:
            error = (
                "Trying to perform a move that is illegal for any " +
                "initial piece configuration"
            )
            raise IllegalMove(error)

        if full_result:
            return problem
        else:
            return True

    def perform_move(self, x1, y1, x2, y2, problem):
        """Perform a move, assuming it is valid."""
        piece = self.grid[x1][y1]
        target_piece = self.grid[x2][y2]

        self.add_move_to_history(x1, y1, x2, y2, piece, target_piece)

        # Update guesses and heuristics
        piece.possible_natures = [
            n for n in piece.possible_natures
            if n not in self.nature_eliminations[-1][2]
        ]
        self.update_guess(problem)

    def move(self, x1, y1, x2, y2):
        """
        Test and perform a move.

        Will raise IllegalMove if the move is not valid.
        """
        problem = self.test_move(x1, y1, x2, y2, full_result=True)
        self.perform_move(x1, y1, x2, y2, problem)
        # print(x1, y1, x2, y2)
        # self.display_guess()
        return True

    def legal_moves_from(self, x1, y1):
        """Search all legal moves starting from a given square."""
        legal_arrivals = []
        illegal_arrivals = []
        for x2 in range(8):
            for y2 in range(8):
                try:
                    self.test_move(x1, y1, x2, y2, full_result=False)
                    legal_arrivals.append((x2, y2))
                except IllegalMove as e:
                    illegal_arrivals.append((x2, y2, e))
        return legal_arrivals

    def all_legal_moves(self):
        """Search all legal move at a given turn."""
        legal_moves = []
        for x1 in range(8):
            for y1 in range(8):
                for (x2, y2) in self.legal_moves_from(x1, y1):
                    legal_moves.append((x1, y1, x2, y2))
        return legal_moves

    def is_legal_nature(self, piece, n):
        """Check if, given the current history, piece could have nature n."""
        if n not in piece.possible_natures:
            return False
        elif len(piece.possible_natures) == 1 and n in piece.possible_natures:
            return True

        piece.forbidden_natures = [
            other_n for other_n in major_piece_natures if other_n != n
        ]
        problem, status = self.quantum_explanation()
        is_legal_nature_n = (status == 1)
        piece.forbidden_natures = []
        return is_legal_nature_n

    def all_legal_natures(self, piece, update=True):
        """Search all legal natures a piece could have."""
        legal_natures = []
        for n in all_natures:
            if self.is_legal_nature(piece, n):
                legal_natures.append(n)
        if update:
            piece.possible_natures = legal_natures
        return legal_natures

    def end_game(self):
        if len(self.all_legal_moves()) > 0:
            return "Legal moves still exist"
        problem1, status1 = self.quantum_explanation(check=True)
        problem2, status2 = self.quantum_explanation(check=False)
        checkmate_possible = status1 == 1
        stalemate_possible = status2 == 2
        if checkmate_possible and stalemate_possible:
            return "Result unclear"
        elif checkmate_possible:
            return "Current player checkmated"
        else:
            return "Stalemate"


class LightBoard():
    def __init__(self):
        self.clean()
        for i in range(8):
            self.board[i][0] = (0, major_piece_natures)
            self.board[i][1] = (0, "P")
            self.board[i][6] = (1, "P")
            self.board[i][7] = (1, major_piece_natures)

    def clean(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]

    def move(self, x1, y1, x2, y2):
        self.board[x2][y2] = self.board[x1][y1]
        self.board[x1][y1] = None

    def setPiece(self, x, y, color,  natures):
        self.board[x][y] = (color, natures)

    def getPiece(self, x, y):
        return self.board[x][y]

    def wrapUp(self):
        wrap = []
        for x in range(8):
            for y in range(8):
                piece = self.board[x][y]
                color = piece[0]
                natures = piece[1]
                wrap.append({"x" : x, "y": y, "color" : color, "natures": natures})
        return wrap

    def unwrap(self, wrap):
        self.clean()
        for piece in wrap:
                x = piece["x"]
                y = piece["y"]
                color = piece["color"]
                natures = piece["nature"]
                self.setPiece(x, y, color, natures)



def main():
    """Main."""
    cb = ChessBoard()
    print(cb)

    cb.move(6, 1, 6, 3)
    print(cb)

    cb.move(3, 6, 3, 4)
    print(cb)

    cb.move(7, 0, 3, 4)
    print(cb)

    cb.move(4, 7, 5, 5)
    print(cb)

    cb.move(3, 4, 3, 3)
    print(cb)

    print(cb.all_legal_moves())


if __name__ == "__main__":
    pass
    # import cProfile
    # import pstats
    #
    # cProfile.run("main()", "stats")
    # p = pstats.Stats("stats")
    # p.strip_dirs().sort_stats("cumtime").print_stats()

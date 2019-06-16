"""First test for chess implementation."""

import itertools
import numpy as np
import pulp
from collections import defaultdict

import sunfish

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

color_nature_to_icon = {
    0: {
        "K": "♔",
        "Q": "♕",
        "R": "♖",
        "B": "♗",
        "N": "♘",
        "P": "♙",
    },
    1: {
        "K": "♚",
        "Q": "♛",
        "R": "♜",
        "B": "♝",
        "N": "♞",
        "P": "♟",
    }
}


class IllegalMove(Exception):
    """Illegal move."""

    pass


class ChessPiece():
    """Chess piece manipulation."""

    def __init__(self, c, i, n, p, b=None):
        """Initialize color, number, nature, position."""
        self.color = c
        self.color_name = "W" if c == 0 else "B"
        self.number = i
        if n is None:
            self.possible_natures = ["K", "Q", "R", "B", "N"]
        else:
            self.possible_natures = [n]
        self.legal_natures = self.possible_natures[:]
        self.position = p
        self.board = b
        self.forbidden_natures = []

        if self.number >= 8:
            self.nature_guess = "P"
        elif self.number in [0, 7]:
            self.nature_guess = "R"
        elif self.number in [1, 6]:
            self.nature_guess = "N"
        elif self.number in [2, 5]:
            self.nature_guess = "B"
        elif self.number == 3:
            self.nature_guess = "Q"
        elif self.number == 4:
            self.nature_guess = "K"

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
            return color_nature_to_icon[self.color][self.nature_guess] + " "
            return (
                color_name +
                self.nature_guess + " "
            )
        elif natures:
            return (
                color_name +
                str(len(self.board.all_legal_natures(self))) + " "
            )


class ChessBoard():
    """Chess board manipulation."""

    def __init__(self):
        """Initialize the board."""
        # Colorized lists of pieces
        white_pieces = [
            ChessPiece(c=0, i=i, n=None, p=(i, 0), b=self)
            for i in major_piece_numbers
        ] + [
            ChessPiece(c=0, i=i, n="P", p=(i - 8, 1), b=self)
            for i in pawn_numbers
        ] + [
            ChessPiece(c=0, i=i, n=None, p=None, b=self)
            for i in promoted_numbers
        ]

        black_pieces = [
            ChessPiece(c=1, i=i, n=None, p=(i, 7), b=self)
            for i in major_piece_numbers
        ] + [
            ChessPiece(c=1, i=i, n="P", p=(i - 8, 6), b=self)
            for i in pawn_numbers
        ] + [
            ChessPiece(c=1, i=i, n=None, p=None, b=self)
            for i in promoted_numbers
        ]

        self.pieces = [white_pieces, black_pieces]

        # Grid with pieces
        self.grid = [[None for y in range(8)] for x in range(8)]
        for x in range(8):
            self.grid[x][0] = self.pieces[0][x]
            self.grid[x][1] = self.pieces[0][x + 8]
            self.grid[x][6] = self.pieces[1][x + 8]
            self.grid[x][7] = self.pieces[1][x]

        # Game history
        self.time = 0
        self.moves = []
        self.nature_eliminations = []
        self.positions = [self.compute_position()]
        self.attacks = [self.compute_attack()]
        self.pieces_alive = [[16, 16]]

    def __str__(self, guess=False, natures=False, letters=True):
        """Display the board in ASCII art."""
        s = "\n"
        s += "At time " + str(self.time) + ":\n"
        s += "\n"
        for y in reversed(range(8)):
            if not guess:
                if letters:
                    s += str(y + 1) + "  "
                else:
                    s += str(y) + "  "
            for x in range(8):
                piece = self.grid[x][y]
                if piece is not None:
                    s += piece.__str__(guess=guess, natures=natures)
                else:
                    # square_color = (x + y) % 2
                    if not guess:
                        s += "-- "
                    elif guess:
                        s += "· "
                        # s += "\u2796"
                s += " "
            s += "\n"
        if not guess:
            s += "   "
            for x in range(8):
                if letters:
                    s += chr(97 + x) + "   "
                else:
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
        for x in range(8):
            for y in range(8):
                piece = self.grid[x][y]
                if piece is None:
                    continue
                c, i = piece.color, piece.number
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

        problem = pulp.LpProblem("Chess", 1)

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
            for i in promoted_numbers:
                problem += z[(c, i, "K")] == 0, "No promoted king " + str((c, i))

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

                problem += (
                    16 * (1 - king) >= dangers,
                    "No king left in check " + str((t, prev_c, s))
                )

        if check is not None:
            cur_c = T % 2
            prev_c = 1 - cur_c

            for s in range(64):

                if self.attacks[T][s, prev_c, :, :].sum() < 0.5:
                    continue
                if self.positions[T][s, cur_c, major_piece_numbers].sum() < 0.5:
                    continue

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
                        current_king <= current_dangers,
                        "Current king in check " + str(s)
                    )

                elif check == False:
                    problem += (
                        16 * (1 - current_king) >= current_dangers,
                        "Current king not in check " + str(s)
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
        self.grid[x1][y1] = None
        promotion = (
            ((y2 == 7 and cur_c == 0) or (y2 == 0 and cur_c == 1))
            and
            "P" in piece.possible_natures
        )
        if promotion:
            promoted_piece = self.pieces[cur_c][i + 8]
            self.grid[x2][y2] = promoted_piece
            piece.position = None
            promoted_piece.position = (x2, y2)
        else:
            self.grid[x2][y2] = piece
            piece.position = (x2, y2)
        alive = self.pieces_alive[-1][:]
        if target_piece is not None:
            target_piece.position = False
            alive[target_piece.color] -= 1
        self.pieces_alive.append(alive)
        self.positions.append(self.compute_position())
        self.attacks.append(self.compute_attack())

    def delete_move_from_history(self, x1, y1, x2, y2, piece, target_piece):
        """Reverse the last move."""
        cur_c, i = piece.color, piece.number
        self.time -= 1
        self.moves.pop()
        self.nature_eliminations.pop()
        self.grid[x1][y1] = piece
        piece.position = (x1, y1)
        self.grid[x2][y2] = target_piece
        if target_piece is not None:
            target_piece.position = (x2, y2)
        promotion = (
            ((y2 == 7 and cur_c == 0) or (y2 == 0 and cur_c == 1))
            and
            "P" in piece.possible_natures
        )
        if promotion:
            promoted_piece = self.pieces[cur_c][i + 8]
            promoted_piece.position = None
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

        if status != 1:
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

        if target_piece is not None:
            target_piece.position = False

        self.update_guess(problem)

    def move(self, x1, y1, x2, y2, disp=True):
        """
        Test and perform a move.

        Will raise IllegalMove if the move is not valid.
        """
        problem = self.test_move(x1, y1, x2, y2, full_result=True)
        self.perform_move(x1, y1, x2, y2, problem)
        if disp:
            print(self.__str__(guess=0))
        return True

    def legal_moves_from_gen(self, x1, y1):
        """Search all legal moves starting from a given square."""
        X2, Y2 = range(8), range(8)
        couples = np.random.permutation(
            list(itertools.product(X2, Y2))
        )
        for x2, y2 in couples:
            try:
                self.test_move(x1, y1, x2, y2, full_result=False)
                yield (x2, y2)
            except IllegalMove:
                pass

    def all_legal_moves_gen(self):
        """Search all legal move at a given turn."""
        X1, Y1, X2, Y2 = range(8), range(8), range(8), range(8)
        quadruples = np.random.permutation(
            list(itertools.product(X1, Y1, X2, Y2))
        )
        for x1, y1, x2, y2 in quadruples:
            try:
                self.test_move(x1, y1, x2, y2, full_result=False)
                yield (x1, y1, x2, y2)
            except IllegalMove:
                pass

    def legal_moves_from(self, x1, y1):
        return list(self.legal_moves_from_gen(x1, y1))

    def all_legal_moves(self):
        return sorted(list(self.all_legal_moves_gen()))

    def sunfish_move_suggestion(self, secs):
        board = (
            "         \n"
            "         \n"
        )
        for y in reversed(range(8)):
            board += ' '
            for x in range(8):
                if self.grid[x][y] is None:
                    board += '.'
                elif self.grid[x][y].color_name == "W":
                    board += self.grid[x][y].nature_guess
                else:
                    board += self.grid[x][y].nature_guess.lower()
            board += '\n'
        board += (
            "         \n"
            "         \n"
        )
        pos = sunfish.Position(
            board, 0, (False, False), (False, False), 0, 0
        )
        if self.time % 2 == 1:
            pos = pos.rotate()

        searcher = sunfish.Searcher()
        move, score = searcher.search(pos, secs=secs)
        if move is None:
            raise IllegalMove("Sunfish didn't find a feasible move")
        if self.time % 2 == 1:
            move = (119-move[0], 119-move[1])
        first_square, last_square = sunfish.render(move[0]), sunfish.render(move[1])
        x1, y1, x2, y2 = self.translate_move((first_square, last_square))
        return x1, y1, x2, y2

    def auto_move(self, intelligent=True, secs=1):
        """Perform one of the legal moves at random."""
        if intelligent:
            try:
                x1, y1, x2, y2 = self.sunfish_move_suggestion(secs=secs)
                self.test_move(x1, y1, x2, y2)
            except IllegalMove:
                self.auto_move(intelligent=False)
        else:
            try:
                x1, y1, x2, y2 = self.all_legal_moves_gen().__next__()
            except StopIteration:
                raise IllegalMove("Game over - " + self.end_game())
        return x1, y1, x2, y2

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
            piece.possible_natures = legal_natures[:]
        return legal_natures

    def end_game(self):
        if len(self.all_legal_moves()) > 0:
            return "Legal moves still exist"
        problem1, status1 = self.quantum_explanation(check=True)
        problem2, status2 = self.quantum_explanation(check=False)
        checkmate_possible = (status1 == 1)
        stalemate_possible = (status2 == 1)
        if checkmate_possible and stalemate_possible:
            return "Result unclear"
        elif checkmate_possible:
            return "Current player checkmated"
        else:
            return "Stalemate"

    def translate_move(self, move):
        if len(move) == 4:
            x1, y1, x2, y2 = move
            a = chr(97 + x1)
            b = chr(97 + x2)
            return (a + str(y1 + 1), b + str(y2 + 1))
        elif len(move) == 2:
            first_square, last_square = move
            x1 = ord(first_square[0]) - 97
            y1 = int(first_square[1]) - 1
            x2 = ord(last_square[0]) - 97
            y2 = int(last_square[1]) - 1
            return (x1, y1, x2, y2)

    def one_player_game(self):
        print(self.__str__())
        while True:
            if self.time % 2 == 1:
                print("The computer is playing")
                try:
                    x1, y1, x2, y2 = self.auto_move()
                    self.move(x1, y1, x2, y2, disp=True)
                except StopIteration as e:
                    print(e)
                    return
            else:
                valid_player_move = False
                while not valid_player_move:
                    print("You have not entered a valid move yet")

                    stop = input("Stop? [y/n] ")
                    if stop == "y":
                        return

                    list_moves = input("List possible moves [y/n] ")
                    if list_moves == "y":
                        legal_moves = self.all_legal_moves()
                        print([
                            self.translate_move(move)
                            for move in legal_moves
                        ])
                        if len(legal_moves) == 0:
                            print(self.end_game())
                            return

                    first_square = input("Go from ")
                    last_square = input("...to ")
                    if not (first_square + last_square).isalnum():
                        print("This move is not a chess move")
                    x1, y1, x2, y2 = self.translate_move(
                        (first_square, last_square)
                    )
                    try:
                        self.move(x1, y1, x2, y2, disp=True)
                        valid_player_move = True
                    except IllegalMove as e:
                        print(e)


class LightBoard():
    def __init__(self):
        self.pieces = []
        for j in range(8):
            self.pieces.append({"position": (j, 0), "color": 0, "natures": major_piece_natures})
        for j in range(8):
            self.pieces.append({"position": (j, 1), "color": 0, "natures": ["P"]})
        for j in range(8):
            self.pieces.append({"position": None, "color": 0, "natures": major_piece_natures})
        for j in range(8):
            self.pieces.append({"position": (j, 7), "color": 1, "natures": major_piece_natures})
        for j in range(8):
            self.pieces.append({"position": (j, 6), "color": 1, "natures": ["P"]})
        for j in range(8):
            self.pieces.append({"position": None, "color": 1, "natures": major_piece_natures})

    def move(self, x1, y1, x2, y2):
        i = self.getPieceIndex(x1, y1)
        if i is not None:
            piece = self.pieces[i]
            natures = self.possibleNaturesFromMove(x1, y1, x2, y2, piece["color"], piece["natures"])
            assert(len(natures) >= 1)
            # Mark the target box as a dead piece if necessary
            j = self.getPieceIndex(x2, y2)
            if j is not None:
                piece2 = self.pieces[j]
                self.setPiece(j, piece2["color"], False, piece2["natures"])
            # Move the main piece
            self.setPiece(i, piece["color"], (x2, y2), natures)
            for x in range(8):
                for y in range(8):
                    if x != x2 and y != y2:
                        k = self.getPieceIndex(x, y)
                        if k is not None:
                            piece = self.pieces[k]
                            if len(piece["natures"]) > 1:
                                self.setPiece(k, piece["color"], (x, y), "E")

    @staticmethod
    def possibleNaturesFromMove(x1, y1, x2, y2, color, natures):
        h = x2 - x1
        v = y2 - y1
        output_natures = []
        for n in natures:
            if n == "K":
                if abs(h) <= 1 and abs(v) <= 1 and (h, v) != (0, 0):
                    output_natures.append("K")
            elif n == "Q":
                if (abs(h) == 0 and abs(v) >= 1) or (abs(v) == 0 and abs(h) >= 1) or (abs(h) == abs(v) and abs(h) >= 1):
                    output_natures.append("Q")
            elif n == "R":
                if (abs(h) == 0 and abs(v) >= 1) or (abs(v) == 0 and abs(h) >= 1):
                    output_natures.append("R")
            elif n == "B":
                if abs(h) == abs(v) and abs(h) >= 1:
                    output_natures.append("B")
            elif n == "N":
                if (abs(h) == 2 and abs(v) == 1) or (abs(h) == 1 and abs(v) == 2):
                    output_natures.append("N")
            elif n == "P":
                if color == 0 and y2 == 7:
                    return ["E"]
                elif color == 0 and y2 == 0:
                    return ["E"]
                else:
                    output_natures.append("P")
            elif n == "E":
                return ["E"]

        return output_natures

    def setPiece(self, i, color, position, natures):
        """i is the index of the piece in self.pieces (same as ChessBoard.pieces)"""
        if position is not None and position is not False:
            position = (int(position[0]), int(position[1]))
        self.pieces[i] = {
            "position": position,
            "color": int(color),
            "natures": natures
        }

    def getPiece(self, x, y):
        for piece in self.pieces:
            if (piece["position"] is not None) and (piece["position"] is not False):
                a, b = piece["position"]
                if x == a and y == b:
                    return piece
        return None

    def getPieceIndex(self, x, y):
        for i, piece in enumerate(self.pieces):
            if (piece["position"] is not None) and (piece["position"] is not False):
                a, b = piece["position"]
                if x == a and y == b:
                    return i
        return None

    def getDeadPieces(self, color):
        return [p for p in self.pieces if p["color"] == color and p["position"] == False]

    def wrapUp(self):
        return self.pieces

    def unwrap(self, wrap):
        self.pieces = wrap


def main():
    """Main."""
    cb = ChessBoard()
    cb.one_player_game()


if __name__ == "__main__":
    cb = ChessBoard()
    cb.move(4, 1, 4, 3)
    cb.move(7, 6, 7, 5)
    cb.move(5, 0, 0, 5)
    cb.move(7, 5, 7, 4)
    cb.move(0, 5, 0, 6)
    cb.move(7, 4, 7, 3)
    cb.move(0, 6, 0, 7)
    cb.move(7, 3, 7, 2)
    cb.move(0, 7, 1, 7)
    cb.move(6, 6, 6, 5)
    cb.move(1, 7, 2, 7)
    cb.move(6, 5, 6, 4)
    cb.move(2, 7, 3, 7)
    cb.move(6, 4, 6, 3)
    cb.move(3, 7, 4, 7)
    cb.move(6, 3, 6, 2)
    cb.move(4, 7, 5, 7)
    cb.move(5, 6, 5, 5)
    cb.move(2, 1, 2, 2)
    cb.move(1, 6, 1, 5)
    cb.move(3, 0, 1, 2)
    cb.move(5, 5, 5, 4)
    cb.move(5, 7, 6, 7)
    cb.display_guess()
    cb.auto_move(intelligent=True)

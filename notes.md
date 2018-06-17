# Haft Schrödinger Chess

## Description

### General principle

See here <http://antumbrastation.com/schroedinger-chess/2017/11/28/introduction-to-haft-schroedinger-chess.html>

The nature of the major pieces is unknown at first, and is determined by the moves they make.

The goal is, for a given series of moves, to check whether there exists an initial choice of piece natures so that:
1. There is no more than 1 king, 1 queen, 2 rooks, 2 bishops, 2 knights in each color
2. Every move played is consistent with these piece natures
3. No move played by a given color left their king in check

### Forgotten chess rules

We discard the following rules:
- pawn promotion
- castling
- en passant

## Mathematical model

### Nomenclature

- $s \in \mathcal{S} = [1, 64]$: square of the chess board
- $c \in \mathcal{C} = \{0, 1\}$: color
- $i \in \mathcal{I} = [1, 16]$: index of a piece for a given color. Belongs to $\mathcal{J} = [1, 8]$ for the major pieces depending on their initial position on the first row, and to $\mathcal{K} = [9, 16]$ for the pawns.
- $n \in \mathcal{N} = \{K, Q, R, B, N\}$: nature of a piece
- $t \in [1, T]$: time, ie. number of turns played

### Variables and their relations

#### Chess constants

At every given time we know the color of the player that moves: let's call it $c_t = t [2]$.

#### Unknown variables

- $x(c, i, n) = 1$ if piece $i$ of color $c$ has nature $n$

#### Known variables

These variables can be calculated at any time without knowing the actual nature of the pieces.

- $p_t(s, c, i) = 1$ if square $s$ of the board contains piece $i$ of color $c$ at time $t$

- $a_t(s, c, i, n) = 1$ if square $s$ of the board would be threatened by piece $i$ of color $c$ at time $t$, assuming its nature was $n$

- $f_T(c, i, n) = 1$ if until time $T$, piece $(c, i)$ has performed a move forbidden for nature $n$

#### Variables deduced from x

- $d_t(c, s)$ is the number of pieces from color $c$ attacking square $s$ (number of dangers)
$$ d_t(c, s) = \sum_i \sum_n a_{t}(s, c, i, n) \cdot x(c, i, n)$$

- $k_t(c, s) = 1$ if the king from color $c$ is located on $s$
$$ k_t(c, s) = \sum_i p_t (s, c, i) \cdot x(c, i, K)$$

### Constraints

1. Variable domain
$$\forall (c, i, n), ~x(c, i, n) \in \{0, 1\}$$
2. Variable interpretation: exactly one nature per piece
$$\forall (c, i), ~\sum_{n} x(c, i, n) = 1$$
3. Right number of pieces of each nature
$$ \forall (c, n), ~\sum_i x(c, i, n) \leq x_{max} (n)$$
4. Feasible moves: no piece can perform forbidden moves
$$\forall (c, i, n), ~x(c, i, n) \leq 1 - f_T(c, i, n)$$
5. Check rules: no player can leave its king in check
$$ \forall t, ~ \forall s, ~ d_t(c_t, s) \leq 16 (1 - k_t(c_{t-1}, s))$$

## Implementation

### Python libraries

- <http://labix.org/python-constraint>
- <http://simpleai.readthedocs.io/en/latest/constraint_satisfaction_problems.html>
- <http://www.cvxpy.org/tutorial/advanced/index.html#mixed-integer-programs>
- <http://mpy.github.io/CyLPdoc/>
- <https://pythonhosted.org/PuLP/>

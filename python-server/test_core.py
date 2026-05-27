"""Test core move→check_winner→undo flow without MySQL."""
import sys
import json
import ctypes

from game_engine import make_board, board_to_list, check_winner_on_board, BOARD_SIZE, EMPTY


def test_board_creation():
    b = make_board()
    assert len(b) == BOARD_SIZE
    assert len(b[0]) == BOARD_SIZE
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            assert b[y][x] == EMPTY, f"Non-zero at ({x},{y}): {b[y][x]}"
    print("✓ board creation: all zeros")


def test_piece_placement():
    b = make_board()
    b[7][7] = 1  # black
    b[7][8] = 2  # white
    assert b[7][7] == 1
    assert b[7][8] == 2
    assert b[0][0] == EMPTY
    print("✓ piece placement: r/w works")


def test_empty_cell_check():
    b = make_board()
    b[7][7] = 1
    assert b[7][7] != 0   # occupied
    assert b[0][0] == 0    # empty (c_int(0) == 0)
    assert not (b[0][0] != 0)  # empty check used in _handle_move
    print("✓ empty cell check: c_int(0) != 0 works correctly")


def test_win_detection():
    # Horizontal win
    b = make_board()
    for i in range(5):
        b[0][i] = 1
    color, line = check_winner_on_board(b, 2, 0)
    assert color == 1, f"Expected 1, got {color}"
    assert line == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)], f"Got {line}"

    # Vertical win
    b2 = make_board()
    for i in range(5):
        b2[i][7] = 2
    color, line = check_winner_on_board(b2, 7, 2)
    assert color == 2, f"Expected 2, got {color}"

    # Diagonal win
    b3 = make_board()
    for i in range(5):
        b3[i][i] = 1
    color, line = check_winner_on_board(b3, 2, 2)
    assert color == 1, f"Expected 1, got {color}"

    # No win
    b4 = make_board()
    b4[0][0] = 1
    b4[0][1] = 2
    color, line = check_winner_on_board(b4, 0, 0)
    assert color == 0, f"Expected 0, got {color}"

    print("✓ win detection: horizontal, vertical, diagonal, no-win all correct")


def test_board_to_list_json():
    b = make_board()
    b[7][7] = 1
    b[0][0] = 2
    lst = board_to_list(b)
    # Verify each value is a Python int (JSON serializable)
    for row in lst:
        for v in row:
            assert type(v) is int, f"Expected int, got {type(v)}: {v}"
    # Verify values
    assert lst[7][7] == 1
    assert lst[0][0] == 2
    assert lst[5][5] == 0
    # Verify JSON serializable
    dumped = json.dumps(lst)
    loaded = json.loads(dumped)
    assert loaded[7][7] == 1
    print("✓ board_to_list: all values are Python int, JSON serializable")


def test_board_to_list_preserves_board():
    """board_to_list must not mutate the original board."""
    b = make_board()
    b[3][4] = 1
    lst = board_to_list(b)
    b[5][5] = 2  # modify AFTER to_list
    assert lst[5][5] == 0, "board_to_list captured a snapshot, not a reference"
    print("✓ board_to_list: snapshot isolation")


def test_ctypes_board_memory():
    """Verify the ctypes array is contiguous in memory (needed for C interop)."""
    b = make_board()
    b[0][0] = 42
    b[14][14] = 99
    # Cast 2D array to flat pointer and verify layout
    ptr = ctypes.cast(b, ctypes.POINTER(ctypes.c_int))
    assert ptr[0] == 42
    assert ptr[14 * BOARD_SIZE + 14] == 99
    print("✓ ctypes board memory: contiguous layout")


def simulate_game_move():
    """Simulate the exact server-side move handler logic."""
    board = make_board()
    current_player = 1  # black starts
    moves = []

    # Move 1: black at (7,7)
    x, y, color = 7, 7, 1
    assert board[y][x] == 0, "position should be empty"
    assert current_player == color, "wrong turn"
    board[y][x] = color
    moves.append((x, y, color))
    current_player = 2

    winner, line = check_winner_on_board(board, x, y)
    assert winner == 0, "should be no winner yet"

    # Move 2: white at (0,0)
    x, y, color = 0, 0, 2
    assert board[y][x] == 0, "position should be empty"
    assert current_player == color, "wrong turn"
    board[y][x] = color
    moves.append((x, y, color))
    current_player = 1

    winner, line = check_winner_on_board(board, x, y)
    assert winner == 0, "should be no winner yet"

    # Reject occupied position
    assert board[7][7] != 0, "should detect occupied position"
    assert board[0][0] != 0, "should detect occupied position"

    print(f"✓ simulate game: {len(moves)} moves, turn tracking correct, occupied detection works")


def simulate_undo():
    """Simulate undo: rebuild board from moves."""
    moves = [(7, 7, 1), (0, 0, 2), (8, 8, 1), (1, 1, 2)]
    # Undo last 2 moves (one from each player)
    moves.pop()
    moves.pop()

    board = make_board()
    for mx, my, mc in moves:
        board[my][mx] = mc

    assert board[7][7] == 1
    assert board[0][0] == 2
    assert board[8][8] == 0  # undone
    assert board[1][1] == 0  # undone
    print("✓ undo: rebuild from moves works correctly")


if __name__ == '__main__':
    test_board_creation()
    test_piece_placement()
    test_empty_cell_check()
    test_win_detection()
    test_board_to_list_json()
    test_board_to_list_preserves_board()
    test_ctypes_board_memory()
    simulate_game_move()
    simulate_undo()
    print("\n✅ All core logic tests passed.")

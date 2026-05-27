#include "board.h"

static int board[BOARD_SIZE][BOARD_SIZE];
static int current_player = BLACK;

void board_init(void) {
    for (int i = 0; i < BOARD_SIZE; i++)
        for (int j = 0; j < BOARD_SIZE; j++)
            board[i][j] = EMPTY;
    current_player = BLACK;
}

int place_piece(int x, int y, int color) {
    if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) return 0;
    if (board[y][x] != EMPTY) return 0;
    if (color != current_player) return 0;
    board[y][x] = color;
    current_player = (current_player == BLACK) ? WHITE : BLACK;
    return 1;
}

void reset_game(void) { board_init(); }
void set_current_player(int color) { current_player = color; }
int get_current_player(void) { return current_player; }

int get_cell(int x, int y) {
    if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) return -1;
    return board[y][x];
}

int is_empty(int x, int y) {
    if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) return 0;
    return board[y][x] == EMPTY;
}

void set_board_state(const int src[BOARD_SIZE][BOARD_SIZE]) {
    for (int i = 0; i < BOARD_SIZE; i++)
        for (int j = 0; j < BOARD_SIZE; j++)
            board[i][j] = src[i][j];
}

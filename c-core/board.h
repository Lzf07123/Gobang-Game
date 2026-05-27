#ifndef BOARD_H
#define BOARD_H

#define BOARD_SIZE 15
#define EMPTY 0
#define BLACK 1
#define WHITE 2

void board_init(void);
int place_piece(int x, int y, int color);
void reset_game(void);
void set_current_player(int color);
int get_current_player(void);
int get_cell(int x, int y);
int is_empty(int x, int y);
void set_board_state(const int board[BOARD_SIZE][BOARD_SIZE]);

#endif

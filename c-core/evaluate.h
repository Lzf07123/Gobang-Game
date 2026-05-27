#ifndef EVALUATE_H
#define EVALUATE_H

#include "board.h"

int evaluate_position(int x, int y, int color);
int count_open_threes(int color);
int count_open_fours(int color);

#endif

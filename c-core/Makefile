CC = gcc
CFLAGS = -fPIC -O2 -Wall -Wextra
LDFLAGS = -shared
TARGET = libgobang.so
OBJS = board.o rules.o evaluate.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $(TARGET) $(OBJS)

board.o: board.c board.h
	$(CC) $(CFLAGS) -c board.c

rules.o: rules.c rules.h board.h
	$(CC) $(CFLAGS) -c rules.c

evaluate.o: evaluate.c evaluate.h board.h
	$(CC) $(CFLAGS) -c evaluate.c

clean:
	rm -f $(TARGET) $(OBJS)

import curses
from random import randrange, choice
from collections import defaultdict

actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']

letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']

actions_mapping = dict(zip(letter_codes, actions * 2))


def get_user_input(keyboard):
    char = "N"
    while char not in actions_mapping:
        char = keyboard.getch()

    return actions_mapping[char]


def flip_horizontally(board):
    return [list(reversed(row)) for row in board]


# zip* is to unzip
def transpose(board):
    return [list(row) for row in zip(*board)]


class TwentyFourtyEight(object):

    def __init__(self, height=4, width=4, win=2048):
        self.height = height
        self.width = width
        self.win_value = win
        self.score = 0
        self.high_score = 0

        self.reset()

    def reset(self):
        if self.score > self.high_score:
            self.high_score = self.score

        self.score = 0
        self.board = [[0 for i in range(self.width)]
                      for j in range(self.height)]

        # Start with two number in the board
        self.spawn()
        self.spawn()

    def spawn(self):
        element = 4 if randrange(100) > 89 else 2

        (i, j) = choice([(i, j) for i in range(self.width)
                         for j in range(self.height) if self.board[i][j] == 0])
        self.board[i][j] = element

    def move(self, direction):
        def move_row(row):
            def tighten(row):
                new_row = [i for i in row if i != 0]  # compact
                new_row += [0] * (len(row) - len(new_row))  # append 0
                return new_row

            # goes from left to right
            def merge(row):
                pair = False
                new_row = []

                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        # Add place holder zero for tightening later
                        new_row.append(0)

                        self.score += 2 * row[i]
                        pair = False
                    else:
                        # same number
                        if i + 1 < len(row)and row[i] == row[i + 1]:
                            pair = True
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row
            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left'] = lambda board: [move_row(row) for row in board]
        # Right is Left flipped horizontally
        moves['Right'] = lambda board: flip_horizontally(
            moves['Left'](flip_horizontally(board)))
        # Up is Left transpose
        moves['Up'] = lambda board: transpose(
            moves['Left'](transpose(board)))
        # Down
        moves['Down'] = lambda board: transpose(
            moves['Right'](transpose(board)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.board = moves[direction](self.board)
                self.spawn()
                return True
        else:
            return False

    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            def can_move_row(i):
                if row[i] == 0 and row[i + 1] != 0:
                    return True

                if row[i] != 0 and row[i + 1] == row[i]:
                    return True

                return False

            return any(can_move_row(i) for i in range(len(row) - 1))

        check = {}
        check['Left'] = lambda board: any(
            row_is_left_movable(row) for row in board)
        # Right is Left flipped horizontally
        check['Right'] = lambda board: check['Left'](flip_horizontally(board))
        # Up is Left transposed
        check['Up'] = lambda board: check['Left'](transpose(board))
        # Down
        check['Down'] = lambda board: check['Right'](transpose(board))

        if direction in check:
            return check[direction](self.board)
        else:
            return False

    def is_win(self):
        return any(any(i >= self.win_value for i in row) for row in self.board)

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    def draw(self, screen):
        info1 = '(W)Up (S)Down (A)Left (D)Right'
        info2 = '(R)Restart (Q)Exit'
        gameover = '    Game Over'
        win = ' YOU WIN!'

        def cast(string):
            screen.addstr(string + '\n')

        def draw_horizontal_seperator():
            line = '+------' * self.width + '+'
            seperator = defaultdict(lambda: line)

            if not hasattr(draw_horizontal_seperator, "counter"):
                draw_horizontal_seperator.counter = 0

            cast(seperator[draw_horizontal_seperator.counter])
            draw_horizontal_seperator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num >
                         0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        if self.high_score != 0:
            cast('HIGH SCORE: ' + str(self.high_score))

        for row in self.board:
            draw_horizontal_seperator()
            draw_row(row)

        draw_horizontal_seperator()

        if self.is_win():
            cast(win)
        elif self.is_gameover():
            cast(gameover)
        else:
            cast(info1)

        cast(info2)

##########################################################################


def main(stdscr):
    def init():
        game_object.reset()
        return 'Game'

    def not_game(state):
        game_object.draw(stdscr)
        action = get_user_input(stdscr)
        responses = defaultdict(lambda: state)
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'
        return responses[action]

    def game():
        game_object.draw(stdscr)
        action = get_user_input(stdscr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'

        if game_object.move(action):
            if game_object.is_win():
                return 'Win'
            if game_object.is_gameover():
                return 'Gameover'

        return 'Game'

    state_actions = {
        'Init': init,
        'Win': lambda: not_game('Win'),
        'Gameover': lambda: not_game('Gameover'),
        'Game': game
    }

    curses.use_default_colors()
    game_object = TwentyFourtyEight(win=2048)
    state = 'Init'
    while state != 'Exit':
        state = state_actions[state]()

curses.wrapper(main)

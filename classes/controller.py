import random
import sys
from classes.neuralnet import NeuralNet


class Controller(object):

    """Docstring for Controller. """

    def __init__(self, gnubg):
        """TODO: to be defined1. """
        self.gnubg = gnubg
        self._first_player = True
        self._net = NeuralNet()

    def setup_game(self, num_points=1):
        """TODO: Docstring for setup_game.

        :num_points: TODO
        :returns: TODO

        """
        num_points = str(num_points)
        self.gnubg.command('set player 0 human')
        self.gnubg.command('set player 1 human')
        self.gnubg.command('set display off')
        self.gnubg.command('save settings')
        self.gnubg.command('new match ' + num_points)

    def train(self, num_games=50000, save_interval=5000):
        """Play num_games and save the state of the neural net
            every save_interval games
        """
        i = 0
        win_stats = [0, 0]
        for i in range(num_games):
            if i != 0 and i % save_interval == 0:
                self._net.save(str(i) + "games")
            winner = int(self.play_training_game())
            win_stats[winner] += 1
        print("player 1 won {} games; player 2 won {} games".format(
            win_stats[0], win_stats[1])
        )

    def play_human_opponent(self):
        computer_player = random.randint(0, 1)
        cur_player = 0
        self.setup_game()
        while not self.hasGameEnded():
            if computer_player == cur_player:
                self.make_smart_move(not computer_player)
            else:
                self._process_input()
            cur_player = int(not cur_player)

    def play_training_game(self):
        """Play neuralnet against neuralnet and learn
        :returns: True if player 1 won, False if player 2 won
        """
        prev_score = 0
        score = 0
        p1_turn = True
        self.setup_game()
        while not self.hasGameEnded():
            move, score = self._get_next_move(p1_turn)
            self._move(move)
            if score and prev_score:
                if self.hasGameEnded():
                    score = 1
                self._net.backprop(
                    prev_score, score, self._encode_board(
                        self._expand_board(self.gnubg.board()),
                        p1_turn=p1_turn)
                )
            prev_score = score
            p1_turn = not p1_turn
        return not p1_turn

    def make_smart_move(self, p1_turn=True):
        """Use neural net to make next move
        """
        self._move(self._get_next_move(p1_turn)[0])

    def _process_input(self):
        """process command from stdin.
        commands:
            list: lists moves
            numbers or text from list will be interpreted as a move
        """
        move_strs = self._get_readable_moves()
        move_nums = range(len(move_strs))
        need_move = True
        while need_move:
            command = sys.stdin.readline().strip()
            if command in move_strs:
                self._move(command)
                need_move = False
            elif command in move_nums:
                self._move(move_strs[command])
                need_move = False
            else:
                print(
                    """
                    commands:
                        help: lists commands
                        list: lists moves
                        numbers or text from list will be interpreted as a move
                    """
                )

    def _get_next_move(self, p1_turn=True):
        """Use neural net to get next move
        """
        move_board_tupl = zip(self._get_readable_moves(),
                              self._net.evaluate(
                                  self._get_all_possible_board_encodings(
                                      p1_turn=p1_turn
                                  )
                              ))
        return max(move_board_tupl, key=lambda item: item[1])

    def _get_moves(self):
        """TODO: Docstring for function.

        :returns: TODO

        """
        moves = []
        for move_info in self.gnubg.hint()['hint']:
            moves.append(self.gnubg.parsemove(move_info['move']))
        return moves

    def _get_all_possible_board_encodings(self, p1_turn=True):
        board = self._expand_board(self.gnubg.board())
        board_encodings = []
        for move in self._get_moves():
            board_encodings.append(
                self._encode_board(
                    self._board_from_move(board, move),
                    p1_turn=p1_turn
                )
            )
        return board_encodings

    def _board_from_move(self, board, moves):
        b1, b2 = self._expand_board(board)
        b2l = list(b2)
        for move in moves:
            b2l[move[0]] -= 1
            b2l[move[1]] += 1
        assert(not any(b2li < 0 for b2li in b2l))
        return (b1, tuple(b2l))

    def _get_readable_moves(self):
        """TODO: Docstring for function.

        :returns: TODO

        """
        moves = []
        for move_info in self.gnubg.hint()['hint']:
            moves.append(
                'move ' +
                ' '.join(
                    map(str,
                        sum(self.gnubg.parsemove(move_info['move']), ())
                        )
                )
            )
        return moves

    def _roll(self):
        """TODO: Docstring for _roll.
        :returns: TODO

        """
        self.gnubg.command('roll')

    def _n_random_moves(self, n=5):
        """TODO: Docstring for _n_random_moves.

        :n: TODO
        :returns: TODO

        """
        i = 0
        while i < n and self.gnubg.posinfo()['gamestate'] != 2:
            moves_ = self._get_readable_moves()
            self._move(moves_[random.randint(0, (len(moves_)-1))])
            i += 1

    def _move(self, move_):
        """TODO: Docstring for _move.

        :move_: TODO
        :returns: TODO

        """
        self.gnubg.command(move_)

    def _get_positions(self):
        """TODO: Docstring for _get_positions.
        :returns: TODO

        """
        save_game_state = self.gnubg.gnubgid()
        positions = []
        for move_ in self._get_readable_moves():
            self._move('move ' + move_)
            self.gnubg.command('set gnubgid ' + save_game_state)
        return positions

    def _encode_slot(self, slot):
        _encoding = [0] * 4
        if slot <= 3:
            _encoding[:slot] = [1] * slot
        else:
            _encoding[:-1] = [1] * 3
            _encoding[-1] = .5 * (slot-3)
        return _encoding

    def _expand_board(self, board):
        b1, b2 = board
        if len(b1) == 26:
            return board
        b1_off_board = abs(sum(b1, -15))
        b2_off_board = abs(sum(b2, -15))
        b1_new = (b1_off_board,) + b1
        b2_new = (b2_off_board,) + b2
        new_board = (b1_new, b2_new)
        return new_board

    def _encode_board(self, board, p1_turn=True):
        board = self._expand_board(board)
        if p1_turn:
            p2, p1 = board
        else:
            p1, p2 = board
        _board = []
        # encode 1-24 slot
        for s1, s2 in zip(p1[1:-1], p2[1:-1]):
            _board = _board + self._encode_slot(s1) + self._encode_slot(s2)
        # encode turn
        if p1_turn:
            _board += [0, 1]
        else:
            _board += [1, 0]

        # encode bar
        _board += [p1[-1]*.5, p2[-1]*.5]

        # encode pieces that have been moved off the board
        _board += [.5 * p1[0], .5*p2[0]]
        return _board

    def hasGameEnded(self):
        """Checks if game is over
        :returns: true if game is over

        """
        return self.gnubg.posinfo()['gamestate'] == 2

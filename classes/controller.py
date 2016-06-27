import random
import base64
import sys
from classes.neuralnet import NeuralNet


class Controller(object):

    """Docstring for Controller. """

    def __init__(self, gnubg=None):
        """TODO: to be defined1. """
        self._gnubg = gnubg
        self._net = NeuralNet()
        self._player = 0

    @property
    def _board(self):
            board = self._gnubg.board()
            if self._current_player() == 0:
                board = board[::-1]
            return self._expand_board(board)

    @_board.setter
    def _board(self, value):
        self._board_obj = self._expand_board(value)

    @_board.deleter
    def _board(self, value):
        self._board_obj = None

    def setup_game(self):
        """TODO: Docstring for setup_game.

        :returns: TODO

        """
        self._gnubg.command('set player 0 human')
        self._gnubg.command('set player 1 human')
        self._gnubg.command('set display off')
        self._gnubg.command('save settings')
        self._gnubg.command('new match 1')
        self._board_obj = self._gnubg.board()

    def train(self, num_games=50000, save_interval=5000, j=0):
        """Play num_games and save the state of the neural net
            every save_interval games
        """
        k = 0
        win_stats = [0, 0]
        for i in range(num_games):
            k = i + j
            if k != 0 and k % save_interval == 0:
                self._net.save(str(k) + "games")
            winner = int(self.play_training_game())
            win_stats[winner] += 1
        print("player 1 won {} games; player 2 won {} games".format(
            win_stats[0], win_stats[1])
        )
        self._net.save(str(k) + "games")

    def test(self, num_games):
        win_stats = [0, 0]
        for i in range(num_games):
            self.setup_game()
            computer_player = random.randint(0, 1)
            while not self._has_game_ended():
                if self._current_player() == computer_player:
                    self.make_smart_move(not computer_player)
                else:
                    self._n_random_moves(n=1)
            if self._current_player() == computer_player:
                win_stats[0] += 1
            else:
                win_stats[1] += 1
            print("smart player: {}, random player: {}".format(*win_stats))

    def play_human_opponent(self):
        computer_player = random.randint(0, 1)
        self.setup_game()
        while not self._has_game_ended():
            if self._current_player() == computer_player:
                self.make_smart_move(not computer_player)
            else:
                self._process_input()

    def play_training_game(self):
        """Play neuralnet against neuralnet and learn
        :returns: True if player 1 won, False if player 2 won
        """
        prev_score = 0
        score = 0
        self.setup_game()
        while not self._has_game_ended():
            move, score = self._next_move()
            self._move(move)
            self._toggle_player()
            if score and prev_score:
                if self._has_game_ended():
                    if self._current_player() == 0:
                        score = 1
                    else:
                        score = 0
                self._net.backprop(
                    prev_score, score, self._encode_board(
                        self._board, self._current_player())
                )
            prev_score = score
        return self._current_player()

    def make_smart_move(self, player):
        """Use neural net to make next move
        """
        best_move = self._next_move()[0]
        self._move(best_move)

    def load_nn(self, folder):
        self._net.load(folder)

    def _process_input(self):
        """process command from stdin.
        commands:
            list: lists moves
            numbers or text from list will be interpreted as a move
        """
        move_strs = self._readable_moves()
        move_nums = [str(i) for i in range(len(move_strs))]
        need_move = True
        print('\n'.join(['{}: {}'.format(*t)
                         for t in zip(move_nums, move_strs)]))
        while need_move:
            command = sys.stdin.readline().strip()
            if command in move_strs:
                self._move(command)
                need_move = False
            elif command in move_nums:
                self._move(move_strs[int(command)])
                need_move = False
            elif command == 'list':
                print('\n'.join(
                    ['{}: {}'.format(*t) for t in zip(move_nums, move_strs)]))
            else:
                print("{} not recognized".format(command))
                print(
                    """
                    commands:
                        list: lists moves
                        numbers or text from list will be interpreted as a move
                    """
                )

    def _next_move(self):
        """Use neural net to get next move
        """
        move_board_tupl = zip(self._readable_moves(),
                              self._net.evaluate(
                                  self._all_possible_board_encoding()
                              ))
        if self._current_player() == 0:
            return max(move_board_tupl, key=lambda item: item[1])
        else:
            return min(move_board_tupl, key=lambda item: item[1])

    def _roll(self):
        """roll dice
        :returns:
            tuple of 2 random rolls

        """
        return (random.randint(0, 6), random.randint(0, 6))

    def _possible_moves_helper(self, start, board, distances):
        """Recursive helper function for getting moves.

        :point:
            the current point 0 - 25
        :returns:
            list of lists each sublist containing a move

        """
        if len(distances) == 0:
            return ()
        b_player = board[self._player]
        if start == 0 and len(distances) == 2:
            return []
        elif start == 0 and len(distances) == 1:
            return ()
        elif b_player[start] == 0:
            return self._possible_moves_helper(start-1, board, distances)
        elif b_player[start] > 0:
            reachable_points = [start-d if start-d > 0 else 0
                                for d in distances]
            for ip, p in enumerate(reachable_points):
                if self._is_legal_move(board, (start, p), self._player):
                    move = ((start, p),)
                    new_brd = self._board_from_move(board, move,
                                                     self._player)
                    new_dist = distances[:]
                    del new_dist[ip]
                    useit = [move + self._possible_moves_helper(
                        start, new_brd, new_dist)]
                    loseit = []
                    if start != 25:
                        loseit = self._possible_moves_helper(
                            start-1, board, distances)
                    return useit + loseit
        else:
            raise ValueError('Point should not have a '
                             'negative number of checkers')

    def _possible_moves(self):
        """Get available moves.

        :returns:
            a list of move tuples

        """
        moves = []
        for move_info in self._gnubg.hint()['hint']:
            move = self._gnubg.parsemove(move_info['move'])
            move = [i for i in sum(move, ())]
            move = tuple(zip(move[::2], move[1::2]))
            moves.append(move)
        return moves

    def _all_possible_board_encoding(self):
        board_encodings = []
        for move in self._possible_moves():
            board_encodings.append(
                self._encode_board(
                    self._board_from_move(self._board, move,
                                           self._current_player()),
                    self._player
                )
            )
        return board_encodings

    def _board_from_move(self, board, moves, swap=False):
        if swap:
            board = board[::-1]
        actor, observer = board
        actorl = list(actor)
        observerl = list(observer)
        moves = [
            [m for m in moves if m[0] == 25],
            [m for m in moves if m[0] != 25 and m[1] != 0],
            [m for m in moves if m[1] == 0]
        ]
        moves = sum(moves, [])
        for start, dest in moves:
            block_point = self._blocking_point(dest)
            actorl[start] -= 1
            actorl[dest] += 1
            if block_point not in [0, 25] and observerl[block_point]:
                observerl[25] += 1
                observerl[block_point] -= 1
        if sum(actorl[:7]) < 15:
            assert not any(m[1] == 0 for m in moves)
        assert not any(x<0 for x in actorl)
        assert not any(x<0 for x in observerl)
        assert(sum(actorl) == 15)
        assert(sum(observerl) == 15)
        if swap:
            return tuple(observerl), tuple(actorl)
        else:
            return tuple(actorl), tuple(observerl)

    def _readable_moves(self):
        """TODO: Docstring for function.

        :returns: TODO

        """
        moves = []
        for move_info in self._gnubg.hint()['hint']:
            moves.append(
                'move ' +
                ' '.join(
                    map(str,
                        sum(self._gnubg.parsemove(move_info['move']), ())
                        )
                )
            )
        return moves

    def _n_random_moves(self, n=5):
        """TODO: Docstring for _n_random_moves.

        :n: TODO
        :returns: TODO

        """
        i = 0
        while i < n and self._gnubg.posinfo()['gamestate'] != 2:
            moves_ = self._readable_moves()
            self._move(moves_[random.randint(0, (len(moves_)-1))])
            i += 1

    def _move(self, move_):
        """TODO: Docstring for _move.

        :move_: TODO
        :returns: TODO

        """
        self._gnubg.command(move_)

    def _encode_point(self, num_checkers_on_point):
        assert (num_checkers_on_point >= 0)
        _encoding = [0] * 4
        if num_checkers_on_point <= 3:
            _encoding[:num_checkers_on_point] = [1] * num_checkers_on_point
        else:
            _encoding[:-1] = [1] * 3
            _encoding[-1] = .5 * (num_checkers_on_point-3)
        return _encoding

    def _expand_board(self, board):
        """Expand the board to include the borne off checkers

        :returns:
            new board tuple with borne off checker count as lead entry
        :raises:
            ValueError: if input board is missing entries or has been expanded
                too many times

        """
        b1, b2 = board
        if len(b1) == 26:
            return board
        elif len(b1) == 25:
            b1_off_board = abs(sum(b1, -15))
            b2_off_board = abs(sum(b2, -15))
            b1_new = (b1_off_board,) + b1
            b2_new = (b2_off_board,) + b2
            new_board = (b1_new, b2_new)
            return new_board
        else:
            raise ValueError(
                'board is missing points or has been expanded too many times.')

    def _encode_board(self, board, player):
        """Encode board tuple as 198 x 1 feature vector for nn

        :returns: 198 x 1 feature vector

        """
        p1, p2 = board
        _board = []
        # encode 1-24 point
        for s1, s2 in zip(p1[1:-1], p2[1:-1]):
            _board = _board + self._encode_point(s1) + self._encode_point(s2)
        # encode turn
        if player == 0:
            _board += [1, 0]
        else:
            _board += [0, 1]

        # encode bar
        _board += [p1[-1]*.5, p2[-1]*.5]

        # encode pieces that have been moved off the board
        _board += [.5 * p1[0], .5*p2[0]]
        assert(len(_board) == 198)
        return _board

    def _toggle_player(self):
        """flip between player 0 and player 1

        :returns:
            the current player

        """
        self._player = (self._player + 1) % 2
        return self._player

    def _blocking_point(self, point):
        if point < 0 or point > 24:
            raise ValueError('no blocking point for ' + point)
        else:
            return 25-point

    def _has_game_ended(self):
        """Checks if game is over

        :returns:
            true if game is over

        """
        borne_off_p1 = self._board[0][0]
        borne_off_p2 = self._board[1][0]
        if borne_off_p1 == 15:
            return True
        elif borne_off_p2 == 15:
            return True
        else:
            return False

    def _current_player(self):
        """The matchid is a base 64 string
        :returns: 0 for player 0 or 1 for player 1

        """
        matchid = self._gnubg.matchid()
        # matchid is a base64 string so convert to data
        decoded_str = base64.decodestring(matchid)

        # decode str to bytes convert char to little endian
        bit_str = "".join([format(ord(x), "08b")[::-1] for x in decoded_str])

        return int(bit_str[11])


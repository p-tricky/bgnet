import random

class Controller(object):

    """Docstring for Controller. """

    def __init__(self, gnubg):
        """TODO: to be defined1. """
        self.gnubg = gnubg

    def setup_game(self, num_points=1):
        """TODO: Docstring for setup_game.

        :num_points: TODO
        :returns: TODO

        """
        num_points = str(num_points)
        self.gnubg.command('set player 0 human')
        self.gnubg.command('set player 1 human')
        self.gnubg.command('save settings')
        self.gnubg.command('new match ' + num_points)

    def _get_moves(self):
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
            moves_ = self._get_moves()
            self._move(moves_[random.randint(0, (len(moves_)-1))])
            self._roll()
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
        for move_ in self._get_moves():
            self._move('move ' + move_)
            self.gnubg.command('set gnubgid ' + save_game_state)
        return positions




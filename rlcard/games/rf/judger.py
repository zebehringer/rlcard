class RFJudger:

    @staticmethod
    def is_game_over(players):
        ''' The game ends when any player's cup is empty

        Args:
            players (list): The list of players who play the game

        Returns:
            (bool): True if any cup is empty
        '''
        return any(not p.chips_out for p in players)

    @staticmethod
    def pot_chips(players):
        ''' Count each player's own chips in the pot

        Args:
            players (list): The list of players who play the game

        Returns:
            (list): the number of chips of each player's color in the pot, by player id
        '''
        pot = [c for p in players for c in p.chips_in]
        return [pot.count(p.player_id) for p in players]

    @staticmethod
    def judge_winner(players, ender):
        ''' Judge the winner of the game: the player with the most chips of their color in the pot.
        On a tie, the player who ended the game wins if they are tied, otherwise the next
        tied player in turn order after them

        Args:
            players (list): The list of players who play the game
            ender (int): the id of the player whose turn ended the game

        Returns:
            (int): The player id of the winner
        '''
        counts = RFJudger.pot_chips(players)
        best = max(counts)
        n = len(players)
        return next(i % n for i in range(ender, ender + n) if counts[i % n] == best)

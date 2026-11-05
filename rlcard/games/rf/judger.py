
class RFJudger:

    @staticmethod
    def judge_winner(players):
        ''' Judge the winner of the game

        Args:
            players (list): The list of players who play the game

        Returns:
            (list): The player id of the winner
        '''
        winners = []
        for idx, p in enumerate(players):
            if not p.chips_out:
                winners.append(idx)
        return winners

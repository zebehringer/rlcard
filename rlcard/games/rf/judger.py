
class RFJudger:

    @staticmethod
    def judge_winner(players, np_random):
        ''' Judge the winner of the game

        Args:
            players (list): The list of players who play the game

        Returns:
            (list): The player id of the winner
        '''
        winners = []
        for idx, item in enumerate(players):
            if item.chips == 0:
                winners.append(idx)
        return winners

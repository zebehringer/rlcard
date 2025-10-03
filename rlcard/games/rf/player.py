
class RFPlayer:

    def __init__(self, player_id, np_random):
        ''' Initilize a player.

        Args:
            player_id (int): The id of the player
        '''
        self.np_random = np_random
        self.player_id = player_id
        self.hand = []
        self.chips_in = []
        self.chips_out = []
        for i in range(7):
            self.chips_out.append(player_id)

    def get_player_id(self):
        ''' Return the id of the player
        '''

        return self.player_id

    def deposit_chip(self):
        for i,c in enumerate(self.chips_out):
            if c == self.player_id:
                self.chips_in.append(c)
                del self.chips_out[i]
                return True
        return False

    def undeposit_chip(self):
        if self.chips_in:
            self.chips_out.append(self.chips_in.pop())

    def count_chips(self, chips):
        count = 0
        for c in chips:
            if c == self.player_id:
                count = count + 1
        return count

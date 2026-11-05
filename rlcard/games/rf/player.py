
class RFPlayer:

    def __init__(self, player_id, np_random):
        ''' Initilize a player.

        Args:
            player_id (int): The id of the player
        '''
        self.np_random = np_random
        self.player_id = player_id
        self.hand = []
        # chips_out is the player's cup: their 7 chips start here, and a player
        # with an empty cup wins. chips_in holds the chips they deposited into the pot.
        self.chips_in = []
        self.chips_out = []
        for i in range(7):
            self.chips_out.append(player_id)

    def get_player_id(self):
        ''' Return the id of the player
        '''

        return self.player_id

    def deposit_chip(self):
        ''' Move one of this player's own chips from their cup to the pot

        Returns:
            (bool): True if a chip was deposited
        '''
        for i,c in enumerate(self.chips_out):
            if c == self.player_id:
                self.chips_in.append(c)
                del self.chips_out[i]
                return True
        return False

    def pick_chip_to_give(self):
        ''' Choose the chip this player gives away when a king makes them give one.
        Other players' chips go first, since this player can't deposit them.

        Returns:
            (int): the owner id of the chip, or None if the cup is empty
        '''
        if not self.chips_out:
            return None
        return next((c for c in self.chips_out if c != self.player_id), self.player_id)

    def take_back_chip(self, other, to_pot=False):
        ''' Take one of this player's chips out of another player's cup

        Args:
            other (RFPlayer): the player whose cup holds the chip
            to_pot (bool): False returns the chip to this player's cup,
                True deposits it into the pot

        Returns:
            (bool): True if a chip was moved
        '''
        for i, c in enumerate(other.chips_out):
            if c == self.player_id:
                del other.chips_out[i]
                (self.chips_in if to_pot else self.chips_out).append(c)
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

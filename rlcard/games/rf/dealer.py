
class RFDealer:
    ''' Initialize a RF dealer class
    '''
    def __init__(self, np_random, cards):
        self.np_random = np_random
        self.deck = cards.copy()
        self.shuffle()

    def shuffle(self):
        ''' Shuffle the deck
        '''
        self.np_random.shuffle(self.deck)

    def deal_cards(self, player, num):
        ''' Deal some cards from deck to one player

        Args:
            player (object): The object of Player
            num (int): The number of cards to be dealed
        '''
        for _ in range(num):
            player.hand.append(self.deck.pop())

    def flip_top_card(self):
        ''' Flip top card when a new game starts

        Returns:
            (object): The object of RFCard at the top of the deck
        '''
        top_card = self.deck.pop()
        return top_card

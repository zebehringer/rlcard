from termcolor import colored
from rlcard.utils.utils import print_card

def split_action(action):
    ''' Split a card action into the card string and where it goes,
    for example 'k-s_p2' -> ('k-s', 'p2') and 'j_thr' -> ('j', 'thr')
    '''
    card, where = action.rsplit('_', 1)
    return card, where


class RFCard:

    info = {'type':  ['number', 'royal', 'action', 'wild'],
            'suit': ['s', 'd', 'h', 'c'],
            'trait': ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'q', 'k', 'w', 'j', 's', 'a']
            }

    def __init__(self, card_type, trait, suit = None):
        ''' Initialize the class of RFCard

        Args:
            card_type (str): The type of card
            suit (str): The suit of card
            trait (str): The trait of card
        '''
        self.type = card_type
        self.suit = suit
        self.trait = trait
        self.str = self.get_str()
        self.rank = RFCard.info['trait'].index(str(trait))

    def get_str(self):
        ''' Get the string representation of card

        Return:
            (str): The string of card's suit and trait
        '''
        if self.suit == None:
            return str(self.trait)
        else:
            return str(self.trait) + '-' + str(self.suit)

    @staticmethod
    def print_actions(actions):
        if isinstance(actions, str):
            actions = [actions]
        for i, action in enumerate(actions):
            if action == 'draw_deck':
                print('Flip from the deck', end='')
                continue
            if action == 'draw_discard':
                print('Take the top discard', end='')
                continue
            if action.startswith('take_p'):
                print('Take a chip back from player '+action[len('take_p'):]+'\'s cup', end='')
                continue
            card, where = split_action(action)
            if where == 'h':
                print('Hold '+card, end='')
            elif where.startswith('rt'):
                print(card+': replace track card '+where[2:], end='')
            elif where == 'thr':
                print(card+': replace throne', end='')
            elif where.startswith('p'):
                print(card+': replace player '+where[1:]+'\'s royal', end='')
            elif where == 'd':
                print(card+': discard', end='')

    @staticmethod
    def print_cards(cards):
        ''' Print out card in a nice form

        Args:
            card (str or list): The string form or a list of a RF card
        '''
        if isinstance(cards, str):
            cards = [cards]
        for i, card in enumerate(cards):
            if card == 's':
                print('---Skip---', end='')
            elif card == 'a':
                print('---Ace in the hole---', end='')
            elif card == 'j':
                print('---Jack---', end='')
            else:
                trait, suit = card.split('-')
                print_card((suit+trait).upper())

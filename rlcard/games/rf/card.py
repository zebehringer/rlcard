from termcolor import colored
from rlcard.utils.utils import print_card

class RFCard:

    info = {'type':  ['number', 'royal', 'action', 'wild'],
            'suit': ['s', 'd', 'h', 'c'],
            'trait': ['2', '3', '4', '5', '6', '7', '8', '9', 'T',
                      's', 'q', 'k', 'a', 'w']
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
            if '_rt' in action:
                print('Replace track card '+action[6:], end='')
            elif '_thr' in action:
                print('Replace throne', end='')
            elif '_p' in action:
                print('Replace player '+action[5:]+'\'s royal', end='')
            elif '_d' in action:
                print('Discard')

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
            else:
                trait, suit = card.split('-')
                print_card((suit+trait).upper())

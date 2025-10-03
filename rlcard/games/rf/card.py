from termcolor import colored

class RFCard:

    info = {'type':  ['number', 'royal', 'action', 'wild'],
            'suit': ['s', 'd', 'h', 'c'],
            'trait': ['2', '3', '4', '5', '6', '7', '8', '9', '10',
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
            trait, suit = card.split('-')
            if trait == 's':
                trait = 'Skip'
            elif trait == 'a':
                trait = 'Ace'
            elif trait == 'q':
                trait = 'Queen'
            elif trait == 'k':
                trait = 'King'
            elif trait == 'w':
                trait = 'Wild'

            if trait == 'Ace' or trait == 'Skip':
                print(trait, end='')
            elif suit == 'h' or suit == 'd':
                print(colored(trait, 'red'), end='')
            else:
                print(colored(trait, 'white'), end='')

            if i < len(cards) - 1:
                print(', ', end='')

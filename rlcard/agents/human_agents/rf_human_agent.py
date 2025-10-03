from rlcard.games.rf.card import RFCard
from rlcard.utils.utils import print_card

class HumanAgent(object):
    ''' A human agent for RF. It can be used to play against trained models
    '''

    def __init__(self, num_actions):
        ''' Initilize the human agent

        Args:
            num_actions (int): the size of the ouput action space
        '''
        self.use_raw = True
        self.num_actions = num_actions

    @staticmethod
    def step(state):
        ''' Human agent will display the state and make decisions through interfaces

        Args:
            state (dict): A dictionary that represents the current state

        Returns:
            action (int): The action decided by human
        '''
        print(state['raw_obs'])
        _print_state(state['raw_obs'], state['action_record'])
        choice = input('>> You choose action (integer): ')
        while True:
            while not choice.isdigit():
                print('Action illegal...')
                choice = input('>> Re-choose action (integer): ')
            action = int(choice)
            if action >= 0 and action < len(state['legal_actions']):
                return state['raw_legal_actions'][action]
            print('Action illegal...')
            choice = input('>> Re-choose action (integer): ')

    def eval_step(self, state):
        ''' Predict the action given the curent state for evaluation. The same to step here.

        Args:
            state (numpy.array): an numpy array that represents the current state

        Returns:
            action (int): the action predicted (randomly chosen) by the random agent
        '''
        return self.step(state), {}

def _print_state(state, action_record):
    ''' Print out the state of a given player

    Args:
        player (int): Player id
    '''
    _action_list = []
    for i in range(1, len(action_record)+1):
        if action_record[-i][0] == state['current_player']:
            break
        _action_list.insert(0, action_record[-i])
    for pair in _action_list:
        print('>> Player', pair[0], 'chooses ', end='')
        _print_action(pair[1])
        print('')

    print('\n=============== Your Hand ===============')
    RFCard.print_cards(state['hand'])
    print('\n=============== Your Chips ==============')
    print('out: {}, in: {}'.format(state['chips_out'],state['chips_in']))
    print('\n=============== The Track ===============')
    cards = []
    for card in state['track']:
        trait, suit = card.split('-')
        cards.append((suit+trait).upper())
    print_card(cards)
    print('')
    print('=============== Last Card ===============')
    RFCard.print_cards(state['target'])
    print('')
    print('========== Players Card Number ===========')
    for i in range(state['num_players']):
        if i != state['current_player']:
            print('Player {} has {} cards.'.format(i, state['num_cards'][i]))
    print('======== Actions You Can Choose =========')
    for i, action in enumerate(state['legal_actions']):
        print(str(i)+': ', end='')
        RFCard.print_actions(action)
        if i < len(state['legal_actions']) - 1:
            print(', ', end='')
    print('\n')

def _print_action(action):
    ''' Print out an action in a nice form

    Args:
        action (str): A string a action
    '''
    RFCard.print_actions(action)

import numpy as np
from collections import OrderedDict

from rlcard.envs import Env
from rlcard.games.rf import Game
from rlcard.games.rf.utils import encode_hand, encode_target, encode_chips
from rlcard.games.rf.utils import cards2list

DEFAULT_GAME_CONFIG = {
        'game_num_players': 4,
        }

class RFEnv(Env):

    def __init__(self, config):
        self.name = 'rf'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = Game()
        super().__init__(config)
        self.num_planes = 8 # or if including all player royals in each player encoding: 7 + self.num_players # + self.num_players if encoding chips
        self.state_shape = [[self.num_planes, 4, 12] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        obs = np.zeros((self.num_planes, 4, 12), dtype=int)
        encode_target(obs[0], state['target'])
        encode_target(obs[1], state['throne'].str)
        encode_target(obs[2], state['player_royal'])
        for i,card in enumerate(state['track']):
            encode_target(obs[3+i], card)
        #for i,player in enumerate(self.game.players):
        #    encode_target(obs[7+i], player.royal.str)
            # chips are just a byproduct of card choices, not necessarily a choice in themself
            #encode_chips(obs[7+self.num_players+i], player.chips_in)
        
        #obs = np.zeros((4, 4, 288), dtype=int)
        #encode_hand(obs[:3], state['hand'])
        #encode_target(obs[3], state['target'])
        legal_action_id = self._get_legal_actions()
        extracted_state = {
            'obs': obs,
            'legal_actions': legal_action_id,
            'raw_obs': state,
            'raw_legal_actions': [a for a in state['legal_actions']],
            'action_record': self.action_recorder
        }
        return extracted_state

    def get_payoffs(self):
        return np.array(self.game.get_payoffs())

    def _decode_action(self, action_id):
        legal_ids = self._get_legal_actions()
        if action_id in legal_ids:
            return self.game.action_space[action_id]
        return self.game.action_space[np.random.choice(legal_ids)]

    def _get_legal_actions(self):
        legal_actions = self.game.get_legal_actions()
        legal_ids = {self.game.action_space.index(action): None for action in legal_actions}
        return OrderedDict(legal_ids)

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        state = {}
        state['num_players'] = self.num_players
        state['hand_cards'] = [cards2list(player.hand)
                               for player in self.game.players]
        state['track'] = cards2list(self.game.round.track)
        state['played_cards'] = cards2list(self.game.round.played_cards)
        state['target'] = self.game.round.target.str
        state['current_player'] = self.game.round.current_player
        state['legal_actions'] = self.game.round.get_legal_actions(
            self.game.players, state['current_player'])
        return state

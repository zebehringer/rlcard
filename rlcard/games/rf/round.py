from rlcard.games.rf.card import RFCard
from rlcard.games.rf.utils import cards2list


class RFRound:

    def __init__(self, dealer, num_players, np_random):
        ''' Initialize the round class

        Args:
            dealer (object): the object of RFDealer
            num_players (int): the number of players in game
        '''
        self.np_random = np_random
        self.dealer = dealer
        self.target = None
        self.current_player = 0
        self.num_players = num_players
        self.played_cards = []
        self.is_over = False
        self.winner = None
    
    def flip_top_card(self):
        ''' Flip the top card of the card pile

        Returns:
            (object of RFCard): the top card in game

        '''
        top = self.dealer.flip_top_card()
        self.target = top
        self.played_cards.append(top)
        return top

    def proceed_round(self, players, action):
        ''' Call other Classes' functions to keep one round running

        Args:
            player (object): object of RFPlayer
            action (str): string of legal action
        '''    
        self.current_player = (self.current_player + 1) % self.num_players

        # replace deck if there is no card in draw pile
        if not self.dealer.deck:
            self.replace_deck()
            #self.is_over = True
            #self.winner = RFJudger.judge_winner(players)
            #return None

        while True:
            card = self.dealer.deck.pop()
            self.target = card
            self.played_cards.append(card)

            if card.type == 'action':
                if card.trait == 's':
                    self.current_player = (self.current_player + 2) % self.num_players
                    continue
                elif card.trait == 'a':
                    #self.current_player.deposit_chip()
                    self.current_player = (self.current_player + 1) % self.num_players
                    continue

            break

    def get_legal_actions(self, players, player_id):
        legal_actions = []
        target = self.target
        if target != None:
            if target.type == 'wild' or target.type == 'number':
                for tc in range(5):
                    legal_actions.append(target.str+'_rt'+str(tc))
                legal_actions.append(target.str+'_d')
            elif target.type == 'royal':
                legal_actions.append(target.str+'_thr')
                for p in players:
                    legal_actions.append(target.str+'_p'+str(p.player_id))
                legal_actions.append(target.str+'_d')

        return legal_actions

    def get_state(self, players, player_id):
        ''' Get player's state

        Args:
            players (list): The list of RFPlayer
            player_id (int): The id of the player
        '''
        state = {}
        player = players[player_id]
        state['hand'] = cards2list(player.hand)
        state['target'] = '' if self.target == None else self.target.str
        state['played_cards'] = cards2list(self.played_cards)
        state['legal_actions'] = self.get_legal_actions(players, player_id)
        state['num_cards'] = []
        for player in players:
            state['num_cards'].append(len(player.hand))
        return state

    def replace_deck(self):
        ''' Add cards have been played to deck
        '''
        self.dealer.deck.extend(self.played_cards)
        self.dealer.shuffle()
        self.played_cards = []

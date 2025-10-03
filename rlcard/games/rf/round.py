from rlcard.games.rf.card import RFCard as Card
from rlcard.games.rf.judger import RFJudger as Judger
from rlcard.games.rf.utils import cards2list, evaluate_cards


class RFRound:

    def __init__(self, dealer, players, np_random):
        ''' Initialize the round class

        Args:
            dealer (object): the object of RFDealer
            players (array): the players in game
        '''
        self.np_random = np_random
        self.dealer = dealer
        self.target = None
        self.current_player = 0
        self.players = players
        self.played_cards = []
        self.is_over = False
        self.winner = None
        self.track = []
        for i in range(5):
            while True:
                card = self.dealer.deck.pop()
                if card.type == 'number' or card.type == 'wild':
                    self.track.append(card)
                    break
                self.played_cards.append(card)
        self.replace_deck()
        while True:
            card = self.dealer.deck.pop()
            if card.trait == 'k' or card.trait == 'q':
                self.throne = card
                break
            self.played_cards.append(card)
        for p in players:
            while True:
                card = self.dealer.deck.pop()
                if card.trait == 'k' or card.trait == 'q':
                    p.royal = card
                    break
                self.played_cards.append(card)
        self.replace_deck()
        
    
    def flip_top_card(self):
        ''' Flip the top card of the card pile

        Returns:
            (object of RFCard): the top card in game

        '''
        while True:
            if not self.dealer.deck:
                self.replace_deck()
    
            card = self.dealer.deck.pop()
            self.target = card
            self.played_cards.append(card)

            if card.type == 'action':
                if card.trait == 's':
                    # there does not seem to be a great way to visualize a skip :(
                    #print('>> Player {} got skipped'.format(self.players[(self.current_player+1) % len(self.players)].player_id))
                    self.current_player = (self.current_player + 2) % len(self.players)
                    continue
                elif card.trait == 'a':
                    # there does not seem to be a great way to visualize an ace :(
                    if self.players[self.current_player].deposit_chip():
                        None
                        #print('>> Player {} deposited 1 chip'.format(self.players[(self.current_player+1) % len(self.players)].player_id))
                    self.current_player = (self.current_player + 1) % len(self.players)
                    continue

            break
        return card

    def proceed_round(self, players, action):
        ''' Call other Classes' functions to keep one round running

        Args:
            player (object): object of RFPlayer
            action (str): string of legal action
        '''
        if '_rt' in action:
            tIdx = int(action[6:])
            self.played_cards.append(self.track[tIdx])
            self.track[tIdx] = self.target

            e = evaluate_cards(self.track)
            if e is not None and 'f' in e:
                self.players[self.current_player].deposit_chip()
                if 's' in e:
                    self.players[self.current_player].deposit_chip()
        elif '_thr' in action:
            self.played_cards.append(self.throne)
            self.throne = self.target
        elif '_p' in action:
            pIdx = int(action[5:])
            self.played_cards.append(self.players[pIdx].royal)
            self.players[pIdx].royal = self.target
        elif '_d' in action:
            self.played_cards.append(self.target)

        winners = Judger.judge_winner(self.players)
        if len(winners) > 0:
            self.winner = winners.pop()
            self.is_over = True
        else:
            self.flip_top_card()
            self.current_player = (self.current_player + 1) % len(self.players)

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
        state['throne'] = self.throne
        state['royals'] = cards2list([p.royal for p in players])
        state['player_royal'] = player.royal.str
        state['track'] = cards2list(self.track)
        state['hand'] = cards2list(player.hand)
        state['chips_out'] = player.chips_out
        state['chips_in'] = player.count_chips(player.chips_in)
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

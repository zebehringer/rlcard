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

            if card.type == 'action':
                # other cards go to the pile once the player decides where they go
                self.played_cards.append(card)
                if card.trait == 's':
                    # there does not seem to be a great way to visualize a skip :(
                    #print('>> Player {} got skipped'.format(self.players[self.current_player].player_id))
                    self.current_player = (self.current_player + 1) % len(self.players)
                    continue
                elif card.trait == 'a':
                    # there does not seem to be a great way to visualize an ace :(
                    if self.players[self.current_player].deposit_chip():
                        #print('>> Player {} deposited 1 chip'.format(self.players[self.current_player].player_id))
                        if self.check_winner():
                            break
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
            if self.target.trait == 'k':
                self.apply_king(self.target.suit, None)
        elif '_p' in action:
            pIdx = int(action[5:])
            self.played_cards.append(self.players[pIdx].royal)
            self.players[pIdx].royal = self.target
            if self.target.trait == 'k':
                self.apply_king(self.target.suit, pIdx)
        elif '_d' in action:
            self.played_cards.append(self.target)

        if not self.check_winner():
            self.current_player = (self.current_player + 1) % len(self.players)
            self.flip_top_card()

    def apply_king(self, suit, pIdx):
        ''' Apply the one-time effect of a king that was just placed

        Args:
            suit (str): the king's suit
            pIdx (int): the player the king was placed in front of, or None for the throne
        '''
        players = self.players
        n = len(players)
        placer = self.current_player
        # on the throne the effect applies to everyone; KD skips the player who placed it
        if pIdx is not None:
            affected = [pIdx]
        elif suit == 'd':
            affected = [i for i in range(n) if i != placer]
        else:
            affected = list(range(n))

        if suit == 'd':
            for i in affected:
                self.retrieve_chip(i)
        else:
            gifts = []
            for i in affected:
                if suit == 's':
                    others = [j for j in range(n) if j != i]
                    to = others[self.np_random.randint(len(others))]
                elif suit == 'c':
                    # play passes to the left, so the next player in turn order is on the left
                    to = (i + 1) % n
                else:
                    to = (i - 1) % n
                chip = players[i].pick_chip_to_give()
                if chip is not None:
                    gifts.append((i, to, chip))
            # everyone gives at the same time, so a chip received can't be passed on
            for i, to, chip in gifts:
                players[i].chips_out.remove(chip)
            for i, to, chip in gifts:
                players[to].chips_out.append(chip)

        # KD in front of an opponent: the placer also moves one of their own chips
        # from that opponent's cup into the pot
        if suit == 'd' and pIdx is not None and pIdx != placer:
            players[placer].take_back_chip(players[pIdx], to_pot=True)

    def retrieve_chip(self, pIdx):
        ''' Return one of a player's chips from a random other cup to their own cup

        Args:
            pIdx (int): the player retrieving a chip
        '''
        p = self.players[pIdx]
        holders = [o for o in self.players if o is not p and p.player_id in o.chips_out]
        if holders:
            p.take_back_chip(holders[self.np_random.randint(len(holders))])

    def check_winner(self):
        ''' End the game if any player's cup is empty

        Returns:
            (bool): True if the game is over
        '''
        winners = Judger.judge_winner(self.players)
        if len(winners) > 0:
            self.winner = winners.pop()
            self.is_over = True
        return self.is_over

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
        # chips left in this player's cup, by owner id, and the number they deposited
        state['chips_out'] = list(player.chips_out)
        state['chips_in'] = len(player.chips_in)
        # chips left in every player's cup, starting with this player and going in turn order
        seats = [players[(player_id + i) % len(players)] for i in range(len(players))]
        state['seat_chips_out'] = [len(p.chips_out) for p in seats]
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

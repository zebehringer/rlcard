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
        # QD extra card drawn this turn, and whether QD applies to the current player
        self.extras = []
        self.qd_turn = False
        # 'draw' (QH choice), 'play' or 'keep' (QD choice of the card to hold)
        self.phase = 'play'
        self.current_player = 0
        self.players = players
        self.played_cards = []
        self.is_over = False
        # the player id of the winner, set when the game ends
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
        
    
    def draw_card(self):
        ''' Pop the top card of the deck, reshuffling the discard pile in when it runs out
        '''
        if not self.dealer.deck:
            self.replace_deck()
        return self.dealer.deck.pop()

    def queens(self, pIdx):
        ''' Return the suits of the queens that apply to a player: the throne's and their own.
        There is one queen per suit, so the two are always different

        Args:
            pIdx (int): the player id

        Returns:
            (list): queen suits
        '''
        suits = []
        if self.throne.trait == 'q':
            suits.append(self.throne.suit)
        royal = self.players[pIdx].royal
        if royal.trait == 'q':
            suits.append(royal.suit)
        return suits

    def deposit(self, pIdx, count):
        ''' Deposit chips for a player, applying QS (blocked) and QC (+1 each)

        Args:
            pIdx (int): the player depositing
            count (int): the number of chips the deposit is worth before queens
        '''
        queens = self.queens(pIdx)
        if 's' in queens:
            return
        if 'c' in queens:
            count += 1
        for _ in range(count):
            self.players[pIdx].deposit_chip()

    def can_draw_discard(self, pIdx):
        ''' QH lets a player take the top of the discard pile instead of flipping,
        when that card is not an action card
        '''
        return ('h' in self.queens(pIdx) and len(self.played_cards) > 0
                and self.played_cards[-1].type != 'action')

    def start_turn(self, offer_discard=True):
        ''' Start the current player's turn: offer the discard pile (QH) or flip.
        Skip and Ace are resolved here and pass the turn on.

        Args:
            offer_discard (bool): False when the current player already chose to flip
        '''
        self.target = None
        self.extras = []
        while True:
            if offer_discard and self.can_draw_discard(self.current_player):
                self.phase = 'draw'
                return
            offer_discard = True

            card = self.draw_card()
            if card.type == 'action':
                # other cards go to the pile once the player decides where they go
                self.played_cards.append(card)
                if card.trait == 'a':
                    self.deposit(self.current_player, 1)
                    if self.check_winner():
                        return
                self.current_player = (self.current_player + 1) % len(self.players)
                continue
            self.target = card
            break
        self.begin_play()

    def begin_play(self):
        ''' The target is set. QD draws one extra card.
        Action cards drawn as extras go to the discard pile without effect.
        '''
        self.extras = []
        self.qd_turn = 'd' in self.queens(self.current_player)
        while self.qd_turn and not self.extras:
            card = self.draw_card()
            if card.type == 'action':
                self.played_cards.append(card)
            else:
                self.extras.append(card)
        self.phase = 'play'

    def candidates(self):
        ''' The cards the current player can play: the target, QD extras and their held card
        '''
        cards = [self.target] if self.target is not None else []
        return cards + self.extras + self.players[self.current_player].hand

    def take_candidate(self, card_str):
        ''' Remove a card from wherever it sits among the candidates and return it
        '''
        player = self.players[self.current_player]
        if self.target is not None and self.target.str == card_str:
            card, self.target = self.target, None
            return card
        for pile in (self.extras, player.hand):
            for i, c in enumerate(pile):
                if c.str == card_str:
                    return pile.pop(i)
        raise ValueError('{} is not playable'.format(card_str))

    def proceed_round(self, players, action):
        ''' Apply the current player's action

        Args:
            players (list): the RFPlayers
            action (str): string of legal action
        '''
        player = self.players[self.current_player]
        if action == 'draw_deck':
            self.start_turn(offer_discard=False)
            return
        if action == 'draw_discard':
            self.target = self.played_cards.pop()
            self.begin_play()
            return
        if self.phase == 'keep':
            kept = self.take_candidate(action[:3])
            self.played_cards.extend(self.candidates())
            self.target = None
            self.extras = []
            player.hand = [kept]
            self.end_turn()
            return

        held = list(player.hand)
        card = self.take_candidate(action[:3])
        if '_rt' in action:
            tIdx = int(action[6:])
            self.played_cards.append(self.track[tIdx])
            self.track[tIdx] = card

            e = evaluate_cards(self.track)
            if e is not None and 'f' in e:
                self.deposit(self.current_player, 2 if 's' in e else 1)
        elif '_thr' in action:
            self.played_cards.append(self.throne)
            self.throne = card
            if card.trait == 'k':
                self.apply_king(card.suit, None)
        elif '_p' in action:
            pIdx = int(action[5:])
            self.played_cards.append(self.players[pIdx].royal)
            self.players[pIdx].royal = card
            if card.trait == 'k':
                self.apply_king(card.suit, pIdx)
        elif '_d' in action:
            self.played_cards.append(card)

        if self.check_winner():
            return

        leftover = self.candidates()
        if self.qd_turn and len(leftover) > 1:
            # QD: the player chooses which card to hold
            self.phase = 'keep'
            return
        self.target = None
        self.extras = []
        if self.qd_turn:
            # QD: the one card left is held
            player.hand = leftover
        else:
            # without QD a player only keeps the card they were already holding
            player.hand = [c for c in leftover if c in held]
            self.played_cards.extend(c for c in leftover if c not in held)
        self.end_turn()

    def end_turn(self):
        ''' Pass the turn on unless the game is over
        '''
        if not self.check_winner():
            self.current_player = (self.current_player + 1) % len(self.players)
            self.start_turn()

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
        # QS blocks this like any other deposit
        if suit == 'd' and pIdx is not None and pIdx != placer and 's' not in self.queens(placer):
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
        ''' End the game if any player's cup is empty. The winner is the player with
        the most chips of their color in the pot; ties go to the current player, who
        ended the game, then to the next tied player in turn order

        Returns:
            (bool): True if the game is over
        '''
        if Judger.is_game_over(self.players):
            self.winner = Judger.judge_winner(self.players, self.current_player)
            self.is_over = True
        return self.is_over

    def get_legal_actions(self, players, player_id):
        if self.phase == 'draw':
            return ['draw_deck', 'draw_discard']
        if self.phase == 'keep':
            return [c.str+'_h' for c in self.candidates()]
        legal_actions = []
        for card in self.candidates():
            if card.type == 'wild' or card.type == 'number':
                for tc in range(5):
                    legal_actions.append(card.str+'_rt'+str(tc))
                legal_actions.append(card.str+'_d')
            elif card.type == 'royal':
                legal_actions.append(card.str+'_thr')
                for p in players:
                    legal_actions.append(card.str+'_p'+str(p.player_id))
                legal_actions.append(card.str+'_d')
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
        state['extras'] = cards2list(self.extras)
        state['discard_top'] = self.played_cards[-1].str if self.played_cards else ''
        state['phase'] = self.phase
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

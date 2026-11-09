from rlcard.games.rf.card import RFCard as Card, split_action
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
        # 'draw' (QH choice), 'play', 'keep' (QD choice of the card to hold)
        # or 'retrieve' (KD choice of the cup to take a chip back from)
        self.phase = 'play'
        # KD: players still to take a chip back, and the opponent whose cup the placer deposits from
        self.retrievers = []
        self.kd_deposit = None
        # whose turn it is, while a KD retrieval hands the decision to someone else,
        # and the card they were holding when they played
        self.turn_player = 0
        self.held = []
        self.current_player = 0
        self.players = players
        self.played_cards = []
        self.is_over = False
        # the player id of the winner, set when the game ends
        self.winner = None
        self.track = []
        self.deal_track()
        self.replace_deck()
        # the throne and each player's spot get a royal: a king, queen or the Jack
        while True:
            card = self.dealer.deck.pop()
            if card.type == 'royal':
                self.throne = card
                break
            self.played_cards.append(card)
        for p in players:
            while True:
                card = self.dealer.deck.pop()
                if card.type == 'royal':
                    p.royal = card
                    break
                self.played_cards.append(card)
        self.replace_deck()
        
    
    def deal_track(self):
        ''' Deal 5 number or wild cards onto an empty track.
        Other cards drawn on the way go to the discard pile with no effect
        '''
        while len(self.track) < 5:
            card = self.draw_card()
            if card.type == 'number' or card.type == 'wild':
                self.track.append(card)
            else:
                self.played_cards.append(card)

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

    def jacked(self, pIdx):
        ''' The Jack on the throne or in front of a player blocks their deposits
        '''
        return self.throne.trait == 'j' or self.players[pIdx].royal.trait == 'j'

    def shielded(self, pIdx):
        ''' QS in front of a player shields them from kings
        '''
        royal = self.players[pIdx].royal
        return royal.trait == 'q' and royal.suit == 's'

    def deposit(self, pIdx, count):
        ''' Deposit chips for a player, applying the Jack (blocked) and QC (+1 each)

        Args:
            pIdx (int): the player depositing
            count (int): the number of chips the deposit is worth before queens
        '''
        if self.jacked(pIdx):
            return
        if 'c' in self.queens(pIdx):
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
            kept = self.take_candidate(split_action(action)[0])
            self.played_cards.extend(self.candidates())
            self.target = None
            self.extras = []
            player.hand = [kept]
            self.end_turn()
            return
        if self.phase == 'retrieve':
            # KD: the player taking a chip back chose the cup
            holder = int(action[len('take_p'):])
            player.take_back_chip(self.players[holder])
            self.retrievers.pop(0)
            self.next_retrieval()
            return

        self.turn_player = self.current_player
        self.held = list(player.hand)
        card_str, where = split_action(action)
        card = self.take_candidate(card_str)
        if where.startswith('rt'):
            tIdx = int(where[2:])
            self.played_cards.append(self.track[tIdx])
            self.track[tIdx] = card

            e = evaluate_cards(self.track)
            if e is not None and 'f' in e:
                count = 2 if 's' in e else 1
                # a royal on the throne in the flush's suit adds 1 (the Jack has no suit)
                if self.throne.suit == self.track[0].suit:
                    count += 1
                self.deposit(self.current_player, count)
        elif where == 'thr':
            self.played_cards.append(self.throne)
            self.throne = card
            if card.trait == 'k':
                self.apply_king(card.suit, None)
        elif where.startswith('p'):
            pIdx = int(where[1:])
            # a QS knocked off by a king still shields the player from that king
            was_shielded = self.shielded(pIdx)
            self.played_cards.append(self.players[pIdx].royal)
            self.players[pIdx].royal = card
            if card.trait == 'k' and not was_shielded:
                self.apply_king(card.suit, pIdx)
        elif where == 'd':
            self.played_cards.append(card)
        self.next_retrieval()

    def retrieval_cups(self, pIdx):
        ''' The cups a player can take one of their chips back from with KD:
        other players' cups that hold one, except cups shielded by QS
        '''
        return [i for i, o in enumerate(self.players)
                if i != pIdx and pIdx in o.chips_out and not self.shielded(i)]

    def next_retrieval(self):
        ''' Work through the players waiting to take a chip back with KD. A player
        with more than one cup to choose from decides (the 'retrieve' phase, even out of turn),
        otherwise it happens on its own. Then play returns to the turn's player
        '''
        while self.retrievers:
            i = self.retrievers[0]
            cups = self.retrieval_cups(i)
            if len(cups) > 1:
                self.current_player = i
                self.phase = 'retrieve'
                return
            if cups:
                self.players[i].take_back_chip(self.players[cups[0]])
            self.retrievers.pop(0)
        self.current_player = self.turn_player
        self.phase = 'play'
        self.finish_play()

    def finish_play(self):
        ''' Finish the turn's play once any KD retrievals are done
        '''
        player = self.players[self.current_player]
        held = self.held
        if self.kd_deposit is not None:
            # KD in front of an opponent: the placer also moves one of their own chips
            # from that opponent's cup into the pot, after the opponent's chip comes back.
            # The Jack blocks this like any other deposit
            pIdx, self.kd_deposit = self.kd_deposit, None
            if not self.jacked(self.current_player):
                player.take_back_chip(self.players[pIdx], to_pot=True)

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
        # QS on the throne cancels kings placed in front of players
        if pIdx is not None and self.throne.trait == 'q' and self.throne.suit == 's':
            return
        if suit == 's' and pIdx is None:
            # shake-up: discard the track and deal a new one. The new track doesn't score
            self.played_cards.extend(self.track)
            self.track = []
            self.deal_track()
            return
        # on the throne the effect applies to everyone; KD skips the player who placed it.
        # Players shielded by QS are left out, and they don't receive chips either
        if pIdx is not None:
            affected = [pIdx]
        elif suit == 'd':
            affected = [i for i in range(n) if i != placer]
        else:
            affected = list(range(n))
        affected = [i for i in affected if not self.shielded(i)]

        if suit == 'd':
            # each player takes a chip back in turn order, starting after the placer
            self.retrievers = sorted(affected, key=lambda i: (i - placer) % n)
            if pIdx is not None and pIdx != placer:
                self.kd_deposit = pIdx
        else:
            gifts = []
            for i in affected:
                if suit == 's':
                    others = [j for j in range(n) if j != i and not self.shielded(j)]
                    if not others:
                        continue
                    to = others[self.np_random.randint(len(others))]
                elif suit == 'c':
                    # play passes to the left, so the next player in turn order is on the left
                    to = (i + 1) % n
                else:
                    to = (i - 1) % n
                if self.shielded(to):
                    continue
                chip = players[i].pick_chip_to_give()
                if chip is not None:
                    gifts.append((i, to, chip))
            # everyone gives at the same time, so a chip received can't be passed on
            for i, to, chip in gifts:
                players[i].chips_out.remove(chip)
            for i, to, chip in gifts:
                players[to].chips_out.append(chip)

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
        if self.phase == 'retrieve':
            return ['take_p'+str(i) for i in self.retrieval_cups(self.current_player)]
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
        # this player's own chips in every player's cup, in the same seat order
        state['seat_own_chips'] = [p.chips_out.count(player_id) for p in seats]
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

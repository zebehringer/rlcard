from rlcard.games.rf.card import RFCard as Card

# a map of color to its index
SUIT_MAP = {'s': 0, 'd': 1, 'h': 2, 'c': 3}

# a map of trait to its index
TRAIT_MAP = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5,
             '8': 6, '9': 7, 'T': 8, 'q': 9, 'k': 10, 'w': 11,
             'a': 12, 's': 13}


def init_deck():
    ''' Generate RF deck of 52 cards
    '''
    deck = []
    card_info = Card.info
    deck.append(Card('action','s'))
    deck.append(Card('action','s'))
    deck.append(Card('action','a'))
    deck.append(Card('action','a'))
    for suit in card_info['suit']:
        # init number cards
        for num in range(2,10):
            deck.append(Card('number', num, suit))
        deck.append(Card('number', 'T', suit))
        
        deck.append(Card('royal', 'q', suit))
        deck.append(Card('royal', 'k', suit))
        deck.append(Card('wild', 'w', suit))

    return deck

def evaluate_cards(cards):
    # check for flush
    last_suit = None
    for card in cards:
        if last_suit is not None and card.suit != last_suit:
            return 's' if is_straight(cards) else None
        last_suit = card.suit
    return 'sf' if is_straight(cards) else 'f'

def is_straight(cards):
    # wilds can stand in for any rank, so the remaining ranks just need to be
    # distinct and fit within a run as long as the hand
    wild_rank = Card.info['trait'].index('w')
    ranks = [c.rank for c in cards if c.rank != wild_rank]
    if len(set(ranks)) != len(ranks):
        return False
    if not ranks:
        return True
    return max(ranks) - min(ranks) < len(cards)

def cards2list(cards):
    ''' Get the corresponding string representation of cards

    Args:
        cards (list): list of RFCards objects

    Returns:
        (string): string representation of cards
    '''
    return [card.str for card in cards]

def encode_target(plane, target):
    ''' Encode target and preserve it into plane

    Args:
        plane (array): 4*12 matrix for all playable cards
        target(str): string of target card
    '''
    target_info = target.split('-')
    if target == 'a' or target == 's':
        return plane
    suit = SUIT_MAP[target_info[1]]
    trait = TRAIT_MAP[target_info[0]]
    plane[suit][trait] = 1

def encode_chips(plane, count):
    ''' Encode a chip count into plane by filling its first count cells

    Args:
        plane (array): 4*12 matrix
        count (int): number of chips
    '''
    plane.flat[:count] = 1

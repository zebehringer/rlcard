import os
import json
import numpy as np
from collections import OrderedDict

import rlcard

from rlcard.games.rf.card import RFCard as Card

# Read required docs
ROOT_PATH = rlcard.__path__[0]

# a map of abstract action to its index and a list of abstract action
#with open(os.path.join(ROOT_PATH, 'games/rf/jsondata/action_space.json'), 'r') as file:
#    ACTION_SPACE = json.load(file, object_pairs_hook=OrderedDict)
#    ACTION_LIST = list(ACTION_SPACE.keys())

# a map of color to its index
SUIT_MAP = {'s': 0, 'd': 1, 'h': 2, 'c': 3}

# a map of trait to its index
TRAIT_MAP = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
             '8': 8, '9': 9, '10': 10, 'skip': 11, 'q': 12, 'k': 13,
             'a': 14, 'w': 15}

WILD = ['w-s', 'w-d', 'w-h', 'w-c']


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
        for num in range(2,11):
            deck.append(Card('number', num, suit))
        
        deck.append(Card('royal', 'q', suit))
        deck.append(Card('royal', 'k', suit))
        deck.append(Card('wild', 'w', suit))

    return deck


def cards2list(cards):
    ''' Get the corresponding string representation of cards

    Args:
        cards (list): list of RFCards objects

    Returns:
        (string): string representation of cards
    '''
    cards_list = []
    for card in cards:
        cards_list.append(card.get_str())
    return cards_list

def hand2dict(hand):
    ''' Get the corresponding dict representation of hand

    Args:
        hand (list): list of string of hand's card

    Returns:
        (dict): dict of hand
    '''
    hand_dict = {}
    for card in hand:
        if card not in hand_dict:
            hand_dict[card] = 1
        else:
            hand_dict[card] += 1
    return hand_dict

def encode_hand(plane, hand):
    ''' Encode hand and represerve it into plane

    Args:
        plane (array): 3*4*15 numpy array
        hand (list): list of string of hand's card

    Returns:
        (array): 3*4*15 numpy array
    '''
    # plane = np.zeros((3, 4, 15), dtype=int)
    plane[0] = np.ones((4, 288), dtype=int)
    hand = hand2dict(hand)
    for card, count in hand.items():
        card_info = card.split('-')
        suit = SUIT_MAP[card_info[1]]
        if card == 'a':
            suit = 4
        elif card == 's':
            suit = 5
        else:
            suit = SUIT_MAP[card_info[1]]
        trait = TRAIT_MAP[card_info[0]]
        if trait >= 13:
            if plane[1][0][trait] == 0:
                for index in range(4):
                    plane[0][index][trait] = 0
                    plane[1][index][trait] = 1
        else:
            plane[0][suit][trait] = 0
            plane[count][suit][trait] = 1
    return plane

def encode_target(plane, target):
    ''' Encode target and represerve it into plane

    Args:
        plane (array):
        target(str): string of target card

    Returns:
        (array): 4*4*288 numpy array
    '''
    target_info = target.split('-')
    if target == 'a' or target == 's':
        return plane
    suit = SUIT_MAP[target_info[1]]
    trait = TRAIT_MAP[target_info[0]]
    plane[suit][trait] = 1
    return plane

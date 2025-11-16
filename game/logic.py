import random
from collections import Counter

SUITS = "CDHS"
RANKS = "23456789TJQKA"
RANK_VALUE = {r: i for i, r in enumerate(RANKS, start=2)}


def make_deck():
    return [r + s for s in SUITS for r in RANKS]


def deal(deck, n):
    return [deck.pop() for _ in range(n)]


def card_ranks(cards):
    ranks = [RANK_VALUE[c[0]] for c in cards]
    ranks.sort(reverse=True)
    return ranks


def is_straight(ranks):
    if ranks == [14, 5, 4, 3, 2]:
        return True
    return all(ranks[i] - 1 == ranks[i + 1] for i in range(len(ranks) - 1))


def is_flush(cards):
    suits = [c[1] for c in cards]
    return len(set(suits)) == 1


def hand_rank(cards):
    ranks = card_ranks(cards)
    counts = Counter(ranks)
    freqs = sorted(counts.values(), reverse=True)
    ordered = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))

    is_st = is_straight(ranks)
    is_fl = is_flush(cards)

    if is_st and is_fl:
        return (8, ranks)
    if freqs == [4, 1]:
        four = ordered[0][0]
        kicker = [r for r in ranks if r != four][0]
        return (7, [four, kicker])
    if freqs == [3, 2]:
        three = ordered[0][0]
        pair = ordered[1][0]
        return (6, [three, pair])
    if is_fl:
        return (5, ranks)
    if is_st:
        return (4, ranks)
    if freqs == [3, 1, 1]:
        three = ordered[0][0]
        kickers = [r for r in ranks if r != three]
        return (3, [three] + kickers)
    if freqs == [2, 2, 1]:
        pair1 = ordered[0][0]
        pair2 = ordered[1][0]
        kicker = [r for r in ranks if r != pair1 and r != pair2][0]
        high_pair, low_pair = max(pair1, pair2), min(pair1, pair2)
        return (2, [high_pair, low_pair, kicker])
    if freqs == [2, 1, 1, 1]:
        pair = ordered[0][0]
        kickers = [r for r in ranks if r != pair]
        return (1, [pair] + kickers)
    return (0, ranks)


def hand_description(cards):
    category, _ = hand_rank(cards)
    names = {
        8: "Escalera de color",
        7: "Póker",
        6: "Full",
        5: "Color",
        4: "Escalera",
        3: "Trío",
        2: "Doble par",
        1: "Par",
        0: "Carta alta",
    }
    return names.get(category, "Desconocida")


def best_hand(hands_by_player):
    best_score = None
    winners = []
    for nick, cards in hands_by_player.items():
        score = hand_rank(cards)
        if best_score is None or score > best_score:
            best_score = score
            winners = [nick]
        elif score == best_score:
            winners.append(nick)
    return best_score, winners
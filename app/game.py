import random

values = ['A','2','3','4','5','6','7','8','9','T','J','Q']
suits = ['H','S']

class Card:
    def __init__(self, val, suit):
        self.val = val
        self.suit = suit
        self.name = val+suit
        self.flipped = True if random.randint(1,6)==1 else False # TODO actually do something legit here

    def __str__(self):
        if self.flipped:
            return self.name
        else:
            return '_'+self.suit

    def flip(self):
        self.flipped = True

class Hand:
    def __init__(self, cards):
        self.cards = cards
        self.cards.sort(key = lambda card: values.index(card.val)) 

    def __str__(self):
        return ' '.join(map(str,self.cards))

class Master: # TODO can this be merged into the Game class?
    def __init__(self, hands=None, players=None):
        deck = []
        for val in values:
            for suit in suits:
                deck.append(Card(val,suit))
        random.shuffle(deck)

        self.hands = []
        for i in range(4):
            self.hands.append(Hand(deck[i*6:i*6+6]))
        if hands:
            self.hands = hands

        self.players = players

    def __str__(self):
        return '\n'.join(map(str,self.hands))

    def flip(self, hand, card):
        self.hands[hand].cards[card].flip()

    def grid(self):
        res = [None]*64
        for i in range(6):
            res[57+i] = self.hands[0].cards[i]
            res[57+i].flipped = True
        res[50] = 'R'+self.players[0]
        for i in range(6):
            res[55-8*i] = self.hands[1].cards[i]
        res[46] = 'U'+self.players[1]
        for i in range(6):
            res[6-i] = self.hands[2].cards[i]
        res[13] = 'L'+self.players[2]
        for i in range(6):
            res[8+8*i] = self.hands[3].cards[i]
        res[17] = 'D'+self.players[3]
        return res

'''
master = Master()
print(master)
while True:
    a,b = map(int,input().split())
    master.flip(a,b)
    print(master)
'''

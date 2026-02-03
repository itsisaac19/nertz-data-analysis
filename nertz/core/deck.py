import random
from typing import List, Optional
from nertz.models.cards import PlayingCard
from nertz.models.cards import SUITS, RANKS

"""The DeckManager class will manage a standard 52-card deck, including shuffling
and dealing cards to player piles. When cards are moved out of the deck,
all operations will modify the deck in place, and should only reference
the original cards in the deck. For example, playing a card from the river 
to a foundation should remove it from the river list, append it to the foundation,
but not create a new PlayingCard instance."""
class DeckManager:
    cards_in_deck: List[Optional[PlayingCard]]
    """Main deck of remaining cards to be dealt"""

    cards_in_stream: List[Optional[PlayingCard]]
    """Contains the cards flipped in groups of 3 from the deck. 
    The stream accumulates all flipped cards."""

    cards_in_river: List[List[Optional[PlayingCard]]]
    """There are 4 river slots, each holding a nested list of cards"""

    cards_in_nertz: List[Optional[PlayingCard]]
    """The Nertz pile starts with 13 cards dealt face down, only the top card is playable"""

    cards_in_lake: List[Optional[PlayingCard]]
    """The lake pile holds cards played to foundations."""

    def __init__(self, player_index: int = -1):
        self.player_index = player_index
        self.cards_in_deck = []
        self.cards_in_stream = []
        self.cards_in_river = [[] for _ in range(4)]
        self.cards_in_nertz = [None] * 13
        self.cards_in_lake = []
    
    def generate_new_deck(self) -> 'DeckManager':
        for suit in SUITS:
            for rank in RANKS:
                card = PlayingCard(suit, rank, self.player_index)
                self.cards_in_deck.append(card)

        return self

    def shuffle(self) -> 'DeckManager':
        random.shuffle(self.cards_in_deck)

        return self

    def deal_card(self) -> PlayingCard:
        if not self.cards_in_deck:
            raise ValueError("No cards left in deck")
        
        card = self.cards_in_deck.pop()

        return card

    def flip__into_stream(self) -> None:
        """Flip top 3 cards from deck to stream"""

        # If deck is empty, recycle stream back into deck
        if not self.cards_in_deck:
            self.cards_in_deck = self.cards_in_stream.copy()
            self.cards_in_stream = []
            
        for _ in range(3):
            if self.cards_in_deck:
                self.cards_in_stream.append(self.deal_card())
    
    def deal_starting_hand(self) -> 'DeckManager':
        """Deal starting hand: 4 river cards and 13 nertz cards"""
        self.generate_new_deck().shuffle()

        # Deal river cards
        for j in range(4):
            self.cards_in_river[j] = [self.deal_card()]

        # Deal nertz cards
        for j in range(13):
            self.cards_in_nertz[j] = self.deal_card()
        
        # Flip initial stream cards
        self.flip__into_stream()

        return self
    
    @property
    def remaining_cards(self) -> List[PlayingCard]:
        """Get remaining cards in deck (read-only)"""
        return self.cards_in_deck.copy()
    
    @property
    def river_cards(self) -> List[PlayingCard]:
        """Get river cards (read-only)"""
        return self.cards_in_river.copy()
    
    @property
    def nertz_cards(self) -> List[PlayingCard]:
        """Get nertz cards (read-only)"""
        return self.cards_in_nertz.copy()
    
    @property
    def lake_cards(self) -> List[PlayingCard]:
        """Get lake cards (read-only)"""
        return self.cards_in_lake.copy()
    
    @property
    def cards_left(self) -> int:
        """Number of cards remaining in deck"""
        return len(self.cards_in_deck)

    def top_nertz_card(self) -> Optional[PlayingCard]:
        for card in reversed(self.cards_in_nertz):
            if card is not None:
                return card
        return None

    def top_stream_cards(self, count: int = 3) -> list[PlayingCard]:
        if len(self.cards_in_stream) < count:
            # Later we need to handle recycling the stream back into the deck
            # for now, just raise an error
            raise ValueError("Not enough cards in stream")
        
        return [c for c in self.cards_in_stream[-count:] if c is not None]
    
    def river_slot_top_cards(self) -> list[Optional[PlayingCard]]:
        """Get the top card of each river slot"""
        top_cards = []
        for slot in self.cards_in_river:
            if slot:
                top_cards.append(slot[-1])
            else:
                top_cards.append(None)
        return top_cards
    
    

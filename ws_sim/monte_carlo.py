from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Mapping, MutableSequence, Sequence, Tuple


@dataclass(frozen=True)
class DeckConfig:
    total_cards: int
    climax_cards: int
    waiting_room_cards: int = 0
    waiting_room_climax_cards: int = 0

    def __post_init__(self) -> None:
        if self.climax_cards > self.total_cards:
            raise ValueError("climax_cards cannot exceed total_cards")
        if self.total_cards <= 0:
            raise ValueError("total_cards must be positive")
        if self.climax_cards < 0:
            raise ValueError("climax_cards cannot be negative")
        if self.waiting_room_cards < 0:
            raise ValueError("waiting_room_cards cannot be negative")
        if self.waiting_room_climax_cards < 0:
            raise ValueError("waiting_room_climax_cards cannot be negative")
        if self.waiting_room_cards > self.total_cards:
            raise ValueError("waiting_room_cards cannot exceed total_cards")
        if self.waiting_room_climax_cards > self.climax_cards:
            raise ValueError("waiting_room_climax_cards cannot exceed climax_cards")

        deck_size = self.total_cards - self.waiting_room_cards
        deck_climax_cards = self.climax_cards - self.waiting_room_climax_cards
        if deck_climax_cards > deck_size:
            raise ValueError("climax_cards in deck cannot exceed remaining deck size")
        if self.waiting_room_climax_cards > self.waiting_room_cards:
            raise ValueError("waiting_room_climax_cards cannot exceed waiting_room_cards")


class DeckState:
    def __init__(self, config: DeckConfig, rng: random.Random) -> None:
        self.rng = rng
        deck_size = config.total_cards - config.waiting_room_cards
        deck_climax_cards = config.climax_cards - config.waiting_room_climax_cards
        self.deck: MutableSequence[bool] = self._build_shuffled_pile(
            deck_size, deck_climax_cards
        )
        self.waiting_room: MutableSequence[bool] = self._build_shuffled_pile(
            config.waiting_room_cards, config.waiting_room_climax_cards
        )

    def _build_shuffled_pile(self, size: int, climax_cards: int) -> MutableSequence[bool]:
        pile = [True] * climax_cards + [False] * (size - climax_cards)
        self.rng.shuffle(pile)
        return pile

    def draw(self) -> Tuple[bool, bool]:
        refresh_damage = False
        if not self.deck:
            # Refresh: shuffle the waiting room back into a deck.
            self.deck = list(self.waiting_room)
            self.waiting_room = []
            self.rng.shuffle(self.deck)
            refresh_damage = True

        card = self.deck.pop()
        self.waiting_room.append(card)
        return card, refresh_damage


def _simulate_attack(damage: int, deck_state: DeckState) -> Tuple[int, bool]:
    cancelled = False
    refresh_damage = False
    for _ in range(damage):
        card, refreshed = deck_state.draw()
        refresh_damage = refresh_damage or refreshed
        if card:
            cancelled = True
    return (0 if cancelled else damage), refresh_damage


def simulate_trials(
    damage_sequence: Sequence[int],
    deck_config: DeckConfig,
    trials: int,
    seed: int | None = None,
) -> List[int]:
    rng = random.Random(seed)
    results: List[int] = []

    for _ in range(trials):
        deck_state = DeckState(deck_config, rng)
        total_damage = 0
        for damage in damage_sequence:
            dealt, refreshed = _simulate_attack(damage, deck_state)
            if refreshed:
                total_damage += 1  # refresh penalty damage
            total_damage += dealt
        results.append(total_damage)

    return results


def cumulative_probability_at_least(damages: Sequence[int], thresholds: Iterable[int]) -> Mapping[int, float]:
    total_trials = len(damages)
    if total_trials == 0:
        raise ValueError("Damages collection cannot be empty")

    probabilities = {}
    for threshold in thresholds:
        count = sum(1 for dmg in damages if dmg >= threshold)
        probabilities[int(threshold)] = count / total_trials
    return probabilities


def tune_trial_count(
    damage_sequence: Sequence[int],
    deck_config: DeckConfig,
    threshold: int,
    target_error: float = 0.01,
    min_trials: int = 500,
    max_trials: int = 50000,
    step_factor: float = 2.0,
    seed: int | None = None,
) -> Tuple[int, List[float]]:
    if min_trials <= 0 or max_trials <= 0:
        raise ValueError("Trial counts must be positive")
    if min_trials > max_trials:
        raise ValueError("min_trials cannot exceed max_trials")
    if step_factor <= 1.0:
        raise ValueError("step_factor must be greater than 1.0")
    if target_error <= 0:
        raise ValueError("target_error must be positive")

    rng = random.Random(seed)
    history: List[float] = []
    trial_count = min_trials

    while True:
        trial_seed = rng.randint(0, 2**32 - 1)
        damages = simulate_trials(damage_sequence, deck_config, trials=trial_count, seed=trial_seed)
        probability = cumulative_probability_at_least(damages, [threshold])[threshold]
        history.append(probability)

        if len(history) >= 2 and abs(history[-1] - history[-2]) <= target_error:
            return trial_count, history

        next_trials = min(max_trials, int(trial_count * step_factor))
        if next_trials == trial_count:
            return trial_count, history

        trial_count = next_trials

        if trial_count > max_trials:
            return max_trials, history

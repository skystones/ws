from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Mapping, MutableSequence, Sequence, Tuple


@dataclass(frozen=True)
class DeckConfig:
    total_cards: int
    climax_cards: int
    initial_waiting_room_cards: int = 0
    initial_waiting_room_climax_cards: int = 0
    waiting_room_cards: int = 0
    waiting_room_climax_cards: int = 0

    def __post_init__(self) -> None:
        if self.climax_cards > self.total_cards:
            raise ValueError("climax_cards cannot exceed total_cards")
        if self.total_cards <= 0:
            raise ValueError("total_cards must be positive")
        if self.climax_cards < 0:
            raise ValueError("climax_cards cannot be negative")
        if self.initial_waiting_room_cards < 0:
            raise ValueError("initial_waiting_room_cards cannot be negative")
        if self.initial_waiting_room_climax_cards < 0:
            raise ValueError("initial_waiting_room_climax_cards cannot be negative")
        if self.initial_waiting_room_cards > self.total_cards:
            raise ValueError("initial_waiting_room_cards cannot exceed total_cards")
        if self.initial_waiting_room_climax_cards > self.initial_waiting_room_cards:
            raise ValueError("initial_waiting_room_climax_cards cannot exceed initial_waiting_room_cards")
        if self.initial_waiting_room_climax_cards > self.climax_cards:
            raise ValueError("initial_waiting_room_climax_cards cannot exceed climax_cards")

        remaining_cards = self.total_cards - self.initial_waiting_room_cards
        remaining_climax_cards = self.climax_cards - self.initial_waiting_room_climax_cards
        if remaining_climax_cards > remaining_cards:
            raise ValueError("Remaining climax cards cannot exceed remaining deck size")
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
        self.config = config
        self.rng = rng
        deck_size = config.total_cards - config.initial_waiting_room_cards
        deck_climax_cards = config.climax_cards - config.initial_waiting_room_climax_cards

        self.waiting_room: MutableSequence[bool] = self._build_shuffled_pile(
            config.initial_waiting_room_cards, config.initial_waiting_room_climax_cards
        )
        self.deck: MutableSequence[bool] = self._build_shuffled_pile(
            deck_size, deck_climax_cards
        )
        self._validate_state()

        if config.waiting_room_cards or config.waiting_room_climax_cards:
            deck_size = config.total_cards - config.waiting_room_cards
            deck_climax_cards = config.climax_cards - config.waiting_room_climax_cards
            self.deck = self._build_shuffled_pile(deck_size, deck_climax_cards)
            self.waiting_room = self._build_shuffled_pile(
                config.waiting_room_cards, config.waiting_room_climax_cards
            )

    def _build_shuffled_pile(self, size: int, climax_cards: int) -> MutableSequence[bool]:
        pile = [True] * climax_cards + [False] * (size - climax_cards)
        self.rng.shuffle(pile)
        return pile

    def _validate_state(self) -> None:
        total_cards = len(self.deck) + len(self.waiting_room)
        total_climax_cards = sum(self.deck) + sum(self.waiting_room)
        if total_cards != self.config.total_cards or total_climax_cards != self.config.climax_cards:
            raise ValueError("Deck and waiting room composition does not match configuration")

    def draw(self) -> Tuple[bool, bool]:
        refresh_damage = False
        if not self.deck:
            # Refresh: shuffle the waiting room back into a deck.
            self.deck = list(self.waiting_room)
            self.waiting_room = []
            self.rng.shuffle(self.deck)
            refresh_damage = True
            self._validate_state()

        card = self.deck.pop()
        self.waiting_room.append(card)
        return card, refresh_damage


def _resolve_damage_event(damage: int, deck_state: DeckState) -> Tuple[int, int, bool]:
    """Resolve cancellable damage against the current ``deck_state``.

    Returns a tuple of ``(damage_dealt, refresh_penalty, cancelled)`` where
    ``refresh_penalty`` counts how many refresh penalty points were incurred while
    resolving the damage event and ``cancelled`` indicates whether any point of
    damage revealed a climax and cancelled the attack.
    """

    cancelled = False
    refresh_penalty = 0
    for _ in range(damage):
        card, refreshed = deck_state.draw()
        if refreshed:
            refresh_penalty += 1
        if card:
            cancelled = True
    return (0 if cancelled else damage), refresh_penalty, cancelled


def _simulate_attack(damage: int, deck_state: DeckState) -> Tuple[int, int]:
    dealt, refresh_penalty, _ = _resolve_damage_event(damage, deck_state)
    return dealt, refresh_penalty


MainPhaseStep = Callable[[DeckState], int]


def simulate_trials(
    damage_sequence: Sequence[int],
    deck_config: DeckConfig,
    trials: int,
    seed: int | None = None,
    main_phase_steps: Iterable[MainPhaseStep] | None = None,
) -> List[int]:
    """Run Monte Carlo trials for a battle damage sequence.

    ``main_phase_steps`` injects optional pre-battle deck manipulation and damage
    hooks. Each step receives the mutable :class:`DeckState` and **must** return
    the immediate damage it dealt (including any refresh penalty it generated)
    before battle attacks resolve. Steps are responsible for calling
    :func:`_resolve_damage_event` (or helpers built on it) when cancellable
    damage is needed.

    Example:
        >>> simulate_trials(
        ...     damage_sequence=[3, 3, 2],
        ...     deck_config=DeckConfig(total_cards=50, climax_cards=8),
        ...     trials=1000,
        ...     main_phase_steps=[main_phase_four_damage_with_bonus],
        ... )
    """

    if trials <= 0:
        raise ValueError("trials must be positive")

    for damage in damage_sequence:
        if damage < 0:
            raise ValueError("damage_sequence values must be non-negative")

    steps: Tuple[MainPhaseStep, ...] = tuple(main_phase_steps or ())
    for step in steps:
        if not callable(step):
            raise ValueError("All main_phase_steps must be callable")

    rng = random.Random(seed)
    results: List[int] = []

    for _ in range(trials):
        deck_state = DeckState(deck_config, rng)
        total_damage = 0
        for step in steps:
            step_damage = step(deck_state)
            if not isinstance(step_damage, int):
                raise TypeError("main_phase_steps must return an integer damage amount")
            if step_damage < 0:
                raise ValueError("main_phase_steps cannot return negative damage")
            total_damage += step_damage
        for damage in damage_sequence:
            dealt, refreshed = _simulate_attack(damage, deck_state)
            if refreshed:
                total_damage += 1  # refresh penalty damage
            total_damage += dealt
        results.append(total_damage)

    return results


def main_phase_four_damage_with_bonus(deck_state: DeckState) -> int:
    """Deal 4 cancellable damage and, on cancel, deal another cancellable 4.

    The helper returns the total damage dealt (including refresh penalties) so
    it can be used directly inside ``main_phase_steps``.
    """

    dealt, refresh_penalty, cancelled = _resolve_damage_event(4, deck_state)
    total = dealt + refresh_penalty
    if cancelled:
        followup_dealt, followup_refresh, _ = _resolve_damage_event(4, deck_state)
        total += followup_dealt + followup_refresh
    return total


def reveal_nine_clock_climaxes(deck_state: DeckState) -> int:
    """Reveal the top 9 cards and clock (uncancellable) for each climax.

    The reveal respects refresh timing via :meth:`DeckState.draw`, so refresh
    penalties are added to the returned damage before battle damage resolves.
    """

    climax_count = 0
    refresh_penalty = 0
    for _ in range(9):
        card, refreshed = deck_state.draw()
        if refreshed:
            refresh_penalty += 1
        if card:
            climax_count += 1
    return climax_count + refresh_penalty


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

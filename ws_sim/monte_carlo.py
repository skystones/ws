from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Mapping, MutableSequence, Sequence, Tuple


@dataclass(frozen=True)
class DeckConfig:
    """Deck and waiting room composition at the start of a simulation.

    ``deck_cards`` / ``deck_climax_cards`` describe the current deck only.
    Waiting room counts (either ``initial_waiting_room_*`` or
    ``waiting_room_*`` overrides) are added on top of the deck rather than
    being subtracted from it, so they represent cards already milled/clocked.
    """
    deck_cards: int
    deck_climax_cards: int
    initial_waiting_room_cards: int = 0
    initial_waiting_room_climax_cards: int = 0
    waiting_room_cards: int = 0
    waiting_room_climax_cards: int = 0
    attacking_deck_size: int | None = None
    attacking_soul_trigger_cards: int = 0

    def __post_init__(self) -> None:
        if self.deck_cards <= 0:
            raise ValueError("deck_cards must be positive")
        if self.deck_climax_cards < 0:
            raise ValueError("deck_climax_cards cannot be negative")
        if self.deck_climax_cards > self.deck_cards:
            raise ValueError("deck_climax_cards cannot exceed deck_cards")
        if self.initial_waiting_room_cards < 0:
            raise ValueError("initial_waiting_room_cards cannot be negative")
        if self.initial_waiting_room_climax_cards < 0:
            raise ValueError("initial_waiting_room_climax_cards cannot be negative")
        if self.initial_waiting_room_climax_cards > self.initial_waiting_room_cards:
            raise ValueError("initial_waiting_room_climax_cards cannot exceed initial_waiting_room_cards")

        if self.waiting_room_cards < 0:
            raise ValueError("waiting_room_cards cannot be negative")
        if self.waiting_room_climax_cards < 0:
            raise ValueError("waiting_room_climax_cards cannot be negative")
        if self.waiting_room_climax_cards > self.waiting_room_cards:
            raise ValueError("waiting_room_climax_cards cannot exceed waiting_room_cards")

        if self.attacking_deck_size is None and self.attacking_soul_trigger_cards:
            raise ValueError("attacking_soul_trigger_cards requires attacking_deck_size")
        if self.attacking_deck_size is not None:
            if self.attacking_deck_size <= 0:
                raise ValueError("attacking_deck_size must be positive")
            if self.attacking_soul_trigger_cards < 0:
                raise ValueError("attacking_soul_trigger_cards cannot be negative")
            if self.attacking_soul_trigger_cards > self.attacking_deck_size:
                raise ValueError("attacking_soul_trigger_cards cannot exceed attacking_deck_size")

    @property
    def starting_waiting_room(self) -> Tuple[int, int]:
        """Return the waiting room composition to seed the simulation."""
        if self.waiting_room_cards or self.waiting_room_climax_cards:
            return self.waiting_room_cards, self.waiting_room_climax_cards
        return self.initial_waiting_room_cards, self.initial_waiting_room_climax_cards


class DeckState:
    def __init__(self, config: DeckConfig, rng: random.Random) -> None:
        self.config = config
        self.rng = rng
        waiting_room_cards, waiting_room_climax_cards = config.starting_waiting_room
        deck_size = config.deck_cards
        deck_climax_cards = config.deck_climax_cards

        self.waiting_room: MutableSequence[bool] = self._build_shuffled_pile(
            waiting_room_cards, waiting_room_climax_cards
        )
        self.deck: MutableSequence[bool] = self._build_shuffled_pile(deck_size, deck_climax_cards)
        self.total_cards = deck_size + waiting_room_cards
        self.total_climax_cards = deck_climax_cards + waiting_room_climax_cards
        self._validate_state(deck_size, deck_climax_cards, waiting_room_cards, waiting_room_climax_cards)

    def _build_shuffled_pile(self, size: int, climax_cards: int) -> MutableSequence[bool]:
        pile = [True] * climax_cards + [False] * (size - climax_cards)
        self.rng.shuffle(pile)
        return pile

    def _validate_state(
        self,
        expected_deck_cards: int,
        expected_deck_climax_cards: int,
        expected_waiting_cards: int,
        expected_waiting_climax_cards: int,
    ) -> None:
        total_cards = len(self.deck) + len(self.waiting_room)
        total_climax_cards = sum(self.deck) + sum(self.waiting_room)
        if total_cards != self.total_cards or total_climax_cards != self.total_climax_cards:
            raise ValueError("Deck and waiting room composition does not match configuration")
        if len(self.deck) != expected_deck_cards or sum(self.deck) != expected_deck_climax_cards:
            raise ValueError("Deck composition does not match configuration")
        if len(self.waiting_room) != expected_waiting_cards or sum(self.waiting_room) != expected_waiting_climax_cards:
            raise ValueError("Waiting room composition does not match configuration")

    def draw(self) -> Tuple[bool, bool]:
        refresh_damage = False
        if not self.deck:
            # Refresh: shuffle the waiting room back into a deck.
            self.deck = list(self.waiting_room)
            self.waiting_room = []
            self.rng.shuffle(self.deck)
            refresh_damage = True
            self._validate_state(
                expected_deck_cards=len(self.deck),
                expected_deck_climax_cards=sum(self.deck),
                expected_waiting_cards=len(self.waiting_room),
                expected_waiting_climax_cards=sum(self.waiting_room),
            )

        card = self.deck.pop()
        self.waiting_room.append(card)
        return card, refresh_damage


@dataclass(frozen=True)
class MagicStoneResult:
    deck_cards: int
    deck_climax_cards: int
    stock_cards: int
    stock_climax_cards: int


def apply_magic_stone_effect(
    stock_cards: int,
    stock_climax_cards: int,
    deck_cards: int,
    deck_climax_cards: int,
    rng: random.Random | None = None,
) -> MagicStoneResult:
    """Mix stock into the deck and redraw stock to model the magic stone effect.

    The function shuffles the combined stock and deck piles, then deals the same
    number of stock cards back out. The returned :class:`MagicStoneResult`
    captures the new climax composition of both piles after resolution.
    """

    for value, label in (
        (stock_cards, "stock_cards"),
        (stock_climax_cards, "stock_climax_cards"),
        (deck_cards, "deck_cards"),
        (deck_climax_cards, "deck_climax_cards"),
    ):
        if value < 0:
            raise ValueError(f"{label} cannot be negative")

    if stock_climax_cards > stock_cards:
        raise ValueError("stock_climax_cards cannot exceed stock_cards")
    if deck_climax_cards > deck_cards:
        raise ValueError("deck_climax_cards cannot exceed deck_cards")

    total_cards = stock_cards + deck_cards
    if total_cards <= 0:
        raise ValueError("stock_cards + deck_cards must be positive")
    total_climax_cards = stock_climax_cards + deck_climax_cards
    if total_climax_cards > total_cards:
        raise ValueError("Total climax cards cannot exceed combined card count")

    local_rng = rng or random.Random()
    combined = [True] * total_climax_cards + [False] * (
        total_cards - total_climax_cards
    )
    local_rng.shuffle(combined)

    new_deck_climax_cards = sum(combined[:deck_cards])
    new_stock_climax_cards = total_climax_cards - new_deck_climax_cards

    return MagicStoneResult(
        deck_cards=deck_cards,
        deck_climax_cards=new_deck_climax_cards,
        stock_cards=stock_cards,
        stock_climax_cards=new_stock_climax_cards,
    )


class AttackingDeckState:
    def __init__(self, deck_size: int, soul_trigger_cards: int, rng: random.Random) -> None:
        self.deck_size = deck_size
        self.soul_trigger_cards = soul_trigger_cards
        self.rng = rng

    def resolve_soul_trigger(self) -> bool:
        if self.deck_size == 0:
            return False

        trigger_hit = self.rng.randrange(self.deck_size) < self.soul_trigger_cards
        self.deck_size -= 1
        if trigger_hit:
            self.soul_trigger_cards -= 1
        return trigger_hit


def _build_attacking_deck(
    deck_config: DeckConfig, rng: random.Random
) -> AttackingDeckState | None:
    if deck_config.attacking_deck_size is None:
        return None
    return AttackingDeckState(
        deck_size=deck_config.attacking_deck_size,
        soul_trigger_cards=deck_config.attacking_soul_trigger_cards,
        rng=rng,
    )


def _resolve_damage_event(
    damage: int, deck_state: DeckState
) -> Tuple[int, int, bool, int | None]:
    """Resolve cancellable damage against the current ``deck_state``.

    Returns a tuple of ``(damage_dealt, refresh_penalty, cancelled, cancel_position)``
    where ``refresh_penalty`` counts how many refresh penalty points were incurred
    while resolving the damage event, ``cancelled`` indicates whether any point of
    damage revealed a climax and ``cancel_position`` records the 1-based index of
    the first cancelling card (or ``None`` if no cancel occurred).
    """

    cancelled = False
    cancel_position: int | None = None
    refresh_penalty = 0
    for index in range(1, damage + 1):
        card, refreshed = deck_state.draw()
        if refreshed:
            refresh_penalty += 1
        if card and not cancelled:
            cancelled = True
            cancel_position = index
    return (0 if cancelled else damage), refresh_penalty, cancelled, cancel_position


def _resolve_attack_trigger(attacking_state: AttackingDeckState | None) -> bool:
    if attacking_state is None:
        return False
    return attacking_state.resolve_soul_trigger()


def _simulate_attack(
    damage: int, deck_state: DeckState, attacking_state: AttackingDeckState | None
) -> Tuple[int, int]:
    damage_after_trigger = damage + 1 if _resolve_attack_trigger(attacking_state) else damage
    dealt, refresh_penalty, _, _ = _resolve_damage_event(damage_after_trigger, deck_state)
    return dealt, refresh_penalty


@dataclass(frozen=True)
class DamageEvent:
    base_damage: int
    is_attack: bool = True

    def __post_init__(self) -> None:
        if self.base_damage < 0:
            raise ValueError("base_damage must be non-negative")


def _normalize_damage_event(raw_damage: int | DamageEvent) -> DamageEvent:
    if isinstance(raw_damage, DamageEvent):
        return raw_damage
    if isinstance(raw_damage, int):
        return DamageEvent(base_damage=raw_damage, is_attack=True)
    raise TypeError("damage_sequence must contain integers or DamageEvent instances")


MainPhaseStep = Callable[[DeckState], int]


def simulate_trials(
    damage_sequence: Sequence[int | DamageEvent],
    deck_config: DeckConfig,
    trials: int,
    seed: int | None = None,
    main_phase_steps: Iterable[MainPhaseStep] | None = None,
) -> List[int]:
    """Run Monte Carlo trials for a battle damage sequence.

    ``damage_sequence`` accepts either integers (for backwards compatibility)
    or :class:`DamageEvent` instances. Attack damage routes through
    :func:`_simulate_attack`, while effect damage bypasses attack-only trigger
    logic but still accounts for refresh penalties when resolving damage.

    ``main_phase_steps`` injects optional pre-battle deck manipulation and damage
    hooks. Each step receives the mutable :class:`DeckState` and **must** return
    the immediate damage it dealt (including any refresh penalty it generated)
    before battle attacks resolve. Steps are responsible for calling
    :func:`_resolve_damage_event` (or helpers built on it) when cancellable
    damage is needed.

    Example:
        >>> simulate_trials(
        ...     damage_sequence=[3, 3, 2],
        ...     deck_config=DeckConfig(deck_cards=50, deck_climax_cards=8),
        ...     trials=1000,
        ...     main_phase_steps=[main_phase_fourth_cancel_bonus_damage],
        ... )
    """

    if trials <= 0:
        raise ValueError("trials must be positive")

    normalized_damage_sequence: Tuple[DamageEvent, ...] = tuple(
        _normalize_damage_event(damage) for damage in damage_sequence
    )

    steps: Tuple[MainPhaseStep, ...] = tuple(main_phase_steps or ())
    for step in steps:
        if not callable(step):
            raise ValueError("All main_phase_steps must be callable")

    rng = random.Random(seed)
    results: List[int] = []

    for _ in range(trials):
        deck_state = DeckState(deck_config, rng)
        attacking_state = _build_attacking_deck(deck_config, rng)
        total_damage = 0
        for step in steps:
            step_damage = step(deck_state)
            if not isinstance(step_damage, int):
                raise TypeError("main_phase_steps must return an integer damage amount")
            if step_damage < 0:
                raise ValueError("main_phase_steps cannot return negative damage")
            total_damage += step_damage
        for event in normalized_damage_sequence:
            if event.is_attack:
                dealt, refresh_penalty = _simulate_attack(
                    event.base_damage, deck_state, attacking_state
                )
                total_damage += dealt + refresh_penalty
            else:
                dealt, refresh_penalty, _, _ = _resolve_damage_event(
                    event.base_damage, deck_state
                )
                total_damage += dealt + refresh_penalty
        results.append(total_damage)

    return results


def main_phase_fourth_cancel_bonus_damage(deck_state: DeckState) -> int:
    """Deal 4 cancellable damage and add 4 more only when the fourth card cancels.

    The helper returns the total damage dealt (including refresh penalties) so
    it can be used directly inside ``main_phase_steps``.
    """

    dealt, refresh_penalty, _, cancel_position = _resolve_damage_event(4, deck_state)
    total = dealt + refresh_penalty
    if cancel_position == 4:
        followup_dealt, followup_refresh, _, _ = _resolve_damage_event(4, deck_state)
        total += followup_dealt + followup_refresh
    return total


# Backwards compatibility alias
main_phase_four_damage_with_bonus = main_phase_fourth_cancel_bonus_damage


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
    damage_sequence: Sequence[int | DamageEvent],
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

from __future__ import annotations

from typing import Iterable, Mapping, MutableSequence, Sequence

from .monte_carlo import (
    DamageEvent,
    DeckConfig,
    DeckState,
    MainPhaseStep,
    simulate_trials,
)


def seed_top_stack(deck_state: DeckState, top_stack: Sequence[bool]) -> int:
    """Place a known ``top_stack`` on top of the current deck.

    The provided ``top_stack`` should be ordered from top to bottom using
    boolean values where ``True`` marks a climax card. The function preserves
    overall deck composition, shuffling the remainder with the deck's RNG.

    Returns the amount of damage dealt, which is always ``0`` so the helper can
    be slotted directly into ``main_phase_steps``.
    """

    total_climax_in_deck = sum(deck_state.deck)
    top_size = len(top_stack)
    if top_size > len(deck_state.deck):
        raise ValueError("Top stack longer than current deck")

    top_climax = sum(top_stack)
    remainder_size = len(deck_state.deck) - top_size
    remainder_climax = total_climax_in_deck - top_climax
    if remainder_climax < 0 or remainder_climax > remainder_size:
        raise ValueError("Top stack uses more climax cards than available in deck")

    remainder: MutableSequence[bool] = [True] * remainder_climax + [
        False
    ] * (remainder_size - remainder_climax)
    deck_state.rng.shuffle(remainder)
    deck_state.deck = remainder + list(reversed(top_stack))
    return 0


def apply_seeded_top_stack(top_stack: Sequence[bool]) -> MainPhaseStep:
    """Wrap :func:`seed_top_stack` for use in ``main_phase_steps``.

    The returned callable captures ``top_stack`` so it can be reused across
    simulations without mutating the source list.
    """

    def _apply(deck_state: DeckState) -> int:
        return seed_top_stack(deck_state, top_stack)

    return _apply


def run_main_phase_and_battle(
    damage_sequence: Sequence[int | DamageEvent],
    deck_config: DeckConfig,
    *,
    main_phase_steps: Iterable[MainPhaseStep] | None = None,
    trials: int,
    seed: int | None = None,
) -> list[int]:
    """Simulate the full main phase and battle flow in one call."""

    return simulate_trials(
        damage_sequence,
        deck_config,
        trials=trials,
        seed=seed,
        main_phase_steps=main_phase_steps,
    )


def run_main_phase_scenarios(
    damage_sequence: Sequence[int | DamageEvent],
    deck_config: DeckConfig,
    scenarios: Mapping[str, Iterable[MainPhaseStep]],
    *,
    trials: int,
    seed: int | None = None,
) -> Mapping[str, list[int]]:
    """Execute multiple named ``main_phase_steps`` scenarios.

    Returns a mapping of scenario labels to the damage lists produced by
    :func:`run_main_phase_and_battle`, allowing callers to reuse battle
    sequences across multiple pre-battle manipulations.
    """

    results = {}
    for label, steps in scenarios.items():
        results[label] = run_main_phase_and_battle(
            damage_sequence,
            deck_config,
            main_phase_steps=steps,
            trials=trials,
            seed=seed,
        )
    return results

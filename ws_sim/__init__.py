"""Utilities for Weiss Schwarz Monte Carlo damage simulation."""

from .monte_carlo import (
    DeckConfig,
    MagicStoneResult,
    apply_magic_stone_effect,
    cumulative_probability_at_least,
    simulate_trials,
    tune_trial_count,
)

__all__ = [
    "DeckConfig",
    "MagicStoneResult",
    "apply_magic_stone_effect",
    "cumulative_probability_at_least",
    "simulate_trials",
    "tune_trial_count",
]

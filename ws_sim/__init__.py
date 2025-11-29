"""Utilities for Weiss Schwarz Monte Carlo damage simulation."""

from .monte_carlo import (
    DeckConfig,
    cumulative_probability_at_least,
    simulate_trials,
    tune_trial_count,
)

__all__ = [
    "DeckConfig",
    "cumulative_probability_at_least",
    "simulate_trials",
    "tune_trial_count",
]

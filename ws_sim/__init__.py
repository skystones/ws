"""Utilities for Weiss Schwarz Monte Carlo damage simulation."""

from .main_phase import (
    apply_seeded_top_stack,
    run_main_phase_and_battle,
    run_main_phase_scenarios,
    seed_top_stack,
)
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
    "seed_top_stack",
    "apply_seeded_top_stack",
    "run_main_phase_and_battle",
    "run_main_phase_scenarios",
]

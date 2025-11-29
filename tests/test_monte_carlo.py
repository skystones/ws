import math

from ws_sim.monte_carlo import (
    DeckConfig,
    cumulative_probability_at_least,
    simulate_trials,
    tune_trial_count,
)


def test_reproducible_trials():
    damage_sequence = [2, 3, 1]
    config = DeckConfig(total_cards=50, climax_cards=8)
    first = simulate_trials(damage_sequence, config, trials=500, seed=123)
    second = simulate_trials(damage_sequence, config, trials=500, seed=123)
    assert first == second


def test_cumulative_probability_is_monotonic():
    damage_sequence = [2, 2, 2]
    config = DeckConfig(total_cards=40, climax_cards=8)
    damages = simulate_trials(damage_sequence, config, trials=2000, seed=321)
    thresholds = list(range(0, max(damages) + 1))
    probabilities = cumulative_probability_at_least(damages, thresholds)

    previous = 1.0
    for threshold in thresholds:
        assert probabilities[threshold] <= previous + 1e-9
        previous = probabilities[threshold]


def test_trial_tuning_converges():
    damage_sequence = [3, 3, 3]
    config = DeckConfig(total_cards=45, climax_cards=8)

    chosen_trials, history = tune_trial_count(
        damage_sequence,
        config,
        threshold=6,
        target_error=0.02,
        min_trials=200,
        max_trials=5000,
        seed=99,
    )

    assert chosen_trials >= 200
    assert chosen_trials <= 5000
    # Final two estimates should be within the target error margin
    assert len(history) >= 2
    assert math.isclose(history[-1], history[-2], rel_tol=0, abs_tol=0.02)

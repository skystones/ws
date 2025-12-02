import math
import random

import pytest

from ws_sim.monte_carlo import (
    DamageEvent,
    DeckConfig,
    DeckState,
    MagicStoneResult,
    apply_magic_stone_effect,
    cumulative_probability_at_least,
    main_phase_four_damage_with_bonus,
    reveal_nine_clock_climaxes,
    simulate_trials,
    tune_trial_count,
)


def test_initial_waiting_room_configuration():
    rng = random.Random(0)
    config = DeckConfig(
        total_cards=10,
        climax_cards=3,
        initial_waiting_room_cards=4,
        initial_waiting_room_climax_cards=1,
    )

    state = DeckState(config, rng)

    assert len(state.waiting_room) == 4
    assert sum(state.waiting_room) == 1
    assert len(state.deck) == 6
    assert sum(state.deck) == 2


def test_refresh_preserves_composition_with_initial_waiting_room():
    rng = random.Random(1)
    config = DeckConfig(
        total_cards=10,
        climax_cards=3,
        initial_waiting_room_cards=4,
        initial_waiting_room_climax_cards=1,
    )

    state = DeckState(config, rng)
    initial_deck_size = len(state.deck)
    for _ in range(initial_deck_size):
        state.draw()

    assert len(state.deck) == 0
    climax_count_before_refresh = sum(state.waiting_room)

    _, refreshed = state.draw()

    assert refreshed is True
    assert len(state.deck) + len(state.waiting_room) == config.total_cards
    assert sum(state.deck) + sum(state.waiting_room) == climax_count_before_refresh == config.climax_cards


@pytest.mark.parametrize(
    "kwargs",
    [
        {"total_cards": 5, "climax_cards": 2, "initial_waiting_room_cards": 6},
        {"total_cards": 5, "climax_cards": 2, "initial_waiting_room_climax_cards": 3},
        {
            "total_cards": 5,
            "climax_cards": 4,
            "initial_waiting_room_cards": 2,
            "initial_waiting_room_climax_cards": 0,
        },
    ],
)
def test_invalid_initial_waiting_room_configuration(kwargs):
    with pytest.raises(ValueError):
        DeckConfig(**kwargs)


def test_magic_stone_shuffles_stock_back_into_deck():
    rng = random.Random(7)

    result = apply_magic_stone_effect(
        stock_cards=5,
        stock_climax_cards=2,
        deck_cards=8,
        deck_climax_cards=3,
        rng=rng,
    )

    assert isinstance(result, MagicStoneResult)
    assert result.deck_cards == 8
    assert result.stock_cards == 5
    assert result.deck_climax_cards == 2
    assert result.stock_climax_cards + result.deck_climax_cards == 5


def test_magic_stone_validates_counts():
    with pytest.raises(ValueError):
        apply_magic_stone_effect(1, 2, 5, 1)
    with pytest.raises(ValueError):
        apply_magic_stone_effect(0, 0, 0, 0)


def test_reproducible_trials():
    damage_sequence = [2, 3, 1]
    config = DeckConfig(total_cards=50, climax_cards=8)
    first = simulate_trials(damage_sequence, config, trials=500, seed=123)
    second = simulate_trials(damage_sequence, config, trials=500, seed=123)
    assert first == second


def test_mixed_damage_events_apply_triggers_only_to_attacks():
    config = DeckConfig(
        total_cards=10,
        climax_cards=0,
        attacking_deck_size=2,
        attacking_soul_trigger_cards=2,
    )
    damage_sequence = [
        DamageEvent(base_damage=1, is_attack=True),
        DamageEvent(base_damage=2, is_attack=False),
        DamageEvent(base_damage=1, is_attack=True),
    ]

    damages = simulate_trials(damage_sequence, config, trials=1, seed=5)

    assert damages == [6]


def test_mixed_damage_trials_are_reproducible():
    config = DeckConfig(
        total_cards=40,
        climax_cards=8,
        attacking_deck_size=3,
        attacking_soul_trigger_cards=1,
    )
    damage_sequence = [
        DamageEvent(base_damage=2, is_attack=True),
        DamageEvent(base_damage=1, is_attack=False),
        DamageEvent(base_damage=3, is_attack=True),
    ]

    first = simulate_trials(damage_sequence, config, trials=500, seed=2024)
    second = simulate_trials(damage_sequence, config, trials=500, seed=2024)

    assert first == second


def test_attack_trigger_applies_bonus_damage():
    config = DeckConfig(
        total_cards=10,
        climax_cards=0,
        attacking_deck_size=1,
        attacking_soul_trigger_cards=1,
    )
    damages = simulate_trials([1], config, trials=3, seed=7)

    assert damages == [2, 2, 2]


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


def test_attacking_deck_validation():
    with pytest.raises(ValueError):
        DeckConfig(total_cards=10, climax_cards=2, attacking_soul_trigger_cards=1)
    with pytest.raises(ValueError):
        DeckConfig(
            total_cards=10,
            climax_cards=2,
            attacking_deck_size=5,
            attacking_soul_trigger_cards=6,
        )


def test_main_phase_four_damage_with_bonus_uses_cancellation():
    rng = random.Random(0)
    config = DeckConfig(total_cards=8, climax_cards=1)
    state = DeckState(config, rng)
    state.deck = [False, False, False, False, True, False, False, False]
    state.waiting_room = []

    damage = main_phase_four_damage_with_bonus(state)

    assert damage == 4
    assert len(state.deck) == 0
    assert sum(state.waiting_room) == 1


def test_reveal_nine_clock_climaxes_counts_climax_damage():
    rng = random.Random(1)
    config = DeckConfig(total_cards=12, climax_cards=3)
    state = DeckState(config, rng)
    state.deck = [True, False, False, False, False, False, False, True, False, False, False, True]
    state.waiting_room = []

    damage = reveal_nine_clock_climaxes(state)

    assert damage == 2
    assert len(state.deck) == 3
    assert sum(state.waiting_room) == 2


def test_simulate_trials_runs_main_phase_steps_first():
    config = DeckConfig(total_cards=8, climax_cards=1)
    seed = 42

    damages = simulate_trials(
        damage_sequence=[0],
        deck_config=config,
        trials=1,
        seed=seed,
        main_phase_steps=[main_phase_four_damage_with_bonus],
    )

    rng = random.Random(seed)
    expected_state = DeckState(config, rng)
    expected_main_phase_damage = main_phase_four_damage_with_bonus(expected_state)

    assert damages == [expected_main_phase_damage]

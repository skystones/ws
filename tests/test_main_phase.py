import random

from ws_sim.main_phase import (
    apply_seeded_top_stack,
    run_main_phase_and_battle,
    seed_top_stack,
)
from ws_sim.monte_carlo import DamageEvent, DeckConfig, DeckState, main_phase_four_damage_with_bonus


def test_seed_top_stack_places_known_cards_on_top():
    rng = random.Random(0)
    config = DeckConfig(total_cards=8, climax_cards=3)
    state = DeckState(config, rng)

    top_stack = [True, False, True]
    seed_top_stack(state, top_stack)

    drawn = [state.draw()[0] for _ in range(len(top_stack))]
    assert drawn == top_stack
    assert len(state.deck) == 5
    assert sum(state.deck) == 1


def test_seeded_stack_triggers_conditional_main_phase_damage():
    config = DeckConfig(total_cards=8, climax_cards=1)
    top_stack = [True, False, False, False]

    damages = run_main_phase_and_battle(
        damage_sequence=[],
        deck_config=config,
        main_phase_steps=[
            apply_seeded_top_stack(top_stack),
            main_phase_four_damage_with_bonus,
        ],
        trials=1,
        seed=9,
    )

    assert damages == [4]


def test_seeded_stack_applies_before_battle_attacks():
    config = DeckConfig(total_cards=3, climax_cards=1)
    top_stack = [True]

    damages = run_main_phase_and_battle(
        damage_sequence=[DamageEvent(base_damage=1, is_attack=True)],
        deck_config=config,
        main_phase_steps=[apply_seeded_top_stack(top_stack)],
        trials=1,
        seed=1,
    )

    assert damages == [0]

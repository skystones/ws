import random

from ws_sim.main_phase import (
    apply_seeded_top_stack,
    run_main_phase_and_battle,
    seed_top_stack,
)
from ws_sim.monte_carlo import (
    DamageEvent,
    DeckConfig,
    DeckState,
    main_phase_fourth_cancel_bonus_damage,
)


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
    top_stack = [False, False, False, True]

    damages = run_main_phase_and_battle(
        damage_sequence=[],
        deck_config=config,
        main_phase_steps=[
            apply_seeded_top_stack(top_stack),
            main_phase_fourth_cancel_bonus_damage,
        ],
        trials=1,
        seed=9,
    )

    assert damages == [4]


def test_seed_top_stack_places_climax_on_fourth_damage_card():
    rng = random.Random(0)
    config = DeckConfig(total_cards=8, climax_cards=1)
    state = DeckState(config, rng)

    seed_top_stack(state, [False, False, False, True])

    damage = main_phase_fourth_cancel_bonus_damage(state)

    assert damage == 4
    assert len(state.deck) == 0
    assert sum(state.waiting_room) == 1


def test_fourth_cancel_triggers_followup_damage_with_seed_top_stack():
    rng = random.Random(3)
    config = DeckConfig(total_cards=8, climax_cards=1)
    state = DeckState(config, rng)

    seed_top_stack(state, [False, False, False, True, False, False, False, False])

    damage = main_phase_fourth_cancel_bonus_damage(state)

    assert damage == 4
    assert len(state.deck) == 0
    assert state.waiting_room[3] is True


def test_seed_top_stack_early_cancel_blocks_bonus_damage():
    rng = random.Random(1)
    config = DeckConfig(total_cards=8, climax_cards=1)
    state = DeckState(config, rng)

    seed_top_stack(state, [False, True, False, False])

    damage = main_phase_fourth_cancel_bonus_damage(state)

    assert damage == 0
    assert len(state.deck) == 4
    assert sum(state.waiting_room) == 1


def test_seed_top_stack_no_cancel_resolves_only_base_damage():
    rng = random.Random(2)
    config = DeckConfig(total_cards=8, climax_cards=1)
    state = DeckState(config, rng)

    seed_top_stack(state, [False, False, False, False])

    damage = main_phase_fourth_cancel_bonus_damage(state)

    assert damage == 4
    assert len(state.deck) == 4
    assert sum(state.waiting_room) == 0


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

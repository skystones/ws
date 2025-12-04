#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from ws_sim.monte_carlo import (
    DeckConfig,
    cumulative_probability_at_least,
    simulate_trials,
    tune_trial_count,
)
from ws_sim.plotting import plot_cumulative_histogram


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weiss Schwarz damage Monte Carlo simulator")
    parser.add_argument("damages", nargs="+", type=int, help="Damage values for each attack (e.g. 2 3 3)")
    parser.add_argument(
        "--deck-cards",
        "--total-cards",
        dest="deck_cards",
        type=int,
        default=50,
        help="Current number of cards in the deck (alias: --total-cards)",
    )
    parser.add_argument(
        "--deck-climax-cards",
        "--climax-cards",
        dest="deck_climax_cards",
        type=int,
        default=8,
        help="Number of climax cards currently in the deck (alias: --climax-cards)",
    )
    parser.add_argument(
        "--waiting-room-cards",
        type=int,
        default=0,
        help=(
            "Number of cards that start in the waiting room (already milled or clocked) in addition to the deck."
        ),
    )
    parser.add_argument(
        "--waiting-room-climax-cards",
        type=int,
        default=0,
        help=(
            "Number of climax cards already in the waiting room at the start of the"
            " simulation, useful for representing decks immediately after a refresh."
        ),
    )
    parser.add_argument("--trials", type=int, default=5000, help="Number of Monte Carlo trials")
    parser.add_argument(
        "--auto-tune",
        action="store_true",
        help="Automatically tune the trial count using the provided threshold",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Threshold used for auto-tuning; probability will be estimated at this value",
    )
    parser.add_argument("--target-error", type=float, default=0.01, help="Absolute error tolerance for auto-tuning")
    parser.add_argument("--seed", type=int, default=1, help="Random seed")
    parser.add_argument("--png", type=Path, default=None, help="Optional path to save the histogram image")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = DeckConfig(
        deck_cards=args.deck_cards,
        deck_climax_cards=args.deck_climax_cards,
        waiting_room_cards=args.waiting_room_cards,
        waiting_room_climax_cards=args.waiting_room_climax_cards,
    )

    trials = args.trials
    history = None
    if args.auto_tune:
        if args.threshold is None:
            raise SystemExit("--auto-tune requires --threshold to be specified")
        trials, history = tune_trial_count(
            args.damages,
            config,
            threshold=args.threshold,
            target_error=args.target_error,
            min_trials=args.trials,
            seed=args.seed,
        )

    damages = simulate_trials(args.damages, config, trials=trials, seed=args.seed)
    max_damage = max(damages)
    thresholds = range(0, max_damage + 1)
    probabilities = cumulative_probability_at_least(damages, thresholds)

    fig, ax = plot_cumulative_histogram(probabilities)
    if args.png:
        ax.text(
            0.99,
            0.95,
            f"trials={trials}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
        )
        fig.savefig(args.png, bbox_inches="tight")
        print(f"Saved histogram to {args.png}")

    if history:
        print(f"Auto-tuned trials: {trials} (estimates: {history})")


if __name__ == "__main__":
    main()

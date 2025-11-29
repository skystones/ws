# Weiss Schwarz Damage Monte Carlo Simulation

This project provides a Monte Carlo simulator for Weiss Schwarz damage resolution, including automatic trial-count tuning and plotting utilities. The code is structured for use from scripts, notebooks, or imported as a library.

## Features
- Simulate sequential damage packets against a deck with configurable climax density.
- Account for refresh reshuffles and the associated refresh damage penalty.
- Estimate probabilities that total damage meets or exceeds thresholds.
- Tune Monte Carlo trial counts by observing estimate stability.
- Plot cumulative (right-shoulder-down) histograms and optionally save them as PNG files.

## Getting Started
Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the simulator from the CLI
```bash
python scripts/run_sim.py 2 3 3 \
  --total-cards 50 --climax-cards 8 --trials 2000 \
  --waiting-room-cards 10 --waiting-room-climax-cards 2 \
  --threshold 6 --auto-tune --target-error 0.02 --png artifacts/hist.png
```

Use `--waiting-room-cards` and `--waiting-room-climax-cards` to represent games in progress—for example, to model a post-refresh state with 10 cards (including 2 climaxes) already in the waiting room.

### Use in a notebook
See `notebooks/damage_simulation.ipynb` for an end-to-end example that tunes trials, runs the simulation, renders the histogram inline, and saves it to `artifacts/damage_hist.png`.

### Library usage
```python
from ws_sim.monte_carlo import DeckConfig, simulate_trials, cumulative_probability_at_least
from ws_sim.plotting import plot_cumulative_histogram

damage_sequence = [2, 3, 3]
deck = DeckConfig(total_cards=50, climax_cards=8)
damages = simulate_trials(damage_sequence, deck, trials=5000, seed=1)
probabilities = cumulative_probability_at_least(damages, range(0, max(damages) + 1))
plot_cumulative_histogram(probabilities, save_path="artifacts/hist.png")
```

## Development
Tests are written with `pytest` to support test-driven development. Run the suite with:

```bash
pytest
```

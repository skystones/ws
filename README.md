# Weiss Schwarz Damage Monte Carlo Simulation
This project provides a Monte Carlo simulator for Weiss Schwarz damage resolution, including automatic trial-count tuning and plotting utilities.

## Features
- 目的: ダメージ解決の挙動と確率分布を素早く把握する。
- 前提/初期状態: デッキ枚数とクライマックス（ダメージを無効化するカード）構成を指定する。
- 試行内容: Monte Carlo でダメージシーケンスを繰り返し解き、山札再構築（refresh reshuffle）やリフレッシュペナルティ（再構築時に受ける1点ダメージ）を含めて計算する。
- 確認する指標（例：P(>=6)）: 累積確率やダメージ閾値到達確率を集計する。
- Simulate sequential damage packets against a deck with configurable climax density.
- Account for refresh reshuffles (山札再構築) and the associated refresh damage penalty (再構築時の追加ダメージ)。
- Estimate probabilities that total damage meets or exceeds thresholds.
- Tune Monte Carlo trial counts by observing estimate stability.
- Plot cumulative (right-shoulder-down) histograms and optionally save them as PNG files.

## Getting Started
- 目的: コマンドラインやノートブックからすぐ試せる環境を用意する。
- 前提/初期状態: Python が動作し、依存ライブラリをインストールできる。
- 試行内容: 依存関係を導入し、サンプルスクリプトでシミュレーターを実行する。
- 確認する指標（例：P(>=6)）: インストール後にサンプル実行が成功し、確率が出力されるかを確認する。
Install dependencies:
```bash
pip install -r requirements.txt
```

### Run the simulator from the CLI
- 目的: スクリプトからダメージシミュレーションを繰り返し実行する方法を示す。
- 前提/初期状態: 依存関係を入れた環境と試したいダメージシーケンスがある。
- 試行内容: `scripts/run_sim.py` にダメージ配列やデッキ条件を渡して Monte Carlo 試行を行う。
- 確認する指標（例：P(>=6)）: 出力される確率や PNG の累積ヒストグラムで閾値到達度を確認する。
```bash
python scripts/run_sim.py 2 3 3 \
  --total-cards 50 --climax-cards 8 --trials 2000 \
  --waiting-room-cards 10 --waiting-room-climax-cards 2 \
  --threshold 6 --auto-tune --target-error 0.02 --png artifacts/hist.png
```
Use `--waiting-room-cards` and `--waiting-room-climax-cards` to represent games in progress—for example, to model a post-refresh state with 10 cards (including 2 climaxes) already in the waiting room.

### Use in a notebook
- 目的: ノートブックで試行数チューニングから可視化まで一連の操作を実演する。
- 前提/初期状態: Jupyter 環境があり、依存パッケージがインストールされている。
- 試行内容: サンプルノートブック `notebooks/damage_simulation.ipynb` を実行し、グラフを描画する。
- 確認する指標（例：P(>=6)）: ノートブックで算出した確率と生成した `artifacts/damage_hist.png` を確認する。
See `notebooks/damage_simulation.ipynb` for an end-to-end example that tunes trials, runs the simulation, renders the histogram inline, and saves it to `artifacts/damage_hist.png`.

### Library usage
- 目的: Python コードからシミュレーターを呼び出し、自動化や分析に組み込む。
- 前提/初期状態: プロジェクトをインポート可能なパスに置き、必要な設定をコードで渡せる。
- 試行内容: `DeckConfig` でデッキを定義し、`simulate_trials` でダメージを生成し、`plot_cumulative_histogram` で図を保存する。
- 確認する指標（例：P(>=6)）: `cumulative_probability_at_least` の出力で閾値達成確率を読み取る。
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
- 目的: テスト駆動でシミュレーターを継続的に改善できるようにする。
- 前提/初期状態: pytest が動作する開発環境とリポジトリのクローンがある。
- 試行内容: `pytest` を実行してユニットテストを走らせる。
- 確認する指標（例：P(>=6)）: テストが全てパスし、失敗がないことを確認する。
Tests are written with `pytest` to support test-driven development. Run the suite with:
```bash
pytest
```

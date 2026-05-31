"""CLI script to train ETA model with XGBoost + Optuna."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aits.ml.train import train_eta_model_v2


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train ETA model with XGBoost + Optuna")
    parser.add_argument("--n-trials", type=int, default=50, help="Optuna trials (default: 50)")
    parser.add_argument("--cv-splits", type=int, default=5, help="TimeSeriesSplit folds (default: 5)")
    args = parser.parse_args()

    print(f"Training ETA model: {args.n_trials} Optuna trials, {args.cv_splits}-fold TimeSeriesSplit")
    result = train_eta_model_v2(n_trials=args.n_trials, cv_splits=args.cv_splits)

    print()
    print("=" * 60)
    print("ETA MODEL TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Test MAE:       {result['test_mae']:.4f} min")
    print(f"  Test RMSE:      {result['test_rmse']:.4f} min")
    print(f"  Test R2:        {result['test_r2']:.4f}")
    print(f"  Test Median AE: {result['test_median_ae']:.4f} min")
    print(f"  Within 1 min:   {result['within_1min_pct']:.1f}%")
    print(f"  Within 2 min:   {result['within_2min_pct']:.1f}%")
    print(f"  Within 3 min:   {result['within_3min_pct']:.1f}%")
    print(f"  CV MAE:         {result['cv_mae_mean']:.4f} (+/- {result['cv_mae_std']:.4f})")
    print(f"  Best MAE:       {result['best_mae']:.4f}")
    print(f"  Features:       {result['n_features']}")
    print(f"  Rows:           {result['n_rows']}")
    print(f"  Trials:         {result['n_trials']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

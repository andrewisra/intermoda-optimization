"""CLI script to train Density model with CatBoost + Optuna."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aits.ml.train import train_density_catboost


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train Density model with CatBoost + Optuna")
    parser.add_argument("--n-trials", type=int, default=15, help="Optuna trials (default: 15)")
    parser.add_argument("--cv-splits", type=int, default=3, help="TimeSeriesSplit folds (default: 3)")
    args = parser.parse_args()

    print(f"Training Density model: {args.n_trials} Optuna trials, {args.cv_splits}-fold TimeSeriesSplit")
    result = train_density_catboost(n_trials=args.n_trials, cv_splits=args.cv_splits)

    print()
    print("=" * 60)
    print("DENSITY MODEL TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Test F1 (macro): {result['test_f1_macro']:.4f}")
    print(f"  Test Accuracy:   {result['test_accuracy']:.4f}")
    print(f"  Test Kappa:      {result['test_kappa']:.4f}")
    print(f"  CV F1 mean:      {result['cv_f1_mean']:.4f} (+/- {result['cv_f1_std']:.4f})")
    print(f"  Best F1 (CV):    {result['best_f1_macro']:.4f}")
    print(f"  Naive F1:        {result['naive_f1_macro']:.4f}")
    print(f"  Naive Accuracy:  {result['naive_accuracy']:.4f}")
    print(f"  Model/Naive:     {result['test_f1_macro'] / max(result['naive_f1_macro'], 0.001):.1f}x")
    print(f"  Features:        {result['n_features']}")
    print(f"  Rows:            {result['n_rows']}")
    print(f"  Trials:          {result['n_trials']}")
    print(f"  Classes:         {result['classes']}")
    print(f"  Model type:      {result['model_type']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

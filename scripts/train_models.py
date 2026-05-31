"""CLI script to train BOTH ETA and Density models."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aits.ml.train import train_all


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train both ETA and Density models")
    parser.add_argument("--eta-trials", type=int, default=50, help="ETA Optuna trials (default: 50)")
    parser.add_argument("--density-trials", type=int, default=15, help="Density Optuna trials (default: 15)")
    args = parser.parse_args()

    print(f"Training both models: ETA ({args.eta_trials} trials) + Density ({args.density_trials} trials)")
    result = train_all()

    print()
    print("=" * 60)
    print("ALL MODELS TRAINED SUCCESSFULLY")
    print("=" * 60)
    print(f"  ETA Test MAE:       {result['eta']['test_mae']:.4f} min")
    print(f"  ETA Test R2:        {result['eta']['test_r2']:.4f}")
    print(f"  Density Test F1:    {result['density']['test_f1_macro']:.4f}")
    print(f"  Density Test Acc:   {result['density']['test_accuracy']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()

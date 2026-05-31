"""Print final density model results (CatBoost)."""
import sys, time
sys.path.insert(0, ".")
from pathlib import Path
import pandas as pd
from src.aits.ml.train import train_density_catboost
from src.aits.data.build_density_dataset import build_density_dataset

RAW_DIR = Path("data/raw")
GTFS_DIR = RAW_DIR / "gtfs_transjakarta"

# Ensure CSV is in new format (skip if already correct)
import os
csv_path = RAW_DIR / "training_density.csv"
if csv_path.exists() and os.path.getsize(csv_path) > 100000:
    df_check = pd.read_csv(csv_path, nrows=1)
    if "routes_through_stop" in df_check.columns:
        print("CSV already in correct format, skipping regeneration.")
    else:
        print("Regenerating density CSV...")
        build_density_dataset(GTFS_DIR, output_path=csv_path)
else:
    build_density_dataset(GTFS_DIR, output_path=csv_path)

import pandas as pd
df = pd.read_csv(csv_path)
dist = df["density_level"].value_counts(normalize=True)
print("Distribution:")
for k, v in dist.items():
    print("  %s: %.2f%%" % (k, v * 100))

start = time.time()
result = train_density_catboost(n_trials=20, cv_splits=3)
elapsed = time.time() - start

print()
print("=" * 60)
print("  DENSITY MODEL: CatBoost + Optuna (20 trials)")
print("=" * 60)
print("  Test F1 (macro):  %.4f" % result["test_f1_macro"])
print("  Test Accuracy:    %.4f" % result["test_accuracy"])
print("  Test Kappa:       %.4f" % result["test_kappa"])
print("  Naive F1:         %.4f" % result["naive_f1_macro"])
print("  Naive Accuracy:   %.4f" % result["naive_accuracy"])
print("  CV F1 (mean):     %.4f (+/- %.4f)" % (result["cv_f1_mean"], result["cv_f1_std"]))
print("  Classes:          %s" % result["classes"])
print("  Features:         %d" % result["n_features"])
print("  Rows:             %d" % result["n_rows"])
print("  Time:             %d sec" % elapsed)
print("=" * 60)

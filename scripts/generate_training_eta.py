"""Generate the actual training_eta.csv from GTFS + weather + delay."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aits.data.build_training_dataset import build_training_eta

gtfs_dir = Path("data/raw/gtfs_transjakarta")
out_path = Path("data/raw/training_eta.csv")

print("Building training ETA dataset...")
df = build_training_eta(gtfs_dir, output_path=out_path)
print(f"Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print()
print("Delay stats:")
print(f"  mean: {df['delay_minutes'].mean():.3f} min")
print(f"  std:  {df['delay_minutes'].std():.3f} min")
print(f"  min:  {df['delay_minutes'].min():.3f} min")
print(f"  max:  {df['delay_minutes'].max():.3f} min")
print(f"  p50:  {df['delay_minutes'].quantile(0.5):.3f} min")
print(f"  p95:  {df['delay_minutes'].quantile(0.95):.3f} min")
print(f"  p99:  {df['delay_minutes'].quantile(0.99):.3f} min")
zero_pct = (df["delay_minutes"] == 0).mean() * 100
print(f"Zero delay: {(df['delay_minutes'] == 0).sum()} ({zero_pct:.1f}%)")
print()
print("Route mode distribution:")
print(df["route_mode"].value_counts().to_string())
print()
print(f"Saved to {out_path}")

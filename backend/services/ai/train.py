"""
Training Data Generator & Model Trainer
────────────────────────────────────────
Run this script to:
  1. Generate synthetic training data
  2. Train XGBoost + Isolation Forest
  3. Save model artifacts to models/artifacts/

Usage:
    python services/ai/train.py
"""
import numpy as np
import pandas as pd
import joblib
import os
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

# Try importing XGBoost; fall back to RandomForest for portability
try:
    from xgboost import XGBClassifier
    MODEL_CLASS = XGBClassifier
    MODEL_KWARGS = dict(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    MODEL_CLASS = RandomForestClassifier
    MODEL_KWARGS = dict(n_estimators=200, max_depth=8, random_state=42)
    print("⚠️  XGBoost not found — using RandomForestClassifier instead")


ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "models" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Synthetic data generation ────────────────────────────────────────────────
def generate_training_data(n: int = 60_000) -> pd.DataFrame:
    """
    Generate synthetic GPS + behavioural feature dataset with labels.
    Labels: 1 = risky, 0 = safe.
    """
    rng = np.random.default_rng(42)
    records = []

    for _ in range(n):
        hour          = rng.integers(0, 24)
        crowd_density = rng.beta(2, 5)
        dwell_time    = rng.exponential(300)
        speed         = rng.exponential(1.2)
        lat           = rng.uniform(8.0, 37.0)   # India bounding box
        lng           = rng.uniform(68.0, 97.0)

        # Cyclic time encoding
        sin_h = np.sin(2 * np.pi * hour / 24)
        cos_h = np.cos(2 * np.pi * hour / 24)

        # Heuristic risk score (ground-truth proxy)
        risk = (
            (hour >= 22 or hour <= 5) * 0.38 +
            crowd_density * 0.25 +
            (dwell_time > 600) * 0.20 +
            (speed < 0.5) * 0.17
        )
        label = int(risk + rng.normal(0, 0.08) > 0.50)

        records.append([lat, lng, speed, dwell_time, sin_h, cos_h,
                        crowd_density, label])

    return pd.DataFrame(records, columns=[
        "lat", "lng", "speed", "dwell_time",
        "sin_hour", "cos_hour", "crowd_density", "label"
    ])


# ── Training ─────────────────────────────────────────────────────────────────
def train():
    print("📊 Generating training data …")
    df = generate_training_data(60_000)
    df.to_csv(ARTIFACTS_DIR / "training_data.csv", index=False)
    print(f"   {len(df):,} rows saved")

    feature_cols = ["lat", "lng", "speed", "dwell_time",
                    "sin_hour", "cos_hour", "crowd_density"]
    X = df[feature_cols].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scaler
    print("📐 Fitting scaler …")
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)
    joblib.dump(scaler, ARTIFACTS_DIR / "scaler.pkl")

    # Classifier
    print("🤖 Training risk classifier …")
    clf = MODEL_CLASS(**MODEL_KWARGS)
    clf.fit(X_train_s, y_train)
    y_pred = clf.predict(X_test_s)
    f1 = f1_score(y_test, y_pred)
    print(f"   F1 score: {f1:.4f}")
    print(classification_report(y_test, y_pred))
    joblib.dump(clf, ARTIFACTS_DIR / "xgb_risk.pkl")

    # Isolation Forest (unsupervised anomaly)
    print("🔍 Training Isolation Forest …")
    iso = IsolationForest(contamination=0.08, random_state=42, n_jobs=-1)
    iso.fit(X_train_s)
    joblib.dump(iso, ARTIFACTS_DIR / "isolation_forest.pkl")

    print(f"\n✅ Artifacts saved to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    train()

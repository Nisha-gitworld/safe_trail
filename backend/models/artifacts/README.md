# ML Model Artifacts

This directory stores trained model files (.pkl).

## Generate models

```bash
cd backend
python services/ai/train.py
```

This will create:
- `xgb_risk.pkl`       — XGBoost risk classifier
- `isolation_forest.pkl` — Isolation Forest anomaly detector
- `scaler.pkl`         — StandardScaler for feature normalisation
- `training_data.csv`  — Generated synthetic training dataset

## Files ignored by git

All `.pkl` and `.csv` files are in `.gitignore`.
For production, store models in an S3 bucket or MLflow registry.

# Model Training Guide

## Overview

Training pipeline ([`train.ipynb`](infer/train.ipynb:1)) evaluates multiple ML algorithms on engineered features for BTC price prediction.

## Process Flow

```
Feature Dataset (final.pkl)
       ↓
   Load & Split Data
       ↓
   Scale Features (StandardScaler)
       ↓
   Create Sliding Windows
       ↓
   Train Multiple Models
       ↓
   Evaluate on Validation/Test
       ↓
   Select Best Model
       ↓
   Save Artifacts
```

## Step 1: Data Loading

### Load Dataset

```python
DATA_PATH = "data/processed/final.pkl"
master_df = pd.read_pickle(DATA_PATH)
master_df['timestamp'] = pd.to_datetime(master_df['timestamp'])
master_df = master_df.sort_values('timestamp').reset_index(drop=True)
```

### Prepare Features and Target

```python
X = master_df.drop(columns=['target', 'timestamp'])
y = master_df['target'].copy()
timestamps = master_df['timestamp'].copy()
```

## Step 2: Train/Val/Test Split

### Chronological Split

```python
n = len(master_df)
train_end = int(n * 0.70)      # 70% training
val_end = int(n * 0.85)        # 15% validation
                                # 15% test

X_train = X.iloc[:train_end]
y_train = y.iloc[:train_end]

X_val = X.iloc[train_end:val_end]
y_val = y.iloc[train_end:val_end]

X_test = X.iloc[val_end:]
y_test = y.iloc[val_end:]
```

### No Leakage Check

```python
assert X_train.index.max() < X_val.index.min()
assert X_val.index.max() < X_test.index.min()
```

**Rationale**: Prevent future data leakage.

## Step 3: Feature Scaling

### StandardScaler

```python
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)
```

**Parameters**:
- Mean: 0
- Std: 1
- Fit on training only

**Why**: Different feature scales (prices vs ratios)

## Step 4: Sliding Window Creation

### Window Function

```python
def make_sliding_window_xy(X, y, window=6, horizon=1):
    """
    Predict y at t+horizon using X[t-window+1 ... t]
    Output index aligns to target timestamp (t+horizon)
    """
    rows, targets, out_index = [], [], []
    
    for t in range(window - 1, len(X) - horizon):
        x_block = X[t - window + 1 : t + 1]
        rows.append(x_block.reshape(-1))  # flatten
        targets.append(y[t + horizon])
        out_index.append(X.index[t + horizon])
    
    # Create lagged feature names
    cols = []
    for lag in range(window, 0, -1):  # lag6 ... lag1
        for f in X.columns:
            cols.append(f"{f}_lag{lag}")
    
    Xw = pd.DataFrame(rows, columns=cols, index=out_index)
    yw = pd.Series(targets, index=out_index, name="target")
    return Xw, yw
```

### Apply to All Splits

```python
WINDOW = 6   # 6 periods = 24 hours
HORIZON = 1  # 1 period = 4 hours

Xtr_w, ytr_w = make_sliding_window_xy(X_train_scaled, y_train, WINDOW, HORIZON)
Xva_w, yva_w = make_sliding_window_xy(X_val_scaled, y_val, WINDOW, HORIZON)
Xte_w, yte_w = make_sliding_window_xy(X_test_scaled, y_test, WINDOW, HORIZON)
```

**Output shapes**:
- Features: `n_features * window` (e.g., 30 * 6 = 180)
- Samples: Reduced by (window + horizon)

### No Leakage Check

```python
assert Xtr_w.index.max() < Xva_w.index.min()
assert Xva_w.index.max() < Xte_w.index.min()
```

## Step 5: Baseline Models

### Zero Baseline

```python
pred0_val = np.zeros(len(yva_w))
pred0_test = np.zeros(len(yte_w))
```

**Rationale**: Random walk baseline (no prediction).

### Last-Value Baseline

```python
pred_last_val = yva_w.shift(1).fillna(0).values
pred_last_test = yte_w.shift(1).fillna(0).values
```

**Rationale**: Persistence model (last return).

## Step 6: Model Definitions

### Linear Models

```python
models = {
    "Ridge": Ridge(alpha=1.0, random_state=42),
    "Lasso": Lasso(alpha=1e-4, max_iter=20000, random_state=42),
    "ElasticNet": ElasticNet(alpha=1e-3, l1_ratio=0.2, random_state=42),
    "Huber": HuberRegressor(epsilon=1.35, alpha=1e-4),
    "SGDRegressor": SGDRegressor(
        loss="squared_error",
        penalty="l2",
        alpha=1e-4,
        learning_rate="optimal",
        max_iter=10000
    )
}
```

### SVM Models

```python
"LinearSVR": LinearSVR(C=1.0, epsilon=5e-4, max_iter=10000),
"SVR_RBF": SVR(kernel="rbf", C=1.0, gamma="scale", epsilon=5e-4)
```

### Tree-Based Models

```python
"DecisionTree": DecisionTreeRegressor(
    max_depth=5,
    min_samples_leaf=50,
    random_state=42
)
```

### Ensemble Models

```python
"RandomForest": RandomForestRegressor(
    n_estimators=300,
    max_depth=6,
    min_samples_leaf=30,
    n_jobs=-1,
    random_state=42
),
"GradientBoosting": GradientBoostingRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=3,
    random_state=42
)
```

## Step 7: Evaluation Metrics

### Evaluation Function

```python
def eval_regression(y_true, y_pred, capital=1_000_000_000, threshold=0.0, fee_bps=0.0):
    # Statistical metrics
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    ic = spearmanr(y_true, y_pred).correlation
    dir_acc = (np.sign(y_true) == np.sign(y_pred)).mean()
    
    # Trading simulation
    pos = np.where(y_pred > threshold, 1,
                  np.where(y_pred < -threshold, -1, 0))
    gross_pnl = capital * pos * y_true
    fee = (fee_bps / 10_000) * capital
    net_pnl = gross_pnl - (np.abs(pos) * fee)
    
    # PnL metrics
    total_pnl = net_pnl.sum()
    avg_pnl = net_pnl.mean()
    trades = int((pos != 0).sum())
    win_rate = (net_pnl[pos != 0] > 0).mean() if trades > 0 else np.nan
    
    # Drawdown
    equity = np.cumsum(net_pnl)
    peak = np.maximum.accumulate(equity)
    drawdown = equity - peak
    max_dd = drawdown.min()
    
    return {
        "RMSE": rmse,
        "MAE": mae,
        "IC_spearman": ic,
        "Directional_Acc": dir_acc,
        "PnL_1B_Total": total_pnl,
        "PnL_1B_AvgPerBar": avg_pnl,
        "Trades": trades,
        "WinRate": win_rate,
        "MaxDrawdown_1B": max_dd
    }
```

### Metrics Explained

| Metric | Purpose | Interpretation |
|--------|---------|----------------|
| RMSE | Error magnitude | Lower is better |
| MAE | Average absolute error | Lower is better |
| IC_spearman | Rank correlation | Higher is better (0-1) |
| Directional_Acc | Sign prediction accuracy | Higher is better (0-1) |
| PnL_1B_Total | Simulated profit/loss | Higher is better |
| PnL_1B_AvgPerBar | Average profit per bar | Higher is better |
| Trades | Number of trades | Depends on strategy |
| WinRate | Profitable trade % | Higher is better (0-1) |
| MaxDrawdown_1B | Peak-to-trough decline | Lower (less negative) is better |

## Step 8: Model Training

### Training Loop

```python
results = []
fitted_models = {}

for name, model in tqdm(models.items()):
    # Train
    model.fit(Xtr_w, ytr_w)
    fitted_models[name] = model
    
    # Predict
    pred_val = model.predict(Xva_w)
    pred_test = model.predict(Xte_w)
    
    # Evaluate
    results.append({
        "Model": name,
        **{f"VAL_{k}": v for k, v in eval_regression(yva_w, pred_val).items()},
        **{f"TEST_{k}": v for k, v in eval_regression(yte_w, pred_test).items()}
    })
```

### Results DataFrame

```python
df_results = pd.DataFrame(baseline_rows + results)
df_results = df_results.sort_values(by="VAL_IC_spearman", ascending=False)
```

## Step 9: Model Selection

### Selection Criteria

Primary: **Validation IC_spearman** (rank correlation)
Secondary: **Validation Directional_Acc**

### Best Model

```python
best_model_name = df_results.iloc[0]["Model"]
best_model = fitted_models[best_model_name]
```

## Step 10: Save Artifacts

### Save Model and Scaler

```python
OUT_DIR = "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(scaler, f"{OUT_DIR}/scaler.joblib")
joblib.dump(best_model, f"{OUT_DIR}/model_{best_model_name}.joblib")
```

### Save Metadata

```python
meta = {
    "best_model": best_model_name,
    "window": int(WINDOW),
    "horizon": int(HORIZON),
    "target_col": "target",
    "time_col": "timestamp",
    "n_rows": int(n),
    "train_end": int(train_end),
    "val_end": int(val_end),
    "feature_cols": list(X.columns),
    "windowed_feature_cols": list(Xtr_w.columns)
}

pd.Series(meta).to_json(f"{OUT_DIR}/train_meta.json")
```

## Model Comparison

### Expected Performance

| Model Type | Strengths | Weaknesses |
|-------------|-----------|-------------|
| Ridge | Fast, stable, handles multicollinearity | Linear only |
| Lasso | Feature selection | Can be unstable |
| ElasticNet | Balanced regularization | Tuning required |
| Huber | Robust to outliers | Slower |
| SGD | Scalable to large data | Sensitive to scaling |
| LinearSVR | Good for high dimensions | Linear only |
| SVR-RBF | Non-linear relationships | Slow, memory heavy |
| Decision Tree | Interpretable, non-linear | Prone to overfitting |
| Random Forest | Robust, handles non-linearity | Slower, less interpretable |
| Gradient Boosting | High accuracy, handles complex patterns | Sensitive to overfitting |

### Baseline Comparison

Compare models against:
- **Zero**: Random prediction
- **Last**: Persistence model

If models don't beat baselines, reconsider features or approach.

## Output

### Artifacts Directory

```
artifacts/
├── scaler.joblib              # Fitted StandardScaler
├── model_{best_name}.joblib # Best trained model
└── train_meta.json          # Training metadata
```

### Results Summary

Display:
- All models ranked by validation IC
- Best model highlighted
- Test set performance of best model

## Troubleshooting

### Poor Model Performance

**Check features**:
- Are features predictive?
- Is there lookahead bias?
- Are features stationary?

**Check data**:
- Enough training samples?
- Correct train/val/test split?
- Proper scaling?

**Check hyperparameters**:
- Grid search for best params
- Regularization strength
- Model complexity

### Overfitting

**Signs**:
- High train IC, low test IC
- Large gap between val and test

**Solutions**:
- Increase regularization
- Reduce model complexity
- Add more training data
- Use cross-validation

### Underfitting

**Signs**:
- Low train and test IC
- Models near baseline performance

**Solutions**:
- Reduce regularization
- Increase model complexity
- Add more features
- Check feature quality

## Next Steps

After training:
1. Load model for inference
2. Apply same preprocessing to new data
3. Create sliding windows
4. Scale with saved scaler
5. Predict with trained model
6. Monitor performance over time

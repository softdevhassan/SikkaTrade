import os
import logging
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from data.binance_data import get_klines
from analysis.indicators import klines_to_dataframe, calculate_indicators

# Setup logging
logger = logging.getLogger(__name__)

# Constants
MODEL_FILE = "sikka_ml_model.joblib"
DAYS_TO_FETCH = 30  # Train on last 30 days
PREDICTION_THRESHOLD = 0.60  # Only buy if confidence > 60%


class MLEngine:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.load_model()

    def load_model(self):
        """Load trained model from disk if exists"""
        if os.path.exists(MODEL_FILE):
            try:
                self.model = joblib.load(MODEL_FILE)
                self.is_trained = True
                logger.info(f"[ML] Loaded existing model from {MODEL_FILE}")
            except Exception as e:
                logger.error(f"[ML] Failed to load model: {e}")
        else:
            logger.info("[ML] No existing model found.")

    def save_model(self):
        """Save trained model to disk"""
        if self.model:
            try:
                joblib.dump(self.model, MODEL_FILE)
                logger.info(f"[ML] Model saved to {MODEL_FILE}")
            except Exception as e:
                logger.error(f"[ML] Failed to save model: {e}")

    def prepare_features(self, df):
        """
        Feature Engineering
        Returns: X (features), y (target)
        """
        try:
            # Ensure we have indicators
            if "RSI" not in df.columns:
                df = calculate_indicators(df)

            # Drop NaNs just in case
            df = df.dropna()

            # --- FEATURES ---
            # 1. Technical Indicators
            df["feat_rsi"] = df["RSI"] / 100.0  # Normalize 0-1
            df["feat_macd"] = df["MACD"]
            df["feat_macd_hist"] = df["MACD_hist"]

            # 2. Volume Trends
            # Ratio of current volume to 20 periods avg
            df["feat_vol_ratio"] = df["volume"] / (df["volume_ma"] + 1e-9)

            # 3. Price Changes (Momentum)
            for lag in [1, 4, 12, 24]:
                df[f"feat_change_{lag}h"] = df["close"].pct_change(lag)

            # 4. Bollinger Band Width
            # (Upper - Lower) / Middle
            if "BB_upper" in df.columns:
                df["feat_bb_width"] = (df["BB_upper"] - df["BB_lower"]) / (
                    df["BB_middle"] + 1e-9
                )
                # Price position relative to bands (0=Lower, 1=Upper)
                df["feat_bb_pos"] = (df["close"] - df["BB_lower"]) / (
                    (df["BB_upper"] - df["BB_lower"]) + 1e-9
                )

            # --- TARGET ---
            # Predict if price will go UP by at least 1.0% in next 4 hours
            # Shift -4 means "look 4 rows ahead"
            future_close = df["close"].shift(-4)
            df["target_return"] = (future_close - df["close"]) / df["close"]
            df["target"] = (df["target_return"] > 0.01).astype(int)

            # Drop rows with NaN (due to shifts/rolling)
            feature_cols = [c for c in df.columns if c.startswith("feat_")]
            final_df = df.dropna(subset=feature_cols + ["target"])

            return final_df[feature_cols], final_df["target"], feature_cols

        except Exception as e:
            logger.error(f"[ML] Feature engineering failed: {e}")
            return None, None, None

    def train(self, coins):
        """
        Train a new model using historical data for given coins
        """
        logger.info(
            f"[ML] Starting training on {len(coins)} coins ({DAYS_TO_FETCH} days)..."
        )

        all_X = []
        all_y = []
        feature_names = []

        for coin in coins:
            try:
                # Fetch 30 days of 1h data
                hours = DAYS_TO_FETCH * 24
                klines = get_klines(coin, hours=hours)

                if not klines or len(klines) < 100:
                    logger.warning(f"[ML] Insufficient data for {coin}")
                    continue

                df = klines_to_dataframe(klines)
                X, y, cols = self.prepare_features(df)

                if X is not None and not X.empty:
                    all_X.append(X)
                    all_y.append(y)
                    feature_names = cols
                    logger.info(f"[ML] Processed {len(X)} samples from {coin}")
            except Exception as e:
                logger.error(f"[ML] Features generation failed for {coin}: {e}")

        if not all_X:
            logger.error("[ML] No training data available!")
            return False

        # Combine all data
        X_final = pd.concat(all_X)
        y_final = pd.concat(all_y)

        logger.info(f"[ML] Training on {len(X_final)} total samples...")

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X_final, y_final, test_size=0.2, random_state=42
        )

        # Initialize RandomForest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,  # Use all CPU cores
        )

        # Train
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        logger.info(f"[ML] Model Trained! Accuracy: {acc:.2%}")
        logger.info(f"[ML] Features: {feature_names}")

        self.is_trained = True
        self.save_model()
        return True

    def predict_proba(self, df):
        """
        Predict probability of BUY (1)
        Returns: float (0.0 to 1.0)
        """
        if not self.is_trained or self.model is None:
            return 0.5  # Neutral if no model

        try:
            # We only need the LAST row for prediction
            # But we need enough history for features
            X, _, cols = self.prepare_features(df)

            if X is None or X.empty:
                return 0.5

            # Get latest row
            latest_features = X.iloc[[-1]]  # Keep as DataFrame

            # Predict Class 1 (Buy) probability
            proba = self.model.predict_proba(latest_features)[0][1]
            return proba

        except Exception as e:
            logger.error(f"[ML] Prediction failed: {e}")
            return 0.5

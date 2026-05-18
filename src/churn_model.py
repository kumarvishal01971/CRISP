import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import warnings
warnings.filterwarnings("ignore")

PROCESSED = "data/processed/"
MODELS    = "models/"
os.makedirs(MODELS, exist_ok=True)

def build_master_dataset():
    rfm     = pd.read_csv(f"{PROCESSED}customer_analytics.csv")
    mkt     = pd.read_csv(f"{PROCESSED}marketing_attribution.csv")
    support = pd.read_csv(f"{PROCESSED}customer_support.csv")
    demo    = pd.read_csv(f"{PROCESSED}customer_demographics.csv")

    df = rfm.merge(mkt,     on="customer_unique_id", how="left")
    df = df.merge(support,  on="customer_unique_id", how="left")
    df = df.merge(demo,     on="customer_unique_id", how="left")
    return df

def prepare_features(df):
    # ⚠️ Removed: recency_days, R_score, F_score, M_score, RFM_score
    # These directly encode or correlate with the churn label definition
    features = [
        "frequency",
        "monetary",
        "engagement_score",
        "spend_per_order",
        "avg_order_value",
        "avg_review_score",
        "avg_delivery_delay",
        "late_delivery_rate",
        "total_items_bought",
        "customer_tenure_days",
        "repeat_customer_flag",
        "clv_estimate",
        "has_support_ticket",
        "acquisition_cost"
    ]

    le = LabelEncoder()
    df["channel_encoded"] = le.fit_transform(df["acquisition_channel"].fillna("Unknown"))
    df["age_encoded"]     = le.fit_transform(df["age_group"].fillna("Unknown"))
    df["income_encoded"]  = le.fit_transform(df["income_segment"].fillna("Unknown"))

    features += ["channel_encoded", "age_encoded", "income_encoded"]

    df[features] = df[features].fillna(0)

    X = df[features]
    y = df["churn_label"]
    return X, y, features

def train_models(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set: {X_train.shape[0]} | Test set: {X_test.shape[0]}")
    print(f"Churn rate in train: {y_train.mean()*100:.1f}%\n")

    # ── Logistic Regression ───────────────────────────────────
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    lr_auc  = roc_auc_score(y_test, lr.predict_proba(X_test)[:,1])
    print("── Logistic Regression ──")
    print(classification_report(y_test, lr_pred))
    print(f"AUC: {lr_auc:.4f}\n")

    # ── Random Forest ─────────────────────────────────────────
    rf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_auc  = roc_auc_score(y_test, rf.predict_proba(X_test)[:,1])
    print("── Random Forest ──")
    print(classification_report(y_test, rf_pred))
    print(f"AUC: {rf_auc:.4f}\n")

    # ── Feature Importance ────────────────────────────────────
    feat_imp = pd.DataFrame({
        "feature":   X.columns,
        "importance": rf.feature_importances_
    }).sort_values("importance", ascending=False)
    print("── Top 10 Features (Random Forest) ──")
    print(feat_imp.head(10).to_string(index=False))

    # ── Save best model ───────────────────────────────────────
    best_model = rf if rf_auc >= lr_auc else lr
    with open(f"{MODELS}churn_model.pkl", "wb") as f:
        pickle.dump(best_model, f)
    print(f"\n✅ Best model saved → models/churn_model.pkl (AUC: {max(rf_auc, lr_auc):.4f})")

    feat_imp.to_csv(f"{MODELS}feature_importance.csv", index=False)
    return best_model, feat_imp

def generate_churn_report(df, model, features):
    X = df[features].fillna(0)
    df["churn_probability"] = model.predict_proba(X)[:,1]
    df["churn_prediction"]  = model.predict(X)

    # High risk customers
    high_risk = df[df["churn_probability"] > 0.75].sort_values(
        "churn_probability", ascending=False
    )[[
        "customer_unique_id", "recency_days", "frequency",
        "monetary", "avg_review_score", "customer_segment",
        "churn_probability"
    ]]

    high_risk.to_csv(f"{MODELS}high_risk_customers.csv", index=False)
    print(f"\n🔴 High churn risk customers (>75%): {len(high_risk)}")
    print(f"💰 Revenue at risk: R$ {high_risk['monetary'].sum():,.2f}")

if __name__ == "__main__":
    print("🤖 Building Churn Prediction Model...\n")
    df           = build_master_dataset()
    X, y, feats  = prepare_features(df)
    model, fi    = train_models(X, y)
    generate_churn_report(df, model, feats)
    print("\n✅ Phase 9 Complete — Churn model ready.")
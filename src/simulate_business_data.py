import pandas as pd
import numpy as np
import os

PROCESSED = "data/processed/"
os.makedirs(PROCESSED, exist_ok=True)

np.random.seed(42)

def load_customers():
    return pd.read_csv(f"{PROCESSED}customer_analytics.csv")

# ── MARKETING ATTRIBUTION ─────────────────────────────────────
def simulate_marketing(df):
    channels = ["Google Ads", "Instagram", "Organic", "Referral", "Email"]
    weights  = [0.30, 0.25, 0.20, 0.15, 0.10]

    df["acquisition_channel"] = np.random.choice(channels, size=len(df), p=weights)

    # Higher CLV customers slightly more likely from Referral/Email
    mask = df["customer_segment"].isin(["VIP", "Loyal"])
    df.loc[mask, "acquisition_channel"] = np.random.choice(
        channels, size=mask.sum(), p=[0.20, 0.20, 0.15, 0.25, 0.20]
    )

    channel_cost = {"Google Ads": 18, "Instagram": 14, "Organic": 2, "Referral": 8, "Email": 3}
    df["acquisition_cost"] = df["acquisition_channel"].map(channel_cost)
    df["marketing_roi"]    = (df["monetary"] - df["acquisition_cost"]) / df["acquisition_cost"].replace(0,1)

    out = df[["customer_unique_id", "acquisition_channel", "acquisition_cost", "marketing_roi"]]
    out.to_csv(f"{PROCESSED}marketing_attribution.csv", index=False)
    print(f"✅ marketing_attribution: {out.shape}")
    return df

# ── CUSTOMER SUPPORT ──────────────────────────────────────────
def simulate_support(df):
    ticket_types = ["Delivery Issue", "Payment Problem", "Product Defect", "Refund Request", "General Query"]

    # Customers with low reviews or late deliveries more likely to raise tickets
    has_ticket = np.random.rand(len(df)) < 0.35
    df["has_support_ticket"] = has_ticket.astype(int)

    # Low review score customers have higher ticket probability
    low_review = df["avg_review_score"] < 3
    df.loc[low_review, "has_support_ticket"] = (np.random.rand(low_review.sum()) < 0.70).astype(int)

    n = len(df)
    df["ticket_type"]           = np.where(df["has_support_ticket"],
                                    np.random.choice(ticket_types, n), None)
    df["resolution_days"]       = np.where(df["has_support_ticket"],
                                    np.random.randint(1, 15, n), None)
    df["support_satisfaction"]  = np.where(df["has_support_ticket"],
                                    np.random.choice([1,2,3,4,5], n, p=[0.10,0.15,0.25,0.30,0.20]), None)

    out = df[["customer_unique_id", "has_support_ticket", "ticket_type",
              "resolution_days", "support_satisfaction"]]
    out.to_csv(f"{PROCESSED}customer_support.csv", index=False)
    print(f"✅ customer_support: {out.shape}")
    return df

# ── CUSTOMER DEMOGRAPHICS ─────────────────────────────────────
def simulate_demographics(df):
    age_groups     = ["18-24", "25-34", "35-44", "45-54", "55+"]
    income_segs    = ["Low", "Mid", "High"]

    df["age_group"]      = np.random.choice(age_groups, len(df), p=[0.15, 0.35, 0.25, 0.15, 0.10])
    df["income_segment"] = np.random.choice(income_segs, len(df), p=[0.30, 0.45, 0.25])

    # VIP customers skew toward higher income
    vip_mask = df["customer_segment"] == "VIP"
    df.loc[vip_mask, "income_segment"] = np.random.choice(
        income_segs, vip_mask.sum(), p=[0.10, 0.35, 0.55]
    )

    out = df[["customer_unique_id", "age_group", "income_segment"]]
    out.to_csv(f"{PROCESSED}customer_demographics.csv", index=False)
    print(f"✅ customer_demographics: {out.shape}")
    return df

if __name__ == "__main__":
    print("🏗️  Simulating business context data...\n")
    df = load_customers()
    df = simulate_marketing(df)
    df = simulate_support(df)
    df = simulate_demographics(df)
    print("\n✅ Phase 5 Complete — Simulated business tables saved.")
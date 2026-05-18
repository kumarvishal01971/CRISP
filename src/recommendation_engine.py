import pandas as pd
import numpy as np
import os

PROCESSED = "data/processed/"
MODELS    = "models/"
os.makedirs(f"{MODELS}recommendations", exist_ok=True)

def load_data():
    rfm     = pd.read_csv(f"{PROCESSED}customer_analytics.csv")
    mkt     = pd.read_csv(f"{PROCESSED}marketing_attribution.csv")
    support = pd.read_csv(f"{PROCESSED}customer_support.csv")
    demo    = pd.read_csv(f"{PROCESSED}customer_demographics.csv")

    df = rfm.merge(mkt,     on="customer_unique_id", how="left")
    df = df.merge(support,  on="customer_unique_id", how="left")
    df = df.merge(demo,     on="customer_unique_id", how="left")
    return df

# ── Rule-based business recommendations ───────────────────────
def generate_recommendations(df):
    recommendations = []

    for _, row in df.iterrows():
        cid      = row["customer_unique_id"]
        segment  = row["customer_segment"]
        churn    = row["churn_label"]
        recency  = row["recency_days"]
        freq     = row["frequency"]
        monetary = row["monetary"]
        review   = row["avg_review_score"]
        delay    = row["avg_delivery_delay"]
        support  = row["has_support_ticket"]
        channel  = row["acquisition_channel"]
        clv      = row["clv_estimate"]

        actions = []
        priority = "Low"

        # ── Churn risk actions ────────────────────────────────
        if churn == 1 and recency > 180:
            actions.append("Send win-back email with 15% discount coupon")
            priority = "High"

        if churn == 1 and review < 3:
            actions.append("Escalate to customer success team for personal outreach")
            priority = "Critical"

        # ── Segment-based actions ─────────────────────────────
        if segment == "VIP":
            actions.append("Enroll in VIP loyalty program with free shipping")
            actions.append("Offer early access to new product launches")
            priority = "High" if priority == "Low" else priority

        elif segment == "Loyal":
            actions.append("Send personalised product recommendations via email")
            actions.append("Offer referral bonus — R$ 20 credit per referral")

        elif segment == "At Risk":
            actions.append("Trigger automated re-engagement campaign")
            actions.append("Offer limited-time bundle discount")
            priority = "High"

        elif segment == "Churning":
            actions.append("Last-chance offer: 25% discount, expires in 48 hours")
            priority = "Critical"

        # ── Review-based actions ──────────────────────────────
        if pd.notna(review) and review < 3:
            actions.append("Investigate delivery/product issues — offer partial refund")
            priority = "High" if priority == "Low" else priority

        # ── Delivery experience actions ───────────────────────
        if pd.notna(delay) and delay > 5:
            actions.append("Apologise for delivery delay — offer next-order free shipping")

        # ── Support ticket actions ────────────────────────────
        if support == 1:
            actions.append("Follow up on open support ticket before next campaign")

        # ── Channel optimisation ──────────────────────────────
        if channel == "Google Ads" and clv < 100:
            actions.append("Review Google Ads targeting — low CLV from this channel")

        if channel == "Organic" and clv > 300:
            actions.append("Invest more in SEO/content — high CLV organic customers")

        # ── Default ───────────────────────────────────────────
        if not actions:
            actions.append("No immediate action required — monitor engagement monthly")
            priority = "Low"

        recommendations.append({
            "customer_unique_id": cid,
            "segment":            segment,
            "churn_risk":         "Yes" if churn == 1 else "No",
            "priority":           priority,
            "num_actions":        len(actions),
            "recommended_actions": " | ".join(actions)
        })

    return pd.DataFrame(recommendations)

def generate_summary(rec_df, df):
    print("\n📋 RECOMMENDATION SUMMARY")
    print("─" * 45)
    print(f"Total customers analysed : {len(rec_df):,}")
    print(f"Critical priority        : {(rec_df['priority']=='Critical').sum():,}")
    print(f"High priority            : {(rec_df['priority']=='High').sum():,}")
    print(f"Low priority             : {(rec_df['priority']=='Low').sum():,}")
    print(f"\nChurn risk — Yes         : {(rec_df['churn_risk']=='Yes').sum():,}")
    print(f"Churn risk — No          : {(rec_df['churn_risk']=='No').sum():,}")

    print("\n📊 Actions by Segment:")
    seg_summary = rec_df.groupby("segment").agg(
        customers   = ("customer_unique_id", "count"),
        avg_actions = ("num_actions", "mean"),
        critical    = ("priority", lambda x: (x == "Critical").sum()),
        high        = ("priority", lambda x: (x == "High").sum()),
    ).round(2)
    print(seg_summary.to_string())

    # Save summary
    seg_summary.to_csv(f"{MODELS}recommendations/segment_action_summary.csv")

def save_outputs(rec_df):
    # Full recommendations
    rec_df.to_csv(f"{MODELS}recommendations/all_recommendations.csv", index=False)

    # Critical only
    critical = rec_df[rec_df["priority"] == "Critical"]
    critical.to_csv(f"{MODELS}recommendations/critical_customers.csv", index=False)

    # High priority
    high = rec_df[rec_df["priority"] == "High"]
    high.to_csv(f"{MODELS}recommendations/high_priority_customers.csv", index=False)

    print(f"\n✅ Saved:")
    print(f"   all_recommendations.csv     → {len(rec_df):,} rows")
    print(f"   critical_customers.csv      → {len(critical):,} rows")
    print(f"   high_priority_customers.csv → {len(high):,} rows")

if __name__ == "__main__":
    print("🎯 Generating Customer Recommendations...\n")
    df      = load_data()
    rec_df  = generate_recommendations(df)
    generate_summary(rec_df, df)
    save_outputs(rec_df)
    print("\n✅ Phase 10 Complete — Recommendation engine done.")
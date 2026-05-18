import pandas as pd
import numpy as np
import os

CLEAN = "data/cleaned/"
PROCESSED = "data/processed/"
os.makedirs(PROCESSED, exist_ok=True)

def load_clean_data():
    customers     = pd.read_csv(f"{CLEAN}customers.csv")
    orders        = pd.read_csv(f"{CLEAN}orders.csv", parse_dates=[
                        "order_purchase_timestamp", "order_approved_at",
                        "order_delivered_carrier_date", "order_delivered_customer_date",
                        "order_estimated_delivery_date"])
    order_items   = pd.read_csv(f"{CLEAN}order_items.csv")
    order_payments= pd.read_csv(f"{CLEAN}order_payments.csv")
    order_reviews = pd.read_csv(f"{CLEAN}order_reviews.csv")
    return customers, orders, order_items, order_payments, order_reviews

def build_customer_features():
    print("⚙️  Building customer features...")
    customers, orders, order_items, order_payments, order_reviews = load_clean_data()

    # ── Snapshot date (day after last purchase) ───────────────
    snapshot_date = orders["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    # ── Payment per order ─────────────────────────────────────
    payment_per_order = order_payments.groupby("order_id")["payment_value"].sum().reset_index()
    payment_per_order.columns = ["order_id", "total_payment"]

    # ── Order items per order ─────────────────────────────────
    items_per_order = order_items.groupby("order_id").agg(
        item_count=("order_item_id", "count"),
        order_revenue=("price", "sum"),
        order_freight=("freight_value", "sum")
    ).reset_index()

    # ── Reviews per order ─────────────────────────────────────
    review_per_order = order_reviews.groupby("order_id")["review_score"].mean().reset_index()
    review_per_order.columns = ["order_id", "review_score"]

    # ── Merge everything to orders ────────────────────────────
    orders = orders.merge(payment_per_order, on="order_id", how="left")
    orders = orders.merge(items_per_order, on="order_id", how="left")
    orders = orders.merge(review_per_order, on="order_id", how="left")

    # ── Delivery delay (actual vs estimated) ──────────────────
    orders["delivery_delay_days"] = (
        orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
    ).dt.days
    orders["late_delivery_flag"] = (orders["delivery_delay_days"] > 0).astype(int)

    # ── Merge orders to customers ─────────────────────────────
    df = orders.merge(customers, on="customer_id", how="left")

    # ── RFM Features ──────────────────────────────────────────
    # Use customer_unique_id so repeat customers are tracked correctly
    rfm = df.groupby("customer_unique_id").agg(
        recency_days        = ("order_purchase_timestamp", lambda x: (snapshot_date - x.max()).days),
        frequency           = ("order_id", "count"),
        monetary            = ("total_payment", "sum"),
        avg_order_value     = ("total_payment", "mean"),
        avg_review_score    = ("review_score", "mean"),
        avg_delivery_delay  = ("delivery_delay_days", "mean"),
        late_delivery_rate  = ("late_delivery_flag", "mean"),
        total_items_bought  = ("item_count", "sum"),
        first_purchase_date = ("order_purchase_timestamp", "min"),
        last_purchase_date  = ("order_purchase_timestamp", "max"),
    ).reset_index()

    # ── Derived features ──────────────────────────────────────
    rfm["customer_tenure_days"] = (
        rfm["last_purchase_date"] - rfm["first_purchase_date"]
    ).dt.days

    rfm["repeat_customer_flag"] = (rfm["frequency"] > 1).astype(int)

    # CLV = total spend * purchase frequency weight (tenure-based)
    rfm["clv_estimate"] = rfm["monetary"] * (1 + np.log1p(rfm["frequency"]))

    # ── RFM Scoring (1–5) ─────────────────────────────────────
    rfm["R_score"] = pd.qcut(rfm["recency_days"], q=5, labels=[5,4,3,2,1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5, labels=[1,2,3,4,5]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), q=5, labels=[1,2,3,4,5]).astype(int)
    rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    # ── Customer Segments ─────────────────────────────────────
    def segment(row):
        if row["RFM_score"] >= 13:
            return "VIP"
        elif row["RFM_score"] >= 10:
            return "Loyal"
        elif row["RFM_score"] >= 7:
            return "Regular"
        elif row["RFM_score"] >= 4:
            return "At Risk"
        else:
            return "Churning"

    rfm["customer_segment"] = rfm.apply(segment, axis=1)

    # ── Churn label (no purchase in last 180 days) ────────────
    # Churn = inactive AND low frequency AND low monetary (truly lost customers)
    rfm["churn_label"] = (
        (rfm["recency_days"] > 180) &
        (rfm["frequency"] <= 2) &
        (rfm["monetary"] < rfm["monetary"].median())
    ).astype(int)


    # Engagement score — higher is more engaged
    rfm["engagement_score"] = (
        rfm["avg_review_score"].fillna(3) * 0.3 +
        np.log1p(rfm["frequency"]) * 0.4 +
        (1 / (rfm["avg_delivery_delay"].fillna(0).abs() + 1)) * 0.3
    )
    
    # Spend consistency
    rfm["spend_per_order"] = rfm["monetary"] / rfm["frequency"].replace(0, 1)

    # ── Save ──────────────────────────────────────────────────
    rfm.to_csv(f"{PROCESSED}customer_analytics.csv", index=False)
    print(f"✅ customer_analytics: {rfm.shape}")
    print(f"\n📊 Segment Distribution:\n{rfm['customer_segment'].value_counts()}")
    print(f"\n🔴 Churn Rate: {rfm['churn_label'].mean()*100:.1f}%")
    print(f"🔁 Repeat Customer Rate: {rfm['repeat_customer_flag'].mean()*100:.1f}%")
    print(f"💰 Avg CLV Estimate: R$ {rfm['clv_estimate'].mean():.2f}")
    return rfm

if __name__ == "__main__":
    print("⚙️  Starting Feature Engineering...\n")
    rfm = build_customer_features()
    print("\n✅ Phase 4 Complete — customer_analytics.csv saved to data/processed/")
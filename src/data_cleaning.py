import pandas as pd
import os

RAW = "data/raw/"
CLEAN = "data/cleaned/"
os.makedirs(CLEAN, exist_ok=True)

def load(name):
    path = os.path.join(RAW, f"olist_{name}_dataset.csv")
    if not os.path.exists(path):
        path = os.path.join(RAW, f"{name}.csv")
    return pd.read_csv(path)

# ── CUSTOMERS ─────────────────────────────────────────────────
def clean_customers():
    df = load("customers")
    df.drop_duplicates(subset="customer_id", inplace=True)
    df["customer_city"] = df["customer_city"].str.strip().str.title()
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    df.to_csv(f"{CLEAN}customers.csv", index=False)
    print(f"✅ customers: {df.shape}")
    return df

# ── ORDERS ────────────────────────────────────────────────────
def clean_orders():
    df = load("orders")
    timestamp_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Validation: delivery must be after purchase
    mask = (
        df["order_delivered_customer_date"].notna() &
        (df["order_delivered_customer_date"] < df["order_purchase_timestamp"])
    )
    print(f"  ⚠️  Invalid delivery dates removed: {mask.sum()}")
    df = df[~mask]
    df.drop_duplicates(subset="order_id", inplace=True)
    df.to_csv(f"{CLEAN}orders.csv", index=False)
    print(f"✅ orders: {df.shape}")
    return df

# ── ORDER ITEMS ───────────────────────────────────────────────
def clean_order_items():
    df = load("order_items")
    df = df[df["price"] >= 0]
    df = df[df["freight_value"] >= 0]
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df.drop_duplicates(inplace=True)
    df.to_csv(f"{CLEAN}order_items.csv", index=False)
    print(f"✅ order_items: {df.shape}")
    return df

# ── ORDER PAYMENTS ────────────────────────────────────────────
def clean_order_payments():
    df = load("order_payments")
    df = df[df["payment_value"] >= 0]
    df.drop_duplicates(inplace=True)
    df.to_csv(f"{CLEAN}order_payments.csv", index=False)
    print(f"✅ order_payments: {df.shape}")
    return df

# ── ORDER REVIEWS ─────────────────────────────────────────────
def clean_order_reviews():
    df = load("order_reviews")
    df = df[df["review_score"].between(1, 5)]
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")
    df.drop_duplicates(subset=["review_id", "order_id"], inplace=True)
    df.to_csv(f"{CLEAN}order_reviews.csv", index=False)
    print(f"✅ order_reviews: {df.shape}")
    return df

# ── PRODUCTS ──────────────────────────────────────────────────
def clean_products():
    df = load("products")
    df["product_category_name"] = df["product_category_name"].fillna("unknown")
    num_cols = ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())
    df.drop_duplicates(subset="product_id", inplace=True)
    df.to_csv(f"{CLEAN}products.csv", index=False)
    print(f"✅ products: {df.shape}")
    return df

# ── SELLERS ───────────────────────────────────────────────────
def clean_sellers():
    df = load("sellers")
    df["seller_city"] = df["seller_city"].str.strip().str.title()
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    df.drop_duplicates(subset="seller_id", inplace=True)
    df.to_csv(f"{CLEAN}sellers.csv", index=False)
    print(f"✅ sellers: {df.shape}")
    return df

# ── GEOLOCATION ───────────────────────────────────────────────
def clean_geolocation():
    df = load("geolocation")
    # deduplicate by zip prefix (keep first lat/lng per zip)
    df.drop_duplicates(subset="geolocation_zip_code_prefix", keep="first", inplace=True)
    df["geolocation_city"] = df["geolocation_city"].str.strip().str.title()
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()
    df.to_csv(f"{CLEAN}geolocation.csv", index=False)
    print(f"✅ geolocation: {df.shape}")
    return df

# ── PRODUCT CATEGORY TRANSLATION ──────────────────────────────
def clean_category_translation():
    path = os.path.join(RAW, "product_category_name_translation.csv")
    df = pd.read_csv(path)
    df.drop_duplicates(inplace=True)
    df.to_csv(f"{CLEAN}product_category_name_translation.csv", index=False)
    print(f"✅ category_translation: {df.shape}")
    return df

# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧹 Starting Data Cleaning Pipeline...\n")
    clean_customers()
    clean_orders()
    clean_order_items()
    clean_order_payments()
    clean_order_reviews()
    clean_products()
    clean_sellers()
    clean_geolocation()
    clean_category_translation()
    print("\n✅ Phase 3 Complete — All cleaned files saved to data/cleaned/")
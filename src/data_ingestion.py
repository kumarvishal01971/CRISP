import pandas as pd
import os
import json

RAW_DATA_PATH = "data/raw/"
OUTPUT_PATH = "outputs/"

# ── Load all CSVs ──────────────────────────────────────────────
def load_all_tables():
    tables = {}
    for file in os.listdir(RAW_DATA_PATH):
        if file.endswith(".csv"):
            name = file.replace(".csv", "").replace("olist_", "").replace("_dataset", "")
            tables[name] = pd.read_csv(os.path.join(RAW_DATA_PATH, file))
            print(f"✅ Loaded: {name} → {tables[name].shape}")
    return tables

# ── Table Summary ──────────────────────────────────────────────
def table_summary(tables):
    summary = []
    for name, df in tables.items():
        summary.append({
            "table": name,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": list(df.columns)
        })
    df_summary = pd.DataFrame(summary)
    df_summary.to_csv(f"{OUTPUT_PATH}table_summary/table_summary.csv", index=False)
    print("\n📊 Table Summary saved.")
    return df_summary

# ── Column Audit (dtypes + nulls) ─────────────────────────────
def column_audit(tables):
    all_audits = []
    for name, df in tables.items():
        for col in df.columns:
            all_audits.append({
                "table": name,
                "column": col,
                "dtype": str(df[col].dtype),
                "null_count": df[col].isnull().sum(),
                "null_pct": round(df[col].isnull().mean() * 100, 2),
                "unique_values": df[col].nunique(),
                "sample_value": str(df[col].dropna().iloc[0]) if df[col].notna().any() else "ALL NULL"
            })
    df_audit = pd.DataFrame(all_audits)
    df_audit.to_csv(f"{OUTPUT_PATH}column_audit/column_audit.csv", index=False)
    print("🔍 Column Audit saved.")
    return df_audit

# ── Relationship Map ───────────────────────────────────────────
def relationship_map():
    relationships = {
        "customers": {"pk": "customer_id", "fk_to": []},
        "orders": {"pk": "order_id", "fk_to": ["customers.customer_id"]},
        "order_items": {"pk": None, "fk_to": ["orders.order_id", "products.product_id", "sellers.seller_id"]},
        "order_payments": {"pk": None, "fk_to": ["orders.order_id"]},
        "order_reviews": {"pk": "review_id", "fk_to": ["orders.order_id"]},
        "products": {"pk": "product_id", "fk_to": []},
        "sellers": {"pk": "seller_id", "fk_to": []},
        "geolocation": {"pk": None, "fk_to": []},
        "product_category_name_translation": {"pk": "product_category_name", "fk_to": []}
    }
    with open(f"{OUTPUT_PATH}relationship_map/relationships.json", "w") as f:
        json.dump(relationships, f, indent=2)
    print("🔗 Relationship Map saved.")
    return relationships

# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(f"{OUTPUT_PATH}table_summary", exist_ok=True)
    os.makedirs(f"{OUTPUT_PATH}column_audit", exist_ok=True)
    os.makedirs(f"{OUTPUT_PATH}relationship_map", exist_ok=True)

    tables = load_all_tables()
    summary = table_summary(tables)
    audit = column_audit(tables)
    rel = relationship_map()

    print("\n✅ Phase 1 Complete — Data Understanding Done!")
    print("\n--- TABLE SUMMARY ---")
    print(summary.to_string(index=False))
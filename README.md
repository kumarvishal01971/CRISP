# CRISP : E-Commerce Analytics Platform

> End-to-end Customer Revenue Intelligence & Strategy Platform built on 100K+ real e-commerce transactions.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45-red?logo=streamlit)
![Scikit-learn](https://img.shields.io/badge/ScikitLearn-1.5.2-orange?logo=scikit-learn)
![Plotly](https://img.shields.io/badge/Plotly-5.24-purple?logo=plotly)
![SQL](https://img.shields.io/badge/MySQL-Schema-blue?logo=mysql)

---

## 🎯 What This Project Does

CRISP answers four core business questions:

| Question | Answer |
|---|---|
| Which customers matter most? | RFM segmentation — VIP, Loyal, Regular, At Risk, Churning |
| Who is likely to leave? | Churn model — AUC 0.92, 34,500 high-risk customers flagged |
| What drives revenue? | SQL analytics — channel, geography, product, segment breakdown |
| What actions should be taken? | Rule-based recommendation engine — 96K customers, 3 priority levels |

---

## 📊 Live Dashboard

🔗 **[Launch App →](https://crisp-kumarvishal01971.streamlit.app/)⚡⚡⚡**

![Dashboard Preview](https://i.postimg.cc/nLVy5QDZ/Screenshot-2026-05-22-000235.png)

---

## 🗂 Project Structure
```
CRISP/
.
├── dashboard
│   └── app.py
├── data
│   ├── cleaned
│   │   ├── customers.csv
│   │   ├── geolocation.csv
│   │   ├── order_items.csv
│   │   ├── order_payments.csv
│   │   ├── order_reviews.csv
│   │   ├── orders.csv
│   │   ├── product_category_name_translation.csv
│   │   ├── products.csv
│   │   └── sellers.csv
│   ├── processed
│   │   ├── customer_analytics.csv
│   │   ├── customer_demographics.csv
│   │   ├── customer_support.csv
│   │   └── marketing_attribution.csv
│   └── raw
│       ├── archive.zip
│       ├── olist_customers_dataset.csv
│       ├── olist_geolocation_dataset.csv
│       ├── olist_order_items_dataset.csv
│       ├── olist_order_payments_dataset.csv
│       ├── olist_order_reviews_dataset.csv
│       ├── olist_orders_dataset.csv
│       ├── olist_products_dataset.csv
│       ├── olist_sellers_dataset.csv
│       └── product_category_name_translation.csv
├── models
│   ├── recommendations
│   │   ├── all_recommendations.csv
│   │   ├── critical_customers.csv
│   │   ├── high_priority_customers.csv
│   │   └── segment_action_summary.csv
│   ├── churn_model.pkl
│   ├── feature_importance.csv
│   ├── high_risk_customers.csv
│   └── prediction_log.csv
├── notebooks
├── outputs
│   ├── column_audit
│   │   └── column_audit.csv
│   ├── relationship_map
│   │   └── relationships.json
│   └── table_summary
│       └── table_summary.csv
├── reports
├── sql
│   ├── business_queries.sql
│   ├── kpi_queries.sql
│   ├── schema.sql
│   └── views.sql
├── src
│   ├── churn_model.py
│   ├── data_cleaning.py
│   ├── data_ingestion.py
│   ├── feature_engineering.py
│   ├── recommendation_engine.py
│   ├── simulate_business_data.py
│   └── utils.py
└── requirements.txt
```
---

## 🔢 Key Numbers

| Metric | Value |
|---|---|
| Customers analysed | 96,096 |
| Total orders | 99,441 |
| Churn rate | 35.9% |
| Churn model AUC | 0.92 |
| High-risk customers | 34,500 |
| Revenue at risk | R$ 2,000,000 |
| Repeat customer rate | 3.1% |
| Avg customer CLV | R$ 286 |

---

## 🏗 Pipeline
```
Raw CSVs (Olist)
↓
Data Cleaning        → data/cleaned/
↓
Feature Engineering  → RFM scores, CLV, engagement, churn label
↓
Business Simulation  → marketing attribution, support, demographics
↓
SQL Analytics        → 20+ queries, KPI layer
↓
Churn Model          → Random Forest, AUC 0.92
↓
Recommendation Engine → 96K customers, 3 priority levels
↓
Streamlit Dashboard  → 6 pages, live predictor, prediction logging
```
---

## 📱 Dashboard Pages

| Page | What it shows |
|---|---|
| 🏠 Executive Summary | Total revenue, churn rate, CLV, monthly trend |
| 👥 Customer Intelligence | Segment breakdown, RFM scatter, age/channel mix |
| 📈 Revenue Analytics | Channel ROI, income segment, spend distribution |
| 🔴 Churn Analysis | Churn by segment/channel, feature importance |
| 🎯 Recommendations | Filterable action table — Critical/High/Low priority |
| 🤖 Churn Predictor | Live prediction with gauge chart + prediction logging |

---

## 🤖 Churn Model

**Algorithm:** Random Forest (50 trees, max_depth=10)  
**AUC:** 0.92  
**Churn definition:** Inactive > 180 days + frequency ≤ 2 + spend below median

Top predictive features:

| Feature | Importance |
|---|---|
| Monetary (total spend) | 33.4% |
| CLV Estimate | 23.6% |
| Avg Order Value | 20.9% |
| Spend per Order | 16.7% |
| Engagement Score | 1.4% |

> **Note:** Initial model had AUC 1.0 due to data leakage (`recency_days` directly encoded the churn label). Leakage was identified and removed — final AUC 0.92 uses only behavioral features.

---

## 🚀 Run Locally

```bash
# Clone
git clone https://github.com/kumarvishal01971/CRISP.git
cd CRISP

# Install dependencies
pip install -r requirements.txt

# Run pipeline (first time only)
python src/data_cleaning.py
python src/feature_engineering.py
python src/simulate_business_data.py
python src/churn_model.py
python src/recommendation_engine.py

# Launch dashboard
streamlit run dashboard/app.py
```
🔗 **[Launch App →](https://crisp-kumarvishal01971.streamlit.app/)⚡⚡⚡**

---

## 📦 Dataset

[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — Kaggle  
9 relational tables · 100K orders · 2016–2018

---

## 👤 Author

**Vishal Kumar**  
B.Tech AI & ML — GGSIPU, New Delhi  
[LinkedIn](https://www.linkedin.com/in/kumarvishal01971-w222b/)

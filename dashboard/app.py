import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="CRISP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    rfm      = pd.read_csv("data/processed/customer_analytics.csv")
    mkt      = pd.read_csv("data/processed/marketing_attribution.csv")
    support  = pd.read_csv("data/processed/customer_support.csv")
    demo     = pd.read_csv("data/processed/customer_demographics.csv")
    rec      = pd.read_csv("models/recommendations/all_recommendations.csv")
    orders   = pd.read_csv("data/cleaned/orders.csv", parse_dates=["order_purchase_timestamp"])
    payments = pd.read_csv("data/cleaned/order_payments.csv")

    df = rfm.merge(mkt,    on="customer_unique_id", how="left")
    df = df.merge(support, on="customer_unique_id", how="left")
    df = df.merge(demo,    on="customer_unique_id", how="left")
    df = df.merge(rec[["customer_unique_id","priority","recommended_actions"]],
                  on="customer_unique_id", how="left")
    return df, orders, payments

@st.cache_resource
def load_model():
    with open("models/churn_model.pkl", "rb") as f:
        return pickle.load(f)

df, orders, payments = load_data()
model = load_model()

LOG_PATH = "models/prediction_log.csv"

def save_prediction(row: dict):
    log_df = pd.DataFrame([row])
    if os.path.exists(LOG_PATH):
        existing = pd.read_csv(LOG_PATH)
        updated  = pd.concat([existing, log_df], ignore_index=True)
    else:
        updated = log_df
    updated.to_csv(LOG_PATH, index=False)
    return updated

def load_log():
    if os.path.exists(LOG_PATH):
        return pd.read_csv(LOG_PATH)
    return pd.DataFrame()

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.markdown("""
<img src="https://i.postimg.cc/mrcFs9Lz/Pngtree-wolf-head-icon-logo-vector-5061887.png"
     width="180"
     style="margin-left:-40px;">
""", unsafe_allow_html=True)
st.sidebar.markdown("<h1 style='font-size:40px;margin-top:-50px;'>CRISP</h1>", unsafe_allow_html=True)
st.sidebar.caption("Customer Revenue Intelligence and Strategy Platform")

page = st.sidebar.radio("Navigate", [
    "🏠 Executive Summary",
    "👥 Customer Intelligence",
    "📈 Revenue Analytics",
    "🔴 Churn Analysis",
    "🎯 Recommendations",
    "🤖 Churn Predictor"
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Dataset:** {len(df):,} customers")
st.sidebar.markdown(f"**Revenue at Risk:** R$ {df[df['churn_label']==1]['monetary'].sum():,.0f}")

# ══════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════
if page == "🏠 Executive Summary":
    st.title("📊 Executive Summary")
    st.caption("Platform-level KPIs at a glance")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Customers",  f"{len(df):,}")
    col2.metric("Total Revenue",    f"R$ {df['monetary'].sum():,.0f}")
    col3.metric("Avg CLV",          f"R$ {df['clv_estimate'].mean():,.0f}")
    col4.metric("Churn Rate",       f"{df['churn_label'].mean()*100:.1f}%")
    col5.metric("Repeat Rate",      f"{df['repeat_customer_flag'].mean()*100:.1f}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        seg = df["customer_segment"].value_counts().reset_index()
        seg.columns = ["Segment", "Count"]
        fig = px.pie(seg, names="Segment", values="Count",
                     title="Customer Segment Distribution",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        op = orders.merge(payments, on="order_id", how="left")
        op["month"] = op["order_purchase_timestamp"].dt.to_period("M").astype(str)
        monthly = op.groupby("month")["payment_value"].sum().reset_index()
        monthly.columns = ["Month", "Revenue"]
        fig2 = px.line(monthly, x="Month", y="Revenue",
                       title="Monthly Revenue Trend", markers=True,
                       color_discrete_sequence=["#00CC96"])
        fig2.update_xaxes(tickangle=45)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        seg_rev = df.groupby("customer_segment")["monetary"].sum().reset_index()
        seg_rev.columns = ["Segment", "Revenue"]
        seg_rev = seg_rev.sort_values("Revenue", ascending=True)
        fig3 = px.bar(seg_rev, x="Revenue", y="Segment", orientation="h",
                      title="Revenue by Customer Segment",
                      color="Revenue", color_continuous_scale="Teal")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        pri = df["priority"].value_counts().reset_index()
        pri.columns = ["Priority", "Count"]
        color_map = {"Critical": "#EF553B", "High": "#FFA15A", "Low": "#00CC96"}
        fig4 = px.bar(pri, x="Priority", y="Count",
                      title="Action Priority Distribution",
                      color="Priority", color_discrete_map=color_map)
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 2 — CUSTOMER INTELLIGENCE
# ══════════════════════════════════════════════════════════════
elif page == "👥 Customer Intelligence":
    st.title("👥 Customer Intelligence")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VIP Customers",   f"{(df['customer_segment']=='VIP').sum():,}")
    col2.metric("Loyal Customers", f"{(df['customer_segment']=='Loyal').sum():,}")
    col3.metric("At Risk",         f"{(df['customer_segment']=='At Risk').sum():,}")
    col4.metric("Churning",        f"{(df['customer_segment']=='Churning').sum():,}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.box(df, x="customer_segment", y="clv_estimate",
                     title="CLV Distribution by Segment",
                     color="customer_segment",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_yaxes(range=[0, df["clv_estimate"].quantile(0.95)])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sample = df.sample(min(3000, len(df)), random_state=42)
        fig2 = px.scatter(sample, x="recency_days", y="monetary",
                          color="customer_segment", size="frequency",
                          title="RFM Scatter — Recency vs Monetary",
                          opacity=0.6,
                          color_discrete_sequence=px.colors.qualitative.Set1)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        age = df["age_group"].value_counts().reset_index()
        age.columns = ["Age Group", "Count"]
        fig3 = px.bar(age, x="Age Group", y="Count",
                      title="Customers by Age Group",
                      color="Count", color_continuous_scale="Blues")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        ch = df["acquisition_channel"].value_counts().reset_index()
        ch.columns = ["Channel", "Count"]
        fig4 = px.pie(ch, names="Channel", values="Count",
                      title="Acquisition Channel Mix",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 3 — REVENUE ANALYTICS
# ══════════════════════════════════════════════════════════════
elif page == "📈 Revenue Analytics":
    st.title("📈 Revenue Analytics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue",   f"R$ {df['monetary'].sum():,.0f}")
    col2.metric("Avg Order Value", f"R$ {df['avg_order_value'].mean():,.2f}")
    col3.metric("Avg CLV",         f"R$ {df['clv_estimate'].mean():,.2f}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        ch_rev = df.groupby("acquisition_channel")["monetary"].agg(["sum","mean"]).reset_index()
        ch_rev.columns = ["Channel", "Total Revenue", "Avg Revenue"]
        fig = px.bar(ch_rev, x="Channel", y="Total Revenue",
                     title="Revenue by Acquisition Channel",
                     color="Avg Revenue", color_continuous_scale="Viridis")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        inc = df.groupby("income_segment")["monetary"].sum().reset_index()
        inc.columns = ["Income Segment", "Revenue"]
        fig2 = px.pie(inc, names="Income Segment", values="Revenue",
                      title="Revenue by Income Segment",
                      color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        clv_ch = df.groupby("acquisition_channel")["clv_estimate"].mean().reset_index()
        clv_ch.columns = ["Channel", "Avg CLV"]
        clv_ch = clv_ch.sort_values("Avg CLV", ascending=True)
        fig3 = px.bar(clv_ch, x="Avg CLV", y="Channel", orientation="h",
                      title="Avg CLV by Acquisition Channel",
                      color="Avg CLV", color_continuous_scale="Teal")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.histogram(df[df["monetary"] < df["monetary"].quantile(0.95)],
                            x="monetary", nbins=50,
                            title="Customer Spend Distribution (95th pct)",
                            color_discrete_sequence=["#636EFA"])
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 4 — CHURN ANALYSIS
# ══════════════════════════════════════════════════════════════
elif page == "🔴 Churn Analysis":
    st.title("🔴 Churn Analysis")

    churned = df[df["churn_label"] == 1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Churn Rate",            f"{df['churn_label'].mean()*100:.1f}%")
    col2.metric("Churned Customers",     f"{len(churned):,}")
    col3.metric("Revenue at Risk",       f"R$ {churned['monetary'].sum():,.0f}")
    col4.metric("Avg Recency (Churned)", f"{churned['recency_days'].mean():.0f} days")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        churn_seg = df.groupby("customer_segment")["churn_label"].mean().reset_index()
        churn_seg.columns = ["Segment", "Churn Rate"]
        churn_seg["Churn Rate"] = churn_seg["Churn Rate"] * 100
        fig = px.bar(churn_seg, x="Segment", y="Churn Rate",
                     title="Churn Rate by Segment (%)",
                     color="Churn Rate", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        churn_ch = df.groupby("acquisition_channel")["churn_label"].mean().reset_index()
        churn_ch.columns = ["Channel", "Churn Rate"]
        churn_ch["Churn Rate"] = churn_ch["Churn Rate"] * 100
        fig2 = px.bar(churn_ch, x="Channel", y="Churn Rate",
                      title="Churn Rate by Acquisition Channel (%)",
                      color="Churn Rate", color_continuous_scale="Oranges")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig3 = px.histogram(df, x="avg_review_score", color="churn_label",
                            barmode="overlay", nbins=5,
                            title="Review Score — Churned vs Retained",
                            labels={"churn_label": "Churned"},
                            color_discrete_map={0: "#00CC96", 1: "#EF553B"})
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fi = pd.read_csv("models/feature_importance.csv").head(8)
        fig4 = px.bar(fi, x="importance", y="feature", orientation="h",
                      title="Top Churn Prediction Features",
                      color="importance", color_continuous_scale="Blues")
        fig4.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 5 — RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════
elif page == "🎯 Recommendations":
    st.title("🎯 Customer Action Recommendations")

    col1, col2, col3 = st.columns(3)
    col1.metric("Critical Priority", f"{(df['priority']=='Critical').sum():,}", delta="Needs immediate action")
    col2.metric("High Priority",     f"{(df['priority']=='High').sum():,}")
    col3.metric("Low Priority",      f"{(df['priority']=='Low').sum():,}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        seg_filter = st.multiselect("Filter by Segment",
                                    options=df["customer_segment"].unique(),
                                    default=df["customer_segment"].unique())
    with col2:
        pri_filter = st.multiselect("Filter by Priority",
                                    options=["Critical", "High", "Low"],
                                    default=["Critical", "High"])

    filtered = df[
        (df["customer_segment"].isin(seg_filter)) &
        (df["priority"].isin(pri_filter))
    ][["customer_unique_id","customer_segment","monetary",
       "avg_review_score","churn_label","priority","recommended_actions"]]

    filtered = filtered.copy()
    filtered.columns = ["Customer ID","Segment","Revenue","Avg Review","Churn Risk","Priority","Actions"]
    filtered["Churn Risk"] = filtered["Churn Risk"].map({1:"Yes", 0:"No"})
    filtered["Revenue"]    = filtered["Revenue"].round(2)

    st.dataframe(filtered.head(500), use_container_width=True, height=400)
    st.caption(f"Showing top 500 of {len(filtered):,} filtered customers")

# ══════════════════════════════════════════════════════════════
# PAGE 6 — CHURN PREDICTOR
# ══════════════════════════════════════════════════════════════
elif page == "🤖 Churn Predictor":
    st.title("🤖 Live Churn Predictor")
    st.caption("Tip: To see HIGH churn risk → set Frequency=1, Total Spend < 100, Review Score=1")

    col1, col2, col3 = st.columns(3)

    with col1:
        frequency       = st.slider("Purchase Frequency",        1, 20, 1)
        monetary        = st.number_input("Total Spend (R$)",     0.0, 10000.0, 50.0)
        avg_order_value = st.number_input("Avg Order Value (R$)", 0.0, 5000.0,  50.0)

    with col2:
        avg_review = st.slider("Avg Review Score",          1.0, 5.0, 2.0, 0.1)
        avg_delay  = st.slider("Avg Delivery Delay (days)", -10, 30, 10)
        late_rate  = st.slider("Late Delivery Rate",        0.0, 1.0, 0.5)

    with col3:
        tenure     = st.number_input("Customer Tenure (days)", 0, 1000, 30)
        has_ticket = st.selectbox("Has Support Ticket", [1, 0])
        channel    = st.selectbox("Acquisition Channel",
                                  ["Google Ads","Instagram","Organic","Referral","Email"])
        age_group  = st.selectbox("Age Group", ["18-24","25-34","35-44","45-54","55+"])
        income     = st.selectbox("Income Segment", ["Low","Mid","High"])

    # ── Encode ────────────────────────────────────────────────
    channel_map  = {"Google Ads": 0, "Email": 1, "Instagram": 2, "Organic": 3, "Referral": 4}
    age_map      = {"18-24": 0, "25-34": 1, "35-44": 2, "45-54": 3, "55+": 4}
    income_map   = {"High": 0, "Low": 1, "Mid": 2}
    acq_cost_map = {"Google Ads": 18, "Instagram": 14, "Organic": 2, "Referral": 8, "Email": 3}

    # ── Derived features ──────────────────────────────────────
    clv         = monetary * (1 + np.log1p(frequency))
    spend_per   = monetary / max(frequency, 1)
    engagement  = (avg_review * 0.3
                   + np.log1p(frequency) * 0.4
                   + (1 / (abs(avg_delay) + 1)) * 0.3)
    repeat_flag = 1 if frequency > 1 else 0
    total_items = float(frequency * 2)

    if st.button("🔮 Predict Churn Risk", type="primary"):

        input_row = {
            "frequency":            float(frequency),
            "monetary":             float(monetary),
            "engagement_score":     float(engagement),
            "spend_per_order":      float(spend_per),
            "avg_order_value":      float(avg_order_value),
            "avg_review_score":     float(avg_review),
            "avg_delivery_delay":   float(avg_delay),
            "late_delivery_rate":   float(late_rate),
            "total_items_bought":   total_items,
            "customer_tenure_days": float(tenure),
            "repeat_customer_flag": float(repeat_flag),
            "clv_estimate":         float(clv),
            "has_support_ticket":   float(has_ticket),
            "acquisition_cost":     float(acq_cost_map[channel]),
            "channel_encoded":      float(channel_map[channel]),
            "age_encoded":          float(age_map[age_group]),
            "income_encoded":       float(income_map[income])
        }

        features = pd.DataFrame([input_row])[model.feature_names_in_]
        prob      = model.predict_proba(features)[0][1]
        risk      = "High" if prob >= 0.75 else "Medium" if prob >= 0.45 else "Low"

        # ── Save to log ───────────────────────────────────────
        log_entry = {
            "timestamp":          datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "frequency":          frequency,
            "total_spend":        round(monetary, 2),
            "avg_order_value":    round(avg_order_value, 2),
            "avg_review_score":   avg_review,
            "avg_delivery_delay": avg_delay,
            "late_delivery_rate": late_rate,
            "tenure_days":        tenure,
            "has_support_ticket": has_ticket,
            "channel":            channel,
            "age_group":          age_group,
            "income_segment":     income,
            "clv_estimate":       round(clv, 2),
            "engagement_score":   round(engagement, 3),
            "churn_probability":  round(prob * 100, 2),
            "risk_level":         risk
        }
        updated_log = save_prediction(log_entry)

        # ── Show result ───────────────────────────────────────
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### Churn Probability: `{prob*100:.1f}%`")
            if prob >= 0.75:
                st.error("🔴 HIGH CHURN RISK")
                st.warning("**Action:** Immediate win-back campaign — 20% discount coupon")
            elif prob >= 0.45:
                st.warning("🟡 MEDIUM CHURN RISK")
                st.info("**Action:** Re-engagement email sequence within 7 days")
            else:
                st.success("🟢 LOW CHURN RISK")
                st.info("**Action:** Enroll in loyalty program")

            st.markdown("**Input Summary:**")
            st.dataframe(pd.DataFrame({
                "Feature": ["Frequency","Total Spend","CLV Estimate",
                            "Engagement Score","Spend/Order"],
                "Value":   [frequency, f"R$ {monetary:.2f}", f"R$ {clv:.2f}",
                            f"{engagement:.3f}", f"R$ {spend_per:.2f}"]
            }), hide_index=True, use_container_width=True)

            st.success(f"✅ Prediction saved — {len(updated_log)} total predictions logged")

        with col2:
            fig = go.Figure(go.Indicator(
                mode  = "gauge+number",
                value = round(prob * 100, 1),
                title = {"text": "Churn Probability (%)"},
                gauge = {
                    "axis":  {"range": [0, 100]},
                    "bar":   {"color": "darkred" if prob > 0.75
                                       else "orange" if prob > 0.45
                                       else "green"},
                    "steps": [
                        {"range": [0,  45], "color": "#d4edda"},
                        {"range": [45, 75], "color": "#fff3cd"},
                        {"range": [75,100], "color": "#f8d7da"},
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

    # ── Prediction History ─────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Prediction History")

    log_df = load_log()

    if not log_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Predictions", f"{len(log_df):,}")
        col2.metric("High Risk",         f"{(log_df['risk_level']=='High').sum():,}")
        col3.metric("Medium Risk",        f"{(log_df['risk_level']=='Medium').sum():,}")
        col4.metric("Avg Churn Prob",    f"{log_df['churn_probability'].mean():.1f}%")

        col1, col2 = st.columns(2)

        with col1:
            risk_counts = log_df["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            color_map = {"High": "#EF553B", "Medium": "#FFA15A", "Low": "#00CC96"}
            fig = px.bar(risk_counts, x="Risk Level", y="Count",
                         title="Logged Predictions — Risk Distribution",
                         color="Risk Level", color_discrete_map=color_map)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.line(log_df.reset_index(), x="index", y="churn_probability",
                           color="risk_level",
                           title="Churn Probability Over Predictions",
                           color_discrete_map={"High":"#EF553B","Medium":"#FFA15A","Low":"#00CC96"},
                           labels={"index":"Prediction #","churn_probability":"Churn %"})
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(
            log_df.sort_values("timestamp", ascending=False),
            use_container_width=True,
            height=300
        )

        csv = log_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label     = "⬇️ Download Prediction Log (CSV)",
            data      = csv,
            file_name = "churn_prediction_log.csv",
            mime      = "text/csv"
        )

        if st.button("🗑️ Clear Prediction History"):
            os.remove(LOG_PATH)
            st.rerun()
    else:
        st.info("No predictions yet. Run a prediction above to start logging.")
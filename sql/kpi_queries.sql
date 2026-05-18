-- ============================================================
-- CommerceIQ — KPI Layer
-- Phase 7: Business KPIs
-- ============================================================
USE commerceiq;

-- ── MRR proxy (last 30 days revenue) ─────────────────────────
SELECT
    ROUND(SUM(p.payment_value), 2) AS mrr_proxy
FROM orders o
JOIN order_payments p ON o.order_id = p.order_id
WHERE o.order_purchase_timestamp >= DATE_SUB('2018-10-18', INTERVAL 30 DAY)
  AND o.order_status = 'delivered';

-- ── Monthly revenue growth rate ───────────────────────────────
WITH monthly AS (
    SELECT
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
        ROUND(SUM(p.payment_value), 2) AS revenue
    FROM orders o
    JOIN order_payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY month
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) /
          NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2) AS growth_pct
FROM monthly
ORDER BY month;

-- ── Customer retention rate ───────────────────────────────────
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT
    ROUND(SUM(order_count > 1) * 100.0 / COUNT(*), 2) AS retention_rate_pct,
    ROUND(SUM(order_count = 1) * 100.0 / COUNT(*), 2) AS churn_rate_pct
FROM customer_orders;

-- ── Average review score trend ────────────────────────────────
SELECT
    DATE_FORMAT(review_creation_date, '%Y-%m') AS month,
    ROUND(AVG(review_score), 3)                AS avg_review_score,
    COUNT(*)                                    AS reviews
FROM order_reviews
GROUP BY month
ORDER BY month;
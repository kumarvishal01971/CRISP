-- ============================================================
-- CommerceIQ — Business Analytics Queries
-- Phase 6: SQL Analytics Layer
-- ============================================================
USE commerceiq;

-- ══════════════════════════════════════════════════════════════
-- SECTION 1: REVENUE ANALYTICS
-- ══════════════════════════════════════════════════════════════

-- Q1: Total platform revenue
SELECT
    ROUND(SUM(payment_value), 2)      AS total_revenue,
    COUNT(DISTINCT order_id)           AS total_orders,
    ROUND(AVG(payment_value), 2)       AS avg_order_value
FROM order_payments;

-- Q2: Monthly revenue trend
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
    ROUND(SUM(p.payment_value), 2)                   AS monthly_revenue,
    COUNT(DISTINCT o.order_id)                        AS orders_count
FROM orders o
JOIN order_payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month;

-- Q3: Revenue by payment type
SELECT
    payment_type,
    COUNT(*)                           AS transactions,
    ROUND(SUM(payment_value), 2)       AS total_revenue,
    ROUND(AVG(payment_value), 2)       AS avg_value
FROM order_payments
GROUP BY payment_type
ORDER BY total_revenue DESC;

-- Q4: Top 10 customers by revenue
SELECT
    c.customer_unique_id,
    c.customer_state,
    COUNT(DISTINCT o.order_id)         AS total_orders,
    ROUND(SUM(p.payment_value), 2)     AS lifetime_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments p ON o.order_id = p.order_id
GROUP BY c.customer_unique_id, c.customer_state
ORDER BY lifetime_value DESC
LIMIT 10;

-- Q5: Revenue by order status
SELECT
    order_status,
    COUNT(*)                           AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;

-- ══════════════════════════════════════════════════════════════
-- SECTION 2: CUSTOMER ANALYTICS
-- ══════════════════════════════════════════════════════════════

-- Q6: Repeat vs one-time customers
SELECT
    CASE WHEN order_count > 1 THEN 'Repeat' ELSE 'One-Time' END AS customer_type,
    COUNT(*)        AS customers,
    ROUND(AVG(total_spend), 2) AS avg_spend
FROM (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id)     AS order_count,
        SUM(p.payment_value)           AS total_spend
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
) t
GROUP BY customer_type;

-- Q7: Customers inactive > 180 days (churn candidates)
SELECT
    c.customer_unique_id,
    MAX(o.order_purchase_timestamp)    AS last_purchase,
    DATEDIFF('2018-10-18', MAX(o.order_purchase_timestamp)) AS days_inactive,
    COUNT(DISTINCT o.order_id)         AS total_orders
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_unique_id
HAVING days_inactive > 180
ORDER BY days_inactive DESC;

-- Q8: Customer acquisition by month
SELECT
    DATE_FORMAT(first_purchase, '%Y-%m') AS cohort_month,
    COUNT(*) AS new_customers
FROM (
    SELECT
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_purchase
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
) t
GROUP BY cohort_month
ORDER BY cohort_month;

-- Q9: High value customers (top 10% by spend)
WITH customer_spend AS (
    SELECT
        c.customer_unique_id,
        SUM(p.payment_value) AS total_spend
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
),
percentiles AS (
    SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY total_spend) AS p90
    FROM customer_spend
)
SELECT COUNT(*) AS high_value_customers
FROM customer_spend
WHERE total_spend >= (SELECT p90 FROM percentiles);

-- ══════════════════════════════════════════════════════════════
-- SECTION 3: PRODUCT ANALYTICS
-- ══════════════════════════════════════════════════════════════

-- Q10: Top 10 product categories by revenue
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'Unknown') AS category,
    COUNT(DISTINCT oi.order_id)        AS orders,
    ROUND(SUM(oi.price), 2)            AS revenue,
    ROUND(AVG(oi.price), 2)            AS avg_price
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
GROUP BY category
ORDER BY revenue DESC
LIMIT 10;

-- Q11: Products with highest avg review score (min 50 orders)
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    COUNT(DISTINCT oi.order_id)        AS orders,
    ROUND(AVG(r.review_score), 2)      AS avg_review
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
JOIN order_reviews r ON oi.order_id = r.order_id
GROUP BY category
HAVING orders >= 50
ORDER BY avg_review DESC
LIMIT 10;

-- Q12: Categories with most late deliveries
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS late_orders,
    ROUND(AVG(DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date)), 1) AS avg_delay_days
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY category
HAVING total_orders >= 100
ORDER BY late_orders DESC
LIMIT 10;

-- ══════════════════════════════════════════════════════════════
-- SECTION 4: SELLER ANALYTICS
-- ══════════════════════════════════════════════════════════════

-- Q13: Top 10 sellers by revenue
SELECT
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT oi.order_id)        AS orders_fulfilled,
    ROUND(SUM(oi.price), 2)            AS total_revenue,
    ROUND(AVG(r.review_score), 2)      AS avg_review
FROM sellers s
JOIN order_items oi ON s.seller_id = oi.seller_id
LEFT JOIN order_reviews r ON oi.order_id = r.order_id
GROUP BY s.seller_id, s.seller_state
ORDER BY total_revenue DESC
LIMIT 10;

-- Q14: Sellers with poor review scores (avg < 3, min 20 orders)
SELECT
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS orders,
    ROUND(AVG(r.review_score), 2) AS avg_review
FROM sellers s
JOIN order_items oi ON s.seller_id = oi.seller_id
JOIN order_reviews r ON oi.order_id = r.order_id
GROUP BY s.seller_id, s.seller_state
HAVING orders >= 20 AND avg_review < 3
ORDER BY avg_review ASC;

-- ══════════════════════════════════════════════════════════════
-- SECTION 5: GEOGRAPHY ANALYTICS
-- ══════════════════════════════════════════════════════════════

-- Q15: Revenue by state
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id)         AS orders,
    ROUND(SUM(p.payment_value), 2)     AS revenue,
    ROUND(AVG(p.payment_value), 2)     AS avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments p ON o.order_id = p.order_id
GROUP BY c.customer_state
ORDER BY revenue DESC;

-- Q16: Top 10 cities by order volume
SELECT
    c.customer_city,
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(p.payment_value), 2) AS revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments p ON o.order_id = p.order_id
GROUP BY c.customer_city, c.customer_state
ORDER BY orders DESC
LIMIT 10;

-- ══════════════════════════════════════════════════════════════
-- SECTION 6: DELIVERY & OPERATIONS
-- ══════════════════════════════════════════════════════════════

-- Q17: Average delivery time by state
SELECT
    c.customer_state,
    ROUND(AVG(DATEDIFF(
        o.order_delivered_customer_date,
        o.order_purchase_timestamp)), 1) AS avg_delivery_days,
    ROUND(AVG(DATEDIFF(
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date)), 1) AS avg_delay_vs_estimate
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC;

-- Q18: On-time vs late delivery summary
SELECT
    CASE
        WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 'On Time'
        ELSE 'Late'
    END AS delivery_status,
    COUNT(*) AS orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM orders
WHERE order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;

-- ══════════════════════════════════════════════════════════════
-- SECTION 7: KPI SUMMARY VIEW
-- ══════════════════════════════════════════════════════════════

-- Q19: Executive KPI snapshot
SELECT
    ROUND(SUM(p.payment_value), 2)                          AS total_revenue,
    COUNT(DISTINCT o.order_id)                               AS total_orders,
    COUNT(DISTINCT c.customer_unique_id)                     AS unique_customers,
    ROUND(AVG(p.payment_value), 2)                          AS avg_order_value,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS revenue_per_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered';

-- Q20: Review score distribution
SELECT
    review_score,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM order_reviews
GROUP BY review_score
ORDER BY review_score DESC;
-- SENSEI (TM) Meta Ads -- Analytical Queries
-- ------------------------------------------------------
-- Run against data/sensei.db (built by scripts/load_db.py).
-- sqlite3 data/sensei.db < sql/queries.sql

-- 1. Angle-level rollup: volume + funnel completion, weighted CTR.
--    Reproduces the "תמונת מצב" numbers per angle from the README.
SELECT
    a.angle_name,
    COUNT(*)                                   AS ads,
    SUM(f.impressions)                         AS impressions,
    SUM(f.clicks)                              AS clicks,
    ROUND(100.0 * SUM(f.clicks) / SUM(f.impressions), 2)      AS ctr_pct,
    SUM(f.add_to_cart)                         AS add_to_cart,
    ROUND(100.0 * SUM(f.add_to_cart) / SUM(f.clicks), 2)      AS add_to_cart_rate_pct,
    SUM(f.initiate_checkout)                   AS checkouts,
    ROUND(100.0 * SUM(f.initiate_checkout) / SUM(f.clicks), 2) AS checkout_rate_pct,
    SUM(f.purchases)                           AS purchases
FROM fact_ad_performance f
JOIN dim_angle a ON a.angle_id = f.angle_id
GROUP BY a.angle_name
ORDER BY a.angle_order;


-- 2. Core insight #1: does a higher CTR angle actually convert better?
--    Compares the highest-CTR angle against the highest add-to-cart-rate angle.
SELECT
    a.angle_name,
    ROUND(100.0 * SUM(f.clicks) / SUM(f.impressions), 2)  AS ctr_pct,
    ROUND(100.0 * SUM(f.add_to_cart) / SUM(f.clicks), 2)  AS add_to_cart_rate_pct
FROM fact_ad_performance f
JOIN dim_angle a ON a.angle_id = f.angle_id
GROUP BY a.angle_name
HAVING SUM(f.clicks) > 0
ORDER BY add_to_cart_rate_pct DESC;


-- 3. Which angles actually produced a purchase, and at what ROAS?
SELECT
    a.angle_name,
    f.display_name,
    f.clicks,
    f.add_to_cart,
    f.initiate_checkout,
    f.purchases,
    f.roas
FROM fact_ad_performance f
JOIN dim_angle a ON a.angle_id = f.angle_id
WHERE f.purchases > 0
ORDER BY a.angle_order;


-- 4. Angle proven at real scale: most clicks + a purchase.
SELECT
    a.angle_name,
    SUM(f.clicks) AS total_clicks,
    SUM(f.purchases) AS total_purchases
FROM fact_ad_performance f
JOIN dim_angle a ON a.angle_id = f.angle_id
GROUP BY a.angle_name
HAVING total_purchases > 0
ORDER BY total_clicks DESC;


-- 5. Full ad-level detail for one angle (parameterize angle_name as needed).
SELECT
    f.display_name,
    f.impressions, f.cpm, f.frequency,
    f.clicks, f.ctr, f.cpc,
    f.landing_page_views, f.add_to_cart,
    f.initiate_checkout, f.purchase_rate_of_clicks, f.roas
FROM fact_ad_performance f
JOIN dim_angle a ON a.angle_id = f.angle_id
WHERE a.angle_name = 'בריאות / רעלים / מיקרופלסטיק'
ORDER BY f.clicks DESC;


-- 6. Sanity check against the README: total ads and total purchases.
SELECT
    (SELECT COUNT(*) FROM fact_ad_performance)         AS total_ads,
    (SELECT SUM(purchases) FROM fact_ad_performance)   AS total_purchases;

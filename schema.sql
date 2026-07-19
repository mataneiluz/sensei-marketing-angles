-- SENSEI (TM) Meta Ads -- Marketing Angle Star Schema
-- ------------------------------------------------------
-- Two tables: one dimension (the marketing angle) and one fact table
-- (ad-level performance). This mirrors the same 16-ad / 7-angle dataset
-- used in the README and in data/processed_by_angle.csv -- built so the
-- same numbers can be reproduced with SQL instead of pandas.

DROP TABLE IF EXISTS fact_ad_performance;
DROP TABLE IF EXISTS dim_angle;

CREATE TABLE dim_angle (
    angle_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    angle_name  TEXT NOT NULL UNIQUE,
    angle_order INTEGER NOT NULL   -- display order, matches the README (1-7)
);

CREATE TABLE fact_ad_performance (
    ad_id                    INTEGER PRIMARY KEY,
    display_name             TEXT NOT NULL,   -- current live name in Ads Manager
    ad_name_raw              TEXT NOT NULL,   -- name as it appears in the raw export
    campaign                 TEXT,
    angle_id                 INTEGER NOT NULL REFERENCES dim_angle(angle_id),

    impressions              INTEGER,
    cpm                      REAL,             -- cost per 1,000 impressions (ILS)
    frequency                REAL,
    clicks                   INTEGER,
    ctr                      REAL,             -- % of impressions that clicked
    cpc                      REAL,             -- cost per click (ILS)

    landing_page_views       INTEGER,
    add_to_cart              INTEGER,

    video_3s_plays           INTEGER,
    video_25pct              INTEGER,
    video_50pct              INTEGER,
    video_75pct              INTEGER,
    video_100pct             INTEGER,

    initiate_checkout        INTEGER,
    purchases                INTEGER,
    purchase_rate_of_clicks  REAL,             -- % of clicks that ended in a purchase
    roas                     REAL              -- return on ad spend (only populated where a purchase occurred)
);

CREATE INDEX idx_fact_angle ON fact_ad_performance(angle_id);

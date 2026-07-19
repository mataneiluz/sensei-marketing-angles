"""
Loads data/processed_by_angle.csv into a SQLite database (sensei.db) using
the star schema defined in sql/schema.sql, so the queries in sql/queries.sql
can be run against real data.

Run:
    python3 scripts/load_db.py
"""

import sqlite3
import pandas as pd

CSV_PATH = "data/processed_by_angle.csv"
SCHEMA_PATH = "sql/schema.sql"
DB_PATH = "data/sensei.db"

# Angle display order, matching the README (1-7)
ANGLE_ORDER = [
    'הוק "זה אתם?"',
    'הוק "לכל האמהות"',
    "פנייה ישירה לאמהות (קליקבייט)",
    "ניקיון ותחזוקה",
    "בריאות / רעלים / מיקרופלסטיק",
    "FOMO ונראות",
    "חסכון לטווח ארוך",
]


def main() -> None:
    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        cur.executescript(f.read())

    cur.executemany(
        "INSERT INTO dim_angle (angle_name, angle_order) VALUES (?, ?)",
        [(name, i + 1) for i, name in enumerate(ANGLE_ORDER)],
    )
    conn.commit()

    angle_id_lookup = dict(cur.execute("SELECT angle_name, angle_id FROM dim_angle"))

    rows = []
    for _, r in df.iterrows():
        rows.append((
            int(r["ad_id"]), r["display_name"], r["ad_name"], r["campaign"],
            angle_id_lookup[r["angle"]],
            _n(r["impressions"]), _f(r["cpm"]), _f(r["frequency"]), _n(r["clicks"]),
            _f(r["ctr"]), _f(r["cpc"]),
            _n(r["landing_page_views"]), _n(r["add_to_cart"]),
            _n(r["video_3s_plays"]), _n(r["video_25pct"]), _n(r["video_50pct"]),
            _n(r["video_75pct"]), _n(r["video_100pct"]),
            _n(r["initiate_checkout"]), _n(r["purchases"]),
            _f(r["purchase_rate_of_clicks"]), _f(r["roas"]),
        ))

    cur.executemany(
        """INSERT INTO fact_ad_performance (
            ad_id, display_name, ad_name_raw, campaign, angle_id,
            impressions, cpm, frequency, clicks, ctr, cpc,
            landing_page_views, add_to_cart,
            video_3s_plays, video_25pct, video_50pct, video_75pct, video_100pct,
            initiate_checkout, purchases, purchase_rate_of_clicks, roas
        ) VALUES (?,?,?,?,?, ?,?,?,?,?,?, ?,?, ?,?,?,?,?, ?,?,?,?)""",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"נטענו {len(rows)} מודעות ל-{DB_PATH}")


def _n(v):
    return None if pd.isna(v) else int(v)


def _f(v):
    return None if pd.isna(v) else float(v)


if __name__ == "__main__":
    main()

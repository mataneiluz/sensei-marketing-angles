"""
SENSEI (TM) -- Meta Ads Marketing Angle Analysis
==================================================
Pulls every row from the raw Meta Ads Manager export and rolls it up by
marketing angle. The angle mapping below is not inferred automatically --
it reflects manual curation against the live Ads Manager UI (ad names were
cross-checked screenshot-by-screenshot against the CSV; three ads carry
unpublished-edit renames that don't yet exist in any export).

Run:
    python3 analysis.py <path-to-csv>

Output:
    Prints one table per marketing angle with every non-identifying metric
    available in the export (spend/ad-id/campaign-id/purchase-count/
    cost-per-result are intentionally left out of the printed report --
    see README.md for why).
"""

import sys
import pandas as pd

RAW_COLUMNS = {
    "שם המודעה": "ad_name",
    "שם הקמפיין": "campaign",
    "חשיפות": "impressions",
    "עלות לאלף חשיפות (ILS)": "cpm",
    "תדירות": "frequency",
    "קליקים על קישור": "clicks",
    "שיעור קליקים על קישור": "ctr",
    "עלות לקליק (עלות לקליק על קישור) (ILS)": "cpc",
    "צפיות בדף נחיתה": "landing_page_views",
    "הוספות לעגלת הקניות": "add_to_cart",
    "הפעלות סרטון למשך 3 שניות": "video_3s_plays",
    "הפעלות של 25% מהסרטון": "video_25pct",
    "הפעלות של 50% מהסרטון": "video_50pct",
    "הפעלות של 75% מהסרטון": "video_75pct",
    "הפעלות של 100% מהסרטון": "video_100pct",
    "מעברים לתשלום": "initiate_checkout",
    "רכישות": "purchases",
    "שיעור רכישות לפי קליקים על קישורים": "purchase_rate_of_clicks",
    "החזר על הוצאות פרסום על רכישות": "roas",
    "מזהה המודעה": "ad_id",
}

# ad_id -> display name actually live in Ads Manager right now.
# Three of these differ from the CSV's `שם המודעה` because the ad was
# renamed in-platform and the rename has not been published yet.
DISPLAY_NAME_OVERRIDES = {
    120249226120700547: 'פרסומת (הוק "לכל האמהות")(פייסבוק)',
    120249122509590547: "מיקרופלסטיק - בריאות",
    120249479509580547: "ניקיון ויעילות - במיוחד לנשים",
    120249740323140547: 'פרסומת (הוק "זה אתם?") (פייסבוק)',  # unlabeled in export, confirmed platform via screenshot
}

# ad_id -> marketing angle, as agreed after manual review of all 25 ads.
ANGLE_MAP = {
    # Angle 1: Organic - "Is this you?" hook
    120249511939230547: 'הוק "זה אתם?" - אינסטגרם',
    120249740323140547: 'הוק "זה אתם?" - פייסבוק',
    120249745738690547: 'הוק "זה אתם?" - עם שיפורים',
    # Angle 2: Organic - "To all the moms" hook
    120249226254440547: 'הוק "לכל האמהות" - אינסטגרם',
    120249226120700547: 'הוק "לכל האמהות" - פייסבוק',
    # Angle 3: Direct clickbait to moms
    120248015987670547: "אמהות-בריאות-ילדים (קליקבייט)",
    # Angle 4: Cleaning & maintenance
    120248745372170547: "ניקיון ותחזוקה",
    120249746698980547: "ניקיון ותחזוקה - עם שיפורים",
    120249479509580547: 'ניקיון ויעילות - במיוחד לנשים',
    # Angle 5: Health / toxins / microplastics
    120249121061510547: "העברת ריחות וטעמים",
    120249312237170547: "העברת ריחות וטעמים - וריאציה (רכישה)",
    120249479492470547: "העברת ריחות וטעמים - עם שיפורים",
    120249122509590547: "מיקרופלסטיק - בריאות",
    120249119410350547: "היגיינה בריאות (קליקבייט)",
    # Angle 6: FOMO & visibility
    120248748106070547: "FOMO ונראות",
    # Angle 7: Long-term savings
    120248744444530547: "חסכון לטווח ארוך",
}

ANGLE_ORDER = [
    'הוק "זה אתם?"',
    'הוק "לכל האמהות"',
    "פנייה ישירה לאמהות (קליקבייט)",
    "ניקיון ותחזוקה",
    "בריאות / רעלים / מיקרופלסטיק",
    "FOMO ונראות",
    "חסכון לטווח ארוך",
]

ANGLE_GROUP = {
    'הוק "זה אתם?" - אינסטגרם': 'הוק "זה אתם?"',
    'הוק "זה אתם?" - פייסבוק': 'הוק "זה אתם?"',
    'הוק "זה אתם?" - עם שיפורים': 'הוק "זה אתם?"',
    'הוק "לכל האמהות" - אינסטגרם': 'הוק "לכל האמהות"',
    'הוק "לכל האמהות" - פייסבוק': 'הוק "לכל האמהות"',
    "אמהות-בריאות-ילדים (קליקבייט)": "פנייה ישירה לאמהות (קליקבייט)",
    "ניקיון ותחזוקה": "ניקיון ותחזוקה",
    "ניקיון ותחזוקה - עם שיפורים": "ניקיון ותחזוקה",
    'ניקיון ויעילות - במיוחד לנשים': "ניקיון ותחזוקה",
    "העברת ריחות וטעמים": "בריאות / רעלים / מיקרופלסטיק",
    "העברת ריחות וטעמים - וריאציה (רכישה)": "בריאות / רעלים / מיקרופלסטיק",
    "העברת ריחות וטעמים - עם שיפורים": "בריאות / רעלים / מיקרופלסטיק",
    "מיקרופלסטיק - בריאות": "בריאות / רעלים / מיקרופלסטיק",
    "היגיינה בריאות (קליקבייט)": "בריאות / רעלים / מיקרופלסטיק",
    "FOMO ונראות": "FOMO ונראות",
    "חסכון לטווח ארוך": "חסכון לטווח ארוך",
}


def load(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[list(RAW_COLUMNS)].rename(columns=RAW_COLUMNS)
    df["ad_id"] = df["ad_id"].astype(int)
    df = df[df["ad_id"].isin(ANGLE_MAP)].copy()
    df["display_name"] = df.apply(
        lambda r: DISPLAY_NAME_OVERRIDES.get(r["ad_id"], r["ad_name"]), axis=1
    )
    df["sub_angle"] = df["ad_id"].map(ANGLE_MAP)
    df["angle"] = df["sub_angle"].map(ANGLE_GROUP)
    return df


def print_report(df: pd.DataFrame) -> None:
    for angle in ANGLE_ORDER:
        sub = df[df["angle"] == angle]
        print(f"\n### {angle} ({len(sub)} מודעות)")
        cols = [
            "display_name", "impressions", "cpm", "frequency", "clicks", "ctr",
            "cpc", "landing_page_views", "add_to_cart", "video_3s_plays",
            "video_25pct", "video_50pct", "video_75pct", "video_100pct",
            "initiate_checkout", "purchase_rate_of_clicks", "roas",
        ]
        print(sub[cols].fillna("-").to_string(index=False))


def export_csv(df: pd.DataFrame, out_path: str) -> None:
    cols = [
        "angle", "display_name", "ad_name", "ad_id", "campaign",
        "impressions", "cpm", "frequency", "clicks", "ctr", "cpc",
        "landing_page_views", "add_to_cart", "video_3s_plays",
        "video_25pct", "video_50pct", "video_75pct", "video_100pct",
        "initiate_checkout", "purchases", "purchase_rate_of_clicks", "roas",
    ]
    df[cols].to_csv(out_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw_meta_export.csv"
    data = load(csv_path)
    print_report(data)
    print(f"\nסה\"כ מודעות בניתוח: {len(data)}")
    print(f"סה\"כ רכישות: {int(data['purchases'].sum())}")
    export_csv(data, "data/processed_by_angle.csv")
    print("\nנשמר: data/processed_by_angle.csv")

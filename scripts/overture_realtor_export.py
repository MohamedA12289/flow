from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import duckdb

RELEASE = "2026-06-17.0"
DATASET_PATH = (
    f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=places/type=place/*"
)
OUT_CSV = Path("overture_us_real_estate_contacts.csv")
OUT_SUMMARY = Path("overture_us_real_estate_contacts_summary.json")

CATEGORIES = [
    "real_estate",
    "real_estate_investment",
    "builders",
    "home_developer",
    "commercial_real_estate",
    "estate_liquidation",
    "home_staging",
    "homeowner_association",
    "housing_cooperative",
    "mobile_home_dealer",
    "mobile_home_park",
    "property_management",
    "real_estate_agent",
    "apartment_agent",
    "real_estate_service",
    "rental_services",
    "vacation_rental_agents",
]

STATE_CODES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
]

con = duckdb.connect()
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("SET s3_region='us-west-2'")
con.execute("SET s3_url_style='path'")
con.execute("SET s3_endpoint='s3.us-west-2.amazonaws.com'")
con.execute("SET s3_use_ssl=true")
con.execute("SET threads=4")
con.execute("SET memory_limit='6GB'")
con.execute("SET preserve_insertion_order=false")

category_sql = ", ".join("'" + category.replace("'", "''") + "'" for category in CATEGORIES)
state_sql = ", ".join("'" + state + "'" for state in STATE_CODES)

query = f"""
WITH extracted AS (
    SELECT
        id AS overture_id,
        names.primary AS company_name,
        categories.primary AS overture_category,
        confidence AS overture_confidence,
        phones[1] AS phone,
        emails[1] AS email,
        websites[1] AS website,
        addresses[1].freeform AS address,
        addresses[1].locality AS city,
        addresses[1].region AS raw_region,
        addresses[1].postcode AS postal_code,
        addresses[1].country AS country,
        operating_status,
        bbox.xmin AS longitude,
        bbox.ymin AS latitude,
        sources[1].dataset AS primary_source_dataset
    FROM read_parquet('{DATASET_PATH}', hive_partitioning=1)
    WHERE categories.primary IN ({category_sql})
      AND names.primary IS NOT NULL
      AND bbox.xmin BETWEEN -170 AND -66
      AND bbox.ymin BETWEEN 18 AND 72
),
normalized AS (
    SELECT
        *,
        CASE
            WHEN upper(raw_region) LIKE 'US-%' THEN substring(upper(raw_region), 4)
            WHEN length(trim(raw_region)) = 2 THEN upper(trim(raw_region))
            ELSE NULL
        END AS state,
        (
            CASE WHEN email IS NOT NULL AND trim(email) <> '' THEN 4 ELSE 0 END +
            CASE WHEN phone IS NOT NULL AND trim(phone) <> '' THEN 3 ELSE 0 END +
            CASE WHEN website IS NOT NULL AND trim(website) <> '' THEN 2 ELSE 0 END +
            CASE WHEN address IS NOT NULL AND trim(address) <> '' THEN 1 ELSE 0 END
        ) AS contact_score
    FROM extracted
    WHERE (country = 'US' OR country IS NULL)
      AND (operating_status IS NULL OR operating_status <> 'closed')
),
contactable AS (
    SELECT *
    FROM normalized
    WHERE state IN ({state_sql})
      AND (
          (email IS NOT NULL AND trim(email) <> '')
          OR (phone IS NOT NULL AND trim(phone) <> '')
          OR (website IS NOT NULL AND trim(website) <> '')
      )
),
ranked AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY state
            ORDER BY
                contact_score DESC,
                overture_confidence DESC NULLS LAST,
                company_name,
                overture_id
        ) AS state_rank
    FROM contactable
)
SELECT
    overture_id,
    company_name,
    overture_category,
    overture_confidence,
    email,
    phone,
    website,
    address,
    city,
    state,
    postal_code,
    latitude,
    longitude,
    country,
    operating_status,
    contact_score,
    state_rank,
    primary_source_dataset,
    '{RELEASE}' AS overture_release,
    'https://docs.overturemaps.org/guides/places/' AS source_url,
    'Overture Maps Places' AS source_type,
    'CDLA Permissive 2.0; source-specific attribution may also apply' AS data_license,
    '2026-08-07' AS last_verified
FROM ranked
WHERE state_rank <= 500
ORDER BY state, state_rank
"""

print("Running Overture nationwide real-estate contact query...", flush=True)
con.execute(
    f"COPY ({query}) TO '{OUT_CSV.as_posix()}' (FORMAT CSV, HEADER TRUE, DELIMITER ',')"
)

with OUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.DictReader(handle))

state_counts = Counter(row.get("state", "") for row in rows if row.get("state"))
category_counts = Counter(
    row.get("overture_category", "") for row in rows if row.get("overture_category")
)
summary = {
    "release": RELEASE,
    "dataset_path": DATASET_PATH,
    "rows": len(rows),
    "with_email": sum(bool((row.get("email") or "").strip()) for row in rows),
    "with_phone": sum(bool((row.get("phone") or "").strip()) for row in rows),
    "with_website": sum(bool((row.get("website") or "").strip()) for row in rows),
    "with_email_and_phone": sum(
        bool((row.get("email") or "").strip() and (row.get("phone") or "").strip())
        for row in rows
    ),
    "states": dict(sorted(state_counts.items())),
    "state_count_including_dc": len(state_counts),
    "categories": dict(category_counts.most_common()),
}
OUT_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2), flush=True)

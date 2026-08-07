from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import duckdb

RELEASE = "2026-06-17.0"
PATH = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=places/type=place/*"
OUT = Path("overture_us_real_estate_contacts_fast.csv")
SUMMARY = Path("overture_us_real_estate_contacts_fast_summary.json")
CATEGORIES = [
    "real_estate","real_estate_investment","builders","home_developer",
    "commercial_real_estate","estate_liquidation","home_staging",
    "homeowner_association","housing_cooperative","mobile_home_dealer",
    "mobile_home_park","property_management","real_estate_agent",
    "apartment_agent","real_estate_service","rental_services",
    "vacation_rental_agents",
]
STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
]
cat_sql = ",".join(f"'{x}'" for x in CATEGORIES)
state_sql = ",".join(f"'{x}'" for x in STATES)

con=duckdb.connect()
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("SET s3_region='us-west-2'")
con.execute("SET s3_url_style='path'")
con.execute("SET s3_endpoint='s3.us-west-2.amazonaws.com'")
con.execute("SET threads=4")
con.execute("SET memory_limit='5GB'")
con.execute("SET preserve_insertion_order=false")

query=f"""
WITH x AS (
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
   CASE WHEN upper(addresses[1].region) LIKE 'US-%'
        THEN substring(upper(addresses[1].region),4)
        WHEN length(trim(addresses[1].region))=2
        THEN upper(trim(addresses[1].region)) ELSE NULL END AS state,
   addresses[1].postcode AS postal_code,
   addresses[1].country AS country,
   operating_status,
   bbox.xmin AS longitude,
   bbox.ymin AS latitude,
   sources[1].dataset AS primary_source_dataset
 FROM read_parquet('{PATH}', hive_partitioning=1)
 WHERE categories.primary IN ({cat_sql})
   AND names.primary IS NOT NULL
   AND bbox.xmin BETWEEN -170 AND -66
   AND bbox.ymin BETWEEN 18 AND 72
)
SELECT
 overture_id,company_name,overture_category,overture_confidence,email,phone,website,
 address,city,state,postal_code,latitude,longitude,country,operating_status,
 primary_source_dataset,'{RELEASE}' AS overture_release,
 'https://docs.overturemaps.org/guides/places/' AS source_url,
 'Overture Maps Places' AS source_type,
 'CDLA Permissive 2.0; source-specific attribution may also apply' AS data_license,
 '2026-08-07' AS last_verified
FROM x
WHERE state IN ({state_sql})
  AND (country='US' OR country IS NULL)
  AND (operating_status IS NULL OR operating_status NOT LIKE 'closed%')
  AND ((email IS NOT NULL AND trim(email)<>'') OR (phone IS NOT NULL AND trim(phone)<>''))
LIMIT 18000
"""
print('Running fast Overture direct-contact export...',flush=True)
con.execute(f"COPY ({query}) TO '{OUT.as_posix()}' (FORMAT CSV, HEADER TRUE)")
with OUT.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
state_counts=Counter(r.get('state','') for r in rows if r.get('state'))
summary={
 'release':RELEASE,'rows':len(rows),'with_email':sum(bool((r.get('email') or '').strip()) for r in rows),
 'with_phone':sum(bool((r.get('phone') or '').strip()) for r in rows),
 'with_email_and_phone':sum(bool((r.get('email') or '').strip() and (r.get('phone') or '').strip()) for r in rows),
 'with_website':sum(bool((r.get('website') or '').strip()) for r in rows),
 'states':dict(sorted(state_counts.items())),'state_count_including_dc':len(state_counts),
 'categories':dict(Counter(r.get('overture_category','') for r in rows).most_common()),
}
SUMMARY.write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)

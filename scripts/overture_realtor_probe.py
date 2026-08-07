from __future__ import annotations

import json
from pathlib import Path

import duckdb

RELEASE = "2026-06-17.0"
PATH = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=places/type=place/*"

con = duckdb.connect()
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("SET s3_region='us-west-2'")
con.execute("SET s3_url_style='path'")
con.execute("SET s3_endpoint='s3.us-west-2.amazonaws.com'")
con.execute("SET s3_use_ssl=true")
con.execute("SET threads=4")
con.execute("SET memory_limit='5GB'")

schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{PATH}', hive_partitioning=1) LIMIT 1").fetchall()

category_rows = con.execute(
    f"""
    SELECT categories.primary AS category, COUNT(*) AS n
    FROM read_parquet('{PATH}', hive_partitioning=1)
    WHERE bbox.xmin BETWEEN -170 AND -66
      AND bbox.ymin BETWEEN 18 AND 72
      AND (
        lower(categories.primary) LIKE '%real_estate%'
        OR lower(categories.primary) LIKE '%property_management%'
        OR lower(categories.primary) LIKE '%realty%'
        OR lower(categories.primary) LIKE '%estate_agent%'
      )
    GROUP BY 1
    ORDER BY n DESC
    LIMIT 200
    """
).fetchall()

name_rows = con.execute(
    f"""
    SELECT
      id,
      names.primary AS name,
      categories.primary AS category,
      CAST(phones AS VARCHAR) AS phones,
      CAST(emails AS VARCHAR) AS emails,
      CAST(websites AS VARCHAR) AS websites,
      CAST(addresses AS VARCHAR) AS addresses,
      confidence,
      bbox.xmin AS longitude,
      bbox.ymin AS latitude
    FROM read_parquet('{PATH}', hive_partitioning=1)
    WHERE bbox.xmin BETWEEN -170 AND -66
      AND bbox.ymin BETWEEN 18 AND 72
      AND (
        lower(categories.primary) LIKE '%real_estate%'
        OR lower(categories.primary) LIKE '%property_management%'
        OR lower(categories.primary) LIKE '%realty%'
        OR lower(categories.primary) LIKE '%estate_agent%'
        OR lower(names.primary) LIKE '%realty%'
        OR lower(names.primary) LIKE '%real estate%'
        OR lower(names.primary) LIKE '%realtor%'
        OR lower(names.primary) LIKE '%home buyers%'
        OR lower(names.primary) LIKE '%house buyers%'
        OR lower(names.primary) LIKE '%we buy houses%'
      )
    LIMIT 50
    """
).fetchall()

out = {
    "release": RELEASE,
    "path": PATH,
    "schema": [list(row) for row in schema],
    "categories": [list(row) for row in category_rows],
    "sample_rows": [list(row) for row in name_rows],
}
Path("overture_realtor_probe.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print(json.dumps(out, indent=2, default=str))

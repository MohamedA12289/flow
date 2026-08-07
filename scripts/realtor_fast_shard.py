from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Any

import requests

from realtor_shard_export import (
    COLUMNS,
    DATE,
    OVERPASS_ENDPOINTS,
    REGIONS,
    USER_AGENT,
    clean,
    finalize_record,
    record_from_element,
)


def build_fast_query(region: dict[str, Any], radius_m: int) -> str:
    lat = region["lat"]
    lon = region["lon"]
    contact_filter = (
        '[~"^(phone|contact:phone|mobile|contact:mobile|email|contact:email|'
        'website|contact:website)$"~"."]'
    )
    return f"""[out:json][timeout:55];
(
  nwr[\"office\"~\"^(estate_agent|property_management|real_estate_agent|real_estate|estate_management)$\"][\"name\"]{contact_filter}(around:{radius_m},{lat},{lon});
  nwr[\"shop\"=\"estate_agent\"][\"name\"]{contact_filter}(around:{radius_m},{lat},{lon});
  nwr[\"name\"~\"(Home Buyers|House Buyers|Cash Buyers|We Buy Houses|Real Estate Investments|Property Investors|Acquisitions)\",i]{contact_filter}(around:{radius_m},{lat},{lon});
);
out center tags 500;"""


def fetch_fast(
    region: dict[str, Any], shard: int, session: requests.Session
) -> tuple[list[dict[str, Any]], str, str]:
    endpoints = OVERPASS_ENDPOINTS[shard % len(OVERPASS_ENDPOINTS) :] + OVERPASS_ENDPOINTS[
        : shard % len(OVERPASS_ENDPOINTS)
    ]
    starting_radius = min(int(region["radius_m"]), 45_000)
    radii = list(dict.fromkeys([starting_radius, 32_000, 22_000]))
    last_error = ""
    for radius in radii:
        for attempt in range(4):
            endpoint = endpoints[attempt % len(endpoints)]
            try:
                response = session.post(
                    endpoint,
                    data={"data": build_fast_query(region, radius)},
                    headers={"User-Agent": USER_AGENT},
                    timeout=(10, 75),
                )
                response.raise_for_status()
                payload = response.json()
                elements = payload.get("elements") or []
                remark = clean(payload.get("remark"))
                if elements:
                    timestamp = clean(
                        (payload.get("osm3s") or {}).get("timestamp_osm_base")
                    )
                    return elements, timestamp, ""
                if remark:
                    last_error = f"Overpass remark: {remark[:400]}"
                else:
                    last_error = "Valid response with zero matching elements"
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(1.0 + attempt * 1.2 + random.random())
    return [], "", last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    selected = [
        region for index, region in enumerate(REGIONS) if index % args.shards == args.shard
    ]
    session = requests.Session()
    records: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for index, region in enumerate(selected, start=1):
        elements, timestamp, error = fetch_fast(region, args.shard, session)
        kept = 0
        for element in elements:
            record = record_from_element(region, element, timestamp, args.shard)
            if not record:
                continue
            record["website_fetch_status"] = (
                "not_attempted_fast_pass" if record.get("website") else "no_website"
            )
            record["research_method"] = (
                "Fast OpenStreetMap public business/contact extraction; official website not yet reviewed"
            )
            finalize_record(record, 0)
            records.append(record)
            kept += 1
        if error:
            errors.append({"region_id": region["region_id"], "error": error})
        print(
            json.dumps(
                {
                    "shard": args.shard,
                    "region": region["region_id"],
                    "progress": f"{index}/{len(selected)}",
                    "elements": len(elements),
                    "kept": kept,
                    "error": error[:160],
                }
            ),
            flush=True,
        )

    # Stable OSM element dedupe within the shard.
    best: dict[str, dict[str, str]] = {}
    for record in records:
        key = f"{record.get('osm_element_type')}:{record.get('osm_element_id')}"
        current = best.get(key)
        if current is None:
            best[key] = record
            continue
        for column in COLUMNS:
            if not current.get(column) and record.get(column):
                current[column] = record[column]

    rows = list(best.values())
    rows.sort(
        key=lambda row: (
            -int(row.get("confidence_score") or 0),
            row.get("company_name", "").lower(),
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["confidence_rank"] = str(rank)
        row["lead_id"] = f"FAST-{args.shard:02d}-{rank:05d}"

    output = Path(args.out)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "pass": "fast",
        "shard": args.shard,
        "shards": args.shards,
        "regions_assigned": len(selected),
        "records": len(rows),
        "with_email": sum(bool(row.get("email")) for row in rows),
        "with_phone": sum(bool(row.get("phone")) for row in rows),
        "with_both": sum(bool(row.get("email") and row.get("phone")) for row in rows),
        "with_website": sum(bool(row.get("website")) for row in rows),
        "states": sorted({row.get("target_states", "") for row in rows if row.get("target_states")}),
        "region_errors": errors,
        "last_verified": DATE,
    }
    output.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

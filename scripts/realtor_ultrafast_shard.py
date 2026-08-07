from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import requests

from realtor_shard_export import (
    COLUMNS,
    DATE,
    REGIONS,
    USER_AGENT,
    clean,
    finalize_record,
    record_from_element,
)

ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def bbox(region: dict[str, Any], radius_km: float = 28.0) -> str:
    lat = float(region["lat"])
    lon = float(region["lon"])
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / max(25.0, 111.0 * math.cos(math.radians(lat)))
    return f"{lat-lat_delta:.6f},{lon-lon_delta:.6f},{lat+lat_delta:.6f},{lon+lon_delta:.6f}"


def query(region: dict[str, Any]) -> str:
    box = bbox(region)
    c = '[~"^(phone|contact:phone|mobile|contact:mobile|email|contact:email|website|contact:website)$"~"."]'
    return f'''[out:json][timeout:24];
(
 nwr["office"~"^(estate_agent|property_management|real_estate_agent|real_estate|estate_management)$"]["name"]{c}({box});
 nwr["shop"="estate_agent"]["name"]{c}({box});
 nwr["name"~"(Home Buyers|House Buyers|Cash Buyers|We Buy Houses|Real Estate Investments|Property Investors|Acquisitions)",i]{c}({box});
);
out center tags 800;'''


def fetch_region(region: dict[str, Any], shard: int, session: requests.Session):
    endpoints = ENDPOINTS[shard % len(ENDPOINTS):] + ENDPOINTS[: shard % len(ENDPOINTS)]
    errors: list[str] = []
    for endpoint in endpoints:
        try:
            response = session.post(
                endpoint,
                data={"data": query(region)},
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
                timeout=(6, 32),
            )
            response.raise_for_status()
            payload = response.json()
            elements = payload.get("elements") or []
            if elements:
                timestamp = clean((payload.get("osm3s") or {}).get("timestamp_osm_base"))
                return elements, timestamp, ""
            remark = clean(payload.get("remark"))
            errors.append((remark or "zero matching elements")[:350])
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    return [], "", " | ".join(errors)[:700]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    selected = [r for i, r in enumerate(REGIONS) if i % args.shards == args.shard]
    session = requests.Session()
    rows: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for pos, region in enumerate(selected, 1):
        elements, timestamp, error = fetch_region(region, args.shard, session)
        kept = 0
        for element in elements:
            record = record_from_element(region, element, timestamp, args.shard)
            if not record:
                continue
            record["website_fetch_status"] = "not_attempted_ultrafast_bbox" if record.get("website") else "no_website"
            record["research_method"] = "Ultrafast OpenStreetMap bounding-box public business/contact extraction; official website not reviewed"
            finalize_record(record, 0)
            rows.append(record)
            kept += 1
        if error:
            errors.append({"region_id": region["region_id"], "error": error})
        print(json.dumps({
            "shard": args.shard,
            "region": region["region_id"],
            "progress": f"{pos}/{len(selected)}",
            "elements": len(elements),
            "kept": kept,
            "error": error[:160],
        }), flush=True)

    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        key = f"{row.get('osm_element_type')}:{row.get('osm_element_id')}"
        current = by_id.get(key)
        if current is None:
            by_id[key] = row
        else:
            for col in COLUMNS:
                if not current.get(col) and row.get(col):
                    current[col] = row[col]

    rows = sorted(by_id.values(), key=lambda r: (-int(r.get("confidence_score") or 0), r.get("company_name", "").lower()))
    for rank, row in enumerate(rows, 1):
        row["confidence_rank"] = str(rank)
        row["lead_id"] = f"ULTRA-{args.shard:02d}-{rank:05d}"

    output = Path(args.out)
    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "pass": "ultrafast-bbox-v3",
        "shard": args.shard,
        "shards": args.shards,
        "regions_assigned": len(selected),
        "records": len(rows),
        "with_email": sum(bool(r.get("email")) for r in rows),
        "with_phone": sum(bool(r.get("phone")) for r in rows),
        "with_both": sum(bool(r.get("email") and r.get("phone")) for r in rows),
        "with_website": sum(bool(r.get("website")) for r in rows),
        "states": sorted({r.get("target_states", "") for r in rows if r.get("target_states")}),
        "region_errors": errors,
        "last_verified": DATE,
    }
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

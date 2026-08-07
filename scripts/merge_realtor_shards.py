from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def company_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def email_key(value: str) -> str:
    return clean(value).lower()


def phone_key(value: str) -> str:
    digits = re.sub(r"\D", "", clean(value))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def domain_key(value: str) -> str:
    value = clean(value)
    if value and not re.match(r"https?://", value, re.I):
        value = "https://" + value
    try:
        return urlsplit(value).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def score(row: dict[str, str]) -> int:
    try:
        return int(float(clean(row.get("confidence_score", "0"))))
    except Exception:
        return 0


def completeness(row: dict[str, str]) -> int:
    fields = [
        "email",
        "phone",
        "website",
        "address",
        "city",
        "property_types",
        "strategy",
        "condition",
        "closing_speed",
        "accepts_assignments",
        "official_pages_reviewed",
        "target_markets",
        "source_url",
    ]
    return sum(bool(clean(row.get(field, ""))) for field in fields)


def dedupe_key(row: dict[str, str]) -> str:
    osm_type = clean(row.get("osm_element_type", ""))
    osm_id = clean(row.get("osm_element_id", ""))
    if osm_id:
        return f"osm:{osm_type}:{osm_id}"
    company = company_key(row.get("company_name", ""))
    email = email_key(row.get("email", ""))
    phone = phone_key(row.get("phone", ""))
    website = domain_key(row.get("website", ""))
    city = clean(row.get("city", "")).lower()
    address = clean(row.get("address", "")).lower()
    if email:
        return f"email:{email}|company:{company[:60]}"
    if phone:
        return f"phone:{phone}|company:{company[:60]}"
    if website:
        return f"site:{website}|loc:{address or city}|company:{company[:60]}"
    return f"source:{clean(row.get('source_url', ''))}|company:{company}"


def merge_rows(preferred: dict[str, str], other: dict[str, str], columns: list[str]) -> dict[str, str]:
    result = dict(preferred)
    for column in columns:
        if not clean(result.get(column, "")) and clean(other.get(column, "")):
            result[column] = clean(other.get(column, ""))
    if score(other) > score(result):
        result["confidence_score"] = other.get("confidence_score", "")
        result["confidence_grade"] = other.get("confidence_grade", "")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    input_root = Path(args.input)
    files = sorted(input_root.rglob("shard_*.csv"))
    if not files:
        raise FileNotFoundError(f"No shard CSV files found beneath {input_root}")

    columns: list[str] = []
    raw_rows: list[dict[str, str]] = []
    for path in files:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not columns:
                columns = list(reader.fieldnames or [])
            for row in reader:
                if clean(row.get("company_name", "")):
                    raw_rows.append({key: clean(value) for key, value in row.items()})

    best: dict[str, dict[str, str]] = {}
    for row in raw_rows:
        key = dedupe_key(row)
        current = best.get(key)
        if current is None:
            best[key] = row
            continue
        if (score(row), completeness(row)) > (score(current), completeness(current)):
            best[key] = merge_rows(row, current, columns)
        else:
            best[key] = merge_rows(current, row, columns)

    rows = list(best.values())
    rows.sort(
        key=lambda row: (
            -score(row),
            -completeness(row),
            company_key(row.get("company_name", "")),
            clean(row.get("city", "")).lower(),
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["confidence_rank"] = str(rank)
        row["lead_id"] = f"OSM-NATIONWIDE-{rank:05d}"

    output_path = Path(args.out)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    states = sorted(
        {
            token
            for row in rows
            for token in re.findall(
                r"\b[A-Z]{2}\b",
                " ".join(
                    [
                        row.get("target_states", ""),
                        row.get("headquarters_state", ""),
                    ]
                ).upper(),
            )
            if token not in {"DC"}
        }
    )
    summary = {
        "shard_files": [str(path) for path in files],
        "raw_rows": len(raw_rows),
        "unique_rows": len(rows),
        "duplicates_removed": len(raw_rows) - len(rows),
        "with_email": sum(bool(row.get("email")) for row in rows),
        "with_phone": sum(bool(row.get("phone")) for row in rows),
        "with_both": sum(bool(row.get("email") and row.get("phone")) for row in rows),
        "with_website": sum(bool(row.get("website")) for row in rows),
        "grades": dict(Counter(row.get("confidence_grade", "") for row in rows)),
        "states": states,
        "state_count": len(states),
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

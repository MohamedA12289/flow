from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

import requests

VERIFY_DATE = "2026-08-06"
ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

# id | market | state | lat | lon | radius_km
REGION_TEXT = """
nyc|New York City / North Jersey|NY|40.7128|-74.0060|80
la|Los Angeles / Orange County|CA|34.0522|-118.2437|90
chicago|Chicago / Northwest Indiana|IL|41.8781|-87.6298|85
dallas|Dallas-Fort Worth|TX|32.7767|-96.7970|100
houston|Houston / Galveston|TX|29.7604|-95.3698|100
dc|Washington DC / Baltimore / Northern Virginia|VA|38.9072|-77.0369|100
philly|Philadelphia / South Jersey / Wilmington|PA|39.9526|-75.1652|85
miami|Miami / Fort Lauderdale / Palm Beach|FL|25.7617|-80.1918|105
atlanta|Atlanta|GA|33.7490|-84.3880|95
phoenix|Phoenix / Scottsdale / Mesa|AZ|33.4484|-112.0740|90
seattle|Seattle / Tacoma / Everett|WA|47.6062|-122.3321|95
boston|Boston / Providence / Southern New Hampshire|MA|42.3601|-71.0589|90
sf|San Francisco Bay Area|CA|37.7749|-122.4194|100
denver|Denver / Front Range|CO|39.7392|-104.9903|105
detroit|Detroit / Ann Arbor / Toledo|MI|42.3314|-83.0458|95
minneapolis|Minneapolis-Saint Paul|MN|44.9778|-93.2650|90
sandiego|San Diego|CA|32.7157|-117.1611|75
tampa|Tampa Bay / Sarasota|FL|27.9506|-82.4572|90
orlando|Orlando / Daytona / Lakeland|FL|28.5383|-81.3792|95
charlotte|Charlotte / Greenville-Spartanburg|NC|35.2271|-80.8431|100
raleigh|Raleigh-Durham / Greensboro|NC|35.7796|-78.6382|95
nashville|Nashville / Clarksville|TN|36.1627|-86.7816|90
portland|Portland / Salem / Vancouver|OR|45.5152|-122.6784|95
sacramento|Sacramento / Stockton|CA|38.5816|-121.4944|90
lasvegas|Las Vegas|NV|36.1699|-115.1398|80
austin|Austin / San Antonio corridor|TX|30.2672|-97.7431|115
cleveland|Cleveland / Akron / Canton|OH|41.4993|-81.6944|90
columbus|Columbus / Dayton|OH|39.9612|-82.9988|95
cincinnati|Cincinnati / Northern Kentucky|OH|39.1031|-84.5120|85
indianapolis|Indianapolis|IN|39.7684|-86.1581|90
stlouis|St. Louis|MO|38.6270|-90.1994|90
kansascity|Kansas City / Lawrence / Topeka|MO|39.0997|-94.5786|100
saltlake|Salt Lake City / Provo / Ogden|UT|40.7608|-111.8910|95
neworleans|New Orleans / Baton Rouge|LA|29.9511|-90.0715|105
richmond|Richmond / Fredericksburg / Charlottesville|VA|37.5407|-77.4360|105
hamptonroads|Hampton Roads / Virginia Beach|VA|36.8529|-75.9780|85
birmingham|Birmingham / Montgomery|AL|33.5186|-86.8104|110
oklahomacity|Oklahoma City|OK|35.4676|-97.5164|95
tulsa|Tulsa / Northwest Arkansas|OK|36.1540|-95.9928|100
albuquerque|Albuquerque / Santa Fe|NM|35.0844|-106.6504|100
omaha|Omaha / Lincoln|NE|41.2565|-95.9345|95
desmoines|Des Moines / Ames|IA|41.5868|-93.6250|90
boise|Boise / Treasure Valley|ID|43.6150|-116.2023|90
jacksonville|Jacksonville / St. Augustine|FL|30.3322|-81.6557|95
memphis|Memphis / North Mississippi|TN|35.1495|-90.0490|90
louisville|Louisville / Lexington|KY|38.2527|-85.7585|105
milwaukee|Milwaukee / Madison|WI|43.0389|-87.9065|105
pittsburgh|Pittsburgh / Morgantown|PA|40.4406|-79.9959|95
buffalo|Buffalo / Rochester / Syracuse|NY|42.8864|-78.8784|110
hartford|Hartford / New Haven / Springfield|CT|41.7658|-72.6734|90
maine|Portland Maine / Southern Maine|ME|43.6591|-70.2568|110
newhampshire|Manchester / Concord / Southern New Hampshire|NH|42.9956|-71.4548|85
vermont|Burlington / Central Vermont|VT|44.4759|-73.2121|120
rhodeisland|Providence / Rhode Island|RI|41.8240|-71.4128|60
delaware|Delaware / Eastern Shore|DE|39.1582|-75.5244|80
southcarolina|Columbia / Charleston / Myrtle Beach|SC|33.8361|-80.8987|140
savannah|Savannah / Hilton Head|GA|32.0809|-81.0912|90
mississippi|Jackson / Gulf Coast|MS|32.2988|-90.1848|140
littlerock|Little Rock / Hot Springs|AR|34.7465|-92.2896|110
fargo|Fargo / Grand Forks|ND|46.8772|-96.7898|130
siouxfalls|Sioux Falls / Sioux City|SD|43.5446|-96.7311|125
montana|Billings / Bozeman / Helena|MT|46.8797|-110.3626|260
wyoming|Cheyenne / Casper|WY|42.8666|-106.3131|230
reno|Reno / Lake Tahoe|NV|39.5296|-119.8138|100
spokane|Spokane / Coeur d'Alene|WA|47.6588|-117.4260|95
eugene|Eugene / Central Oregon|OR|44.0521|-123.0868|145
elpaso|El Paso / Las Cruces|TX|31.7619|-106.4850|95
southtexas|Corpus Christi / Rio Grande Valley|TX|27.8006|-97.3964|155
westtexas|Lubbock / Amarillo / Midland-Odessa|TX|33.5779|-101.8552|225
hawaiioahu|Honolulu / Oahu|HI|21.3069|-157.8583|65
hawaiiouter|Hawaii Island / Maui|HI|19.8968|-155.5828|140
anchorage|Anchorage / Mat-Su|AK|61.2181|-149.9003|120
fairbanks|Fairbanks|AK|64.8378|-147.7164|80
westvirginia|Charleston / Huntington / Parkersburg|WV|38.3498|-81.6326|125
marylandeastern|Annapolis / Eastern Shore|MD|38.9784|-76.4922|90
newjersey|Central / South New Jersey|NJ|40.0583|-74.4057|90
"""
REGIONS = [
    (rid, market, state, float(lat), float(lon), int(float(radius) * 1000))
    for rid, market, state, lat, lon, radius in (
        line.split("|") for line in REGION_TEXT.strip().splitlines()
    )
]

NAME_REGEX = (
    "Realty|Real Estate|Realtor|Brokerage|Properties|Property Management|"
    "Home Buyers|House Buyers|Cash Buyers|We Buy Houses|Investments|"
    "Investment Group|Acquisitions|Land Buyers|Capital Partners|"
    "Commercial Real Estate|Real Estate Development|RE/MAX|Keller Williams|"
    "Coldwell Banker|Century 21|Sotheby|Compass Real Estate|eXp Realty|"
    "Berkshire Hathaway|Douglas Elliman|ERA Real Estate"
)
CONTACT_KEYS = ["phone", "contact:phone", "email", "contact:email", "website", "contact:website"]

COLUMNS = [
    "record_type","source_batch","region_id","region_name","confidence_rank","lead_id",
    "confidence_score","confidence_grade","company_name","contact_name","contact_title",
    "broad_group","category","headquarters_state","target_states","target_markets",
    "property_types","strategy","price_min_usd","price_max_usd","units_min","units_max",
    "beds_min","sqft_min","condition","other_criteria","financing","closing_speed",
    "accepts_assignments","email","phone","contact_status","website","address","city",
    "postal_code","latitude","longitude","source_url","source_domain","source_type",
    "source_data_timestamp","criteria_source_type","contact_source_type","buy_box_detail_level",
    "public_data_gaps","confidence_notes","verification_status","last_verified",
    "official_pages_reviewed","website_fetch_status","osm_element_type","osm_element_id",
    "research_method","data_license"
]


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_url(value: object) -> str:
    value = clean(value)
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    if not re.match(r"https?://", value, flags=re.I):
        value = "https://" + value
    try:
        return value if urlsplit(value).netloc else ""
    except Exception:
        return ""


def domain(value: object) -> str:
    try:
        return urlsplit(clean(value)).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def normalize_email(value: object) -> str:
    value = clean(value).replace("mailto:", "").split("?")[0]
    for candidate in re.split(r"[;,\s]+", value):
        candidate = candidate.lower()
        if re.fullmatch(
            r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}",
            candidate,
            flags=re.I,
        ) and not re.search(
            r"example\.|sentry\.io|wixpress\.com|\.(?:png|jpg|jpeg|gif|svg|css|js)$",
            candidate,
            flags=re.I,
        ):
            return candidate
    return ""


def normalize_phone(value: object) -> str:
    value = clean(value)
    if not value:
        return ""
    for candidate in re.split(r"[;,/]|(?:\bor\b)", value, flags=re.I):
        digits = re.sub(r"\D", "", candidate)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return value[:80]


def query_for(region: tuple[str, str, str, float, float, int]) -> str:
    _, _, _, lat, lon, radius = region
    clauses = [
        f'nwr["office"~"^(estate_agent|property_management|real_estate_agent|real_estate|estate_management)$"](around:{radius},{lat},{lon});',
        f'nwr["shop"="estate_agent"](around:{radius},{lat},{lon});',
    ]
    for key in CONTACT_KEYS:
        clauses.append(
            f'nwr["name"~"{NAME_REGEX}",i]["{key}"](around:{radius},{lat},{lon});'
        )
        clauses.append(
            f'nwr["brand"~"{NAME_REGEX}",i]["{key}"](around:{radius},{lat},{lon});'
        )
    return "[out:json][timeout:180];(" + "".join(clauses) + ");out center tags 1400;"


def fetch_region(index: int, region: tuple[str, str, str, float, float, int]):
    last_error = ""
    endpoints = ENDPOINTS[index % len(ENDPOINTS):] + ENDPOINTS[: index % len(ENDPOINTS)]
    query = query_for(region)
    for attempt in range(6):
        endpoint = endpoints[attempt % len(endpoints)]
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                headers={"User-Agent": "PublicRealEstateContactResearch/6.0"},
                timeout=225,
            )
            response.raise_for_status()
            return region, response.json().get("elements", []), ""
        except Exception as exc:
            last_error = f"{endpoint}: {exc}"
            time.sleep(min(18, 2 + attempt * 2 + random.random() * 2))
    return region, [], last_error


def is_relevant(name: str, tags: dict[str, object]) -> bool:
    lowered = name.lower()
    positive = bool(
        re.search(
            r"realty|real estate|realtor|broker|properties|property management|"
            r"home buyers?|house buyers?|cash buyers?|we buy houses|invest|acquisition|"
            r"land buyer|capital partners|commercial real estate|development|"
            r"re/max|keller williams|coldwell banker|century 21|sotheby|compass|"
            r"exp realty|berkshire hathaway",
            lowered,
        )
        or tags.get("office") in {
            "estate_agent","property_management","real_estate_agent","real_estate","estate_management"
        }
        or tags.get("shop") == "estate_agent"
    )
    clearly_unrelated = bool(
        re.search(
            r"mortgage|title company|insurance|attorney|law firm|apprais|home inspect|"
            r"moving|storage|photograph|architect|cleaning|roofing|plumbing|furniture|"
            r"hardware|credit union|\bbank\b",
            lowered,
        )
        and not re.search(
            r"realty|real estate|realtor|properties|property management|home buyer|invest",
            lowered,
        )
    )
    return positive and not clearly_unrelated


def classify(name: str, tags: dict[str, object]):
    combined = f"{name} {clean(tags.get('description'))}".lower()
    if re.search(r"we buy houses|cash home buyer|cash buyer|home buyers?|house buyers?", combined):
        return "Direct Residential Cash Buyer", "Cash Home Buyer / Local Investor", "Direct cash purchase"
    if re.search(r"investment|acquisition|capital partners|holdings|\bfund\b", combined):
        return "Investor / Investment Company", "Real Estate Investor / Acquisitions Company", "Public investor/acquisition signal"
    if re.search(r"property management|rental management", combined):
        return "Property Management / Rental Operator", "Property Management Company", "Property management"
    if re.search(r"commercial real estate|investment sales", combined):
        return "Realtor / Brokerage", "Commercial Real Estate Brokerage", "Commercial brokerage/investment sales"
    if re.search(r"development|home builder", combined):
        return "Builder / Developer", "Real Estate Developer / Builder", "Development"
    return "Realtor / Brokerage", "Real Estate Brokerage / Agent", "Residential brokerage"


def row_from_element(region, element):
    rid, market, query_state, *_ = region
    tags = element.get("tags") or {}
    name = clean(tags.get("name") or tags.get("brand") or tags.get("operator"))
    if not name or not is_relevant(name, tags):
        return None

    phone = normalize_phone(
        tags.get("contact:phone") or tags.get("phone") or
        tags.get("contact:mobile") or tags.get("mobile")
    )
    email = normalize_email(tags.get("contact:email") or tags.get("email"))
    website = normalize_url(
        tags.get("contact:website") or tags.get("website") or tags.get("url")
    )
    if not (phone or email or website):
        return None

    center = element.get("center") or {}
    city = clean(tags.get("addr:city") or tags.get("addr:town") or tags.get("addr:village"))
    state = clean(tags.get("addr:state") or query_state)
    street_line = " ".join(
        filter(None, [clean(tags.get("addr:housenumber")), clean(tags.get("addr:street"))])
    )
    address = clean(
        tags.get("addr:full")
        or ", ".join(filter(None, [street_line, city, state, clean(tags.get("addr:postcode"))]))
    )

    broad_group, category, strategy = classify(name, tags)
    score = 30 + 15 * bool(email) + 15 * bool(phone) + 5 * bool(email and phone)
    score += 8 * bool(website) + 4 * bool(address or city)
    score += 5 * bool("Investor" in broad_group or "Cash Buyer" in broad_group)
    score = min(100, score)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 55 else "D"
    status = (
        "Direct email + phone" if email and phone
        else "Email only" if email
        else "Phone only" if phone
        else "Website only"
    )
    gaps = []
    if not email: gaps.append("public email")
    if not phone: gaps.append("public phone")
    if not website: gaps.append("website")
    gaps.extend(["explicit property criteria", "price range", "closing speed"])

    return {
        "record_type": "CONTACT",
        "source_batch": "OSM-GHA-SHARDED-20260806",
        "region_id": rid,
        "region_name": market,
        "confidence_rank": "",
        "lead_id": "",
        "confidence_score": score,
        "confidence_grade": grade,
        "company_name": name,
        "contact_name": "",
        "contact_title": "",
        "broad_group": broad_group,
        "category": category,
        "headquarters_state": state,
        "target_states": state,
        "target_markets": ", ".join(filter(None, [city, state])),
        "property_types": "",
        "strategy": strategy,
        "price_min_usd": "",
        "price_max_usd": "",
        "units_min": "",
        "units_max": "",
        "beds_min": "",
        "sqft_min": "",
        "condition": "",
        "other_criteria": clean(tags.get("description") or tags.get("note")),
        "financing": "Cash" if "Cash Buyer" in broad_group else "",
        "closing_speed": "",
        "accepts_assignments": "",
        "email": email,
        "phone": phone,
        "contact_status": status,
        "website": website,
        "address": address,
        "city": city,
        "postal_code": clean(tags.get("addr:postcode")),
        "latitude": str(element.get("lat", center.get("lat", ""))),
        "longitude": str(element.get("lon", center.get("lon", ""))),
        "source_url": f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}",
        "source_domain": "; ".join(filter(None, ["openstreetmap.org", domain(website)])),
        "source_type": "OpenStreetMap public business record",
        "source_data_timestamp": clean(element.get("timestamp")),
        "criteria_source_type": "Public business-name/category signal only; exact buy box not confirmed",
        "contact_source_type": "; ".join(filter(None, [
            "Public OSM email" if email else "",
            "Public OSM phone" if phone else "",
            "Public OSM website" if website else "",
        ])),
        "buy_box_detail_level": "Basic",
        "public_data_gaps": "; ".join(gaps),
        "confidence_notes": "Public real-estate business record with available contact fields; exact active-buyer status and buy box not directly confirmed.",
        "verification_status": "Public-source researched; not directly contacted",
        "last_verified": VERIFY_DATE,
        "official_pages_reviewed": "",
        "website_fetch_status": "not_reviewed",
        "osm_element_type": clean(element.get("type")),
        "osm_element_id": clean(element.get("id")),
        "research_method": "OpenStreetMap public business/contact discovery",
        "data_license": "OpenStreetMap data © OpenStreetMap contributors, ODbL 1.0",
    }


def dedupe_key(row):
    company = re.sub(r"[^a-z0-9]+", " ", row["company_name"].lower()).strip()
    email = row["email"].lower()
    phone_digits = re.sub(r"\D", "", row["phone"])[-10:]
    web_domain = domain(row["website"])
    if email:
        return "email:" + email
    if phone_digits:
        return f"phone:{phone_digits}|company:{company[:45]}"
    if web_domain:
        return f"domain:{web_domain}|company:{company[:45]}"
    return f"osm:{row['osm_element_type']}:{row['osm_element_id']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--total-shards", type=int, default=10)
    parser.add_argument("--output-dir", default="generated-temp-export")
    args = parser.parse_args()

    selected = REGIONS[args.shard :: args.total_shards]
    rows = []
    errors = []
    with ThreadPoolExecutor(max_workers=min(4, len(selected))) as executor:
        futures = {
            executor.submit(fetch_region, index, region): region
            for index, region in enumerate(selected)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            region, elements, error = future.result()
            region_rows = [
                candidate
                for candidate in (row_from_element(region, element) for element in elements)
                if candidate is not None
            ]
            rows.extend(region_rows)
            if error:
                errors.append({"region": region[0], "error": error})
            print(
                f"shard={args.shard} {completed}/{len(selected)} "
                f"region={region[0]} elements={len(elements)} kept={len(region_rows)} "
                f"error={bool(error)}",
                flush=True,
            )

    best = {}
    for row in rows:
        key = dedupe_key(row)
        existing = best.get(key)
        if existing is None or int(row["confidence_score"]) > int(existing["confidence_score"]):
            best[key] = row
    rows = sorted(
        best.values(),
        key=lambda row: (-int(row["confidence_score"]), row["company_name"].lower()),
    )
    for index, row in enumerate(rows, start=1):
        row["confidence_rank"] = index
        row["lead_id"] = f"OSM-S{args.shard:02d}-{index:05d}"

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"shard_{args.shard:02d}.csv"
    summary_path = output_dir / f"shard_{args.shard:02d}_summary.json"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "shard": args.shard,
        "total_shards": args.total_shards,
        "regions": [region[0] for region in selected],
        "records": len(rows),
        "with_email": sum(bool(row["email"]) for row in rows),
        "with_phone": sum(bool(row["phone"]) for row in rows),
        "with_both": sum(bool(row["email"] and row["phone"]) for row in rows),
        "grades": {
            grade: sum(row["confidence_grade"] == grade for row in rows)
            for grade in "ABCD"
        },
        "region_errors": errors,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

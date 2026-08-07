from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests

DATE = "2026-08-07"
USER_AGENT = (
    "Mozilla/5.0 (compatible; PublicRealEstateContactResearch/1.0; "
    "+https://www.openstreetmap.org/)"
)
OVERPASS_ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

# id | market label | state | latitude | longitude | radius_km
REGION_DATA = """
al-birmingham|Birmingham|AL|33.5186|-86.8104|55
al-huntsville|Huntsville|AL|34.7304|-86.5861|50
al-mobile|Mobile|AL|30.6954|-88.0399|50
ak-anchorage|Anchorage / Mat-Su|AK|61.2181|-149.9003|85
ak-fairbanks|Fairbanks|AK|64.8378|-147.7164|55
az-phoenix|Phoenix metro|AZ|33.4484|-112.0740|70
az-tucson|Tucson|AZ|32.2226|-110.9747|55
ar-littlerock|Little Rock|AR|34.7465|-92.2896|55
ar-fayetteville|Northwest Arkansas|AR|36.0626|-94.1574|60
ca-losangeles|Los Angeles / Orange County|CA|34.0522|-118.2437|75
ca-sanfrancisco|San Francisco Bay Area|CA|37.7749|-122.4194|75
ca-sandiego|San Diego|CA|32.7157|-117.1611|60
ca-sacramento|Sacramento / Stockton|CA|38.5816|-121.4944|70
ca-fresno|Fresno|CA|36.7378|-119.7871|55
ca-riverside|Inland Empire|CA|33.9806|-117.3755|65
ca-bakersfield|Bakersfield|CA|35.3733|-119.0187|55
ca-sanjose|San Jose / Silicon Valley|CA|37.3382|-121.8863|55
co-denver|Denver / Front Range|CO|39.7392|-104.9903|75
co-coloradosprings|Colorado Springs|CO|38.8339|-104.8214|55
co-fortcollins|Fort Collins|CO|40.5853|-105.0844|55
ct-hartford|Hartford|CT|41.7658|-72.6734|50
ct-newhaven|New Haven|CT|41.3083|-72.9279|45
ct-stamford|Stamford / Fairfield County|CT|41.0534|-73.5387|45
de-wilmington|Wilmington|DE|39.7391|-75.5398|45
de-dover|Dover / Southern Delaware|DE|39.1582|-75.5244|65
fl-miami|Miami / Fort Lauderdale|FL|25.7617|-80.1918|70
fl-tampa|Tampa Bay|FL|27.9506|-82.4572|65
fl-orlando|Orlando / Central Florida|FL|28.5383|-81.3792|70
fl-jacksonville|Jacksonville|FL|30.3322|-81.6557|65
fl-fortmyers|Fort Myers / Naples|FL|26.6406|-81.8723|70
fl-tallahassee|Tallahassee|FL|30.4383|-84.2807|55
fl-pensacola|Pensacola|FL|30.4213|-87.2169|55
ga-atlanta|Atlanta|GA|33.7490|-84.3880|75
ga-savannah|Savannah|GA|32.0809|-81.0912|55
ga-augusta|Augusta|GA|33.4735|-82.0105|50
ga-columbus|Columbus|GA|32.4610|-84.9877|50
hi-honolulu|Oahu / Honolulu|HI|21.3069|-157.8583|45
hi-hilo|Hawaii Island / Hilo|HI|19.7070|-155.0810|75
id-boise|Boise / Treasure Valley|ID|43.6150|-116.2023|70
id-idahofalls|Idaho Falls|ID|43.4917|-112.0339|55
il-chicago|Chicago metro|IL|41.8781|-87.6298|75
il-springfield|Springfield|IL|39.7817|-89.6501|50
il-peoria|Peoria|IL|40.6936|-89.5890|50
il-rockford|Rockford|IL|42.2711|-89.0940|45
in-indianapolis|Indianapolis|IN|39.7684|-86.1581|65
in-fortwayne|Fort Wayne|IN|41.0793|-85.1394|50
in-evansville|Evansville|IN|37.9716|-87.5711|50
in-southbend|South Bend|IN|41.6764|-86.2520|45
ia-desmoines|Des Moines / Ames|IA|41.5868|-93.6250|65
ia-cedarrapids|Cedar Rapids / Iowa City|IA|41.9779|-91.6656|55
ks-wichita|Wichita|KS|37.6872|-97.3301|55
ks-overlandpark|Kansas City Kansas / Overland Park|KS|38.9822|-94.6708|55
ks-topeka|Topeka|KS|39.0473|-95.6752|50
ky-louisville|Louisville|KY|38.2527|-85.7585|60
ky-lexington|Lexington|KY|38.0406|-84.5037|55
ky-bowlinggreen|Bowling Green|KY|36.9685|-86.4808|50
la-neworleans|New Orleans|LA|29.9511|-90.0715|60
la-batonrouge|Baton Rouge|LA|30.4515|-91.1871|55
la-shreveport|Shreveport|LA|32.5252|-93.7502|50
la-lafayette|Lafayette|LA|30.2241|-92.0198|50
me-portland|Portland / Southern Maine|ME|43.6591|-70.2568|65
me-bangor|Bangor|ME|44.8012|-68.7778|55
md-baltimore|Baltimore|MD|39.2904|-76.6122|60
md-annapolis|Annapolis / Eastern Shore|MD|38.9784|-76.4922|55
md-frederick|Frederick / Western Maryland|MD|39.4143|-77.4105|55
ma-boston|Boston metro|MA|42.3601|-71.0589|65
ma-worcester|Worcester|MA|42.2626|-71.8023|50
ma-springfield|Springfield|MA|42.1015|-72.5898|50
mi-detroit|Detroit / Ann Arbor|MI|42.3314|-83.0458|75
mi-grandrapids|Grand Rapids|MI|42.9634|-85.6681|55
mi-lansing|Lansing|MI|42.7325|-84.5555|50
mn-minneapolis|Minneapolis-Saint Paul|MN|44.9778|-93.2650|70
mn-duluth|Duluth|MN|46.7867|-92.1005|50
mn-rochester|Rochester|MN|44.0121|-92.4802|50
ms-jackson|Jackson|MS|32.2988|-90.1848|55
ms-gulfport|Mississippi Gulf Coast|MS|30.3674|-89.0928|60
ms-tupelo|Tupelo|MS|34.2576|-88.7034|50
mo-stlouis|St. Louis|MO|38.6270|-90.1994|65
mo-kansascity|Kansas City|MO|39.0997|-94.5786|65
mo-springfield|Springfield|MO|37.2089|-93.2923|55
mo-columbia|Columbia|MO|38.9517|-92.3341|50
mt-billings|Billings|MT|45.7833|-108.5007|65
mt-missoula|Missoula|MT|46.8721|-113.9940|60
mt-bozeman|Bozeman|MT|45.6770|-111.0429|60
ne-omaha|Omaha / Council Bluffs|NE|41.2565|-95.9345|65
ne-lincoln|Lincoln|NE|40.8136|-96.7026|55
nv-lasvegas|Las Vegas|NV|36.1699|-115.1398|65
nv-reno|Reno / Tahoe|NV|39.5296|-119.8138|65
nh-manchester|Manchester / Concord|NH|42.9956|-71.4548|55
nh-portsmouth|Portsmouth / Seacoast|NH|43.0718|-70.7626|50
nj-newark|North Jersey / Newark|NJ|40.7357|-74.1724|55
nj-trenton|Central Jersey / Trenton|NJ|40.2171|-74.7429|55
nj-atlanticcity|South Jersey / Atlantic City|NJ|39.3643|-74.4229|55
nm-albuquerque|Albuquerque|NM|35.0844|-106.6504|65
nm-santafe|Santa Fe|NM|35.6870|-105.9378|55
nm-lascruces|Las Cruces|NM|32.3199|-106.7637|55
ny-newyork|New York City / Long Island|NY|40.7128|-74.0060|75
ny-buffalo|Buffalo|NY|42.8864|-78.8784|55
ny-rochester|Rochester|NY|43.1566|-77.6088|55
ny-syracuse|Syracuse|NY|43.0481|-76.1474|50
ny-albany|Albany / Capital Region|NY|42.6526|-73.7562|55
nc-charlotte|Charlotte|NC|35.2271|-80.8431|70
nc-raleigh|Raleigh-Durham|NC|35.7796|-78.6382|70
nc-greensboro|Greensboro / Winston-Salem|NC|36.0726|-79.7920|65
nc-wilmington|Wilmington|NC|34.2257|-77.9447|55
nc-asheville|Asheville|NC|35.5951|-82.5515|55
nd-fargo|Fargo|ND|46.8772|-96.7898|55
nd-bismarck|Bismarck|ND|46.8083|-100.7837|55
oh-cleveland|Cleveland / Akron|OH|41.4993|-81.6944|70
oh-columbus|Columbus|OH|39.9612|-82.9988|65
oh-cincinnati|Cincinnati|OH|39.1031|-84.5120|60
oh-dayton|Dayton|OH|39.7589|-84.1916|50
oh-toledo|Toledo|OH|41.6528|-83.5379|50
ok-oklahomacity|Oklahoma City|OK|35.4676|-97.5164|65
ok-tulsa|Tulsa|OK|36.1540|-95.9928|60
or-portland|Portland / Vancouver|OR|45.5152|-122.6784|70
or-eugene|Eugene|OR|44.0521|-123.0868|55
or-bend|Bend|OR|44.0582|-121.3153|55
or-medford|Medford|OR|42.3265|-122.8756|55
pa-philadelphia|Philadelphia|PA|39.9526|-75.1652|70
pa-pittsburgh|Pittsburgh|PA|40.4406|-79.9959|65
pa-harrisburg|Harrisburg / York / Lancaster|PA|40.2732|-76.8867|65
pa-allentown|Lehigh Valley|PA|40.6023|-75.4714|55
pa-erie|Erie|PA|42.1292|-80.0851|50
ri-providence|Rhode Island / Providence|RI|41.8240|-71.4128|50
sc-charleston|Charleston|SC|32.7765|-79.9311|60
sc-columbia|Columbia|SC|34.0007|-81.0348|55
sc-greenville|Greenville / Spartanburg|SC|34.8526|-82.3940|65
sc-myrtlebeach|Myrtle Beach|SC|33.6891|-78.8867|55
sd-siouxfalls|Sioux Falls|SD|43.5446|-96.7311|55
sd-rapidcity|Rapid City|SD|44.0805|-103.2310|55
tn-nashville|Nashville|TN|36.1627|-86.7816|65
tn-memphis|Memphis|TN|35.1495|-90.0490|60
tn-knoxville|Knoxville|TN|35.9606|-83.9207|55
tn-chattanooga|Chattanooga|TN|35.0456|-85.3097|55
tx-dallas|Dallas-Fort Worth|TX|32.7767|-96.7970|80
tx-houston|Houston|TX|29.7604|-95.3698|80
tx-austin|Austin|TX|30.2672|-97.7431|65
tx-sanantonio|San Antonio|TX|29.4241|-98.4936|65
tx-elpaso|El Paso|TX|31.7619|-106.4850|60
tx-lubbock|Lubbock|TX|33.5779|-101.8552|55
tx-corpus|Corpus Christi|TX|27.8006|-97.3964|55
tx-mcallen|Rio Grande Valley|TX|26.2034|-98.2300|55
ut-saltlake|Salt Lake / Ogden|UT|40.7608|-111.8910|70
ut-provo|Provo / Orem|UT|40.2338|-111.6585|50
ut-stgeorge|St. George|UT|37.0965|-113.5684|55
vt-burlington|Burlington|VT|44.4759|-73.2121|55
vt-montpelier|Montpelier / Central Vermont|VT|44.2601|-72.5754|55
va-richmond|Richmond|VA|37.5407|-77.4360|65
va-hamptonroads|Virginia Beach / Hampton Roads|VA|36.8529|-75.9780|65
va-nova|Northern Virginia / DC suburbs|VA|38.8048|-77.0469|65
va-roanoke|Roanoke|VA|37.2709|-79.9414|55
wa-seattle|Seattle / Tacoma|WA|47.6062|-122.3321|75
wa-spokane|Spokane|WA|47.6588|-117.4260|60
wa-vancouver|Vancouver / Southwest Washington|WA|45.6387|-122.6615|55
wv-charleston|Charleston|WV|38.3498|-81.6326|55
wv-morgantown|Morgantown|WV|39.6295|-79.9559|55
wv-huntington|Huntington|WV|38.4192|-82.4452|50
wi-milwaukee|Milwaukee|WI|43.0389|-87.9065|60
wi-madison|Madison|WI|43.0731|-89.4012|55
wi-greenbay|Green Bay|WI|44.5133|-88.0133|50
wy-cheyenne|Cheyenne|WY|41.1400|-104.8202|55
wy-casper|Casper|WY|42.8666|-106.3131|55
dc-washington|Washington DC|DC|38.9072|-77.0369|55
""".strip()

REGIONS: list[dict[str, Any]] = []
for line in REGION_DATA.splitlines():
    region_id, market, state, lat, lon, radius = line.split("|")
    REGIONS.append(
        {
            "region_id": region_id,
            "market": market,
            "state": state,
            "lat": float(lat),
            "lon": float(lon),
            "radius_m": int(float(radius) * 1000),
        }
    )

COLUMNS = [
    "record_type",
    "source_batch",
    "region_id",
    "region_name",
    "confidence_rank",
    "lead_id",
    "confidence_score",
    "confidence_grade",
    "company_name",
    "contact_name",
    "contact_title",
    "broad_group",
    "category",
    "headquarters_state",
    "target_states",
    "target_markets",
    "target_cities_counties_or_zip_codes",
    "property_types",
    "strategy",
    "price_min_usd",
    "price_max_usd",
    "units_min",
    "units_max",
    "beds_min",
    "baths_min",
    "sqft_min",
    "lot_size_min",
    "year_built_min",
    "year_built_max",
    "condition",
    "other_criteria",
    "financing",
    "closing_speed",
    "accepts_assignments",
    "proof_of_funds",
    "email",
    "phone",
    "contact_status",
    "website",
    "address",
    "city",
    "postal_code",
    "latitude",
    "longitude",
    "source_url",
    "secondary_source_url",
    "source_domain",
    "source_type",
    "source_data_timestamp",
    "criteria_source_type",
    "contact_source_type",
    "buy_box_detail_level",
    "public_data_gaps",
    "confidence_notes",
    "verification_status",
    "last_verified",
    "official_pages_reviewed",
    "website_fetch_status",
    "osm_element_type",
    "osm_element_id",
    "research_method",
    "data_license",
]

EMAIL_RE = re.compile(
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I
)
PHONE_RE = re.compile(
    r"(?:\+?1[\s.\-()]*)?(?:\(?\d{3}\)?[\s.\-]*)\d{3}[\s.\-]*\d{4}"
)
HREF_RE = re.compile(r"href\s*=\s*[\"']([^\"']+)[\"']", re.I)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_email(value: str) -> str:
    value = html.unescape(clean(value)).lower().replace("mailto:", "").split("?")[0]
    for candidate in re.split(r"[;,\s]+", value):
        if EMAIL_RE.fullmatch(candidate):
            if re.search(
                r"(?:example\.(?:com|org|net)|sentry\.io|wixpress\.com|"
                r"\.(?:png|jpg|jpeg|gif|svg|webp|css|js)$)",
                candidate,
                re.I,
            ):
                continue
            return candidate
    return ""


def normalize_phone(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    for candidate in re.split(r"[;,/]|\bor\b", value, flags=re.I):
        digits = re.sub(r"\D", "", candidate)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) == 10 and digits[:3] not in {"000", "111", "123", "555"}:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return ""


def normalize_url(value: str) -> str:
    value = html.unescape(clean(value))
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    if not re.match(r"https?://", value, re.I):
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        return value if parsed.netloc else ""
    except Exception:
        return ""


def domain(value: str) -> str:
    try:
        return urlsplit(normalize_url(value)).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def strip_html(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return clean(html.unescape(raw))


def build_query(region: dict[str, Any], radius_m: int | None = None) -> str:
    radius = radius_m or region["radius_m"]
    lat = region["lat"]
    lon = region["lon"]
    return f"""[out:json][timeout:120];
(
  nwr[\"office\"~\"^(estate_agent|property_management|real_estate_agent|real_estate|estate_management)$\"][\"name\"](around:{radius},{lat},{lon});
  nwr[\"shop\"=\"estate_agent\"][\"name\"](around:{radius},{lat},{lon});
  nwr[\"name\"~\"(Home Buyers|House Buyers|Cash Buyers|We Buy Houses|Real Estate Investments|Property Investors|Acquisitions)\",i][~\"^(phone|contact:phone|mobile|contact:mobile|email|contact:email|website|contact:website)$\"~\".\"](around:{radius},{lat},{lon});
);
out center tags 1200;"""


def fetch_region(
    region: dict[str, Any], shard: int, session: requests.Session
) -> tuple[list[dict[str, Any]], str, str]:
    endpoints = OVERPASS_ENDPOINTS[shard % len(OVERPASS_ENDPOINTS) :] + OVERPASS_ENDPOINTS[
        : shard % len(OVERPASS_ENDPOINTS)
    ]
    last_error = ""
    radii = [region["radius_m"], max(30000, int(region["radius_m"] * 0.65))]
    for radius in radii:
        for attempt in range(7):
            endpoint = endpoints[attempt % len(endpoints)]
            try:
                response = session.post(
                    endpoint,
                    data={"data": build_query(region, radius)},
                    headers={"User-Agent": USER_AGENT},
                    timeout=(20, 190),
                )
                response.raise_for_status()
                payload = response.json()
                remark = clean(payload.get("remark"))
                elements = payload.get("elements") or []
                if remark and not elements:
                    raise RuntimeError(remark[:500])
                timestamp = clean((payload.get("osm3s") or {}).get("timestamp_osm_base"))
                if elements:
                    return elements, timestamp, ""
                last_error = "Valid Overpass response contained no matching elements"
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(min(16, 1.5 + attempt * 1.8 + random.random()))
    return [], "", last_error


def category_for(name: str, tags: dict[str, Any]) -> tuple[str, str, str]:
    text = " ".join(
        [name, clean(tags.get("description")), clean(tags.get("operator"))]
    ).lower()
    if re.search(r"we buy houses|cash home buyer|cash buyer|home buyers?|house buyers?", text):
        return (
            "Direct Residential Cash Buyer",
            "Cash Home Buyer / Local Investor",
            "Direct cash purchase",
        )
    if re.search(r"investments?|acquisitions?|capital partners|holdings|\bfund\b", text):
        return (
            "Investor / Investment Company",
            "Real Estate Investor / Acquisitions Company",
            "Public investor or acquisition signal",
        )
    if re.search(r"property management|rental management", text) or tags.get(
        "office"
    ) == "property_management":
        return (
            "Property Management / Rental Operator",
            "Property Management Company",
            "Property management and rental operations",
        )
    if re.search(r"commercial real estate|investment sales", text):
        return (
            "Realtor / Brokerage",
            "Commercial Real Estate Brokerage",
            "Commercial brokerage or investment sales",
        )
    if re.search(r"development|home builder|builders?", text):
        return (
            "Builder / Developer",
            "Real Estate Developer / Builder",
            "Development",
        )
    return (
        "Realtor / Brokerage",
        "Real Estate Brokerage / Agent",
        "Residential brokerage and buyer representation",
    )


def record_from_element(
    region: dict[str, Any], element: dict[str, Any], timestamp: str, shard: int
) -> dict[str, str] | None:
    tags = element.get("tags") or {}
    name = clean(tags.get("name") or tags.get("brand") or tags.get("operator"))
    if not name:
        return None
    lower_name = name.lower()
    if re.search(
        r"mortgage|title agency|title company|insurance|attorney|law firm|apprais|"
        r"home inspect|moving company|photograph|architect|cleaning service|roofing|"
        r"plumbing|furniture|hardware|credit union|\bbank\b|school of real estate",
        lower_name,
    ) and not re.search(r"realty|real estate|realtor|properties|property management", lower_name):
        return None

    phone = normalize_phone(
        clean(
            tags.get("contact:phone")
            or tags.get("phone")
            or tags.get("contact:mobile")
            or tags.get("mobile")
        )
    )
    email = normalize_email(clean(tags.get("contact:email") or tags.get("email")))
    website = normalize_url(
        clean(tags.get("contact:website") or tags.get("website") or tags.get("url"))
    )
    if not (phone or email or website):
        return None

    center = element.get("center") or {}
    lat = element.get("lat", center.get("lat", ""))
    lon = element.get("lon", center.get("lon", ""))
    city = clean(
        tags.get("addr:city")
        or tags.get("addr:town")
        or tags.get("addr:village")
        or tags.get("addr:suburb")
    )
    state = clean(tags.get("addr:state") or region["state"])
    postcode = clean(tags.get("addr:postcode"))
    street_line = clean(
        " ".join(
            filter(
                None,
                [clean(tags.get("addr:housenumber")), clean(tags.get("addr:street"))],
            )
        )
    )
    address = clean(
        tags.get("addr:full")
        or ", ".join(filter(None, [street_line, city, state, postcode]))
    )
    broad_group, category, strategy = category_for(name, tags)
    source_url = (
        f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}"
    )
    notes = clean(tags.get("description") or tags.get("note"))
    return {
        "record_type": "CONTACT",
        "source_batch": f"OSM-SHARD-{shard:02d}",
        "region_id": region["region_id"],
        "region_name": region["market"],
        "confidence_rank": "",
        "lead_id": "",
        "confidence_score": "",
        "confidence_grade": "",
        "company_name": name,
        "contact_name": clean(tags.get("contact:person") or tags.get("operator")),
        "contact_title": "",
        "broad_group": broad_group,
        "category": category,
        "headquarters_state": state,
        "target_states": region["state"],
        "target_markets": region["market"],
        "target_cities_counties_or_zip_codes": clean(
            ", ".join(filter(None, [city, postcode]))
        ),
        "property_types": "",
        "strategy": strategy,
        "price_min_usd": "",
        "price_max_usd": "",
        "units_min": "",
        "units_max": "",
        "beds_min": "",
        "baths_min": "",
        "sqft_min": "",
        "lot_size_min": "",
        "year_built_min": "",
        "year_built_max": "",
        "condition": "",
        "other_criteria": notes,
        "financing": "Cash" if broad_group == "Direct Residential Cash Buyer" else "",
        "closing_speed": "",
        "accepts_assignments": "",
        "proof_of_funds": "",
        "email": email,
        "phone": phone,
        "contact_status": "",
        "website": website,
        "address": address,
        "city": city,
        "postal_code": postcode,
        "latitude": clean(lat),
        "longitude": clean(lon),
        "source_url": source_url,
        "secondary_source_url": website,
        "source_domain": "; ".join(filter(None, ["openstreetmap.org", domain(website)])),
        "source_type": "OpenStreetMap public business record",
        "source_data_timestamp": timestamp,
        "criteria_source_type": (
            "Public business-name/category signal only; exact buy box not confirmed"
        ),
        "contact_source_type": "; ".join(
            filter(
                None,
                [
                    "Public OSM email" if email else "",
                    "Public OSM phone" if phone else "",
                    "Public OSM website" if website else "",
                ],
            )
        ),
        "buy_box_detail_level": "Basic",
        "public_data_gaps": "",
        "confidence_notes": "",
        "verification_status": "Public-source researched; not directly contacted",
        "last_verified": DATE,
        "official_pages_reviewed": "",
        "website_fetch_status": "not_attempted" if website else "no_website",
        "osm_element_type": clean(element.get("type")),
        "osm_element_id": clean(element.get("id")),
        "research_method": (
            "OpenStreetMap business/contact extraction plus limited official-website enrichment"
        ),
        "data_license": "OpenStreetMap data: ODbL; official-site facts remain attributed to source URLs",
    }


def extract_contact_page_urls(base_url: str, raw_html: str) -> list[str]:
    base_domain = domain(base_url)
    scored: list[tuple[int, str]] = []
    for href in HREF_RE.findall(raw_html):
        href = html.unescape(href).strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        candidate = normalize_url(urljoin(base_url, href))
        if not candidate or domain(candidate) != base_domain:
            continue
        lowered = candidate.lower()
        score = 0
        for token, points in [
            ("contact", 12),
            ("about", 5),
            ("team", 4),
            ("acquisition", 11),
            ("buy-box", 12),
            ("buybox", 12),
            ("invest", 7),
            ("submit", 5),
            ("sell", 3),
        ]:
            if token in lowered:
                score += points
        if score:
            scored.append((score, candidate.split("#")[0]))
    unique: list[str] = []
    for _, url in sorted(scored, reverse=True):
        if url not in unique and url != base_url:
            unique.append(url)
        if len(unique) >= 2:
            break
    return unique


def extract_page_facts(raw_html: str) -> dict[str, Any]:
    decoded = html.unescape(raw_html)
    decoded = re.sub(r"\s*(?:\[at\]|\(at\))\s*", "@", decoded, flags=re.I)
    decoded = re.sub(r"\s*(?:\[dot\]|\(dot\))\s*", ".", decoded, flags=re.I)
    emails: list[str] = []
    for value in EMAIL_RE.findall(decoded):
        normalized = normalize_email(value)
        if normalized and normalized not in emails:
            emails.append(normalized)
    phones: list[str] = []
    for value in PHONE_RE.findall(decoded):
        normalized = normalize_phone(value)
        if normalized and normalized not in phones:
            phones.append(normalized)

    text = strip_html(decoded)
    lower = text.lower()
    property_types: list[str] = []
    for label, pattern in [
        ("Single-family", r"single[ -]family"),
        ("Townhouses", r"townhous|townhome"),
        ("Condos", r"\bcondo"),
        ("Multifamily", r"multi[ -]family|apartment building"),
        ("Duplex / triplex / fourplex", r"duplex|triplex|fourplex"),
        ("Mobile / manufactured homes", r"mobile home|manufactured home"),
        ("Land", r"vacant land|raw land|land buyer"),
        ("Commercial", r"commercial real estate|retail property|office building"),
    ]:
        if re.search(pattern, lower):
            property_types.append(label)

    strategies: list[str] = []
    for label, pattern in [
        ("Direct cash purchase", r"cash offer|buy houses for cash|we buy houses"),
        ("Fix and flip", r"fix and flip|house flipp"),
        ("Rental / buy and hold", r"buy and hold|rental propert|landlord"),
        ("BRRRR", r"\bbrrrr\b"),
        ("Wholesale / assignments", r"wholesale deal|assignment of contract"),
        ("Development", r"real estate development|developable land"),
        ("Property management", r"property management|rental management"),
    ]:
        if re.search(pattern, lower):
            strategies.append(label)

    conditions: list[str] = []
    for label, pattern in [
        ("Any condition / as-is", r"any condition|as[ -]is|no repairs"),
        ("Distressed / fixer-upper", r"distressed|fixer[ -]upper|needs repairs"),
        ("Inherited / probate", r"inherited|probate"),
        ("Foreclosure / pre-foreclosure", r"pre[ -]foreclosure|foreclosure"),
        ("Tenant-occupied", r"tenant[ -]occupied|bad tenants"),
        ("Fire / water damage", r"fire damage|water damage|flood damage"),
    ]:
        if re.search(pattern, lower):
            conditions.append(label)

    closing_speed = ""
    speed_match = re.search(
        r"(?:close|closing)[^.!?]{0,55}?(?:in|within|as little as)\s+"
        r"(\d{1,3}(?:\s*(?:-|to)\s*\d{1,3})?\s*(?:business\s+)?days?)",
        lower,
    )
    if speed_match:
        closing_speed = "Close " + clean(speed_match.group(1))
    elif "offer within 24 hours" in lower or "cash offer in 24 hours" in lower:
        closing_speed = "Offer within 24 hours"

    accepts_assignments = ""
    if re.search(r"accept(?:s|ing)? assignments?|assignment of contract", lower):
        accepts_assignments = "Yes — assignment language found on official site"
    elif re.search(r"do not accept assignments?|no assignments?", lower):
        accepts_assignments = "No — official site states assignments are not accepted"

    return {
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "property_types": "; ".join(property_types),
        "strategy": "; ".join(strategies),
        "condition": "; ".join(conditions),
        "closing_speed": closing_speed,
        "accepts_assignments": accepts_assignments,
        "criteria_signal_count": len(property_types)
        + len(strategies)
        + len(conditions)
        + bool(closing_speed)
        + bool(accepts_assignments),
    }


def fetch_official_site(website: str) -> dict[str, Any]:
    website = normalize_url(website)
    result: dict[str, Any] = {
        "status": "failed",
        "pages": [],
        "email": "",
        "phone": "",
        "property_types": "",
        "strategy": "",
        "condition": "",
        "closing_speed": "",
        "accepts_assignments": "",
        "criteria_signal_count": 0,
    }
    if not website:
        result["status"] = "no_website"
        return result

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.8",
        }
    )
    urls = [website]
    raw_pages: list[tuple[str, str]] = []
    try:
        first = session.get(website, timeout=(8, 14), allow_redirects=True)
        if first.status_code >= 400:
            result["status"] = f"http_{first.status_code}"
            return result
        if "text/html" not in first.headers.get("content-type", "").lower():
            result["status"] = "non_html"
            return result
        first_text = first.text[:2_000_000]
        first_url = first.url
        raw_pages.append((first_url, first_text))
        urls.extend(extract_contact_page_urls(first_url, first_text))
        for url in urls[1:3]:
            try:
                page = session.get(url, timeout=(8, 12), allow_redirects=True)
                if page.status_code < 400 and "text/html" in page.headers.get(
                    "content-type", ""
                ).lower():
                    raw_pages.append((page.url, page.text[:1_500_000]))
            except Exception:
                continue
    except Exception as exc:
        result["status"] = f"request_error:{type(exc).__name__}"
        return result

    combined = "\n".join(raw for _, raw in raw_pages)
    facts = extract_page_facts(combined)
    result.update(facts)
    result["pages"] = [url for url, _ in raw_pages]
    result["status"] = "enriched" if raw_pages else "failed"
    return result


def confidence_score(record: dict[str, str], criteria_signals: int = 0) -> int:
    email = bool(record.get("email"))
    phone = bool(record.get("phone"))
    website = bool(record.get("website"))
    score = 24
    score += 18 if email else 0
    score += 18 if phone else 0
    score += 8 if email and phone else 0
    score += 7 if website else 0
    score += 5 if record.get("address") or record.get("city") else 0
    score += 6 if record.get("website_fetch_status") == "enriched" else 0
    score += 7 if record.get("broad_group") in {
        "Direct Residential Cash Buyer",
        "Investor / Investment Company",
    } else 0
    score += min(8, int(criteria_signals) * 2)
    score += 2 if record.get("contact_name") else 0
    return min(100, score)


def grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def finalize_record(record: dict[str, str], criteria_signals: int = 0) -> None:
    email = bool(record.get("email"))
    phone = bool(record.get("phone"))
    website = bool(record.get("website"))
    record["contact_status"] = (
        "Direct email + phone"
        if email and phone
        else "Email only"
        if email
        else "Phone only"
        if phone
        else "Website only"
        if website
        else "No direct public contact"
    )
    missing: list[str] = []
    if not email:
        missing.append("public email")
    if not phone:
        missing.append("public phone")
    if not record.get("property_types"):
        missing.append("explicit property types")
    if not record.get("price_min_usd") and not record.get("price_max_usd"):
        missing.append("price range")
    if not record.get("closing_speed"):
        missing.append("closing speed")
    if not record.get("accepts_assignments"):
        missing.append("assignment policy")
    record["public_data_gaps"] = "; ".join(missing)
    score = confidence_score(record, criteria_signals)
    record["confidence_score"] = str(score)
    record["confidence_grade"] = grade(score)
    details = []
    if email and phone:
        details.append("public email and phone")
    elif email or phone:
        details.append("one direct public contact method")
    else:
        details.append("website-only public contact")
    if record.get("website_fetch_status") == "enriched":
        details.append("official website reviewed")
    if criteria_signals:
        details.append(f"{criteria_signals} acquisition/property signals found")
    else:
        details.append("exact buyer buy box not publicly confirmed")
    record["confidence_notes"] = "; ".join(details) + "."
    record["buy_box_detail_level"] = (
        "Detailed" if criteria_signals >= 5 else "Moderate" if criteria_signals >= 2 else "Basic"
    )
    if criteria_signals:
        record["criteria_source_type"] = (
            "Official website keyword-supported criteria; exact limits may remain incomplete"
        )


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
    all_records: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for index, region in enumerate(selected, start=1):
        elements, timestamp, error = fetch_region(region, args.shard, session)
        if error:
            errors.append({"region_id": region["region_id"], "error": error})
        region_records: list[dict[str, str]] = []
        for element in elements:
            record = record_from_element(region, element, timestamp, args.shard)
            if record:
                region_records.append(record)
        all_records.extend(region_records)
        print(
            json.dumps(
                {
                    "shard": args.shard,
                    "region": region["region_id"],
                    "progress": f"{index}/{len(selected)}",
                    "elements": len(elements),
                    "kept": len(region_records),
                    "error": error[:180],
                }
            ),
            flush=True,
        )

    # Deduplicate by the stable OSM element identifier before web enrichment.
    by_osm: dict[str, dict[str, str]] = {}
    for record in all_records:
        key = f"{record['osm_element_type']}:{record['osm_element_id']}"
        existing = by_osm.get(key)
        if existing is None:
            by_osm[key] = record
            continue
        for column in COLUMNS:
            if not existing.get(column) and record.get(column):
                existing[column] = record[column]
    all_records = list(by_osm.values())

    # Enrich one time per official domain, prioritizing buyers/investors and
    # records missing an email or phone.
    domains_to_url: dict[str, str] = {}
    priority: list[tuple[int, str]] = []
    for record in all_records:
        website = record.get("website", "")
        site_domain = domain(website)
        if not site_domain or site_domain in domains_to_url:
            continue
        points = 0
        if record.get("broad_group") in {
            "Direct Residential Cash Buyer",
            "Investor / Investment Company",
        }:
            points += 25
        if not record.get("email"):
            points += 10
        if not record.get("phone"):
            points += 8
        points += 3 if record.get("address") else 0
        domains_to_url[site_domain] = website
        priority.append((points, site_domain))

    max_domains = min(240, len(priority))
    selected_domains = [d for _, d in sorted(priority, reverse=True)[:max_domains]]
    enrichment: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_map = {
            executor.submit(fetch_official_site, domains_to_url[d]): d
            for d in selected_domains
        }
        for completed, future in enumerate(as_completed(future_map), start=1):
            site_domain = future_map[future]
            try:
                enrichment[site_domain] = future.result()
            except Exception as exc:
                enrichment[site_domain] = {
                    "status": f"worker_error:{type(exc).__name__}",
                    "pages": [],
                    "criteria_signal_count": 0,
                }
            if completed % 25 == 0 or completed == len(future_map):
                print(
                    json.dumps(
                        {
                            "shard": args.shard,
                            "website_enrichment": f"{completed}/{len(future_map)}",
                        }
                    ),
                    flush=True,
                )

    for record in all_records:
        facts = enrichment.get(domain(record.get("website", "")))
        criteria_signals = 0
        if facts:
            if not record.get("email"):
                record["email"] = normalize_email(clean(facts.get("email")))
            if not record.get("phone"):
                record["phone"] = normalize_phone(clean(facts.get("phone")))
            for field in [
                "property_types",
                "condition",
                "closing_speed",
                "accepts_assignments",
            ]:
                if not record.get(field) and clean(facts.get(field)):
                    record[field] = clean(facts.get(field))
            if clean(facts.get("strategy")):
                if record.get("strategy"):
                    existing = [x.strip() for x in record["strategy"].split(";") if x.strip()]
                    for value in [x.strip() for x in clean(facts["strategy"]).split(";")]:
                        if value and value not in existing:
                            existing.append(value)
                    record["strategy"] = "; ".join(existing)
                else:
                    record["strategy"] = clean(facts["strategy"])
            record["official_pages_reviewed"] = "; ".join(facts.get("pages") or [])
            record["website_fetch_status"] = clean(facts.get("status"))
            criteria_signals = int(facts.get("criteria_signal_count") or 0)
            if record.get("email") or record.get("phone"):
                sources = [
                    x.strip()
                    for x in record.get("contact_source_type", "").split(";")
                    if x.strip()
                ]
                if facts.get("email") and "Official website email extraction" not in sources:
                    sources.append("Official website email extraction")
                if facts.get("phone") and "Official website phone extraction" not in sources:
                    sources.append("Official website phone extraction")
                record["contact_source_type"] = "; ".join(sources)
        finalize_record(record, criteria_signals)

    all_records.sort(
        key=lambda row: (
            -int(row.get("confidence_score") or 0),
            row.get("company_name", "").lower(),
            row.get("region_id", ""),
        )
    )
    for rank, record in enumerate(all_records, start=1):
        record["confidence_rank"] = str(rank)
        record["lead_id"] = f"OSM-{args.shard:02d}-{rank:05d}"

    output = Path(args.out)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)

    summary = {
        "shard": args.shard,
        "shards": args.shards,
        "regions_assigned": len(selected),
        "records": len(all_records),
        "with_email": sum(bool(r.get("email")) for r in all_records),
        "with_phone": sum(bool(r.get("phone")) for r in all_records),
        "with_both": sum(bool(r.get("email") and r.get("phone")) for r in all_records),
        "with_website": sum(bool(r.get("website")) for r in all_records),
        "grades": {
            grade_name: sum(r.get("confidence_grade") == grade_name for r in all_records)
            for grade_name in ["A", "B", "C", "D"]
        },
        "region_errors": errors,
    }
    summary_path = output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()

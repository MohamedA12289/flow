from __future__ import annotations

import math
from typing import Any

import realtor_ultrafast_shard as base


def small_bbox(region: dict[str, Any], radius_km: float = 18.0) -> str:
    lat = float(region["lat"])
    lon = float(region["lon"])
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / max(25.0, 111.0 * math.cos(math.radians(lat)))
    return f"{lat-lat_delta:.6f},{lon-lon_delta:.6f},{lat+lat_delta:.6f},{lon+lon_delta:.6f}"


base.bbox = small_bbox

if __name__ == "__main__":
    base.main()

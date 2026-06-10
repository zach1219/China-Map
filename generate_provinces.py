#!/usr/bin/env python
"""Process China GeoJSON into SVG path data with label centers."""
import json
import math
import urllib.request
import sys

# ── Configuration ──
VIEW_W, VIEW_H = 560, 470
CENTER_LON, CENTER_LAT = 105.0, 36.0
SCALE_FACTOR = 6.5  # approximate pixels per degree

# Derived projection constants
# x = (lon - 105) * cos(36°) * SCALE_FACTOR + VIEW_W/2
# y = (36 - lat) * SCALE_FACTOR + VIEW_H/2
COS36 = math.cos(math.radians(36))
OFFSET_X = VIEW_W / 2
OFFSET_Y = VIEW_H / 2

def project(lon, lat):
    x = (lon - CENTER_LON) * COS36 * SCALE_FACTOR + OFFSET_X
    y = (CENTER_LAT - lat) * SCALE_FACTOR + OFFSET_Y
    return x, y

# Province short names
SHORT_NAMES = {
    "北京市": "京", "天津市": "津", "河北省": "冀", "山西省": "晋",
    "内蒙古自治区": "蒙", "辽宁省": "辽", "吉林省": "吉", "黑龙江省": "黑",
    "上海市": "沪", "江苏省": "苏", "浙江省": "浙", "安徽省": "皖",
    "福建省": "闽", "江西省": "赣", "山东省": "鲁", "河南省": "豫",
    "湖北省": "鄂", "湖南省": "湘", "广东省": "粤", "广西壮族自治区": "桂",
    "海南省": "琼", "重庆市": "渝", "四川省": "川", "贵州省": "黔",
    "云南省": "滇", "西藏自治区": "藏", "陕西省": "陕", "甘肃省": "甘",
    "青海省": "青", "宁夏回族自治区": "宁", "新疆维吾尔自治区": "新",
    "台湾省": "台", "香港特别行政区": "港", "澳门特别行政区": "澳",
}

# Province IDs (pinyin abbreviations)
PROVINCE_IDS = {
    110000: "BEJ", 120000: "TJN", 130000: "HEB", 140000: "SHX",
    150000: "NMG", 210000: "LIA", 220000: "JIL", 230000: "HLJ",
    310000: "SHA", 320000: "JSU", 330000: "ZHJ", 340000: "ANH",
    350000: "FUJ", 360000: "JXI", 370000: "SHD", 410000: "HEN",
    420000: "HUB", 430000: "HUN", 440000: "GUD", 450000: "GXI",
    460000: "HAI", 500000: "CQG", 510000: "SIC", 520000: "GUI",
    530000: "YUN", 540000: "TIB", 610000: "SHA2", 620000: "GAN",
    630000: "QIH", 640000: "NIX", 650000: "XJG",
    710000: "TAI", 810000: "HKG", 820000: "MAC",
}

def coords_to_svg_path(coords, is_polygon=True):
    """Convert a GeoJSON coordinate ring to SVG path string."""
    parts = []
    for ring in coords:
        points = []
        for pt in ring:
            x, y = project(pt[0], pt[1])
            points.append((round(x, 2), round(y, 2)))
        if not points:
            continue
        d = f"M{points[0][0]},{points[0][1]}"
        for p in points[1:]:
            d += f"L{p[0]},{p[1]}"
        d += "Z"
        parts.append(d)
    return "".join(parts)

def coords_to_svg_path_line(coords):
    """Convert nine-dash line coords to SVG path (no fill)."""
    d_parts = []
    for line in coords:
        points = []
        for pt in line:
            x, y = project(pt[0], pt[1])
            points.append((round(x, 2), round(y, 2)))
        if not points:
            continue
        d = f"M{points[0][0]},{points[0][1]}"
        for p in points[1:]:
            d += f"L{p[0]},{p[1]}"
        d_parts.append(d)
    return "".join(d_parts)

def polygon_area_and_centroid(rings):
    """Compute centroid of first ring using shoelace formula."""
    ring = rings[0]
    if len(ring) < 3:
        # fallback: average of points
        sx = sum(project(p[0], p[1])[0] for p in ring)
        sy = sum(project(p[0], p[1])[1] for p in ring)
        n = len(ring)
        return round(sx/n, 1), round(sy/n, 1)
    
    # Project all points
    pts = [project(p[0], p[1]) for p in ring]
    
    cx, cy = 0.0, 0.0
    signed_area = 0.0
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        cross = pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        signed_area += cross
        cx += (pts[i][0] + pts[j][0]) * cross
        cy += (pts[i][1] + pts[j][1]) * cross
    signed_area *= 0.5
    if abs(signed_area) < 1e-10:
        sx = sum(p[0] for p in pts)
        sy = sum(p[1] for p in pts)
        return round(sx/n, 1), round(sy/n, 1)
    cx /= (6 * signed_area)
    cy /= (6 * signed_area)
    return round(cx, 1), round(cy, 1)

def compute_centroid(geometry):
    """Compute centroid for MultiPolygon or Polygon geometry."""
    coords = geometry["coordinates"]
    gtype = geometry["type"]
    
    if gtype == "Polygon":
        return polygon_area_and_centroid(coords)
    elif gtype == "MultiPolygon":
        # Use largest polygon by area for centroid
        best_cx, best_cy = 0, 0
        best_area = 0
        for poly in coords:
            ring = poly[0]
            pts = [project(p[0], p[1]) for p in ring]
            # Shoelace area
            area = 0.0
            n = len(pts)
            for i in range(n):
                j = (i + 1) % n
                area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
            area = abs(area) * 0.5
            if area > best_area:
                best_area = area
                best_cx, best_cy = polygon_area_and_centroid(poly)
        return best_cx, best_cy
    return 280, 235

def build_svg_path(geometry):
    """Convert geometry to SVG path d string."""
    coords = geometry["coordinates"]
    gtype = geometry["type"]
    
    if gtype == "Polygon":
        return coords_to_svg_path(coords)
    elif gtype == "MultiPolygon":
        parts = []
        for poly in coords:
            parts.append(coords_to_svg_path(poly))
        return "".join(parts)
    return ""

# ── Main ──
print("Loading GeoJSON...")
with open("C:/Users/zach/China-Map/china.geojson", "r", encoding="utf-8") as f:
    geo = json.load(f)

features = geo["features"]
print(f"Found {len(features)} features")

results = []
city_adcodes_map = {}  # province adcode -> list of city adcodes

for feat in features:
    props = feat["properties"]
    adcode = props["adcode"]
    name = props["name"]
    geom = feat["geometry"]
    
    # Check if this is the nine-dash line
    adcode_str = str(adcode)
    if "JD" in adcode_str or adcode_str == "100000_JD":
        # Nine-dash line - render as dashed polyline
        d = build_svg_path(geom)
        # Compute rough center
        cx, cy = 305, 370  # Bottom-right of map
        results.append({
            "id": "JDX",
            "name": "南海诸岛",
            "short": "",
            "d": d,
            "center": [cx, cy],
            "cityAdcode": None,
            "isDash": True
        })
        print(f"  JDX: 南海诸岛 (nine-dash line)")
        continue
    
    # Determine province ID
    pid = PROVINCE_IDS.get(adcode)
    if pid is None:
        # Skip features that aren't provinces
        print(f"  Skipping adcode={adcode} name={name} (no province ID mapping)")
        continue
    
    short = SHORT_NAMES.get(name, "")
    
    # Build SVG path
    d = build_svg_path(geom)
    
    # Compute centroid
    cx, cy = compute_centroid(geom)
    
    results.append({
        "id": pid,
        "name": name,
        "short": short,
        "d": d,
        "center": [cx, cy],
        "cityAdcode": adcode,
        "isDash": False
    })
    print(f"  {pid}: {name} ({short}) center=[{cx},{cy}]")

# Nine-dash line is already handled in the main loop above

# ── Fetch city adcodes per province ──
print("\nFetching city adcodes for each province...")
for entry in results:
    if entry["isDash"] or entry["cityAdcode"] is None:
        entry["cityAdcodes"] = []
        continue
    
    adcode = entry["cityAdcode"]
    url = f"https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json"
    try:
        print(f"  Fetching {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        city_codes = []
        city_names = []
        for f2 in data.get("features", []):
            ca = f2["properties"]["adcode"]
            cn = f2["properties"]["name"]
            city_codes.append(ca)
            city_names.append(cn)
        entry["cityAdcodes"] = city_codes
        entry["cityNames"] = city_names
        print(f"    -> {len(city_codes)} cities")
    except Exception as e:
        print(f"    ERROR: {e}")
        entry["cityAdcodes"] = []

# ── Adjust viewBox based on actual coordinates ──
# Find bounding box of all paths
all_x = []
all_y = []
for entry in results:
    if entry["isDash"]:
        continue
    d = entry["d"]
    # Quick parse to find coordinate range
    import re
    nums = re.findall(r'[-\d.]+', d)
    for i in range(0, len(nums)-1, 2):
        try:
            all_x.append(float(nums[i]))
            all_y.append(float(nums[i+1]))
        except:
            pass

if all_x:
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    print(f"\nSVG path bounds: x=[{min_x:.1f}, {max_x:.1f}] y=[{min_y:.1f}, {max_y:.1f}]")
    print(f"ViewBox: 0 0 {VIEW_W} {VIEW_H}")

# ── Remove cityNames and cityAdcodes from output (keep cityAdcode) ──
for entry in results:
    if "cityNames" in entry:
        del entry["cityNames"]

# ── Save ──
out_path = "C:/Users/zach/China-Map/provinces_data.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(results)} entries to {out_path}")
print("Done!")

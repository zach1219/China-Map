#!/usr/bin/env python3
"""Build the self-contained index.html with embedded province data."""
import json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SCRIPT_DIR, "provinces_data.json"), encoding="utf-8") as f:
    provinces = json.load(f)

# Build minimal JSON: only id, name, d, center, isDash
minimal = []
for p in provinces:
    minimal.append({
        "id": p["id"],
        "name": p["name"],
        "d": p["d"],
        "center": p["center"],
        "isDash": p.get("isDash", False)
    })
provinces_json = json.dumps(minimal, ensure_ascii=False, separators=(",", ":"))

html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中国地图可视化工具</title>
<style>
:root {
    --bg-primary: #f5f7fa;
    --bg-card: #ffffff;
    --text-primary: #333333;
    --text-secondary: #666666;
    --accent: #4a90d9;
    --accent-hover: #357abd;
    --border: #e0e0e0;
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --header-from: #1a3a5c;
    --header-to: #4a90d9;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, var(--header-from), var(--header-to));
    color: #fff;
    padding: 18px 24px;
    text-align: center;
}
.header h1 { font-size: 22px; font-weight: 600; }
.header p  { font-size: 13px; opacity: 0.85; margin-top: 4px; }
.container {
    max-width: 1400px;
    margin: 16px auto;
    padding: 0 12px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.map-panel {
    flex: 0 0 750px;
    background: var(--bg-card);
    border-radius: 10px;
    box-shadow: var(--shadow);
    padding: 12px;
    position: relative;
}
.map-panel svg { width: 100%; height: auto; display: block; }
.province {
    fill: #f0f0f0;
    stroke: #ffffff;
    stroke-width: 0.8;
    stroke-linejoin: round;
    cursor: pointer;
    transition: fill 0.35s ease, stroke-width 0.2s ease;
}
.province:hover { stroke-width: 1.6; stroke: #333; }
.jdx-line {
    stroke: #999;
    stroke-width: 1;
    stroke-dasharray: 4 3;
    fill: none;
    pointer-events: none;
}
.outer-border {
    stroke: #333;
    stroke-width: 2;
    fill: none;
    pointer-events: none;
}
.province-label {
    font-size: 9px;
    fill: #333;
    text-anchor: middle;
    dominant-baseline: central;
    pointer-events: none;
    font-weight: 500;
}
.province-label.small { font-size: 8px; }
#tooltip {
    position: fixed;
    background: rgba(0,0,0,0.78);
    color: #fff;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s;
    z-index: 1000;
    white-space: nowrap;
}
.right-panel {
    flex: 1;
    min-width: 350px;
    display: flex;
    flex-direction: column;
    gap: 14px;
}
.card {
    background: var(--bg-card);
    border-radius: 10px;
    box-shadow: var(--shadow);
    padding: 16px;
}
.card h3 {
    font-size: 15px;
    margin-bottom: 12px;
    color: var(--accent);
    border-bottom: 2px solid var(--accent);
    padding-bottom: 6px;
}
textarea#text-input {
    width: 100%;
    height: 120px;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    resize: vertical;
    font-family: inherit;
}
textarea#text-input:focus { outline: none; border-color: var(--accent); }
.btn {
    display: inline-block;
    padding: 8px 18px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: background 0.2s;
    color: #fff;
    margin: 4px 4px 4px 0;
}
.btn-primary   { background: var(--accent); }
.btn-primary:hover { background: var(--accent-hover); }
.btn-success   { background: #5cb85c; }
.btn-success:hover { background: #4a9a4a; }
.btn-info      { background: #5bc0de; }
.btn-info:hover { background: #46b8da; }
.btn-group { margin-top: 10px; }
.color-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.color-row label { font-size: 13px; min-width: 70px; }
.color-row input[type="color"] {
    width: 36px; height: 28px;
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    padding: 1px;
}
.gradient-bar {
    height: 18px;
    border-radius: 4px;
    margin-top: 6px;
    border: 1px solid var(--border);
}
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 8px;
    margin-bottom: 12px;
}
.stat-item {
    text-align: center;
    padding: 8px 4px;
    background: #f9f9f9;
    border-radius: 6px;
}
.stat-value { font-size: 20px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
th { background: #f0f4f8; padding: 6px 8px; text-align: left; font-weight: 600; }
td { padding: 5px 8px; border-bottom: 1px solid #eee; }
.color-swatch {
    display: inline-block;
    width: 20px; height: 14px;
    border-radius: 3px;
    border: 1px solid #ccc;
    vertical-align: middle;
}
.bar-cell { width: 90px; }
.bar-bg {
    background: #eee;
    border-radius: 3px;
    height: 12px;
    position: relative;
}
.bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
}
.export-group { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.export-group label { font-size: 12px; color: var(--text-secondary); width: 100%; margin-bottom: 2px; }
@media (max-width: 1100px) {
    .container { flex-direction: column; }
    .map-panel { flex: none; width: 100%; }
    .right-panel { min-width: auto; }
}
</style>
</head>
<body>
<div class="header">
    <h1>🇨🇳 中国地图可视化工具</h1>
    <p>输入文本自动匹配省份和城市 · 零依赖离线可用</p>
</div>
<div class="container">
    <div class="map-panel">
        <svg id="china-map" viewBox="80 100 480 400" xmlns="http://www.w3.org/2000/svg">
            <g id="outer-border-group"></g>
            <g id="provinces-group"></g>
            <g id="labels-group"></g>
        </svg>
    </div>
    <div class="right-panel">
        <div class="card">
            <h3>📝 文本输入</h3>
            <textarea id="text-input" placeholder="粘贴文本，自动匹配省份和城市名称……"></textarea>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="processText()">开始分析</button>
                <button class="btn btn-success" onclick="clearAll()">清除</button>
            </div>
        </div>
        <div class="card">
            <h3>🎨 颜色配置</h3>
            <div class="color-row">
                <label>最低频次</label>
                <input type="color" id="min-color" value="#ffffcc">
            </div>
            <div class="color-row">
                <label>最高频次</label>
                <input type="color" id="max-color" value="#800020">
            </div>
            <div class="color-row">
                <label>边界颜色</label>
                <input type="color" id="border-color" value="#ffffff">
            </div>
            <div class="gradient-bar" id="gradient-bar"></div>
        </div>
        <div class="card">
            <h3>📊 统计信息</h3>
            <div class="stats-grid">
                <div class="stat-item"><div class="stat-value" id="stat-total">0</div><div class="stat-label">总匹配数</div></div>
                <div class="stat-item"><div class="stat-value" id="stat-provinces">0</div><div class="stat-label">匹配省份</div></div>
                <div class="stat-item"><div class="stat-value" id="stat-max">0</div><div class="stat-label">最高频次</div></div>
            </div>
            <div id="stats-table-wrap"></div>
        </div>
        <div class="card">
            <h3>💾 导出</h3>
            <div class="export-group">
                <button class="btn btn-info" onclick="exportSVG()">导出 SVG</button>
                <button class="btn btn-info" onclick="exportPNG(2)">PNG 2x</button>
                <button class="btn btn-info" onclick="exportPNG(3)">PNG 3x</button>
                <button class="btn btn-info" onclick="exportPNG(2,true)">PNG 透明</button>
            </div>
        </div>
    </div>
</div>
<div id="tooltip"></div>

<script>
"use strict";
// ── Embedded province data ──
var PROVINCES = ''' + provinces_json + r''';

// ── City → Province mapping (all prefecture-level cities) ──
var CITY_MAP = {
"北京":"BEJ","天津":"TJN","石家庄":"HEB","唐山":"HEB","秦皇岛":"HEB","邯郸":"HEB","邢台":"HEB","保定":"HEB","张家口":"HEB","承德":"HEB","沧州":"HEB","廊坊":"HEB","衡水":"HEB",
"太原":"SHX","大同":"SHX","阳泉":"SHX","长治":"SHX","晋城":"SHX","朔州":"SHX","晋中":"SHX","运城":"SHX","忻州":"SHX","临汾":"SHX","吕梁":"SHX",
"呼和浩特":"NMG","包头":"NMG","乌海":"NMG","赤峰":"NMG","通辽":"NMG","鄂尔多斯":"NMG","呼伦贝尔":"NMG","巴彦淖尔":"NMG","乌兰察布":"NMG","兴安":"NMG","锡林郭勒":"NMG","阿拉善":"NMG",
"沈阳":"LIA","大连":"LIA","鞍山":"LIA","抚顺":"LIA","本溪":"LIA","丹东":"LIA","锦州":"LIA","营口":"LIA","阜新":"LIA","辽阳":"LIA","盘锦":"LIA","铁岭":"LIA","朝阳":"LIA","葫芦岛":"LIA",
"长春":"JIL","吉林":"JIL","四平":"JIL","辽源":"JIL","通化":"JIL","白山":"JIL","松原":"JIL","白城":"JIL","延边":"JIL",
"哈尔滨":"HLJ","齐齐哈尔":"HLJ","鸡西":"HLJ","鹤岗":"HLJ","双鸭山":"HLJ","大庆":"HLJ","伊春":"HLJ","佳木斯":"HLJ","七台河":"HLJ","牡丹江":"HLJ","黑河":"HLJ","绥化":"HLJ","大兴安岭":"HLJ",
"上海":"SHA",
"南京":"JSU","无锡":"JSU","徐州":"JSU","常州":"JSU","苏州":"JSU","南通":"JSU","连云港":"JSU","淮安":"JSU","盐城":"JSU","扬州":"JSU","镇江":"JSU","泰州":"JSU","宿迁":"JSU",
"杭州":"ZHJ","宁波":"ZHJ","温州":"ZHJ","嘉兴":"ZHJ","湖州":"ZHJ","绍兴":"ZHJ","金华":"ZHJ","衢州":"ZHJ","舟山":"ZHJ","台州":"ZHJ","丽水":"ZHJ",
"合肥":"ANH","芜湖":"ANH","蚌埠":"ANH","淮南":"ANH","马鞍山":"ANH","淮北":"ANH","铜陵":"ANH","安庆":"ANH","黄山":"ANH","滁州":"ANH","阜阳":"ANH","宿州":"ANH","六安":"ANH","亳州":"ANH","池州":"ANH","宣城":"ANH",
"福州":"FUJ","厦门":"FUJ","莆田":"FUJ","三明":"FUJ","泉州":"FUJ","漳州":"FUJ","南平":"FUJ","龙岩":"FUJ","宁德":"FUJ",
"南昌":"JXI","景德镇":"JXI","萍乡":"JXI","九江":"JXI","新余":"JXI","鹰潭":"JXI","赣州":"JXI","吉安":"JXI","宜春":"JXI","抚州":"JXI","上饶":"JXI",
"济南":"SHD","青岛":"SHD","淄博":"SHD","枣庄":"SHD","东营":"SHD","烟台":"SHD","潍坊":"SHD","济宁":"SHD","泰安":"SHD","威海":"SHD","日照":"SHD","临沂":"SHD","德州":"SHD","聊城":"SHD","滨州":"SHD","菏泽":"SHD",
"郑州":"HEN","开封":"HEN","洛阳":"HEN","平顶山":"HEN","安阳":"HEN","鹤壁":"HEN","新乡":"HEN","焦作":"HEN","濮阳":"HEN","许昌":"HEN","漯河":"HEN","三门峡":"HEN","南阳":"HEN","商丘":"HEN","信阳":"HEN","周口":"HEN","驻马店":"HEN","济源":"HEN",
"武汉":"HUB","黄石":"HUB","十堰":"HUB","宜昌":"HUB","襄阳":"HUB","鄂州":"HUB","荆门":"HUB","孝感":"HUB","荆州":"HUB","黄冈":"HUB","咸宁":"HUB","随州":"HUB","恩施":"HUB","仙桃":"HUB","潜江":"HUB","天门":"HUB","神农架":"HUB",
"长沙":"HUN","株洲":"HUN","湘潭":"HUN","衡阳":"HUN","邵阳":"HUN","岳阳":"HUN","常德":"HUN","张家界":"HUN","益阳":"HUN","郴州":"HUN","永州":"HUN","怀化":"HUN","娄底":"HUN","湘西":"HUN",
"广州":"GUD","韶关":"GUD","深圳":"GUD","珠海":"GUD","汕头":"GUD","佛山":"GUD","江门":"GUD","湛江":"GUD","茂名":"GUD","肇庆":"GUD","惠州":"GUD","梅州":"GUD","汕尾":"GUD","河源":"GUD","阳江":"GUD","清远":"GUD","东莞":"GUD","中山":"GUD","潮州":"GUD","揭阳":"GUD","云浮":"GUD",
"南宁":"GXI","柳州":"GXI","桂林":"GXI","梧州":"GXI","北海":"GXI","防城港":"GXI","钦州":"GXI","贵港":"GXI","玉林":"GXI","百色":"GXI","贺州":"GXI","河池":"GXI","来宾":"GXI","崇左":"GXI",
"海口":"HAI","三亚":"HAI","三沙":"HAI","儋州":"HAI","五指山":"HAI","琼海":"HAI","文昌":"HAI","万宁":"HAI","东方":"HAI","定安":"HAI","屯昌":"HAI","澄迈":"HAI","临高":"HAI","白沙":"HAI","昌江":"HAI","乐东":"HAI","陵水":"HAI","保亭":"HAI","琼中":"HAI",
"重庆":"CQG",
"成都":"SIC","自贡":"SIC","攀枝花":"SIC","泸州":"SIC","德阳":"SIC","绵阳":"SIC","广元":"SIC","遂宁":"SIC","内江":"SIC","乐山":"SIC","南充":"SIC","眉山":"SIC","宜宾":"SIC","广安":"SIC","达州":"SIC","雅安":"SIC","巴中":"SIC","资阳":"SIC","阿坝":"SIC","甘孜":"SIC","凉山":"SIC",
"贵阳":"GUI","六盘水":"GUI","遵义":"GUI","安顺":"GUI","毕节":"GUI","铜仁":"GUI","黔西南":"GUI","黔东南":"GUI","黔南":"GUI",
"昆明":"YUN","曲靖":"YUN","玉溪":"YUN","保山":"YUN","昭通":"YUN","丽江":"YUN","普洱":"YUN","临沧":"YUN","楚雄":"YUN","红河":"YUN","文山":"YUN","西双版纳":"YUN","大理":"YUN","德宏":"YUN","怒江":"YUN","迪庆":"YUN",
"拉萨":"TIB","日喀则":"TIB","昌都":"TIB","林芝":"TIB","山南":"TIB","那曲":"TIB","阿里":"TIB",
"西安":"SHA2","铜川":"SHA2","宝鸡":"SHA2","咸阳":"SHA2","渭南":"SHA2","延安":"SHA2","汉中":"SHA2","榆林":"SHA2","安康":"SHA2","商洛":"SHA2",
"兰州":"GAN","嘉峪关":"GAN","金昌":"GAN","白银":"GAN","天水":"GAN","武威":"GAN","张掖":"GAN","平凉":"GAN","酒泉":"GAN","庆阳":"GAN","定西":"GAN","陇南":"GAN","临夏":"GAN","甘南":"GAN",
"西宁":"QIH","海东":"QIH","海北":"QIH","黄南":"QIH","海南":"QIH","果洛":"QIH","玉树":"QIH","海西":"QIH",
"银川":"NIX","石嘴山":"NIX","吴忠":"NIX","固原":"NIX","中卫":"NIX",
"乌鲁木齐":"XJG","克拉玛依":"XJG","吐鲁番":"XJG","哈密":"XJG","昌吉":"XJG","博尔塔拉":"XJG","巴音郭楞":"XJG","阿克苏":"XJG","克孜勒苏":"XJG","喀什":"XJG","和田":"XJG","伊犁":"XJG","塔城":"XJG","阿勒泰":"XJG",
"台北":"TAI","高雄":"TAI","台中":"TAI","台南":"TAI","新北":"TAI","桃园":"TAI",
"香港":"HKG","九龙":"HKG","新界":"HKG",
"澳门":"MAC"
};

// ── Helpers ──
var provinceMap = {};
PROVINCES.forEach(function(p){ provinceMap[p.id] = p; });

var countByProvince = {};
var maxCount = 0;

function getContrastColor(hexBg) {
    var c = hexBg.replace('#','');
    var r = parseInt(c.substr(0,2),16), g = parseInt(c.substr(2,2),16), b = parseInt(c.substr(4,2),16);
    var lum = (0.299*r + 0.587*g + 0.114*b) / 255;
    return lum > 0.5 ? '#333333' : '#ffffff';
}

function lerpColor(a, b, t) {
    var ar = parseInt(a.substr(1,2),16), ag = parseInt(a.substr(3,2),16), ab = parseInt(a.substr(5,2),16);
    var br = parseInt(b.substr(1,2),16), bg = parseInt(b.substr(3,2),16), bb = parseInt(b.substr(5,2),16);
    var rr = Math.round(ar + (br-ar)*t), rg = Math.round(ag + (bg-ag)*t), rb = Math.round(ab + (bb-ab)*t);
    return '#' + ((1<<24)+(rr<<16)+(rg<<8)+rb).toString(16).slice(1);
}

function updateGradientBar() {
    var minC = document.getElementById('min-color').value;
    var maxC = document.getElementById('max-color').value;
    document.getElementById('gradient-bar').style.background =
        'linear-gradient(to right, ' + minC + ', ' + maxC + ')';
}

// ── Build SVG ──
function buildMap() {
    var svg = document.getElementById('china-map');
    var provGroup = document.getElementById('provinces-group');
    var labelGroup = document.getElementById('labels-group');
    var outerGroup = document.getElementById('outer-border-group');
    var borderColor = document.getElementById('border-color').value;

    // Outer border group: duplicate all province paths behind for border effect
    var outerPathParts = [];
    PROVINCES.forEach(function(p) {
        if (p.isDash) return; // skip nine-dash line
        outerPathParts.push(p.d);
    });
    var outerPath = document.createElementNS("http://www.w3.org/2000/svg","path");
    outerPath.setAttribute("d", outerPathParts.join(" "));
    outerPath.setAttribute("class", "outer-border");
    outerPath.setAttribute("stroke", borderColor);
    outerGroup.appendChild(outerPath);

    // Province paths
    var SMALL_PROVINCES = {"香港特别行政区":1,"澳门特别行政区":1,"上海市":1,"天津市":1,"北京市":1,"重庆市":1};

    PROVINCES.forEach(function(p) {
        var path = document.createElementNS("http://www.w3.org/2000/svg","path");
        path.setAttribute("d", p.d);
        path.setAttribute("data-id", p.id);
        path.setAttribute("data-name", p.name);
        if (p.isDash) {
            path.setAttribute("class", "jdx-line");
        } else {
            path.setAttribute("class", "province");
            path.setAttribute("fill", "#f0f0f0");
            path.setAttribute("stroke", borderColor);
            path.setAttribute("stroke-width", "0.8");
        }
        provGroup.appendChild(path);

        // Label
        if (p.id !== "JDX") {
            var txt = document.createElementNS("http://www.w3.org/2000/svg","text");
            txt.setAttribute("x", p.center[0]);
            txt.setAttribute("y", p.center[1]);
            txt.setAttribute("class", "province-label" + (SMALL_PROVINCES[p.name] ? " small" : ""));
            txt.setAttribute("data-id", p.id);
            txt.textContent = p.name;
            labelGroup.appendChild(txt);
        }
    });

    // Offset overlapping labels
    var labels = labelGroup.querySelectorAll("text");
    var positions = [];
    labels.forEach(function(lbl) {
        positions.push({ el: lbl, x: parseFloat(lbl.getAttribute("x")), y: parseFloat(lbl.getAttribute("y")) });
    });
    for (var i = 0; i < positions.length; i++) {
        for (var j = i + 1; j < positions.length; j++) {
            var dx = positions[i].x - positions[j].x;
            var dy = positions[i].y - positions[j].y;
            var dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < 20) {
                positions[j].y += 12;
                positions[j].el.setAttribute("y", positions[j].y);
            }
        }
    }

    // Province hover tooltip
    var tooltip = document.getElementById('tooltip');
    svg.addEventListener('mousemove', function(e) {
        var tgt = e.target;
        if (tgt.classList.contains('province')) {
            var id = tgt.getAttribute('data-id');
            var name = tgt.getAttribute('data-name');
            var cnt = countByProvince[id] || 0;
            tooltip.textContent = cnt > 0 ? (name + ' — 出现 ' + cnt + ' 次') : name;
            tooltip.style.left = (e.clientX + 14) + 'px';
            tooltip.style.top  = (e.clientY - 10) + 'px';
            tooltip.style.opacity = 1;
        } else {
            tooltip.style.opacity = 0;
        }
    });
    svg.addEventListener('mouseleave', function() { tooltip.style.opacity = 0; });

    updateGradientBar();
    document.getElementById('min-color').addEventListener('input', function(){ updateGradientBar(); applyColors(); });
    document.getElementById('max-color').addEventListener('input', function(){ updateGradientBar(); applyColors(); });
    document.getElementById('border-color').addEventListener('input', function(){ applyBorderColor(); });
}

function applyBorderColor() {
    var borderColor = document.getElementById('border-color').value;
    document.querySelectorAll('.province').forEach(function(p){ p.setAttribute('stroke', borderColor); });
    document.querySelectorAll('.outer-border').forEach(function(p){ p.setAttribute('stroke', borderColor); });
}

// ── Color provinces by count ──
function applyColors() {
    var minC = document.getElementById('min-color').value;
    var maxC = document.getElementById('max-color').value;
    var provGroup = document.getElementById('provinces-group');

    provGroup.querySelectorAll('.province').forEach(function(path) {
        var id = path.getAttribute('data-id');
        var cnt = countByProvince[id] || 0;
        if (cnt === 0) {
            path.setAttribute('fill', '#f0f0f0');
        } else {
            var t = maxCount > 1 ? (cnt - 1) / (maxCount - 1) : 1;
            path.setAttribute('fill', lerpColor(minC, maxC, t));
        }
    });
    // Update label colors
    document.querySelectorAll('.province-label').forEach(function(lbl) {
        var id = lbl.getAttribute('data-id');
        var cnt = countByProvince[id] || 0;
        if (cnt > 0) {
            var t = maxCount > 1 ? (cnt - 1) / (maxCount - 1) : 1;
            var bg = lerpColor(minC, maxC, t);
            lbl.setAttribute('fill', getContrastColor(bg));
        } else {
            lbl.setAttribute('fill', '#333333');
        }
    });
}

// ── Process text ──
function processText() {
    var text = document.getElementById('text-input').value;
    if (!text.trim()) return;

    countByProvince = {};
    maxCount = 0;

    // Sort keys by length descending to match longer names first
    var provinceNames = [];
    var cityNames = [];
    PROVINCES.forEach(function(p) { if (p.id !== 'JDX') provinceNames.push(p.name); });
    Object.keys(CITY_MAP).forEach(function(c) { cityNames.push(c); });

    var allNames = provinceNames.concat(cityNames);
    allNames.sort(function(a,b){ return b.length - a.length; });

    // Create a text copy for removal tracking
    var remaining = text;
    // Use regex-based matching to avoid double-counting
    var matchedEntries = [];

    allNames.forEach(function(name) {
        var escaped = name.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        var re = new RegExp(escaped, 'g');
        var match;
        while ((match = re.exec(text)) !== null) {
            matchedEntries.push({ name: name, index: match.index });
        }
    });

    // Sort by index to handle overlaps (keep earliest/longest)
    matchedEntries.sort(function(a,b){ return a.index - b.index || b.name.length - a.name.length; });

    // Remove overlapping matches
    var used = [];
    var finalMatches = [];
    matchedEntries.forEach(function(entry) {
        var start = entry.index;
        var end = start + entry.name.length;
        var overlap = false;
        for (var i = 0; i < used.length; i++) {
            if (start < used[i].end && end > used[i].start) { overlap = true; break; }
        }
        if (!overlap) {
            used.push({ start: start, end: end });
            finalMatches.push(entry.name);
        }
    });

    // Aggregate counts
    finalMatches.forEach(function(name) {
        var provId = null;
        // Check if it's a province name
        for (var i = 0; i < PROVINCES.length; i++) {
            if (PROVINCES[i].name === name && PROVINCES[i].id !== 'JDX') {
                provId = PROVINCES[i].id;
                break;
            }
        }
        // Check if it's a city name
        if (!provId && CITY_MAP[name]) {
            provId = CITY_MAP[name];
        }
        if (provId) {
            countByProvince[provId] = (countByProvince[provId] || 0) + 1;
            if (countByProvince[provId] > maxCount) maxCount = countByProvince[provId];
        }
    });

    applyColors();
    updateStats();
}

// ── Statistics ──
function updateStats() {
    var entries = [];
    var totalCount = 0;
    Object.keys(countByProvince).forEach(function(id) {
        var cnt = countByProvince[id];
        totalCount += cnt;
        var p = provinceMap[id];
        if (p) entries.push({ id: id, name: p.name, count: cnt });
    });
    entries.sort(function(a,b){ return b.count - a.count; });

    document.getElementById('stat-total').textContent = totalCount;
    document.getElementById('stat-provinces').textContent = entries.length;
    document.getElementById('stat-max').textContent = maxCount;

    var wrap = document.getElementById('stats-table-wrap');
    if (entries.length === 0) { wrap.innerHTML = '<p style="color:#999;font-size:13px;">暂无匹配数据</p>'; return; }

    var minC = document.getElementById('min-color').value;
    var maxC = document.getElementById('max-color').value;

    var html = '<table><thead><tr><th>颜色</th><th>省份</th><th>频次</th><th class="bar-cell">占比</th></tr></thead><tbody>';
    entries.forEach(function(e) {
        var t = maxCount > 1 ? (e.count - 1) / (maxCount - 1) : 1;
        var color = lerpColor(minC, maxC, t);
        var pct = maxCount > 0 ? (e.count / maxCount * 100) : 0;
        html += '<tr>';
        html += '<td><span class="color-swatch" style="background:' + color + '"></span></td>';
        html += '<td>' + e.name + '</td>';
        html += '<td>' + e.count + '</td>';
        html += '<td class="bar-cell"><div class="bar-bg"><div class="bar-fill" style="width:' + pct + '%;background:' + color + '"></div></div></td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    wrap.innerHTML = html;
}

// ── Clear ──
function clearAll() {
    document.getElementById('text-input').value = '';
    countByProvince = {};
    maxCount = 0;
    applyColors();
    updateStats();
}

// ── Export SVG ──
function exportSVG() {
    var svg = document.getElementById('china-map');
    var clone = svg.cloneNode(true);
    var vb = svg.getAttribute('viewBox');
    clone.setAttribute('viewBox', vb);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    // Inline styles on all elements
    clone.querySelectorAll('.province').forEach(function(el) {
        el.style.fill = el.getAttribute('fill') || '#f0f0f0';
        el.style.stroke = el.getAttribute('stroke') || '#ffffff';
        el.style.strokeWidth = el.getAttribute('stroke-width') || '0.8';
        el.style.strokeLinejoin = 'round';
    });
    clone.querySelectorAll('.outer-border').forEach(function(el) {
        el.style.stroke = el.getAttribute('stroke') || '#333';
        el.style.strokeWidth = '2';
        el.style.fill = 'none';
    });
    clone.querySelectorAll('.province-label, .province-label.small').forEach(function(el) {
        el.style.fontFamily = 'sans-serif';
        el.style.fontSize = el.classList.contains('small') ? '8px' : '9px';
        el.style.textAnchor = 'middle';
        el.style.dominantBaseline = 'central';
        el.style.fontWeight = '500';
        el.style.fill = el.getAttribute('fill') || '#333';
    });
    clone.querySelectorAll('.jdx-line').forEach(function(el) {
        el.style.stroke = '#999';
        el.style.strokeWidth = '1';
        el.style.strokeDasharray = '4 3';
        el.style.fill = 'none';
    });

    var svgData = new XMLSerializer().serializeToString(clone);
    var blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    downloadBlob(blob, 'china-map.svg');
}

// ── Export PNG ──
function exportPNG(scale, transparent) {
    var svg = document.getElementById('china-map');
    var vb = svg.getAttribute('viewBox').split(' ').map(Number);
    var w = vb[2] * scale;
    var h = vb[3] * scale;

    var canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    var ctx = canvas.getContext('2d');

    var clone = svg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    clone.setAttribute('width', w);
    clone.setAttribute('height', h);
    // Inline styles
    clone.querySelectorAll('.province').forEach(function(el) {
        el.style.fill = el.getAttribute('fill') || '#f0f0f0';
        el.style.stroke = el.getAttribute('stroke') || '#ffffff';
        el.style.strokeWidth = (el.getAttribute('stroke-width') || '0.8') * scale;
        el.style.strokeLinejoin = 'round';
    });
    clone.querySelectorAll('.outer-border').forEach(function(el) {
        el.style.stroke = el.getAttribute('stroke') || '#333';
        el.style.strokeWidth = 2 * scale;
        el.style.fill = 'none';
    });
    clone.querySelectorAll('.province-label, .province-label.small').forEach(function(el) {
        el.style.fontFamily = 'sans-serif';
        el.style.fontSize = (el.classList.contains('small') ? 8 : 9) * scale + 'px';
        el.style.textAnchor = 'middle';
        el.style.dominantBaseline = 'central';
        el.style.fontWeight = '500';
        el.style.fill = el.getAttribute('fill') || '#333';
    });
    clone.querySelectorAll('.jdx-line').forEach(function(el) {
        el.style.stroke = '#999';
        el.style.strokeWidth = 1 * scale;
        el.style.strokeDasharray = (4*scale) + ' ' + (3*scale);
        el.style.fill = 'none';
    });

    if (!transparent) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, w, h);
    }

    var svgData = new XMLSerializer().serializeToString(clone);
    var img = new Image();
    img.onload = function() {
        ctx.drawImage(img, 0, 0, w, h);
        canvas.toBlob(function(blob) {
            downloadBlob(blob, 'china-map-' + scale + 'x' + (transparent ? '-transparent' : '') + '.png');
        }, 'image/png');
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
}

function downloadBlob(blob, filename) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
}

// ── Init ──
buildMap();
updateGradientBar();
</script>
</body>
</html>
'''

out_path = os.path.join(SCRIPT_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
sz = os.path.getsize(out_path)
print(f"Written {out_path} ({sz:,} bytes, {sz/1024:.0f} KB)")

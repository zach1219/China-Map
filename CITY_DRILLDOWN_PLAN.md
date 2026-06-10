# 城市/区县下钻功能设计方案

## 一、现有代码架构分析

### 1.1 文件结构
- **单文件 HTML** (604 行, ~48KB)
- 结构: `<style>` → `<body HTML>` → `<script>`
- 无外部依赖，无框架，纯原生 JS + SVG

### 1.2 核心数据结构

| 组件 | 位置 | 作用 |
|------|------|------|
| `PROVINCES` 数组 | 行 315 | 34 个省份对象 `{id, d (SVG path), n (名称)}` |
| `centerOverrides` | 行 321-334 | 12 个小省份的标签坐标手动偏移 |
| `nameToId` / `allNames` | 行 317-319 | 名称→ID 映射，用于文本匹配 |
| `currentCounts` | 行 450 | 全局变量，当前匹配计数 |

### 1.3 核心函数流程

```
DOMContentLoaded
  → initMap()        生成 SVG（path + text label），绑定鼠标事件
  → updateLegend()   初始化渐变条
  → input 监听       → processText()
                         → 遍历省份名称匹配文本
                         → updateMap(counts)     按比例着色
                         → updateStats(counts)   更新统计表格
```

### 1.4 着色机制
- `lerpColor(minColor, maxColor, t)` — HSL 空间插值
- count=0 → `#f0f0f0`; count=1 → minColor; 其余按比例插值
- 图例条: `linear-gradient(to right, minColor, maxColor)`

### 1.5 导出机制
- `getExportSVG()` → cloneNode 克隆 SVG
- `exportSVG()` → Blob 下载
- `exportPNG(scale, transparent)` → Canvas 绘制后下载

---

## 二、城市下钻设计方案

### 2.1 新增状态管理

```javascript
var drillState = {
    level: 'china',          // 'china' | 'province'
    currentProvince: null,    // 当前省份对象 {id, name, adcode}
    cityGeoJSON: null,        // 缓存的城市 GeoJSON
    cityCounts: {}            // 城市级计数 {cityName: count}
};
```

每个省份需要新增一个 `adcode` 字段（如北京=110000, 广东=440000），用于调用 DataV API。

### 2.2 PROVINCES 数组扩展

在现有 PROVINCES 每个对象上新增 `adcode` 属性：

```javascript
{"id":"BEJ","d":"...","n":"北京","adcode":"110000"},
{"id":"GUD","d":"...","n":"广东","adcode":"440000"},
// ... 全部 34 个
```

完整 adcode 映射表见附录 A。

### 2.3 API 调用策略

```
URL: https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json
```

- 点击省份 → fetch 该省 adcode 的 `_full.json`
- 响应为 GeoJSON FeatureCollection，`features[].properties.name` 为城市名
- 缓存策略: 内存对象 `cityCache[adcode] = geojson`，避免重复请求
- 错误处理: 加载失败时 toast 提示，保持省份视图

### 2.4 地图渲染架构

**核心变更：SVG 不再写死省份 path，改为动态生成**

```javascript
function renderMap(geojson, level) {
    // 1. 计算 GeoJSON 的 bbox → 投影到 0-560 × 0-470 viewBox
    // 2. 使用简单等距圆柱投影或 d3-like 简化投影
    //    将经纬度 → SVG 坐标
    // 3. 生成 SVG path 的 d 属性
    // 4. 生成 label text 元素
}
```

**投影方案（轻量，无需 d3）：**

```javascript
function geoToSVG(coords, bbox) {
    var lng = coords[0], lat = coords[1];
    var x = ((lng - bbox.minLng) / (bbox.maxLng - bbox.minLng)) * mapWidth;
    var y = ((bbox.maxLat - lat) / (bbox.maxLat - bbox.minLat)) * mapHeight;
    return [x, y];
}
```

对于省份视图，bbox 从 GeoJSON 的 features 自动计算并加 padding。

**GeoJSON → SVG path 转换：**

```javascript
function geojsonToPath(geometry) {
    // 处理 Polygon 和 MultiPolygon
    // 将每个 ring 的坐标投影后拼成 SVG path d 字符串
}
```

### 2.5 导航交互

#### 面包屑导航
在地图面板标题区域新增面包屑：

```html
<div class="breadcrumb">
    <span class="crumb" onclick="navigateTo('china')">中国</span>
    <span class="crumb-sep">›</span>
    <span class="crumb active">广东省</span>
</div>
```

CSS:
```css
.breadcrumb { font-size: 13px; margin-bottom: 8px; }
.breadcrumb .crumb { color: var(--primary); cursor: pointer; }
.breadcrumb .crumb.active { color: var(--text); cursor: default; font-weight: 600; }
.breadcrumb .crumb-sep { color: #aaa; margin: 0 4px; }
```

#### 点击省份进入
```javascript
el.addEventListener("click", function() {
    var id = this.id.replace("prov-", "");
    var prov = PROVINCES.find(p => p.id === id);
    drillIntoProvince(prov);
});
```

#### 点击城市（可选功能）
城市下钻到区县，使用同一 API 格式 `{adcode}_full.json`。
但首次迭代可只做省份→城市一级。

### 2.6 核心函数改造

#### `navigateTo(level)` — 统一导航入口

```javascript
function navigateTo(level, province) {
    if (level === 'china') {
        drillState.level = 'china';
        drillState.currentProvince = null;
        initMap();              // 恢复全国地图
        processText();          // 重新着色
    } else if (level === 'province') {
        drillIntoProvince(province);
    }
    updateBreadcrumb();
}
```

#### `drillIntoProvince(prov)` — 进入省份

```javascript
async function drillIntoProvince(prov) {
    drillState.level = 'province';
    drillState.currentProvince = prov;
    
    showLoading();  // 显示加载指示器
    
    if (!cityCache[prov.adcode]) {
        var resp = await fetch(
            'https://geo.datav.aliyun.com/areas_v3/bound/' + prov.adcode + '_full.json'
        );
        cityCache[prov.adcode] = await resp.json();
    }
    
    drillState.cityGeoJSON = cityCache[prov.adcode];
    renderCityMap(drillState.cityGeoJSON);
    processText();  // 城市级着色
    updateBreadcrumb();
    hideLoading();
}
```

#### `renderCityMap(geojson)` — 渲染城市地图

```javascript
function renderCityMap(geojson) {
    var container = document.getElementById("cn-map");
    var bbox = calcBBox(geojson);
    var pad = 20;
    var vb = { x: -pad, y: -pad, w: 560 + pad*2, h: 470 + pad*2 };
    
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + vb.x + ' ' + vb.y + ' ' + vb.w + ' ' + vb.h + '">';
    
    geojson.features.forEach(function(feat, i) {
        var cityName = feat.properties.name;
        var d = geojsonToPath(feat.geometry, bbox);
        svg += '<path class="city" id="city-' + i + '" data-name="' + cityName + '" d="' + d + '"/>';
    });
    
    // Labels
    geojson.features.forEach(function(feat, i) {
        var center = calcCentroid(feat.geometry);
        var [cx, cy] = geoToSVG(center, bbox);
        svg += '<text class="city-label" x="' + cx + '" y="' + cy + '">' + feat.properties.name + '</text>';
    });
    
    svg += '</svg>';
    container.innerHTML = svg;
    
    bindCityEvents();
}
```

#### `processText()` 改造

```javascript
function processText() {
    var text = document.getElementById("input-text").value;
    
    if (drillState.level === 'china') {
        // 原有逻辑：匹配省份名
        var counts = {};
        var sortedNames = allNames.slice().sort((a, b) => b.length - a.length);
        sortedNames.forEach(name => {
            var matches = text.match(new RegExp(name, "g"));
            if (matches) counts[nameToId[name]] = matches.length;
        });
        currentCounts = counts;
        updateMap(counts);
        updateStats(counts, Object.values(counts).reduce((a,b) => a+b, 0));
    } else if (drillState.level === 'province') {
        // 新逻辑：匹配城市名
        var cityCounts = {};
        var total = 0;
        drillState.cityGeoJSON.features.forEach(feat => {
            var name = feat.properties.name;
            // 去掉"市"后缀再匹配（如"广州市"匹配文本中的"广州"）
            var shortName = name.replace(/市$|地区$|州$|盟$/, '');
            var regex = new RegExp(shortName, "g");
            var matches = text.match(regex);
            if (matches) {
                cityCounts[name] = matches.length;
                total += matches.length;
            }
        });
        drillState.cityCounts = cityCounts;
        updateCityMap(cityCounts);
        updateCityStats(cityCounts, total);
    }
}
```

### 2.7 标签颜色自适应（对比度）

**问题：** 深色背景上黑色文字不可读。

**方案：基于相对亮度计算文字颜色**

```javascript
function getContrastColor(hexBg) {
    hexBg = hexBg.replace('#', '');
    var r = parseInt(hexBg.substr(0, 2), 16);
    var g = parseInt(hexBg.substr(2, 2), 16);
    var b = parseInt(hexBg.substr(4, 2), 16);
    // W3C 相对亮度公式
    var luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#333333' : '#ffffff';
}
```

在 `updateMap` / `updateCityMap` 中着色后立即更新对应 label：

```javascript
var label = document.querySelector('text[data-id="' + p.id + '"]');
if (label) {
    label.style.fill = getContrastColor(el.style.fill);
}
```

### 2.8 统计面板改造

- 省份视图: 表头 "省份 | 频次"（现有逻辑）
- 城市视图: 表头 "城市 | 频次"
- 统计摘要文案: "匹配省份" → "匹配城市"
- 添加"返回全国"按钮到统计卡片顶部

### 2.9 导出函数适配

现有 `getExportSVG()` 已通过 `cloneNode` 工作，无需大改。
城市视图的 SVG viewBox 可能不同，需从当前 SVG 元素动态读取：

```javascript
function getExportSVG() {
    var svgEl = document.querySelector("#cn-map svg");
    if (!svgEl) return null;
    var clone = svgEl.cloneNode(true);
    // viewBox 已在 clone 中，直接使用
    return clone;
}
```

PNG 导出的 canvas 尺寸也需从 viewBox 动态计算：

```javascript
var vb = svgEl.getAttribute('viewBox').split(' ').map(Number);
var w = vb[2] * scale, h = vb[3] * scale;
```

---

## 三、CSS 新增/修改

```css
/* 城市 path 样式 — 与省份统一 */
.city {
    fill: #f0f0f0;
    stroke: #ffffff;
    stroke-width: 0.5;       /* 城市边界更细 */
    cursor: pointer;
    transition: fill 0.4s ease, opacity 0.3s;
}
.city:hover {
    opacity: 0.85;
    stroke: #333;
    stroke-width: 1;
}
.city-label {
    font-size: 8px;          /* 城市标签更小 */
    fill: #333;
    text-anchor: middle;
    dominant-baseline: central;
    pointer-events: none;
    font-weight: 400;
}

/* 面包屑 */
.breadcrumb { ... }

/* 加载指示器 */
.loading-overlay { ... }
```

---

## 四、实施步骤

### Phase 1: 基础架构（~120 行新增）
1. 在 PROVINCES 每个对象中添加 `adcode` 字段
2. 新增 `drillState`、`cityCache` 全局变量
3. 新增 `geoToSVG`、`geojsonToPath`、`calcBBox`、`calcCentroid` 投影函数
4. 新增 `getContrastColor` 对比度函数

### Phase 2: 城市渲染（~80 行新增）
5. 新增 `renderCityMap(geojson)` 函数
6. 新增 `drillIntoProvince(prov)` 异步函数
7. 新增 `navigateTo(level, prov)` 统一导航
8. 给省份 path 添加 click 事件 → `drillIntoProvince`

### Phase 3: 数据流适配（~40 行修改）
9. 改造 `processText()` — 根据 level 分支
10. 新增 `updateCityMap(counts)` — 城市级着色 + 标签对比度
11. 新增 `updateCityStats(counts, total)` — 城市级统计表
12. 改造 `updateMap()` — 加入标签对比度

### Phase 4: UI 完善（~40 行新增）
13. 新增面包屑 HTML + CSS + `updateBreadcrumb()`
14. 地图面板标题改为动态（面包屑替代固定标题）
15. 统计卡片增加"返回全国"按钮
16. 加载状态指示器

### Phase 5: 导出适配（~10 行修改）
17. `getExportSVG()` 适配动态 viewBox
18. `exportPNG()` 适配动态 canvas 尺寸

---

## 五、附录 A：省份 Adcode 映射表

| 省份 | ID | Adcode |
|------|-----|--------|
| 北京 | BEJ | 110000 |
| 天津 | TAJ | 120000 |
| 河北 | HEB | 130000 |
| 山西 | SHX | 140000 |
| 内蒙古 | NMG | 150000 |
| 辽宁 | LIA | 210000 |
| 吉林 | JIL | 220000 |
| 黑龙江 | HLJ | 230000 |
| 上海 | SHH | 310000 |
| 江苏 | JIA | 320000 |
| 浙江 | ZHJ | 330000 |
| 安徽 | ANH | 340000 |
| 福建 | FUJ | 350000 |
| 江西 | JXI | 360000 |
| 山东 | SHD | 370000 |
| 河南 | HEN | 410000 |
| 湖北 | HUB | 420000 |
| 湖南 | HUN | 430000 |
| 广东 | GUD | 440000 |
| 广西 | GXI | 450000 |
| 海南 | HAI | 460000 |
| 重庆 | CHQ | 500000 |
| 四川 | SCI | 510000 |
| 贵州 | GUI | 520000 |
| 云南 | YUN | 530000 |
| 西藏 | TIB | 540000 |
| 陕西 | SHA | 610000 |
| 甘肃 | GAN | 620000 |
| 青海 | QIH | 630000 |
| 宁夏 | NXA | 640000 |
| 新疆 | XIN | 650000 |
| 台湾 | TAI | 710000 |
| 香港 | HKG | 810000 |
| 澳门 | MAC | 820000 |

---

## 六、关键风险与对策

| 风险 | 对策 |
|------|------|
| GeoJSON 大省份文件较大（新疆~2MB） | 内存缓存 + 加载指示器 |
| 城市名与文本匹配率低 | 支持去后缀匹配（"广州" 匹配 "广州市"） |
| 小城市标签重叠 | 城市视图 font-size 降至 8px，可选隐藏小区域标签 |
| 投影精度不如 d3 | 对省级以下区域，简单线性投影视觉效果可接受 |
| API 跨域 | DataV API 支持 CORS，无问题 |
| 导出 viewBox 不同 | 动态从 SVG 元素读取，不硬编码 |

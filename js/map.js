// === map.js - 地图渲染核心 ===

var countByProvince = {};
var maxCount = 0;
var provinceMap = {};
PROVINCES.forEach(function(p){ provinceMap[p.id] = p; });

function getShortName(name) {
    return name.replace(/壮族自治区|回族自治区|维吾尔自治区|特别行政区|自治区|省|市$/g, '');
}

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
            // Stroke matches page background so shared borders don't double up
            // (border-color picker only controls outer China border)
        }
        provGroup.appendChild(path);

        // Label
        if (p.id !== "JDX") {
            var txt = document.createElementNS("http://www.w3.org/2000/svg","text");
            var lx = p.center[0], ly = p.center[1];
            if (p.labelOffset) { lx += p.labelOffset[0]; ly += p.labelOffset[1]; }
            txt.setAttribute("x", lx);
            txt.setAttribute("y", ly);
            txt.setAttribute("class", "province-label" + (SMALL_PROVINCES[p.name] ? " small" : ""));
            txt.setAttribute("data-id", p.id);
            txt.setAttribute("data-base-name", getShortName(p.name));
            txt.textContent = getShortName(p.name);
            txt.setAttribute('visibility', 'hidden'); // hidden by default, shown when has data
            labelGroup.appendChild(txt);
        }
    });

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
    document.getElementById('stroke-width-slider').addEventListener('input', function(){ applyBorderColor(); document.getElementById('stroke-width-val').textContent = this.value; });
    document.getElementById('hide-labels').addEventListener('change', function(){ applyColors(); });
    document.getElementById('show-count').addEventListener('change', function(){ applyColors(); });
    document.getElementById('label-size').addEventListener('input', function(){
        var sz = this.value;
        document.getElementById('label-size-val').textContent = sz + 'px';
        document.querySelectorAll('.province-label').forEach(function(l){ l.style.fontSize = sz + 'px'; });
        document.querySelectorAll('.province-label.small').forEach(function(l){ l.style.fontSize = Math.max(6, sz - 2) + 'px'; });
    });
}

function applyColors() {
    var minC = document.getElementById('min-color').value;
    var maxC = document.getElementById('max-color').value;
    var provGroup = document.getElementById('provinces-group');

    provGroup.querySelectorAll('.province').forEach(function(path) {
        var id = path.getAttribute('data-id');
        var cnt = countByProvince[id] || 0;
        if (cnt === 0) {
            path.style.fill = '#f0f0f0';
        } else {
            var t = maxCount > 1 ? (cnt - 1) / (maxCount - 1) : 1;
            path.style.fill = lerpColor(minC, maxC, t);
        }
    });
    // Update label colors + hide option
    var hideUnchecked = document.getElementById('hide-labels').checked;
    var showCount = document.getElementById('show-count').checked;
    document.querySelectorAll('.province-label').forEach(function(lbl) {
        var id = lbl.getAttribute('data-id');
        var cnt = countByProvince[id] || 0;
        if (hideUnchecked && cnt === 0) {
            lbl.setAttribute('visibility', 'hidden');
        } else {
            lbl.setAttribute('visibility', 'visible');
            if (cnt > 0) {
                var t = maxCount > 1 ? (cnt - 1) / (maxCount - 1) : 1;
                var bg = lerpColor(minC, maxC, t);
                lbl.style.fill = getContrastColor(bg);
            } else {
                lbl.style.fill = '#333333';
            }
            // 更新标签文字：省份名称 + 可选频次
            var baseName = lbl.getAttribute('data-base-name') || lbl.textContent;
            lbl.textContent = (showCount && cnt > 0) ? (baseName + ' ' + cnt) : baseName;
        }
    });
}

function applyBorderColor() {
    var borderColor = document.getElementById('border-color').value;
    var strokeWidth = document.getElementById('stroke-width-slider').value;
    document.querySelectorAll('.province').forEach(function(p){
        p.style.stroke = borderColor;
        p.style.strokeWidth = strokeWidth;
    });
    document.querySelectorAll('.outer-border').forEach(function(p){
        p.style.stroke = borderColor;
        p.style.strokeWidth = strokeWidth;
    });
}

function processText() {
    var text = document.getElementById('text-input').value;
    if (!text.trim()) return;

    countByProvince = {};
    maxCount = 0;

    var provinceNames = [];
    PROVINCES.forEach(function(p) { if (p.id !== 'JDX') { provinceNames.push(p.name); var sn = getShortName(p.name); if (sn !== p.name) provinceNames.push(sn); }});

    // Sort by length descending to match longer names first
    provinceNames.sort(function(a,b){ return b.length - a.length; });

    var matchedEntries = [];

    provinceNames.forEach(function(name) {
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
        // Check if it's a province name (full or short)
        for (var i = 0; i < PROVINCES.length; i++) {
            if (PROVINCES[i].id !== 'JDX' && (PROVINCES[i].name === name || getShortName(PROVINCES[i].name) === name)) {
                provId = PROVINCES[i].id;
                break;
            }
        }
        if (provId) {
            countByProvince[provId] = (countByProvince[provId] || 0) + 1;
            if (countByProvince[provId] > maxCount) maxCount = countByProvince[provId];
        }
    });

    applyColors();
    updateStats();
    trackUsage();
}

function clearAll() {
    document.getElementById('text-input').value = '';
    countByProvince = {};
    maxCount = 0;
    applyColors();
    updateStats();
}

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

function updateGradientBar() {
    var minC = document.getElementById('min-color').value;
    var maxC = document.getElementById('max-color').value;
    document.getElementById('gradient-bar').style.background =
        'linear-gradient(to right, ' + minC + ', ' + maxC + ')';
}

function trackUsage() {
    try {
        var data = JSON.parse(localStorage.getItem('cnmap_stats') || '{"uses":0,"provTotal":{}}');
        data.uses++;
        Object.keys(countByProvince).forEach(function(id) {
            var name = provinceMap[id] ? getShortName(provinceMap[id].name) : id;
            data.provTotal[name] = (data.provTotal[name] || 0) + countByProvince[id];
        });
        localStorage.setItem('cnmap_stats', JSON.stringify(data));
        renderFooter(data);
    } catch(e) {}
}

function loadUsage() {
    try {
        var data = JSON.parse(localStorage.getItem('cnmap_stats') || '{"uses":0,"provTotal":{}}');
        renderFooter(data);
    } catch(e) {}
}

function renderFooter(data) {
    document.getElementById('ft-uses').textContent = data.uses;
    var topName = '-', topVal = 0;
    Object.keys(data.provTotal).forEach(function(n) {
        if (data.provTotal[n] > topVal) { topVal = data.provTotal[n]; topName = n; }
    });
    document.getElementById('ft-top').textContent = topVal > 0 ? (topName + '（' + topVal + ' 次）') : '-';
}



// === Init ===
buildMap();
updateGradientBar();
loadUsage();

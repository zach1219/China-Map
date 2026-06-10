// === export.js - 导出功能 ===
// 导出时从原始DOM的 computedStyle 读取实际渲染值，确保与网页一致

function downloadBlob(blob, filename) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
}

// 从原始DOM读取计算样式，应用到克隆元素
function inlineStyles(origSvg, clone) {
    var origProvinces = origSvg.querySelectorAll('.province');
    var cloneProvinces = clone.querySelectorAll('.province');
    for (var i = 0; i < origProvinces.length; i++) {
        var cs = getComputedStyle(origProvinces[i]);
        var el = cloneProvinces[i];
        el.style.fill = origProvinces[i].style.fill || cs.fill || '#f0f0f0';
        el.style.stroke = origProvinces[i].style.stroke || cs.stroke || '#999999';
        el.style.strokeWidth = origProvinces[i].style.strokeWidth || cs.strokeWidth || '0.5';
        el.style.strokeLinejoin = 'round';
        el.style.paintOrder = 'stroke fill';
    }

    var origOuter = origSvg.querySelectorAll('.outer-border');
    var cloneOuter = clone.querySelectorAll('.outer-border');
    for (var i = 0; i < origOuter.length; i++) {
        var cs = getComputedStyle(origOuter[i]);
        var el = cloneOuter[i];
        el.style.fill = 'none';
        el.style.stroke = origOuter[i].style.stroke || cs.stroke || '#999999';
        el.style.strokeWidth = origOuter[i].style.strokeWidth || cs.strokeWidth || '0.5';
        el.style.pointerEvents = 'none';
    }

    var origLabels = origSvg.querySelectorAll('.province-label, .province-label.small');
    var cloneLabels = clone.querySelectorAll('.province-label, .province-label.small');
    for (var i = 0; i < origLabels.length; i++) {
        var cs = getComputedStyle(origLabels[i]);
        var el = cloneLabels[i];
        var orig = origLabels[i];
        el.style.fontFamily = cs.fontFamily || 'sans-serif';
        // 从原始DOM读取实际字号（由slider控制），而非硬编码
        el.style.fontSize = orig.style.fontSize || cs.fontSize || '6px';
        el.style.fontWeight = orig.style.fontWeight || cs.fontWeight || '500';
        el.style.textAnchor = 'middle';
        el.style.dominantBaseline = 'central';
        // 读取实际文字颜色（深色板块反白由 getContrastColor 设置）
        el.style.fill = orig.style.fill || cs.fill || '#333';
    }

    var origJdx = origSvg.querySelectorAll('.jdx-line');
    var cloneJdx = clone.querySelectorAll('.jdx-line');
    for (var i = 0; i < origJdx.length; i++) {
        var el = cloneJdx[i];
        el.style.stroke = '#999';
        el.style.strokeWidth = '1';
        el.style.strokeDasharray = '4 3';
        el.style.fill = 'none';
    }
}

function exportSVG() {
    var svg = document.getElementById('china-map');
    var clone = svg.cloneNode(true);
    var vb = svg.getAttribute('viewBox');
    clone.setAttribute('viewBox', vb);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    inlineStyles(svg, clone);

    var svgData = new XMLSerializer().serializeToString(clone);
    var blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    downloadBlob(blob, 'china-map.svg');
}

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

    inlineStyles(svg, clone);

    // PNG导出需要缩放stroke和字号
    clone.querySelectorAll('.province').forEach(function(el) {
        el.style.strokeWidth = (parseFloat(el.style.strokeWidth) || 0.5) * scale;
    });
    clone.querySelectorAll('.outer-border').forEach(function(el) {
        el.style.strokeWidth = (parseFloat(el.style.strokeWidth) || 0.5) * scale;
    });
    clone.querySelectorAll('.province-label').forEach(function(el) {
        el.style.fontSize = (parseFloat(el.style.fontSize) || 6) * scale + 'px';
    });
    clone.querySelectorAll('.province-label.small').forEach(function(el) {
        el.style.fontSize = Math.max(4, (parseFloat(el.style.fontSize) || 4)) * scale + 'px';
    });
    clone.querySelectorAll('.jdx-line').forEach(function(el) {
        el.style.strokeWidth = 1 * scale;
        el.style.strokeDasharray = (4 * scale) + ' ' + (3 * scale);
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

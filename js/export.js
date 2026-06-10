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
        el.style.fontSize = orig.style.fontSize || cs.fontSize || '6px';
        el.style.fontWeight = orig.style.fontWeight || cs.fontWeight || '500';
        el.style.textAnchor = 'middle';
        el.style.dominantBaseline = 'central';
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

function exportPNG() {
    var svg = document.getElementById('china-map');
    var vb = svg.getAttribute('viewBox').split(' ').map(Number);
    var scale = 3;
    var w = vb[2] * scale;
    var h = vb[3] * scale;

    var clone = svg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    clone.setAttribute('width', w);
    clone.setAttribute('height', h);

    inlineStyles(svg, clone);

    var svgData = new XMLSerializer().serializeToString(clone);
    var svgBase64 = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));

    var canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    var ctx = canvas.getContext('2d');

    var img = new Image();
    img.onload = function() {
        ctx.drawImage(img, 0, 0, w, h);
        try {
            var dataUrl = canvas.toDataURL('image/png');
            var a = document.createElement('a');
            a.href = dataUrl;
            a.download = 'china-map.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch(e) {
            alert('导出失败：' + e.message);
        }
    };
    img.onerror = function() {
        alert('图片渲染失败，请改用导出 SVG');
    };
    img.src = svgBase64;
}

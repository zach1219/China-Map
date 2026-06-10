// === export.js - 导出功能 ===

function downloadBlob(blob, filename) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
}

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


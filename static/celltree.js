/* ================================================================
   细胞谱系树动画（欢迎页背景）
   自相似的“一分二”分裂 + 沿左侧主链推进的镜头 + DNA 条形码。
   挂到 <canvas id="celltree"> 上；不可见时暂停，省电。
   ================================================================ */
(function () {
  'use strict';

  var canvas = document.getElementById('celltree');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');

  var VW = 800, VH = 800;
  var CX = VW / 2, CY = VH / 2;

  var DPR = 1, SCALE = 1, OX = 0, OY = 0, CW = 0, CH = 0;

  function fit() {
    DPR = window.devicePixelRatio || 1;
    var W = canvas.clientWidth || window.innerWidth;
    var H = canvas.clientHeight || window.innerHeight;
    CW = W; CH = H;
    canvas.width  = Math.round(W * DPR);
    canvas.height = Math.round(H * DPR);
    SCALE = Math.min(W / VW, H / VH);
    OX = (W - VW * SCALE) / 2;
    OY = (H - VH * SCALE) / 2;
  }
  fit();
  window.addEventListener('resize', fit);

  /* 层与层之间的基础间距 */
  var D = 80, Hh = 130, K = 1.6;
  var r0 = 42;

  /* 整棵树旋转角度：0 = 竖版，90 = 横版 */
  var ROT_DEG = 90;
  var ROT = ROT_DEG * Math.PI / 180;
  var RC = Math.cos(ROT), RS = Math.sin(ROT);
  var ROT_LEFT = ROT_DEG >= 45 && ROT_DEG < 135;   // 横版时淡出方向改到左边

  /* 画面整体平移：略上移，让树占满画面、上方不留白 */
  var VIEW_DX = 60, VIEW_DY = -40;

  /* 折线生长分量的切分比例：K : 1，使每个细胞落在横线中间 */
  var BRANCH = K / (1 + K);

  var ZOOM_STEPS = 10;                  // 一个循环内分裂次数
  var GENERATIONS = ZOOM_STEPS + 2;     // 细胞代数（多留 2 代垫底）

  /* ---------------- 配色：深蓝底 + 谱系彩虹 ---------------- */
  var TAU = Math.PI * 2;
  var RAMP = [
    [ 63, 142, 247], [ 95, 176, 255], [ 63, 192, 224], [ 34, 184, 102],
    [242, 173,  52], [239,  91,  91], [200, 168, 255], [ 63, 142, 247],
  ];
  function ramp(t) {
    t = ((t % 1) + 1) % 1;
    var x = t * (RAMP.length - 1), i = Math.floor(x), f = x - i;
    var a = RAMP[i], b = RAMP[i + 1];
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
  }
  function mixc(a, b, t) {
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
  }
  function rgba(c, a) {
    return 'rgba(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ',' + a + ')';
  }

  var CELLS = [], LINES = [], BIRTH = {}, IDX = {};

  function hashId(s) {
    var h = 2166136261 >>> 0;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  /* 细胞性状随机种子：只取决于“角色 + 代数 mod ZOOM_STEPS”，首尾一致 */
  function roleRnd(role, gen) {
    var m = ((gen % ZOOM_STEPS) + ZOOM_STEPS) % ZOOM_STEPS;
    return hashId(role + ':' + m);
  }
  function addCell(id, wx, wy, r, gen, rnd) {
    var c = { id: id, wx: wx, wy: wy, r: r, gen: gen, rnd: rnd === undefined ? hashId(id) : rnd };
    CELLS.push(c);
    IDX[id] = c;
    return c;
  }

  /* 树形：主链每代向左上一个子细胞；另一侧各生出一个子细胞，
     该子细胞只再分裂一次、长出两片叶子（后代不再分裂）。
     向“祖先”方向补 ANCESTORS 代，保证循环首尾一致。 */
  var ANCESTORS = 7;
  var GEN_MIN = -ANCESTORS;

  var spineS  = function (g) { return (Math.pow(K, -g) - 1) * K / (K - 1); };
  var spineId = function (g) { return 'S' + g; };

  for (var g = GEN_MIN; g <= GENERATIONS; g++) {
    var s = spineS(g);
    addCell(spineId(g), D * s, Hh * s, r0 * Math.pow(K, -g), g, roleRnd('s', g));
    if (g >= 3) BIRTH[spineId(g)] = spineId(g - 1);
  }

  function birth(id, gen, parId) { if (gen >= 3) BIRTH[id] = parId; }

  for (var gg = GEN_MIN; gg <= GENERATIONS - 1; gg++) {
    var sp = IDX[spineId(gg)];
    var dx = D / Math.pow(K, gg);
    var dy = Hh / Math.pow(K, gg);
    var rr = r0 / Math.pow(K, gg + 1);

    LINES.push([sp.id, spineId(gg + 1)]);

    var right = addCell('R' + gg, sp.wx + dx, sp.wy - dy, rr, gg + 1, roleRnd('r', gg + 1));
    LINES.push([sp.id, right.id]);
    birth(right.id, gg + 1, sp.id);

    if (gg + 2 <= GENERATIONS) {
      var dx2 = dx / K, dy2 = dy / K, r2 = rr / K;
      var l1 = addCell('R' + gg + 'a', right.wx - dx2, right.wy - dy2, r2, gg + 2, roleRnd('a', gg + 2));
      var l2 = addCell('R' + gg + 'b', right.wx + dx2, right.wy - dy2, r2, gg + 2, roleRnd('b', gg + 2));
      LINES.push([right.id, l1.id], [right.id, l2.id]);
      birth(l1.id, gg + 2, right.id);
      birth(l2.id, gg + 2, right.id);
    }
  }

  /* 每个细胞按“代数”取彩虹色（周期 ZOOM_STEPS，循环无缝） */
  for (var ci = 0; ci < CELLS.length; ci++) {
    var cgen = ((CELLS[ci].gen % ZOOM_STEPS) + ZOOM_STEPS) % ZOOM_STEPS;
    CELLS[ci].col = ramp(cgen / ZOOM_STEPS);
  }

  /* ---------------- DNA 序列 ---------------- */
  var SPINE = {};
  for (var sg = GEN_MIN; sg <= GENERATIONS; sg++) SPINE[sg] = IDX[spineId(sg)];

  var DNA_ROOT = ['A', 'T', 'C', 'G', 'A', 'T', 'C', 'G'];
  var MUT_POS  = [3, 0, 1, 2, 4, 3, 0, 1, 2, 4];
  var MUT_BASE = ['C', 'T', 'A', 'G', 'T', 'G', 'A', 'T', 'C', 'A'];
  var DNA = [DNA_ROOT.slice()];
  for (var dg = 1; dg <= ZOOM_STEPS; dg++) {
    var nextDNA = DNA[dg - 1].slice();
    nextDNA[MUT_POS[dg - 1]] = MUT_BASE[dg - 1];
    DNA.push(nextDNA);
  }
  /* 姊妹细胞（右子）的条形码：另加一个不同的突变；其叶子不展示 */
  var NEXT_BASE = { A: 'T', T: 'G', G: 'C', C: 'A' };
  var SIB_POS = MUT_POS.map(function (p) { return (p + 3) % DNA_ROOT.length; });
  var SIB_DNA = DNA.slice(0, ZOOM_STEPS).map(function (seq, k) {
    var s2 = seq.slice();
    s2[SIB_POS[k]] = NEXT_BASE[s2[SIB_POS[k]]];
    return s2;
  });
  var SIB = {};
  for (var sbg = GEN_MIN; sbg <= GENERATIONS - 1; sbg++) SIB[sbg] = IDX['R' + sbg];

  var EDGE_R = 240, EDGE_B = 240, MIN_ALPHA = 0.12;
  var WX0 = 0, WY0 = 0, WX1 = VW, WY1 = VH;

  function alphaForXY(sx, sy) {
    var distR = (ROT_LEFT ? (sx - WX0) : (WX1 - sx)) / EDGE_R;
    var distB = (WY1 - sy) / EDGE_B;
    var d = Math.min(1, distR, distB);
    if (d >= 1) return 1;
    if (d <= 0) return MIN_ALPHA;
    var sm = d * d * (3 - 2 * d);
    return MIN_ALPHA + (1 - MIN_ALPHA) * sm;
  }

  var STARS = [];
  for (var si = 0; si < 220; si++) {
    STARS.push({
      nx: Math.random(), ny: Math.random(),
      r: 0.4 + Math.random() * 1.6,
      a: 0.06 + Math.random() * 0.28,
      ph: Math.random() * TAU,
    });
  }

  var lerp = function (a, b, t) { return a + (b - a) * t; };

  function paintCell(sx, sy, sr, alpha, col, rnd) {
    if (sr <= 0.01 || alpha <= 0.001) return;
    if (sx + sr < WX0 || sx - sr > WX1 || sy + sr < WY0 || sy - sr > WY1) return;

    if (sr < 2.2) {
      ctx.globalAlpha = alpha;
      ctx.fillStyle = rgba(mixc(col, [255, 255, 255], 0.4), 0.95);
      ctx.beginPath(); ctx.arc(sx, sy, sr, 0, TAU); ctx.fill();
      return;
    }

    var memb   = mixc(col, [255, 255, 255], 0.62);
    var cyto   = mixc(col, [255, 255, 255], 0.42);
    var rimCol = mixc(col, [255, 255, 255], 0.82);
    var nuc    = mixc(col, [26, 30, 52], 0.32);
    var nucHi  = mixc(col, [255, 255, 255], 0.12);

    if (sr < 220) {
      var gr = sr * 1.7;
      var glow = ctx.createRadialGradient(sx, sy, sr * 0.7, sx, sy, gr);
      glow.addColorStop(0, rgba(memb, 0.16 * alpha));
      glow.addColorStop(1, rgba(memb, 0));
      ctx.globalAlpha = 1;
      ctx.fillStyle = glow;
      ctx.beginPath(); ctx.arc(sx, sy, gr, 0, TAU); ctx.fill();
    }
    ctx.globalAlpha = alpha;

    var ruffled = (rnd % 8) === 0;
    var amp = ruffled ? 0.055 : 0.012;
    var ph  = (rnd % 7) * 1.1;
    var f1 = 3 + (rnd % 3);
    var f2 = 5 + ((rnd >> 5) % 4);
    var p1 = (rnd % 10) * 0.7;
    var p2 = ((rnd >> 3) % 10) * 0.9;
    ctx.fillStyle = rgba(memb, 0.96);
    ctx.beginPath();
    var N = 48;
    for (var i = 0; i <= N; i++) {
      var a = (i / N) * TAU;
      var rw = sr * (1 + amp * Math.sin(a * f1 + p1) + amp * 0.6 * Math.sin(a * f2 + p2));
      var x = sx + Math.cos(a) * rw, y = sy + Math.sin(a) * rw;
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.lineWidth = Math.max(0.5, sr * 0.02);
    ctx.strokeStyle = rgba(rimCol, 0.55);
    ctx.stroke();

    ctx.fillStyle = rgba(cyto, 0.85);
    ctx.beginPath(); ctx.arc(sx, sy, sr * 0.82, 0, TAU); ctx.fill();

    ctx.fillStyle = 'rgba(255, 255, 255, 0.13)';
    ctx.beginPath();
    ctx.ellipse(sx - sr * 0.30, sy - sr * 0.32, sr * 0.40, sr * 0.26, -0.6, 0, TAU);
    ctx.fill();

    var stretch = (rnd & 16) ? 0.15 : 0.0;
    var ang = ph * 0.6;
    var ca = Math.cos(ang), sa = Math.sin(ang);
    var nx = sx + sr * 0.10 * Math.cos(ph);
    var ny = sy + sr * 0.10 * Math.sin(ph);
    var nr = sr * 0.50;
    var nN = 22;
    ctx.fillStyle = rgba(nuc, 0.96);
    ctx.beginPath();
    for (var j = 0; j <= nN; j++) {
      var an = (j / nN) * TAU;
      var wob = 1 + 0.05 * Math.sin(an * 3 + ph);
      var ux = Math.cos(an) * nr * (1 + stretch) * wob;
      var uy = Math.sin(an) * nr * (1 - stretch * 0.5) * wob;
      var xx = nx + ux * ca - uy * sa;
      var yy = ny + ux * sa + uy * ca;
      if (j) ctx.lineTo(xx, yy); else ctx.moveTo(xx, yy);
    }
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = rgba(nucHi, 0.35);
    ctx.beginPath();
    ctx.ellipse(nx - nr * 0.26, ny - nr * 0.28, nr * 0.50, nr * 0.38, ang, 0, TAU);
    ctx.fill();

    if (rnd & 8) {
      ctx.fillStyle = rgba(nuc, 0.45);
      for (var k = 0; k < 4; k++) {
        var ak = ph + k * 1.9;
        var px = sx + Math.cos(ak) * sr * 0.6;
        var py = sy + Math.sin(ak) * sr * 0.6;
        ctx.beginPath(); ctx.arc(px, py, Math.max(0.4, sr * 0.05), 0, TAU); ctx.fill();
      }
    }
  }

  function drawBarcode(s, seq, hi) {
    var fs = Math.min(26, s.r * 0.5);
    if (fs < 0.6) return;
    if (s.x < WX0 - s.r || s.x > WX1 + s.r || s.y < WY0 - s.r || s.y > WY1 + s.r) return;
    var vis = Math.min(1, s.r / 16) * Math.max(0, Math.min(1, (240 - s.r) / 70));
    if (vis <= 0.002) return;

    ctx.font = '700 ' + fs.toFixed(1) + 'px ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    var cw = ctx.measureText('M').width;
    var lx = s.x - cw * seq.length / 2;
    var ly = s.y - s.r - 8;

    for (var i = 0; i < seq.length; i++) {
      if (i === hi) {
        ctx.globalAlpha = s.a * vis;
        ctx.fillStyle = '#f2ad34';
        ctx.shadowColor = 'rgba(242, 173, 52, 0.9)';
        ctx.shadowBlur = 12;
      } else {
        ctx.globalAlpha = 0.9 * s.a * vis;
        ctx.fillStyle = 'rgba(205, 224, 248, 0.9)';
        ctx.shadowBlur = 0;
      }
      ctx.fillText(seq[i], lx + i * cw, ly);
    }
    ctx.shadowBlur = 0;
  }

  function paintBranch(px, py, cx, cy, alpha, pcol, ccol, w) {
    if (alpha <= 0.001) return;
    ctx.globalAlpha = alpha;
    var lg = ctx.createLinearGradient(px, py, cx, cy);
    lg.addColorStop(0, rgba(pcol, 0.85));
    lg.addColorStop(1, rgba(ccol, 0.95));
    ctx.strokeStyle = lg;
    ctx.lineWidth = w;
    var gx = RS, gy = -RC;
    var lx = RC, ly = RS;
    var vx = cx - px, vy = cy - py;
    var gd = vx * gx + vy * gy;
    var ld = vx * lx + vy * ly;
    var a = gd * BRANCH;
    var mx = px + gx * a;
    var my = py + gy * a;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(mx, my);
    ctx.lineTo(mx + lx * ld, my + ly * ld);
    ctx.lineTo(cx, cy);
    ctx.stroke();
  }

  function drawEdgeMask() {
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
    var x0 = WX0, y0 = WY0, x1 = WX1, y1 = WY1;

    if (ROT_LEFT) {
      var gradL = ctx.createLinearGradient(x0, 0, x0 + EDGE_R, 0);
      gradL.addColorStop(0, 'rgba(5, 10, 20, 0.92)');
      gradL.addColorStop(1, 'rgba(5, 10, 20, 0)');
      ctx.fillStyle = gradL;
      ctx.fillRect(x0, y0, EDGE_R, y1 - y0);
    } else {
      var gradR = ctx.createLinearGradient(x1 - EDGE_R, 0, x1, 0);
      gradR.addColorStop(0, 'rgba(5, 10, 20, 0)');
      gradR.addColorStop(1, 'rgba(5, 10, 20, 0.92)');
      ctx.fillStyle = gradR;
      ctx.fillRect(x1 - EDGE_R, y0, EDGE_R, y1 - y0);
    }

    var gradB = ctx.createLinearGradient(0, y1 - EDGE_B, 0, y1);
    gradB.addColorStop(0, 'rgba(5, 10, 20, 0)');
    gradB.addColorStop(1, 'rgba(5, 10, 20, 0.92)');
    ctx.fillStyle = gradB;
    ctx.fillRect(x0, y1 - EDGE_B, x1 - x0, EDGE_B);
  }

  /* ---------------- 主循环 ---------------- */
  var SPLIT_MS = 5500;
  var T = SPLIT_MS * ZOOM_STEPS;
  var t0 = performance.now();

  var running = false;
  var pausedAt = 0;
  var totalPaused = 0;

  function frame(now) {
    if (!running) return;
    var elapsed = now - t0 - totalPaused;
    var t = (elapsed % T) / T;
    var p = t;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(DPR * SCALE, 0, 0, DPR * SCALE, DPR * OX, DPR * OY);

    var fx0 = -OX / SCALE, fy0 = -OY / SCALE;
    var fw = CW / SCALE, fh = CH / SCALE;
    var gw = Math.max(fw, fh);
    WX0 = fx0; WY0 = fy0; WX1 = fx0 + fw; WY1 = fy0 + fh;

    var bgR = gw * 0.7;
    var bg = ctx.createRadialGradient(CX, CY, bgR * 0.06, CX, CY, bgR);
    bg.addColorStop(0,    '#0c1a2e');
    bg.addColorStop(0.55, '#08111f');
    bg.addColorStop(1,    '#050a14');
    ctx.globalAlpha = 1;
    ctx.fillStyle = bg;
    ctx.fillRect(fx0, fy0, fw, fh);

    var gl1x = fx0 + fw * 0.8, gl1y = fy0 + fh * 0.05;
    var gl1 = ctx.createRadialGradient(gl1x, gl1y, 0, gl1x, gl1y, gw * 0.55);
    gl1.addColorStop(0, 'rgba(58, 120, 220, 0.18)');
    gl1.addColorStop(1, 'rgba(58, 120, 220, 0)');
    ctx.fillStyle = gl1;
    ctx.fillRect(fx0, fy0, fw, fh);
    var gl2x = fx0 + fw * 0.1, gl2y = fy0 + fh * 0.12;
    var gl2 = ctx.createRadialGradient(gl2x, gl2y, 0, gl2x, gl2y, gw * 0.5);
    gl2.addColorStop(0, 'rgba(90, 70, 200, 0.14)');
    gl2.addColorStop(1, 'rgba(90, 70, 200, 0)');
    ctx.fillStyle = gl2;
    ctx.fillRect(fx0, fy0, fw, fh);

    for (var sti = 0; sti < STARS.length; sti++) {
      var st = STARS[sti];
      var tw = 0.55 + 0.45 * Math.sin(now * 0.0016 + st.ph);
      var sxg = fx0 + st.nx * fw;
      var syg = fy0 + st.ny * fh;
      ctx.globalAlpha = st.a * tw;
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(sxg, syg, st.r, 0, TAU);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    var q = new Array(ZOOM_STEPS);
    for (var i = 0; i < ZOOM_STEPS; i++) {
      var v = ZOOM_STEPS * p - i;
      q[i] = v < 0 ? 0 : (v > 1 ? 1 : v);
    }
    var camX = 0, camY = 0, camS = 1;
    for (var ci2 = 0; ci2 < ZOOM_STEPS; ci2++) {
      var qs = q[ci2];
      var kk = Math.pow(K, ci2);
      camX += qs * (-D / kk);
      camY += qs * (-Hh / kk);
      camS *= 1 + (K - 1) * qs;
    }

    var state = {};
    for (var cj = 0; cj < CELLS.length; cj++) {
      var c = CELLS[cj];
      var wx = c.wx, wy = c.wy, wr = c.r;
      var par = BIRTH[c.id];
      if (par) {
        var pc = IDX[par];
        var bp = q[c.gen - 3];
        wx = lerp(pc.wx, c.wx, bp);
        wy = lerp(pc.wy, c.wy, bp);
        wr = c.r * bp;
      }
      var sx = CX + camS * (wx - camX);
      var sy = CY + camS * (wy - camY);
      if (ROT_DEG) {
        var ddx = sx - CX, ddy = sy - CY;
        sx = CX + ddx * RC - ddy * RS;
        sy = CY + ddx * RS + ddy * RC;
      }
      sx += VIEW_DX;
      sy += VIEW_DY;
      var sr = wr * camS;
      var al = alphaForXY(sx, sy);
      state[c.id] = { x: sx, y: sy, r: sr, a: al };
    }

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    for (var li = 0; li < LINES.length; li++) {
      var ln = LINES[li];
      var A = state[ln[0]], B = state[ln[1]];
      if (A.r <= 0.01 || B.r <= 0.01) continue;
      if (Math.max(A.x, B.x) < WX0 || Math.min(A.x, B.x) > WX1) continue;
      if (Math.max(A.y, B.y) < WY0 || Math.min(A.y, B.y) > WY1) continue;
      var w = Math.max(1, Math.min(6, B.r * 0.17));
      paintBranch(A.x, A.y, B.x, B.y, Math.min(A.a, B.a), IDX[ln[0]].col, IDX[ln[1]].col, w);
    }

    for (var ck = 0; ck < CELLS.length; ck++) {
      var cc = CELLS[ck];
      var sc = state[cc.id];
      if (sc.r <= 0.01) continue;
      paintCell(sc.x, sc.y, sc.r, sc.a, cc.col, cc.rnd);
    }

    for (var bg2 = GEN_MIN; bg2 <= GENERATIONS; bg2++) {
      var bdi = ((bg2 % ZOOM_STEPS) + ZOOM_STEPS) % ZOOM_STEPS;
      drawBarcode(state[SPINE[bg2].id], DNA[bdi], MUT_POS[(bdi === 0 ? ZOOM_STEPS : bdi) - 1]);
    }
    for (var sg2 = GEN_MIN; sg2 <= GENERATIONS - 1; sg2++) {
      var sdi = ((sg2 % ZOOM_STEPS) + ZOOM_STEPS) % ZOOM_STEPS;
      drawBarcode(state[SIB[sg2].id], SIB_DNA[sdi], SIB_POS[sdi]);
    }
    ctx.globalAlpha = 1;

    drawEdgeMask();

    requestAnimationFrame(frame);
  }

  function startLoop() {
    if (running) return;
    running = true;
    if (pausedAt) { totalPaused += performance.now() - pausedAt; pausedAt = 0; }
    requestAnimationFrame(frame);
  }
  function stopLoop() {
    if (!running) return;
    running = false;
    pausedAt = performance.now();
  }

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) startLoop(); else stopLoop();
    }, { threshold: 0 }).observe(canvas);
  } else {
    startLoop();
  }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stopLoop(); else startLoop();
  });
})();

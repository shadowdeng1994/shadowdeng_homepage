(function () {
  'use strict';

  /* ---------- 语言切换（默认英文） ---------- */
  var LANG_KEY = 'lang';
  var phrasesByLang = {
    en: ['Prof. Shanjun Deng',
         'Sun Yat-sen University',
         'School of Life Sciences',
         'Molecular Evolution',
         'Cell Lineage',
         'Cell Population History'],
    zh: ['邓善俊',
         '中山大学',
         '生命科学学院',
         '分子进化学',
         '细胞谱系',
         '细胞群体历史']
  };

  function currentLang() {
    return document.documentElement.classList.contains('lang-zh') ? 'zh' : 'en';
  }

  function applyLang(lang) {
    var d = document.documentElement;
    d.classList.toggle('lang-en', lang === 'en');
    d.classList.toggle('lang-zh', lang === 'zh');
    d.setAttribute('lang', lang === 'zh' ? 'zh-CN' : 'en');
    var t = d.getAttribute('data-title-' + lang);
    if (t) { document.title = t; }
    var sw = document.querySelectorAll('.lang-switch');
    for (var i = 0; i < sw.length; i++) {
      sw[i].setAttribute('aria-checked', lang === 'en' ? 'true' : 'false');
      sw[i].setAttribute('aria-label', lang === 'en' ? 'Switch to 中文' : 'Switch to English');
    }
    startTyping();
  }

  function setLang(lang) {
    try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
    applyLang(lang);
  }

  var switches = document.querySelectorAll('.lang-switch');
  for (var ti = 0; ti < switches.length; ti++) {
    (function (btn) {
      btn.addEventListener('click', function () {
        setLang(currentLang() === 'en' ? 'zh' : 'en');
      });
    })(switches[ti]);
  }

  /* ---------- 主题切换（默认浅色） ---------- */
  function currentTheme() {
    return document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    var d = document.documentElement;
    d.classList.toggle('theme-light', theme === 'light');
    d.classList.toggle('theme-dark', theme === 'dark');
    var sw = document.querySelectorAll('.theme-switch');
    for (var i = 0; i < sw.length; i++) {
      sw[i].setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
      sw[i].setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
  }

  function setTheme(theme) {
    try { localStorage.setItem('theme', theme); } catch (e) {}
    applyTheme(theme);
  }

  var themeSwitches = document.querySelectorAll('.theme-switch');
  for (var tsi = 0; tsi < themeSwitches.length; tsi++) {
    (function (btn) {
      btn.addEventListener('click', function () {
        setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
      });
    })(themeSwitches[tsi]);
  }

  /* ---------- 星光 ---------- */
  var starsBox = document.getElementById('stars');
  if (starsBox) {
    for (var i = 0; i < 42; i++) {
      var s = document.createElement('span');
      s.className = 'star';
      var size = 1 + Math.random() * 2.5;
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      s.style.left = Math.random() * 100 + '%';
      s.style.top = Math.random() * 100 + '%';
      s.style.animationDuration =
        (8 + Math.random() * 10) + 's, ' + (2 + Math.random() * 3) + 's';
      s.style.animationDelay =
        (-Math.random() * 15) + 's, ' + (-Math.random() * 3) + 's';
      starsBox.appendChild(s);
    }
  }

  /* ---------- 帷幕打字动画（随语言切换） ---------- */
  var typedText = document.getElementById('typedText');
  var typeTimer = null;

  function startTyping() {
    if (!typedText) { return; }
    if (typeTimer) { clearTimeout(typeTimer); typeTimer = null; }
    var phrases = phrasesByLang[currentLang()];
    var pi = 0, ci = 0, deleting = false;
    var TYPE_MS = 90, DELETE_MS = 45, HOLD_MS = 1500, GAP_MS = 380;
    var jitter = function (base, spread) { return base + Math.random() * spread; };
    var step = function () {
      var cur = phrases[pi];
      if (!deleting) {
        ci++;
        typedText.textContent = cur.slice(0, ci);
        if (ci >= cur.length) { deleting = true; typeTimer = setTimeout(step, HOLD_MS); }
        else { typeTimer = setTimeout(step, jitter(TYPE_MS, 55)); }
      } else {
        ci--;
        typedText.textContent = cur.slice(0, ci);
        if (ci <= 0) {
          deleting = false;
          pi = (pi + 1) % phrases.length;
          typeTimer = setTimeout(step, GAP_MS);
        } else { typeTimer = setTimeout(step, jitter(DELETE_MS, 25)); }
      }
    };
    typeTimer = setTimeout(step, 400);
  }

  /* ---------- 视差背景 ---------- */
  var bgFar = document.querySelector('.bg-far');
  var bgNear = document.querySelector('.bg-near');
  if (bgFar || bgNear) {
    var bgTicking = false;
    var updateBG = function () {
      var y = window.scrollY;
      if (bgFar) bgFar.style.transform = 'translate3d(0,' + (-y * 0.08) + 'px,0)';
      if (bgNear) bgNear.style.transform = 'translate3d(0,' + (-y * 0.68) + 'px,0)';
      bgTicking = false;
    };
    window.addEventListener('scroll', function () {
      if (!bgTicking) { requestAnimationFrame(updateBG); bgTicking = true; }
    }, { passive: true });
    updateBG();
  }

  /* ---------- 自定义缓动滚动 ---------- */
  var SCROLL_DURATION = 900;
  function smoothScrollTo(targetY, duration) {
    duration = duration || SCROLL_DURATION;
    var html = document.documentElement;
    var prevBehavior = html.style.scrollBehavior;
    html.style.scrollBehavior = 'auto';
    var startY = window.scrollY;
    var diff = targetY - startY;
    var start = performance.now();
    var ease = function (t) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    };
    return new Promise(function (resolve) {
      function step(now) {
        var t = Math.min((now - start) / duration, 1);
        window.scrollTo(0, startY + diff * ease(t));
        if (t < 1) requestAnimationFrame(step);
        else { html.style.scrollBehavior = prevBehavior; resolve(); }
      }
      requestAnimationFrame(step);
    });
  }

  /* ---------- 帷幕 / 主页切换 ---------- */
  var curtain = document.getElementById('curtain');
  var skipCurtain = document.documentElement.classList.contains('skip-curtain');
  if (curtain && !skipCurtain) {
    var curtainHeight = function () { return curtain.offsetHeight; };
    var locked = false;

    var goHome = function () {
      if (locked) return;
      locked = true;
      curtain.classList.remove('entering');
      curtain.classList.add('leaving');
      smoothScrollTo(curtainHeight()).then(function () {
        setTimeout(function () { locked = false; }, 120);
      });
    };
    var goCurtain = function () {
      if (locked) return;
      locked = true;
      smoothScrollTo(0).then(function () {
        curtain.classList.remove('leaving');
        curtain.classList.add('entering');
        setTimeout(function () { curtain.classList.remove('entering'); }, 950);
        setTimeout(function () { locked = false; }, 120);
      });
    };

    // 桌面端鼠标点击进入（触屏忽略；点开关/链接不触发）
    var onClickEnter = function (e) {
      if (locked) return;
      if (e.target && e.target.closest && e.target.closest('button, a')) return;
      if (window.scrollY > curtainHeight() - 5) return;
      goHome();
    };
    if (window.PointerEvent) {
      curtain.addEventListener('pointerup', function (e) {
        if (e.pointerType !== 'mouse') return;
        onClickEnter(e);
      });
    } else {
      curtain.addEventListener('click', onClickEnter);
    }

    window.addEventListener('wheel', function (e) {
      if (locked) { e.preventDefault(); return; }
      var y = window.scrollY;
      var ch = curtainHeight();
      if (y <= 5 && e.deltaY > 0) { e.preventDefault(); goHome(); return; }
      if (y > 0 && y <= ch && e.deltaY < 0) { e.preventDefault(); goCurtain(); return; }
    }, { passive: false });

    var touchStartY = 0;
    curtain.addEventListener('touchstart', function (e) {
      touchStartY = e.touches[0].clientY;
    }, { passive: true });
    curtain.addEventListener('touchmove', function (e) {
      if (window.scrollY < curtainHeight() - 5) { e.preventDefault(); }
    }, { passive: false });
    curtain.addEventListener('touchend', function (e) {
      if (locked) return;
      var dy = touchStartY - e.changedTouches[0].clientY;
      if (dy > 36) goHome();
    }, { passive: true });

    document.addEventListener('keydown', function (e) {
      if (locked) return;
      var y = window.scrollY;
      if (y < 5 &&
          (e.key === 'Enter' || e.key === ' ' ||
           e.key === 'ArrowDown' || e.key === 'PageDown')) {
        e.preventDefault();
        goHome();
      }
    });

    var navName = document.getElementById('navName');
    if (navName) navName.addEventListener('click', goCurtain);
  }

  /* ---------- 吸顶导航显隐 ---------- */
  var stickyNav = document.getElementById('stickyNav');
  if (stickyNav) {
    var navThreshold = function () {
      return (curtain && !skipCurtain ? curtain.offsetHeight : 0) - 80;
    };
    var toggleNav = function () {
      stickyNav.classList.toggle('visible', window.scrollY > navThreshold());
    };
    window.addEventListener('scroll', toggleNav, { passive: true });
    toggleNav();
  }

  /* ---------- 研究轮播（可拖动 · 双向无限循环） ---------- */
  var track = document.getElementById('track');
  if (track) {
    var viewport = track.parentElement;
    var realSlides = Array.prototype.slice.call(track.children);
    var total = realSlides.length;
    var dotsBox = document.getElementById('dots');
    var curNum = document.getElementById('curNum');
    var totalNum = document.getElementById('totalNum');
    var progress = document.getElementById('progress');
    var AUTO_MS = 4000;
    var dots = [];
    var pos = 1;                 // 当前轨道位置（1 = 第一张真实幻灯片）
    var isAnimating = false;
    var autoTimer = null;

    if (totalNum) totalNum.textContent = String(total).padStart(2, '0');

    // 头尾各克隆一张，实现无缝循环
    if (total > 1) {
      var lastClone = realSlides[total - 1].cloneNode(true);
      var firstClone = realSlides[0].cloneNode(true);
      lastClone.setAttribute('aria-hidden', 'true');
      firstClone.setAttribute('aria-hidden', 'true');
      track.insertBefore(lastClone, realSlides[0]);
      track.appendChild(firstClone);
    }

    if (dotsBox) {
      for (var d = 0; d < total; d++) {
        (function (n) {
          var dot = document.createElement('button');
          dot.className = 'dot' + (n === 0 ? ' active' : '');
          dot.setAttribute('aria-label', 'slide ' + (n + 1));
          dot.addEventListener('click', function () {
            if (isAnimating) { resetAuto(); return; }
            goToPos(n + 1, true); resetAuto();
          });
          dotsBox.appendChild(dot);
          dots.push(dot);
        })(d);
      }
    }

    function slideWidth() { return viewport.clientWidth || track.clientWidth || 1; }
    function realIndex() { return ((pos - 1) % total + total) % total; }

    function setTransform(px, animate) {
      if (animate) {
        track.style.transition = '';
        void track.offsetWidth;
        track.style.transform = 'translateX(' + px + 'px)';
      } else {
        track.style.transition = 'none';
        track.style.transform = 'translateX(' + px + 'px)';
        void track.offsetWidth;
      }
    }

    function updateUI() {
      var ri = realIndex();
      for (var k = 0; k < dots.length; k++) dots[k].classList.toggle('active', k === ri);
      if (curNum) curNum.textContent = String(ri + 1).padStart(2, '0');
      if (progress) {
        progress.style.transition = 'none';
        progress.style.width = '0';
        void progress.offsetWidth;
        progress.style.transition = 'width ' + AUTO_MS + 'ms linear';
        progress.style.width = '100%';
      }
    }

    function goToPos(p, animate) {
      if (total <= 1) { setTransform(0, false); return; }
      pos = p;
      isAnimating = animate !== false;
      setTransform(-pos * slideWidth(), isAnimating);
      updateUI();
    }

    function next() { if (total <= 1 || isAnimating) return; goToPos(pos + 1, true); }
    function prev() { if (total <= 1 || isAnimating) return; goToPos(pos - 1, true); }

    track.addEventListener('transitionend', function (e) {
      if (e.propertyName !== 'transform') return;
      isAnimating = false;
      if (total <= 1) return;
      if (pos === 0) { pos = total; setTransform(-pos * slideWidth(), false); }
      else if (pos === total + 1) { pos = 1; setTransform(-pos * slideWidth(), false); }
    });

    function resetAuto() {
      clearInterval(autoTimer);
      autoTimer = setInterval(next, AUTO_MS);
    }

    var prevBtn = document.getElementById('prev');
    var nextBtn = document.getElementById('next');
    if (prevBtn) prevBtn.addEventListener('click', function () { prev(); resetAuto(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { next(); resetAuto(); });

    // 拖动 / 滑动
    var dragging = false, startX = 0, startY = 0, curDx = 0, axis = null;
    viewport.addEventListener('pointerdown', function (e) {
      if (total <= 1) return;
      dragging = true; axis = null; curDx = 0;
      startX = e.clientX; startY = e.clientY;
      isAnimating = false;
      clearInterval(autoTimer);
      track.style.transition = 'none';
      if (viewport.setPointerCapture && e.pointerId != null) {
        try { viewport.setPointerCapture(e.pointerId); } catch (err) {}
      }
    });
    viewport.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var dx = e.clientX - startX, dy = e.clientY - startY;
      if (axis === null) {
        if (Math.abs(dx) > Math.abs(dy) + 4) axis = 'x';
        else if (Math.abs(dy) > Math.abs(dx) + 4) axis = 'y';
        else return;
      }
      if (axis !== 'x') return;
      curDx = dx;
      track.style.transform = 'translateX(' + (-pos * slideWidth() + dx) + 'px)';
      if (e.cancelable) e.preventDefault();
    }, { passive: false });
    function endDrag() {
      if (!dragging) return;
      dragging = false;
      var w = slideWidth();
      if (axis === 'x' && Math.abs(curDx) > Math.max(40, w * 0.15)) {
        if (curDx < 0) goToPos(pos + 1, true);
        else goToPos(pos - 1, true);
      } else {
        goToPos(pos, true);
      }
      resetAuto();
    }
    viewport.addEventListener('pointerup', endDrag);
    viewport.addEventListener('pointercancel', endDrag);
    viewport.addEventListener('lostpointercapture', endDrag);

    window.addEventListener('resize', function () {
      if (total <= 1) return;
      setTransform(-pos * slideWidth(), false);
    });

    if (total > 0) { pos = 1; updateUI(); setTransform(-slideWidth(), false); resetAuto(); }
  }

  /* ---------- 导航高亮 ---------- */
  var navLinks = document.querySelectorAll('.nav-links a[data-nav]');
  var sections = document.querySelectorAll('.section');
  if (navLinks.length && sections.length && 'IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var id = entry.target.id;
          navLinks.forEach(function (a) {
            a.classList.toggle('active', a.getAttribute('data-nav') === id);
          });
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });
    sections.forEach(function (sec) { obs.observe(sec); });
  }

  /* ---------- 初始语言 / 主题 ---------- */
  applyLang(currentLang());
  applyTheme(currentTheme());
})();

(function () {
  'use strict';

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

  /* ---------- 视差背景 ---------- */
  var bgFar = document.querySelector('.bg-far');
  var bgNear = document.querySelector('.bg-near');
  if (bgFar || bgNear) {
    var root = document.documentElement;
    var bgTicking = false;
    var updateBG = function () {
      var y = window.scrollY;
      if (bgFar) root.style.setProperty('--bg-far-y', (-y * 0.08) + 'px');
      if (bgNear) root.style.setProperty('--bg-near-y', (-y * 0.68) + 'px');
      bgTicking = false;
    };
    window.addEventListener('scroll', function () {
      if (!bgTicking) { requestAnimationFrame(updateBG); bgTicking = true; }
    }, { passive: true });
    updateBG();
  }

  /* ---------- 自定义缓动滚动 ---------- */
  var SCROLL_DURATION = 3000;
  function smoothScrollTo(targetY, duration) {
    duration = duration || SCROLL_DURATION;
    var html = document.documentElement;
    var prevBehavior = html.style.scrollBehavior;
    html.style.scrollBehavior = 'auto';
    var startY = window.scrollY;
    var diff = targetY - startY;
    var start = performance.now();
    var ease = function (t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); };
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
  if (curtain) {
    var stickyNav = document.getElementById('stickyNav');
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

    curtain.addEventListener('click', goHome);

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
    curtain.addEventListener('touchend', function (e) {
      var dy = touchStartY - e.changedTouches[0].clientY;
      if (dy > 30) goHome();
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

    if (stickyNav) {
      window.addEventListener('scroll', function () {
        stickyNav.classList.toggle('visible', window.scrollY > curtainHeight() - 80);
      }, { passive: true });
    }
  }

  /* ---------- 研究轮播 ---------- */
  var track = document.getElementById('track');
  if (track) {
    var total = track.children.length;
    var dotsBox = document.getElementById('dots');
    var curNum = document.getElementById('curNum');
    var totalNum = document.getElementById('totalNum');
    var progress = document.getElementById('progress');
    var idx = 0;
    var autoTimer = null;
    var AUTO_MS = 4000;
    var dots = [];

    if (totalNum) totalNum.textContent = String(total).padStart(2, '0');
    if (dotsBox) {
      for (var d = 0; d < total; d++) {
        (function (n) {
          var dot = document.createElement('button');
          dot.className = 'dot' + (n === 0 ? ' active' : '');
          dot.setAttribute('aria-label', '第 ' + (n + 1) + ' 个');
          dot.addEventListener('click', function () { goTo(n); resetAuto(); });
          dotsBox.appendChild(dot);
          dots.push(dot);
        })(d);
      }
    }

    function goTo(i) {
      idx = (i + total) % total;
      track.style.transform = 'translateX(-' + (idx * 100) + '%)';
      for (var k = 0; k < dots.length; k++) {
        dots[k].classList.toggle('active', k === idx);
      }
      if (curNum) curNum.textContent = String(idx + 1).padStart(2, '0');
      if (progress) {
        progress.style.transition = 'none';
        progress.style.width = '0';
        void progress.offsetWidth;
        progress.style.transition = 'width ' + AUTO_MS + 'ms linear';
        progress.style.width = '100%';
      }
    }
    function resetAuto() {
      clearInterval(autoTimer);
      autoTimer = setInterval(function () { goTo(idx + 1); }, AUTO_MS);
    }

    var prevBtn = document.getElementById('prev');
    var nextBtn = document.getElementById('next');
    if (prevBtn) prevBtn.addEventListener('click', function () { goTo(idx - 1); resetAuto(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { goTo(idx + 1); resetAuto(); });

    if (total > 0) { goTo(0); resetAuto(); }
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
})();

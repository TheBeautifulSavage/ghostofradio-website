/* ============================================
   Ghost of Radio — Main JavaScript
   ============================================ */

(function () {
  'use strict';

  // --- Header scroll effect ---
  const header = document.querySelector('.site-header');
  if (header) {
    window.addEventListener('scroll', function () {
      header.classList.toggle('scrolled', window.scrollY > 50);
    });
  }

  // --- Mobile nav toggle ---
  const toggle = document.querySelector('.nav__toggle');
  const navLinks = document.querySelector('.nav__links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', function () {
      navLinks.classList.toggle('open');
      toggle.setAttribute('aria-expanded', navLinks.classList.contains('open'));
    });

    // Close menu when a link is clicked
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // --- Set active nav link ---
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav__links a').forEach(function (link) {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

  // --- Fade-in on scroll ---
  const fadeElements = document.querySelectorAll('.fade-in');
  if (fadeElements.length > 0 && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    fadeElements.forEach(function (el) {
      observer.observe(el);
    });
  }

  // --- Typewriter effect for hero subtitle ---
  const typewriterEl = document.querySelector('.typewriter');
  if (typewriterEl) {
    const text = typewriterEl.getAttribute('data-text');
    if (text) {
      typewriterEl.textContent = '';
      let i = 0;
      function typeChar() {
        if (i < text.length) {
          typewriterEl.textContent += text.charAt(i);
          i++;
          setTimeout(typeChar, 60 + Math.random() * 40);
        }
      }
      // Start after a short delay
      setTimeout(typeChar, 800);
    }
  }

  // --- Year in footer ---
  const yearEl = document.querySelector('.current-year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

})();

/* --- Fade-in CSS (injected) --- */
(function () {
  var style = document.createElement('style');
  style.textContent = [
    '.fade-in {',
    '  opacity: 0;',
    '  transform: translateY(20px);',
    '  transition: opacity 0.6s ease, transform 0.6s ease;',
    '}',
    '.fade-in.visible {',
    '  opacity: 1;',
    '  transform: translateY(0);',
    '}'
  ].join('\n');
  document.head.appendChild(style);
})();

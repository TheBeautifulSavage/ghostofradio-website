// Email Capture Modal — Ghost of Radio Lead Magnet
(function () {
  if (localStorage.getItem('gor-email-dismissed')) return;

  var DELAY = 30000;

  function createModal() {
    var overlay = document.createElement('div');
    overlay.id = 'gor-email-overlay';
    overlay.innerHTML =
      '<div class="gor-email-modal">' +
        '<button class="gor-email-close" aria-label="Close">&times;</button>' +
        '<h2 class="gor-email-headline">FREE: The Essential OTR Listening Guide</h2>' +
        '<p class="gor-email-subhead">50 classic shows. 8 must-hear episodes. The full golden age timeline.</p>' +
        '<form class="gor-email-form" id="gorEmailForm">' +
          '<input type="email" class="gor-email-input" placeholder="Your email address" required />' +
          '<button type="submit" class="gor-email-btn">Get the Free Guide &rarr;</button>' +
        '</form>' +
        '<p class="gor-email-fine">No spam. Unsubscribe anytime.</p>' +
        '<div class="gor-email-success" id="gorEmailSuccess" style="display:none">' +
          '<p class="gor-email-thanks">You\u2019re in! Download your free guide:</p>' +
          '<a href="/downloads/ghost-of-radio-guide.pdf" class="gor-email-download" download>Download the Guide (PDF)</a>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);

    // Animate in
    requestAnimationFrame(function () {
      overlay.classList.add('gor-email-visible');
    });

    // Close handlers
    overlay.querySelector('.gor-email-close').addEventListener('click', dismiss);
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) dismiss();
    });

    // Submit
    document.getElementById('gorEmailForm').addEventListener('submit', function (e) {
      e.preventDefault();
      var email = this.querySelector('input').value;
      if (!email) return;

      // Store email
      localStorage.setItem('gor-email-address', email);
      localStorage.setItem('gor-email-dismissed', '1');

      // Show success
      this.style.display = 'none';
      overlay.querySelector('.gor-email-subhead').style.display = 'none';
      overlay.querySelector('.gor-email-fine').style.display = 'none';
      document.getElementById('gorEmailSuccess').style.display = 'block';
    });
  }

  function dismiss() {
    localStorage.setItem('gor-email-dismissed', '1');
    var overlay = document.getElementById('gor-email-overlay');
    if (overlay) {
      overlay.classList.remove('gor-email-visible');
      setTimeout(function () { overlay.remove(); }, 400);
    }
  }

  setTimeout(createModal, DELAY);
})();

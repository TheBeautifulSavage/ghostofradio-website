/**
 * Ghost of Radio — Membership Layer
 * Play: free, no login required
 * Download: requires account (free to create now, paid tiers later)
 */

const GOR = {
  // Check if user is logged in
  isLoggedIn() {
    return !!localStorage.getItem('gor_user');
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('gor_user'));
    } catch { return null; }
  },

  login(email, password) {
    // Simple client-side auth for now — replace with real backend later
    // Any email/password combo creates an account (collect leads)
    const user = { email, joinedAt: Date.now(), tier: 'free' };
    localStorage.setItem('gor_user', JSON.stringify(user));
    return user;
  },

  logout() {
    localStorage.removeItem('gor_user');
    location.reload();
  },

  // Show the login/signup modal
  showModal(reason = 'download') {
    document.getElementById('gor-modal-overlay')?.remove();

    const overlay = document.createElement('div');
    overlay.id = 'gor-modal-overlay';
    overlay.innerHTML = `
      <div class="gor-modal">
        <button class="gor-modal__close" onclick="document.getElementById('gor-modal-overlay').remove()">✕</button>
        <div class="gor-modal__icon">📻</div>
        <h2 class="gor-modal__title">Join Ghost of Radio</h2>
        <p class="gor-modal__sub">
          ${reason === 'download'
            ? 'Create a free account to download MP3s and access playlists.'
            : 'Sign in to your Ghost of Radio account.'}
        </p>
        <form class="gor-modal__form" onsubmit="GOR._handleSubmit(event)">
          <input
            type="email"
            id="gor-email"
            class="gor-modal__input"
            placeholder="Your email address"
            required
            autocomplete="email"
          />
          <input
            type="password"
            id="gor-password"
            class="gor-modal__input"
            placeholder="Create a password"
            required
            minlength="6"
            autocomplete="new-password"
          />
          <button type="submit" class="gor-modal__btn">
            Enter the Archive →
          </button>
        </form>
        <p class="gor-modal__fine">
          Free forever to listen. Downloads &amp; playlists included with free account during launch.
        </p>
      </div>
    `;

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.remove();
    });

    document.body.appendChild(overlay);
    setTimeout(() => document.getElementById('gor-email')?.focus(), 100);
  },

  _handleSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('gor-email').value;
    const password = document.getElementById('gor-password').value;
    const user = this.login(email, password);

    // Hide modal
    document.getElementById('gor-modal-overlay')?.remove();

    // Update UI
    this._updateNav();

    // If they came from a download click, trigger it now
    if (this._pendingDownload) {
      this._pendingDownload();
      this._pendingDownload = null;
    }

    // Show welcome message
    this._toast(`Welcome to Ghost of Radio, ${email.split('@')[0]}!`);
  },

  _pendingDownload: null,

  // Intercept download clicks
  gateDownload(url, filename) {
    if (this.isLoggedIn()) {
      // Trigger download directly
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || url.split('/').pop();
      a.click();
    } else {
      // Save the download action, show modal
      this._pendingDownload = () => this.gateDownload(url, filename);
      this.showModal('download');
    }
  },

  _toast(msg) {
    const t = document.createElement('div');
    t.className = 'gor-toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('gor-toast--show'), 10);
    setTimeout(() => { t.classList.remove('gor-toast--show'); setTimeout(() => t.remove(), 400); }, 3500);
  },

  _updateNav() {
    const user = this.getUser();
    const existing = document.getElementById('gor-account-nav');
    if (existing) existing.remove();

    if (user) {
      const nav = document.querySelector('.nav__links');
      if (nav) {
        const li = document.createElement('li');
        li.id = 'gor-account-nav';
        li.innerHTML = `<span class="gor-nav-user" title="${user.email}">● ${user.email.split('@')[0]}</span>`;
        nav.appendChild(li);
      }
    }
  },

  init() {
    // Wire up all download buttons on the page
    document.querySelectorAll('.gor-download-btn, [data-download]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const url = btn.getAttribute('data-src') || btn.href;
        const filename = btn.getAttribute('data-filename') || '';
        GOR.gateDownload(url, filename);
      });
    });

    // Update nav if logged in
    this._updateNav();
  }
};

document.addEventListener('DOMContentLoaded', () => GOR.init());

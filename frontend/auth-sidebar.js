/**
 * auth-sidebar.js
 * - Injects dark mode + Hindi language toggles into every page's sidebar
 * - Hindi toggle uses Google Translate cookie method to translate the full page
 * - Dark mode persisted in localStorage
 */

// ── Apply dark mode IMMEDIATELY (before DOM to prevent flash) ──────
(function applyThemeEarly() {
    if (localStorage.getItem('sehat_theme') === 'dark') {
        document.documentElement.classList.add('dark');
        document.body && document.body.classList.add('dark');
    }
})();

// ── Google Translate: apply language cookie on page load ───────────
(function applyLangEarly() {
    const lang = localStorage.getItem('sehat_lang');
    if (lang === 'hi') {
        setGoogleTranslateCookie('hi');
    }
})();

function setGoogleTranslateCookie(lang) {
    // Set the cookie Google Translate reads to auto-translate
    const cookieVal = lang === 'hi' ? '/en/hi' : '/en/en';
    document.cookie = 'googtrans=' + cookieVal + '; path=/';
    document.cookie = 'googtrans=' + cookieVal + '; path=/; domain=' + location.hostname;
}

function loadGoogleTranslate() {
    if (document.getElementById('gt-script')) return; // already loaded
    // Hidden container required by Google Translate widget
    const el = document.createElement('div');
    el.id = 'google_translate_element';
    el.style.display = 'none';
    document.body.appendChild(el);

    window.googleTranslateElementInit = function () {
        new google.translate.TranslateElement({
            pageLanguage: 'en',
            includedLanguages: 'hi',
            autoDisplay: false
        }, 'google_translate_element');
    };

    const script = document.createElement('script');
    script.id = 'gt-script';
    script.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    document.head.appendChild(script);
}

(function () {
    const token = localStorage.getItem('access_token');
    const name  = localStorage.getItem('user_name')  || 'Guest';
    const email = localStorage.getItem('user_email') || '';

    document.addEventListener('DOMContentLoaded', () => {
        // Apply dark mode to body
        if (localStorage.getItem('sehat_theme') === 'dark') {
            document.body.classList.add('dark');
        }

        // Load Google Translate if Hindi is active
        if (localStorage.getItem('sehat_lang') === 'hi') {
            loadGoogleTranslate();
        }

        // ── Inject sidebar controls ─────────────────────────────────
        const sidebar   = document.querySelector('.sidebar');
        const profileEl = document.querySelector('.user-profile');
        if (!sidebar || !profileEl) return;

        const controls = document.createElement('div');
        controls.style.cssText = 'display:flex; gap:6px; margin-bottom:16px;';

        // ── Dark mode button ────────────────────────────────────────
        const isDark  = localStorage.getItem('sehat_theme') === 'dark';
        const darkBtn = document.createElement('button');
        const btnStyle = 'flex:1; padding:8px 4px; border-radius:8px; border:1px solid rgba(255,255,255,0.2); background:rgba(255,255,255,0.1); color:white; font-size:12px; font-weight:600; font-family:Inter,sans-serif; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:4px;';
        darkBtn.style.cssText = btnStyle;
        darkBtn.innerHTML = isDark ? '☀️ Light' : '🌙 Dark';
        darkBtn.onclick = function () {
            const nowDark = document.body.classList.toggle('dark');
            localStorage.setItem('sehat_theme', nowDark ? 'dark' : 'light');
            darkBtn.innerHTML = nowDark ? '☀️ Light' : '🌙 Dark';
        };

        // ── Hindi language button ───────────────────────────────────
        const isHindi = localStorage.getItem('sehat_lang') === 'hi';
        const langBtn = document.createElement('button');
        langBtn.style.cssText = btnStyle;
        langBtn.innerHTML = isHindi ? '🇮🇳 हिंदी' : '🇬🇧 Eng';
        langBtn.title = 'Translate page to Hindi';
        langBtn.onclick = function () {
            const nowHindi = localStorage.getItem('sehat_lang') !== 'hi';
            localStorage.setItem('sehat_lang', nowHindi ? 'hi' : 'en');
            setGoogleTranslateCookie(nowHindi ? 'hi' : 'en');
            // Reload to apply translation
            location.reload();
        };

        controls.appendChild(darkBtn);
        controls.appendChild(langBtn);
        sidebar.insertBefore(controls, profileEl);

        // ── User profile ────────────────────────────────────────────
        if (token) {
            const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
            profileEl.innerHTML = `
                <div style="background:rgba(255,255,255,0.25);color:white;font-weight:700;font-size:14px;
                    display:flex;align-items:center;justify-content:center;width:36px;height:36px;
                    border-radius:50%;flex-shrink:0;">${initials}</div>
                <div style="flex:1;min-width:0;">
                    <strong style="display:block;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${name}</strong>
                    <span style="font-size:11px;opacity:0.75;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;">${email}</span>
                </div>
                <button onclick="deleteAccount()" title="Delete Account" style="background:rgba(239,68,68,0.15);border:none;
                    color:#ef4444;border-radius:6px;width:28px;height:28px;cursor:pointer;font-size:14px;
                    display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-right:4px;"
                    onmouseover="this.style.background='rgba(239,68,68,0.25)'"
                    onmouseout="this.style.background='rgba(239,68,68,0.15)'">🗑️</button>
                <button onclick="logout()" title="Sign out" style="background:rgba(255,255,255,0.15);border:none;
                    color:white;border-radius:6px;width:28px;height:28px;cursor:pointer;font-size:14px;
                    display:flex;align-items:center;justify-content:center;flex-shrink:0;"
                    onmouseover="this.style.background='rgba(255,255,255,0.25)'"
                    onmouseout="this.style.background='rgba(255,255,255,0.15)'">⏏</button>
            `;
        } else {
            profileEl.innerHTML = `
                <div style="background:rgba(255,255,255,0.15);display:flex;align-items:center;
                    justify-content:center;font-size:16px;width:36px;height:36px;border-radius:50%;flex-shrink:0;">👤</div>
                <div style="flex:1;">
                    <strong style="display:block;font-size:13px;">Guest User</strong>
                    <a href="login.html" style="font-size:11px;background:rgba(255,255,255,0.2);color:white;
                        text-decoration:none;padding:2px 8px;border-radius:4px;font-weight:600;
                        display:inline-block;margin-top:2px;"
                        onmouseover="this.style.background='rgba(255,255,255,0.35)'"
                        onmouseout="this.style.background='rgba(255,255,255,0.2)'">Sign In →</a>
                </div>
            `;
        }
    });

    window.deleteAccount = async function () {
        if (!confirm('DANGER: Are you sure you want to permanently delete your account? This action cannot be undone and will delete all your data.')) return;
        const token = localStorage.getItem('access_token');
        if (!token) return;
        try {
            const res = await fetch('/api/auth/me', {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                alert('Your account has been deleted successfully.');
                logout(true); // pass true to skip confirm
            } else {
                alert('Failed to delete account. Please try again.');
            }
        } catch (e) {
            alert('Connection error while trying to delete account.');
        }
    };

    window.logout = function (skipConfirm = false) {
        if (!skipConfirm && !confirm('Sign out of Sehat Saathi?')) return;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('user_email');
        window.location.href = 'login.html';
    };
})();

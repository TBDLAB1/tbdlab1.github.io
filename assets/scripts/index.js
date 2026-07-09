function handleScroll() {
    window.__store__ = window.__store__ || {};
    var top = window.scrollY;
    var threshold = 30;
    // Use classList (not className=) so other state like nav-open survives.
    if (!window.__store__.scrolled && top > threshold) {
        window.__store__.scrolled = true;
        document.getElementById('header').classList.add('header-scrolled');
    } else if (window.__store__.scrolled && top <= threshold) {
        window.__store__.scrolled = false;
        document.getElementById('header').classList.remove('header-scrolled');
    }
}
window.addEventListener('scroll', handleScroll);

// Mobile: toggle the menu panel open/closed with the hamburger button.
function setupNavToggle() {
    var header = document.getElementById('header');
    var toggle = header && header.querySelector('[data-nav-toggle]');
    if (!header || !toggle) return;
    function setOpen(open) {
        header.classList.toggle('nav-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    toggle.addEventListener('click', function () {
        setOpen(!header.classList.contains('nav-open'));
    });
    // Close the panel after tapping an actual navigation link.
    header.querySelectorAll('.header-menu a').forEach(function (a) {
        a.addEventListener('click', function () { setOpen(false); });
    });
}
setupNavToggle();

// Two-level menu: tap/click a dropdown label to toggle its submenu (touch devices).
function setupDropdowns() {
    var dropdowns = document.querySelectorAll('.header-dropdown');
    dropdowns.forEach(function (dropdown) {
        var label = dropdown.querySelector('.header-dropdown-label');
        if (!label) return;
        label.addEventListener('click', function (event) {
            // Let real links (top-level items with a URL) navigate normally.
            if (label.tagName.toLowerCase() === 'a') return;
            event.preventDefault();
            var isOpen = dropdown.classList.contains('open');
            dropdowns.forEach(function (d) { d.classList.remove('open'); });
            if (!isOpen) dropdown.classList.add('open');
        });
    });
    document.addEventListener('click', function (event) {
        if (event.target.closest && event.target.closest('.header-dropdown')) return;
        dropdowns.forEach(function (d) { d.classList.remove('open'); });
    });
}
setupDropdowns();

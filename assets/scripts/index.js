function handleScroll() {
    window.__store__ = window.__store__ || {};
    var top = window.scrollY;
    var threshold = 30;
    if (!window.__store__.scrolled && top > threshold) {
        window.__store__.scrolled = true;
        document.getElementById('header').className = 'header header-scrolled';
    } else if (window.__store__.scrolled && top <= threshold) {
        window.__store__.scrolled = false;
        document.getElementById('header').className = 'header';
    }
}
window.addEventListener('scroll', handleScroll);

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

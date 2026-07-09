function initCarousels() {
    var carousels = document.querySelectorAll('[data-carousel]');
    Array.prototype.forEach.call(carousels, function (carousel) {
        var track = carousel.querySelector('[data-carousel-track]');
        if (!track) return;
        var slides = Array.prototype.slice.call(track.children);
        if (slides.length === 0) return;

        var prev = carousel.querySelector('[data-carousel-prev]');
        var next = carousel.querySelector('[data-carousel-next]');
        var dotsWrap = carousel.querySelector('[data-carousel-dots]');

        var dots = slides.map(function (_, i) {
            var dot = document.createElement('button');
            dot.className = 'carousel-dot';
            dot.setAttribute('aria-label', 'Go to slide ' + (i + 1));
            dot.addEventListener('click', function () { goTo(i); });
            if (dotsWrap) dotsWrap.appendChild(dot);
            return dot;
        });

        function currentIndex() {
            var idx = Math.round(track.scrollLeft / track.clientWidth);
            return Math.max(0, Math.min(slides.length - 1, idx));
        }
        function goTo(i) {
            i = Math.max(0, Math.min(slides.length - 1, i));
            track.scrollTo({ left: i * track.clientWidth, behavior: 'smooth' });
        }
        function update() {
            var idx = currentIndex();
            dots.forEach(function (d, i) { d.classList.toggle('active', i === idx); });
            if (prev) prev.disabled = idx === 0;
            if (next) next.disabled = idx === slides.length - 1;
        }

        if (prev) prev.addEventListener('click', function () { goTo(currentIndex() - 1); });
        if (next) next.addEventListener('click', function () { goTo(currentIndex() + 1); });
        track.addEventListener('scroll', function () { window.requestAnimationFrame(update); });
        window.addEventListener('resize', update);

        // Single-slide albums don't need controls.
        if (slides.length < 2) {
            if (prev) prev.style.display = 'none';
            if (next) next.style.display = 'none';
        }
        update();
    });
}

if (document.readyState !== 'loading') {
    initCarousels();
} else {
    document.addEventListener('DOMContentLoaded', initCarousels);
}

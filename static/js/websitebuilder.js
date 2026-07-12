document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-wb-carousel]").forEach((carousel) => {
        const items = Array.from(carousel.querySelectorAll(".carousel-item"));
        const indicators = Array.from(carousel.querySelectorAll("[data-wb-slide-to]"));
        const prev = carousel.querySelector("[data-wb-slide='prev']");
        const next = carousel.querySelector("[data-wb-slide='next']");
        if (items.length <= 1) return;

        let activeIndex = Math.max(items.findIndex((item) => item.classList.contains("active")), 0);
        let timer = null;

        function showSlide(index) {
            activeIndex = (index + items.length) % items.length;
            items.forEach((item, itemIndex) => item.classList.toggle("active", itemIndex === activeIndex));
            indicators.forEach((indicator, indicatorIndex) => {
                const isActive = indicatorIndex === activeIndex;
                indicator.classList.toggle("active", isActive);
                indicator.setAttribute("aria-current", isActive ? "true" : "false");
            });
        }

        function start() {
            stop();
            timer = window.setInterval(() => showSlide(activeIndex + 1), 6000);
        }

        function stop() {
            if (timer) window.clearInterval(timer);
        }

        indicators.forEach((indicator) => {
            indicator.addEventListener("click", () => {
                showSlide(Number(indicator.dataset.wbSlideTo || 0));
                start();
            });
        });
        if (prev) prev.addEventListener("click", () => {
            showSlide(activeIndex - 1);
            start();
        });
        if (next) next.addEventListener("click", () => {
            showSlide(activeIndex + 1);
            start();
        });
        carousel.addEventListener("mouseenter", stop);
        carousel.addEventListener("mouseleave", start);
        start();
    });
});

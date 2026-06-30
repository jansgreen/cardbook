document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.querySelector("[data-menu-toggle]");
    const menu = document.querySelector("[data-menu]");
    if (menuButton && menu) {
        menuButton.addEventListener("click", () => menu.classList.toggle("open"));
    }

    const fadeEls = document.querySelectorAll(".fade-in");
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) entry.target.classList.add("visible");
        });
    }, { threshold: 0.12 });
    fadeEls.forEach((el) => observer.observe(el));

    document.querySelectorAll("[data-share]").forEach((button) => {
        button.addEventListener("click", async () => {
            if (navigator.share) {
                await navigator.share({ title: document.title, url: window.location.href });
            } else {
                await navigator.clipboard.writeText(window.location.href);
                button.textContent = "Copiado";
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.querySelector(".dashboard-sidebar");
    if (button && sidebar) {
        button.addEventListener("click", () => sidebar.classList.toggle("open"));
    }

    document.querySelectorAll("img[data-fallback-text]").forEach((image) => {
        image.addEventListener("error", () => {
            const fallback = document.createElement("span");
            fallback.className = "image-fallback";
            fallback.textContent = (image.dataset.fallbackText || "CB").slice(0, 2).toUpperCase();
            image.replaceWith(fallback);
        }, { once: true });
    });
});

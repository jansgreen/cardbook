document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.querySelector("[data-menu-toggle]");
    const menu = document.querySelector("[data-menu]");
    if (menuButton && menu) {
        menuButton.addEventListener("click", () => menu.classList.toggle("open"));
    }

    const fadeEls = document.querySelectorAll(".fade-in");
    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) entry.target.classList.add("visible");
            });
        }, { threshold: 0.12 });
        fadeEls.forEach((el) => observer.observe(el));
    } else {
        fadeEls.forEach((el) => el.classList.add("visible"));
    }

    document.querySelectorAll("[data-share]").forEach((button) => {
        button.addEventListener("click", async () => {
            const payload = {
                title: button.dataset.shareTitle || document.title,
                text: button.dataset.shareText || "",
                url: button.dataset.shareUrl || window.location.href,
            };
            try {
                if (window.CardbookNativeShare) {
                    window.CardbookNativeShare(payload.title, payload.text, payload.url);
                    return;
                }
                if (window.CardbookAndroid && window.CardbookAndroid.share) {
                    window.CardbookAndroid.share(payload.title, payload.text, payload.url);
                    return;
                }
                if (navigator.share) {
                    await navigator.share(payload);
                    return;
                }
                await navigator.clipboard.writeText(payload.url);
                button.textContent = "Copiado";
            } catch (error) {
                try {
                    await navigator.clipboard.writeText(payload.url);
                    button.textContent = "Copiado";
                } catch (ignored) {
                    button.textContent = "No disponible";
                }
            }
        });
    });

    document.querySelectorAll("img[data-fallback-text]").forEach((image) => {
        image.addEventListener("error", () => {
            const fallback = document.createElement("span");
            fallback.className = `${image.className || ""} image-fallback`.trim();
            fallback.textContent = (image.dataset.fallbackText || "CB").slice(0, 2).toUpperCase();
            image.replaceWith(fallback);
        }, { once: true });
    });
});

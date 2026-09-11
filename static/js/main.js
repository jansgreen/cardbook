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

    const trackCardClick = (element) => {
        const clickType = element.dataset.trackClick;
        const clickUrl = element.closest("[data-card-click-url]")?.dataset.cardClickUrl;
        if (!clickType || !clickUrl) return;

        const payload = JSON.stringify({ click_type: clickType });
        if (navigator.sendBeacon) {
            const body = new Blob([payload], { type: "application/json" });
            navigator.sendBeacon(clickUrl, body);
            return;
        }
        fetch(clickUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: payload,
            keepalive: true,
        }).catch(() => {});
    };

    document.querySelectorAll("[data-track-click]").forEach((element) => {
        if (element.hasAttribute("data-contact-reveal")) return;
        element.addEventListener("click", () => trackCardClick(element));
    });

    document.querySelectorAll("[data-contact-reveal]").forEach((button) => {
        button.addEventListener("click", () => {
            const panel = button.closest(".contact-reveal-panel");
            const targetId = button.dataset.contactTarget || "";
            const escapedTargetId = window.CSS && CSS.escape ? CSS.escape(targetId) : targetId.replace(/"/g, "");
            const targetSelector = targetId ? `#${escapedTargetId}` : "";
            const content = (targetSelector ? document.querySelector(targetSelector) : null)
                || panel?.querySelector(".contact-reveal-content")
                || button.nextElementSibling;
            if (!content) return;

            const isHidden = content.hasAttribute("hidden");
            if (isHidden) trackCardClick(button);
            content.toggleAttribute("hidden", !isHidden);
            button.setAttribute("aria-expanded", isHidden ? "true" : "false");
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

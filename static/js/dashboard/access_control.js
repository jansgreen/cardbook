document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll("[data-tab]");
    const panels = document.querySelectorAll(".access-tab-panel");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.tab;

            tabs.forEach((item) => item.classList.remove("is-active"));
            panels.forEach((panel) => panel.classList.remove("is-active"));

            tab.classList.add("is-active");
            document.getElementById(`tab-${target}`)?.classList.add("is-active");
        });
    });

    const openButtons = document.querySelectorAll("[data-modal-open]");
    const closeButtons = document.querySelectorAll("[data-modal-close]");

    openButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const modal = document.getElementById(button.dataset.modalOpen);
            modal?.classList.add("is-open");
            modal?.setAttribute("aria-hidden", "false");
        });
    });

    closeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const modal = button.closest(".access-modal");
            modal?.classList.remove("is-open");
            modal?.setAttribute("aria-hidden", "true");
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            document.querySelectorAll(".access-modal.is-open").forEach((modal) => {
                modal.classList.remove("is-open");
                modal.setAttribute("aria-hidden", "true");
            });
        }
    });
});

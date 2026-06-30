document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.querySelector(".dashboard-sidebar");
    if (button && sidebar) {
        button.addEventListener("click", () => sidebar.classList.toggle("open"));
    }
});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-finance-chart]").forEach((chart) => {
        chart.setAttribute("data-ready", "true");
    });
});

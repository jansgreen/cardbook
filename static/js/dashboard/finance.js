document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".finance-segments button").forEach((button) => {
        button.addEventListener("click", () => {
            button.parentElement.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
        });
    });
});

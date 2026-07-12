(function () {
    const form = document.querySelector("[data-post-form]");
    if (!form) return;

    const titleInput = form.querySelector(".post-title-input");
    const descriptionInput = form.querySelector(".post-description-input");
    const typeSelect = form.querySelector("[data-post-type]");
    const fileInput = form.querySelector("[data-post-file]");
    const uploadBox = form.querySelector("[data-upload-box]");
    const fileName = form.querySelector("[data-file-name]");
    const uploadHelp = form.querySelector("[data-upload-help]");
    const remaining = document.querySelector("[data-remaining-chars]");
    const progress = document.querySelector("[data-character-progress]");
    const descriptionError = form.querySelector("[data-description-error]");
    const postSearch = document.querySelector("[data-post-search]");

    function updateCounter(input, selector, max) {
        if (!input) return;
        const counter = form.querySelector(selector);
        if (input.value.length > max) input.value = input.value.slice(0, max);
        if (counter) counter.textContent = input === descriptionInput ? `${input.value.length}/${max} caracteres` : `${input.value.length}/${max}`;
    }

    function updateDescriptionState() {
        if (!descriptionInput) return;
        const max = 200;
        if (descriptionInput.value.length > max) descriptionInput.value = descriptionInput.value.slice(0, max);
        const used = descriptionInput.value.length;
        const left = Math.max(max - used, 0);
        if (remaining) remaining.textContent = left;
        if (progress) progress.style.width = `${Math.min((used / max) * 100, 100)}%`;
        if (descriptionError) descriptionError.textContent = left === 0 ? "Limite alcanzado" : "";
        updateCounter(descriptionInput, "[data-counter-for='caption']", max);
    }

    function updateAcceptedFileType() {
        if (!typeSelect || !fileInput) return;
        const isVideo = typeSelect.value === "video";
        fileInput.accept = isVideo ? "video/mp4,video/*" : "image/png,image/jpeg,image/jpg";
        if (uploadHelp) uploadHelp.textContent = isVideo ? "MP4 hasta 50MB" : "PNG, JPG hasta 10MB";
    }

    function validateFile(file) {
        if (!file || !typeSelect) return true;
        const isVideo = typeSelect.value === "video";
        const max = isVideo ? 50 * 1024 * 1024 : 10 * 1024 * 1024;
        const validType = isVideo ? file.type.startsWith("video/") : file.type.startsWith("image/");
        if (!validType) {
            alert(isVideo ? "Selecciona un archivo de video." : "Selecciona una imagen PNG o JPG.");
            fileInput.value = "";
            return false;
        }
        if (file.size > max) {
            alert(isVideo ? "El video no puede superar 50MB." : "La imagen no puede superar 10MB.");
            fileInput.value = "";
            return false;
        }
        return true;
    }

    titleInput?.addEventListener("input", () => updateCounter(titleInput, "[data-counter-for='title']", 100));
    descriptionInput?.addEventListener("input", updateDescriptionState);
    typeSelect?.addEventListener("change", updateAcceptedFileType);

    fileInput?.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file && validateFile(file) && fileName) fileName.textContent = file.name;
    });

    uploadBox?.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadBox.classList.add("dragover");
    });
    uploadBox?.addEventListener("dragleave", () => uploadBox.classList.remove("dragover"));
    uploadBox?.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadBox.classList.remove("dragover");
        const file = event.dataTransfer.files[0];
        if (!file || !validateFile(file)) return;
        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
        if (fileName) fileName.textContent = file.name;
    });

    document.querySelectorAll("[data-post-media-choice]").forEach((button) => {
        button.addEventListener("click", () => {
            if (!typeSelect || !fileInput) return;
            typeSelect.value = button.dataset.postMediaChoice;
            updateAcceptedFileType();
            fileInput.click();
        });
    });

    postSearch?.addEventListener("input", () => {
        const query = postSearch.value.trim().toLowerCase();
        document.querySelectorAll("[data-post-card]").forEach((card) => {
            card.style.display = card.dataset.title.includes(query) ? "" : "none";
        });
    });

    updateCounter(titleInput, "[data-counter-for='title']", 100);
    updateDescriptionState();
    updateAcceptedFileType();
})();

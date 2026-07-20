document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ai-agent-form textarea").forEach((textarea) => {
    textarea.addEventListener("input", () => {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    });
  });

  const guideDataNode = document.getElementById("ai-guide-data");
  const widget = document.querySelector("[data-ai-guide]");
  if (!guideDataNode || !widget) {
    return;
  }

  let guide;
  try {
    guide = JSON.parse(guideDataNode.textContent);
  } catch (error) {
    return;
  }

  if (!guide.enabled || !Array.isArray(guide.steps) || guide.steps.length === 0) {
    return;
  }

  const storageKey = `cardbook-guide:${guide.route}`;
  const panel = widget.querySelector("[data-guide-panel]");
  const openButton = widget.querySelector("[data-guide-open]");
  const closeButton = widget.querySelector("[data-guide-close]");
  const titleNode = widget.querySelector("[data-guide-title]");
  const bodyNode = widget.querySelector("[data-guide-body]");
  const counterNode = widget.querySelector("[data-guide-counter]");
  const progressNode = widget.querySelector("[data-guide-progress]");
  const prevButton = widget.querySelector("[data-guide-prev]");
  const nextButton = widget.querySelector("[data-guide-next]");
  const doneButton = widget.querySelector("[data-guide-done]");
  let stepIndex = 0;
  let highlightedElement = null;

  const clearHighlight = () => {
    if (highlightedElement) {
      highlightedElement.removeAttribute("data-guide-highlight");
      highlightedElement = null;
    }
  };

  const highlightStepTarget = (step) => {
    clearHighlight();
    if (!step.selector) {
      return;
    }
    const target = document.querySelector(step.selector);
    if (!target) {
      return;
    }
    highlightedElement = target;
    highlightedElement.setAttribute("data-guide-highlight", "true");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  const renderStep = () => {
    const step = guide.steps[stepIndex];
    titleNode.textContent = step.title || guide.title;
    bodyNode.textContent = step.body || guide.intro;
    counterNode.textContent = `${stepIndex + 1}/${guide.steps.length}`;
    progressNode.style.width = `${((stepIndex + 1) / guide.steps.length) * 100}%`;
    prevButton.disabled = stepIndex === 0;
    nextButton.textContent = stepIndex === guide.steps.length - 1 ? "Finalizar" : "Siguiente";
    highlightStepTarget(step);
  };

  const openGuide = () => {
    widget.hidden = false;
    panel.hidden = false;
    renderStep();
  };

  const closeGuide = () => {
    panel.hidden = true;
    clearHighlight();
  };

  const completeGuide = () => {
    localStorage.setItem(storageKey, "done");
    closeGuide();
  };

  widget.hidden = false;
  if (localStorage.getItem(storageKey) !== "done") {
    window.setTimeout(openGuide, 700);
  }

  openButton.addEventListener("click", openGuide);
  closeButton.addEventListener("click", closeGuide);
  doneButton.addEventListener("click", completeGuide);
  prevButton.addEventListener("click", () => {
    if (stepIndex > 0) {
      stepIndex -= 1;
      renderStep();
    }
  });
  nextButton.addEventListener("click", () => {
    if (stepIndex >= guide.steps.length - 1) {
      completeGuide();
      return;
    }
    stepIndex += 1;
    renderStep();
  });
});

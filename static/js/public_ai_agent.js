document.addEventListener("DOMContentLoaded", () => {
  const widget = document.querySelector("[data-public-ai-agent]");
  if (!widget) {
    return;
  }

  const panel = widget.querySelector("[data-ai-panel]");
  const openButton = widget.querySelector("[data-ai-open]");
  const closeButton = widget.querySelector("[data-ai-close]");
  const form = widget.querySelector("[data-ai-form]");
  const leadForm = widget.querySelector("[data-ai-lead-form]");
  const leadOpenButton = widget.querySelector("[data-ai-lead-open]");
  const leadCloseButton = widget.querySelector("[data-ai-lead-close]");
  const input = widget.querySelector("[data-ai-input]");
  const submitButton = widget.querySelector("[data-ai-submit]");
  const messages = widget.querySelector("[data-ai-messages]");
  const statusNode = widget.querySelector("[data-ai-status]");
  const endpoint = widget.dataset.endpoint;
  const agentId = widget.dataset.agentId;
  let isSending = false;

  const appendMessage = (role, content) => {
    const node = document.createElement("div");
    node.className = `wb-ai-message ${role}`;
    node.textContent = content;
    messages.appendChild(node);
    messages.scrollTop = messages.scrollHeight;
  };

  const setStatus = (message = "") => {
    if (!statusNode) {
      return;
    }
    statusNode.textContent = message;
    statusNode.hidden = !message;
  };

  openButton.addEventListener("click", () => {
    panel.hidden = false;
    input.focus();
  });

  closeButton.addEventListener("click", () => {
    panel.hidden = true;
  });

  const openLeadForm = () => {
    if (leadForm) {
      leadForm.hidden = false;
      leadForm.querySelector("input, textarea")?.focus();
    }
  };

  const closeLeadForm = () => {
    if (leadForm) {
      leadForm.hidden = true;
    }
  };

  leadOpenButton?.addEventListener("click", openLeadForm);
  leadCloseButton?.addEventListener("click", closeLeadForm);

  const sendQuestion = async (message) => {
    if (!message) {
      return;
    }
    if (isSending) {
      return;
    }
    isSending = true;
    submitButton.disabled = true;
    input.disabled = true;
    setStatus("El asistente esta pensando...");
    appendMessage("user", message);
    input.value = "";

    const body = new URLSearchParams();
    body.append("agent", agentId);
    body.append("message", message);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body,
        credentials: "same-origin",
      });
      const data = await response.json();
      appendMessage("agent", data.success ? data.answer : data.message || "No pude responder ahora mismo.");
      if (data.lead_prompt) {
        appendMessage("agent", "Si quieres, deja tus datos y la empresa podra contactarte directamente.");
        openLeadForm();
      }
    } catch (error) {
      appendMessage("agent", "No pude conectar con el asistente. Revisa tu conexion e intentalo de nuevo.");
    } finally {
      isSending = false;
      submitButton.disabled = false;
      input.disabled = false;
      setStatus("");
      input.focus();
    }
  };

  widget.querySelectorAll("[data-ai-suggestion]").forEach((button) => {
    button.addEventListener("click", () => {
      panel.hidden = false;
      sendQuestion(button.dataset.aiSuggestion || button.textContent.trim());
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    await sendQuestion(message);
  });

  leadForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (isSending) {
      return;
    }
    isSending = true;
    setStatus("Guardando tus datos...");
    const body = new URLSearchParams(new FormData(leadForm));
    body.append("agent", agentId);
    body.append("intent", "lead");

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body,
        credentials: "same-origin",
      });
      const data = await response.json();
      appendMessage("agent", data.success ? data.answer : data.message || "No pude guardar tus datos ahora mismo.");
      if (data.success) {
        leadForm.reset();
        closeLeadForm();
      }
    } catch (error) {
      appendMessage("agent", "No pude guardar tus datos. Intentalo otra vez en unos minutos.");
    } finally {
      isSending = false;
      setStatus("");
    }
  });
});

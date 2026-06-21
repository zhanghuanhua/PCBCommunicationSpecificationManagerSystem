document.addEventListener("click", (event) => {
  const addButton = event.target.closest("[data-add-parameter-row]");
  if (addButton) {
    const section = addButton.closest("[data-batch-parameter-section]");
    const list = section?.querySelector("[data-parameter-list]");
    const templateId = section?.dataset.rowTemplateId;
    const template = templateId ? document.getElementById(templateId) : null;
    if (list && template) {
      list.append(template.content.cloneNode(true));
      updateRemoveButtons(list);
      updateRowIndexes(list);
      bindAutoGrowTextareas(list);
    }
    return;
  }

  const removeButton = event.target.closest("[data-remove-parameter-row]");
  if (removeButton) {
    const row = removeButton.closest("[data-parameter-row]");
    const list = removeButton.closest("[data-parameter-list]");
    if (row && list && list.querySelectorAll("[data-parameter-row]").length > 1) {
      row.remove();
      updateRemoveButtons(list);
      updateRowIndexes(list);
    }
  }
});

document.querySelectorAll("[data-parameter-list]").forEach((list) => {
  updateRemoveButtons(list);
  updateRowIndexes(list);
});
bindAutoGrowTextareas(document);

function updateRemoveButtons(list) {
  const rows = list.querySelectorAll("[data-parameter-row]");
  rows.forEach((row) => {
    const button = row.querySelector("[data-remove-parameter-row]");
    if (button) {
      button.disabled = rows.length <= 1;
    }
  });
}

function updateRowIndexes(list) {
  list.querySelectorAll("[data-row-index]").forEach((cell, index) => {
    cell.textContent = String(index + 1);
  });
}

function bindAutoGrowTextareas(scope) {
  scope.querySelectorAll(".auto-grow-textarea").forEach((textarea) => {
    if (textarea.dataset.autoGrowBound === "1") {
      autoGrow(textarea);
      return;
    }
    textarea.dataset.autoGrowBound = "1";
    autoGrow(textarea);
    textarea.addEventListener("input", () => autoGrow(textarea));
  });
}

function autoGrow(textarea) {
  textarea.style.height = "34px";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 140)}px`;
}

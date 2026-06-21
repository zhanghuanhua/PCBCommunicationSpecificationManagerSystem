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
    }
  }
});

document.querySelectorAll("[data-parameter-list]").forEach(updateRemoveButtons);

function updateRemoveButtons(list) {
  const rows = list.querySelectorAll("[data-parameter-row]");
  rows.forEach((row) => {
    const button = row.querySelector("[data-remove-parameter-row]");
    if (button) {
      button.disabled = rows.length <= 1;
    }
  });
}

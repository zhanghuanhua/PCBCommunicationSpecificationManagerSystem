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
      ensureRowKeys(list);
      bindAutoGrowTextareas(list);
      syncCustomNodeArea(section);
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
      syncCustomNodeArea(removeButton.closest("[data-batch-parameter-section]"));
    }
    return;
  }

  const addNodeButton = event.target.closest("[data-add-node-row]");
  if (addNodeButton) {
    const card = addNodeButton.closest("[data-node-card]");
    const list = card?.querySelector("[data-node-parameter-list]");
    const firstRow = list?.querySelector("[data-node-row]");
    if (list && firstRow) {
      list.append(firstRow.cloneNode(true));
      const newRow = list.querySelector("[data-node-row]:last-child");
      newRow?.querySelectorAll("input:not([type='hidden']), textarea").forEach((input) => {
        input.value = "";
      });
      updateNodeRows(card);
      bindAutoGrowTextareas(card);
    }
    return;
  }

  const removeNodeButton = event.target.closest("[data-remove-node-row]");
  if (removeNodeButton) {
    const card = removeNodeButton.closest("[data-node-card]");
    const list = card?.querySelector("[data-node-parameter-list]");
    const row = removeNodeButton.closest("[data-node-row]");
    if (card && list && row && list.querySelectorAll("[data-node-row]").length > 1) {
      row.remove();
      updateNodeRows(card);
    }
  }
});

document.addEventListener("input", (event) => {
  const target = event.target;
  if (target.matches("[name$='_field_name'], [name$='_custom_data_type']")) {
    syncCustomNodeArea(target.closest("[data-batch-parameter-section]"));
  }
});

document.addEventListener("change", (event) => {
  const target = event.target;
  if (target.matches("[name$='_data_type_choice']")) {
    syncCustomNodeArea(target.closest("[data-batch-parameter-section]"));
  }
});

document.querySelectorAll("[data-parameter-list]").forEach((list) => {
  updateRemoveButtons(list);
  updateRowIndexes(list);
  ensureRowKeys(list);
  syncCustomNodeArea(list.closest("[data-batch-parameter-section]"));
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

function ensureRowKeys(list) {
  list.querySelectorAll("[data-parameter-row]").forEach((row) => {
    const input = row.querySelector("[data-row-key-input]");
    if (input && !input.value) {
      input.value = `row-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
  });
}

function syncCustomNodeArea(section) {
  if (!section) {
    return;
  }
  const nodeArea = section.querySelector("[data-node-area]");
  const nodeList = nodeArea?.querySelector("[data-node-list]");
  const template = nodeArea ? document.getElementById(nodeArea.dataset.nodeTemplateId) : null;
  if (!nodeArea || !nodeList || !template) {
    return;
  }

  const activeParents = new Map();
  section.querySelectorAll("[data-parameter-row]").forEach((row) => {
    const rowKey = row.querySelector("[data-row-key-input]")?.value;
    const fieldName = row.querySelector("[name$='_field_name']")?.value.trim();
    const typeChoice = row.querySelector("[name$='_data_type_choice']")?.value;
    const customType = row.querySelector("[name$='_custom_data_type']")?.value.trim();
    const nodeType = extractNodeType(typeChoice, customType);
    if (rowKey && fieldName && nodeType) {
      activeParents.set(rowKey, { fieldName, customType, nodeType });
    }
  });

  nodeList.querySelectorAll("[data-node-card]").forEach((card) => {
    const parentKey = card.dataset.parentKey;
    if (!activeParents.has(parentKey)) {
      card.hidden = true;
      card.querySelectorAll("input, select, textarea").forEach((input) => {
        input.disabled = true;
      });
      return;
    }
    updateNodeCard(card, activeParents.get(parentKey));
  });

  activeParents.forEach((parent, rowKey) => {
    let card = nodeList.querySelector(`[data-node-card][data-parent-key="${cssEscape(rowKey)}"]`);
    if (!card) {
      nodeList.append(template.content.cloneNode(true));
      card = nodeList.querySelector("[data-node-card]:last-child");
      card.dataset.parentKey = rowKey;
    }
    updateNodeCard(card, parent);
    updateNodeRows(card);
    bindAutoGrowTextareas(card);
  });

  const visibleCards = nodeList.querySelectorAll("[data-node-card]:not([hidden])").length;
  const emptyTip = nodeArea.querySelector("[data-empty-node-tip]");
  if (emptyTip) {
    emptyTip.hidden = visibleCards > 0;
  }
}

function updateNodeCard(card, parent) {
  card.hidden = false;
  card.querySelectorAll("input, select, textarea").forEach((input) => {
    input.disabled = false;
  });
  card.querySelector("[data-node-title]").textContent = `${parent.nodeType} 节点参数`;
  card.querySelector("[data-node-meta]").textContent = `父字段：${parent.fieldName} / 自定义类型：${parent.customType}`;
  card.querySelectorAll("[data-node-parent-input]").forEach((input) => {
    input.value = card.dataset.parentKey;
  });
}

function updateNodeRows(card) {
  const section = card.closest("[data-batch-parameter-section]");
  let parentIndex = "";
  section?.querySelectorAll("[data-parameter-row]").forEach((row) => {
    if (row.querySelector("[data-row-key-input]")?.value === card.dataset.parentKey) {
      parentIndex = row.querySelector("[data-row-index]")?.textContent.trim() || "";
    }
  });
  card.querySelectorAll("[data-node-row]").forEach((row, index) => {
    const indexCell = row.querySelector("[data-node-row-index]");
    if (indexCell) {
      indexCell.textContent = parentIndex ? `${parentIndex}.${index + 1}` : String(index + 1);
    }
    row.querySelectorAll("[data-node-parent-input]").forEach((input) => {
      input.value = card.dataset.parentKey;
    });
  });
  const rows = card.querySelectorAll("[data-node-row]");
  rows.forEach((row) => {
    const button = row.querySelector("[data-remove-node-row]");
    if (button) {
      button.disabled = rows.length <= 1;
    }
  });
}

function extractNodeType(typeChoice, customType) {
  if (typeChoice !== "CUSTOM" || !customType) {
    return "";
  }
  const match = customType.match(/^(?:List|Array)\s*<\s*([^>]+?)\s*>$/i);
  const rawType = match ? match[1] : customType;
  return rawType.trim();
}

function cssEscape(value) {
  if (window.CSS?.escape) {
    return CSS.escape(value);
  }
  return value.replace(/["\\]/g, "\\$&");
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

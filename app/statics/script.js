const toastLiveExample = document.getElementById("toast");

var token = "";
var hostname = "";

const prepend_url = (url) => {
  const isProduction =
    hostname &&
    (hostname.includes("staging-bo.snapp.supply") || hostname.includes("bo.snapp.supply"));
  return isProduction ? `/api-bo${url}` : url;
};

function createToast(message, severity, status = 500, delay = 5000) {
  const toastTemplate = document.getElementById("toastTemplate");
  if (!toastTemplate) {
    console.error("Toast template not found");
    return;
  }
  // Clone and clear the ID to prevent duplicates.
  const toastClone = toastTemplate.cloneNode(true);
  toastClone.removeAttribute("id");

  const severityConfig = {
    warning: { alertClass: "alert-warning", iconClass: "bi-exclamation-triangle-fill" },
    error: { alertClass: "alert-danger", iconClass: "bi-exclamation-triangle-fill", customDelay: 300000 },
    failed: { alertClass: "alert-danger", iconClass: "bi-exclamation-triangle-fill" },
    unknown: { alertClass: "alert-warning", iconClass: "bi-exclamation-triangle-fill" },
    success: { alertClass: "alert-success", iconClass: "bi-check-circle-fill" },
  };

  const config = severityConfig[severity];
  if (!config) {
    console.error(`Invalid severity: ${severity}`);
    return;
  }

  // Set message based on severity.
  const alertMessage = toastClone.querySelector(".alert-message");
  if (alertMessage) {
    alertMessage.textContent = severity === "success" ? message : `Error ${status}: ${message}`;
  }

  // Apply the configured classes.
  const alertElement = toastClone.querySelector(".alert");
  if (alertElement) {
    alertElement.classList.add(config.alertClass);
  }
  const svgIcon = toastClone.querySelector(".svg-icon");
  if (svgIcon) {
    svgIcon.classList.add(config.iconClass);
  }

  // Use a custom delay if defined.
  const effectiveDelay = config.customDelay || delay;
  const toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) {
    console.error("Toast container not found");
    return;
  }
  toastContainer.appendChild(toastClone);

  const bsToast = new bootstrap.Toast(toastClone, { delay: effectiveDelay });
  bsToast.show();

  // Remove the toast element once hidden.
  toastClone.addEventListener("hidden.bs.toast", () => toastClone.remove());
}

function createOrUpdateToastTask(status, jobName, autohide = false) {
  const toastId = `toast-${jobName}`;
  let toastElement = document.getElementById(toastId);

  if (!toastElement) {
    const toastTemplate = document.getElementById("toastTemplate");
    if (!toastTemplate) {
      console.error("Toast template not found");
      return;
    }
    toastElement = toastTemplate.cloneNode(true);
    toastElement.id = toastId;
    const toastContainer = document.getElementById("toastContainer");
    if (!toastContainer) {
      console.error("Toast container not found");
      return;
    }
    toastContainer.appendChild(toastElement);
  }

  const statusConfig = {
    active: {
      alertClass: "alert-light",
      iconClass: "bi-hourglass-split",
      message: `Job ${jobName} Status: Active`,
      autohide: autohide,
    },
    pending: {
      alertClass: "alert-warning",
      iconClass: "bi-hourglass-split",
      message: `Job ${jobName} Status: Pending`,
      autohide: autohide,
    },
    succeeded: {
      alertClass: "alert-success",
      iconClass: "bi-check2-circle",
      message: `Job ${jobName} Status: Succeeded`,
      autohide: autohide,
    },
    failed: {
      alertClass: "alert-danger",
      iconClass: "bi-exclamation-triangle-fill",
      message: `Job ${jobName} Status: Failed`,
      autohide: autohide,
    },
    unknown: {
      alertClass: "alert-warning",
      iconClass: "bi-exclamation-triangle-fill",
      message: `Job ${jobName} Status: Unknown`,
      autohide: autohide,
    },
  };

  const config = statusConfig[status];
  if (!config) {
    console.error(`Invalid status: ${status}`);
    return;
  }

  // Update alert element classes.
  const alertElement = toastElement.querySelector(".alert");
  if (alertElement) {
    alertElement.className = `alert me-auto d-flex align-items-center justify-content-between mb-0 ${config.alertClass}`;
  }

  // Update icon classes.
  const iconElement = toastElement.querySelector(".svg-icon");
  if (iconElement) {
    iconElement.className = `svg-icon bi h4 me-2 my-auto ${config.iconClass}`;
  }

  // Update the message.
  const messageElement = toastElement.querySelector(".alert-message");
  if (messageElement) {
    messageElement.textContent = config.message;
  }

  const bsToast = new bootstrap.Toast(toastElement, {
    autohide: config.autohide,
  });
  bsToast.show();

  // Remove toast after it is hidden.
  toastElement.addEventListener("hidden.bs.toast", () => toastElement.remove());
}

function inProgress() {
  const wrapper = $("#wrapper");
  const actionButtons = $(".btn");
  const loadOverlay = $("#loadOverlay");

  if (wrapper.length) {
    wrapper.css({ cursor: "not-allowed", "pointer-events": "none" });
  }
  if (actionButtons.length) {
    actionButtons.prop("disabled", true).addClass("disabled");
  }
  if (loadOverlay.length) {
    loadOverlay.css("display", "flex");
  }
}

function finishedProgress() {
  const wrapper = $("#wrapper");
  const actionButtons = $(".btn");
  const loadOverlay = $("#loadOverlay");

  if (wrapper.length) {
    wrapper.css({ cursor: "", "pointer-events": "" });
  }
  if (actionButtons.length) {
    actionButtons.prop("disabled", false).removeClass("disabled");
  }
  if (loadOverlay.length) {
    loadOverlay.css("display", "none");
  }
}

function isJSONObject(obj) {
  return Object.prototype.toString.call(obj) === "[object Object]";
}

function handleErrors(status, message) {
  const msgStr = isJSONObject(message) ? JSON.stringify(message) : message;
  createToast(msgStr, "error", status);
  console.error(`Error: ${msgStr}`);
}

function updateSettings() {
  inProgress();
  const orderLock = $("#order-lock-in-days").val();

  // If no change is needed, stop further processing.
  if (orderLock == lastOrderLock) {
    finishedProgress();
    return;
  }

  // Validate the input.
  if (!orderLock || orderLock < 0 || orderLock > 1000) {
    createToast("Need to fill inputs!", "warning", 422);
    finishedProgress();
    return;
  }

  const url = prepend_url("/devops-tools/v1/order/lock/edit");
  $.ajax({
    url,
    type: "PUT",
    data: JSON.stringify({ lock: orderLock }),
    headers: {
      "Content-Type": "application/json",
      Authorization: token,
    },
    statusCode: {
      200: (res) => {
        createToast("Order lock Updated.", "success");
        lastOrderLock = orderLock;
      },
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: finishedProgress,
  });
}

function resetSettings() {
  $("#order-lock-in-days").val(lastOrderLock);
}

function responseHandler(res) {
  if (Array.isArray(res.rows)) {
    res.rows.forEach((row) => {
      row.state = selections.includes(row.id);
    });
  }
  return res;
}

function applyTransforms(value, transforms) {
  if (!transforms) return value;
  if (typeof transforms === "string") {
    transforms = [transforms];
  }
  transforms.forEach(fnName => {
    if (typeof window[fnName] === "function") {
      value = window[fnName](value);
    }
  });
  return value;
}

function removeMoneyFormat(str) {
  if (typeof str === "string") {
    return str.replace(/ Toman$/g, "").replace(/,/g, "");
  }
  return str;
}

function removeRateFormat(str) {
  if (typeof str === "string") {
    return str.replace(/\%$/g, "")
  }
  return str;
}

function exportCSV(url) {
  $.ajax({
    url: prepend_url(url),
    type: "GET",
    headers: { Authorization: token },
    xhrFields: {
      responseType: "blob",
    },
    success: (data, status, xhr) => {
      let filename = "";
      const disposition = xhr.getResponseHeader("Content-Disposition");

      if (disposition && disposition.includes("attachment")) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, "");
        }
      }
      if (!filename) {
        filename = "unknown.csv";
      }
      const bom = new Uint8Array([0xef, 0xbb, 0xbf]);
      const blob = new Blob([bom, data], { type: "text/csv;charset=utf-8" });
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
  });
}

function ajaxEdit(endpoint, data, successMsgPrefix, successCallback) {
  const url = prepend_url(endpoint);
  inProgress();
  
  $.ajax({
    url,
    type: "PUT",
    headers: {
      Authorization: token,
      "Content-Type": "application/json",
    },
    data: JSON.stringify(data),
    statusCode: {
      200: (res) => {
        createToast(`${successMsgPrefix} ${res.id} updated.`, "success", res.status);
        if (typeof successCallback === "function") {
          successCallback(res);
        }
        $("#table").bootstrapTable("refresh");
      },
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: finishedProgress,
  });
}

function ajaxDelete(endpoint, rowId) {
  const url = prepend_url(endpoint + rowId);
  inProgress();
  $.ajax({
    url,
    type: "DELETE",
    headers: { Authorization: token,
      "Content-Type": "application/json",
    },
    success: (res) => {
      createToast("Record deleted successfully.", "success");
      $table.bootstrapTable("refresh");
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: finishedProgress,
  });
}

function ajaxAddRecord(endpoint, data) {
  const url = prepend_url(endpoint);
  inProgress();
  $.ajax({
    url,
    type: "POST",
    headers: {
      Authorization: token,
      "Content-Type": "application/json",
    },
    data: JSON.stringify(data),
    success: (res) => {
      createToast("Record added successfully.", "success");
      $table.bootstrapTable("refresh");
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: finishedProgress,
  });
}

function ajaxEditProductTaxAndMoadian(productID) {
  const tax_rate = document.getElementById("editTaxRate").value;
  const moadian_product_id = document.getElementById("editMoadianProductId").value;
  
  // Build data object; if tax_rate is empty, send null.
  const data = tax_rate === ""
    ? { tax_rate: null, moadian_product_id }
    : { tax_rate, moadian_product_id };

  ajaxEdit(`/devops-tools/v1/products/tax_and_moadian/${productID}`, data, "Product");
}

function ajaxEditProductsDailyPurchased(ID) {
  const productID   = document.getElementById("editProductID").value;
  const date        = document.getElementById("editDate").value;
  const price       = document.getElementById("editPrice").value;
  const count       = document.getElementById("editCount").value;
  const description = document.getElementById("editDescription").value;
  
  const data = { product_id: productID, date, price, count, description };
  
  ajaxEdit(`/devops-tools/v1/products/products_daily_purchased/${ID}`, data, "Product Daily Purchased");
}

function ajaxRequestList(endpoint, params, rowMapper) {
  const url = prepend_url(endpoint);
  $.ajax({
    url: url + "?" + $.param(params.data),
    type: "GET",
    headers: { Authorization: token },
    statusCode: {
      200: (res) => {
        if (Array.isArray(res.rows)) {
          if (typeof rowMapper === "function") {
            res.rows = res.rows.map(rowMapper);
          }
        } else {
          console.error("Response rows are missing or not an array");
        }
        params.success(res);
      },
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
  });
}

function ajaxRequestProductTaxMoadian(params) {
  const endpoint = "/devops-tools/v1/products/tax_and_moadian/list";
  const rowMapper = (row) => {
    row.tax_rate = row.tax_rate !== null ? row.tax_rate + "%" : "Not Defined";
    row.moadian_product_id = row.moadian_product_id !== "" ? row.moadian_product_id : "Not Defined";
    row.state = row.state === true ? "Online" : "Offline";
    row.actions = `
      <button class="btn btn-sm btn-primary open-modal-edit-btn" data-id="${row.id}">
        <i class="bi bi-pen h6"></i> Edit
      </button>`;
    return row;
  };

  ajaxRequestList(endpoint, params, rowMapper);
}

function ajaxRequestProductsDailyPurchased(params) {
  const endpoint = "/devops-tools/v1/products/products_daily_purchased/list";
  const rowMapper = (row) => {
    row.product_id = row.product_id !== null ? row.product_id : "Not Defined";
    row.product_name = row.product_name !== null ? row.product_name : "Not Defined";
    row.date = row.date !== null ? row.date : "Not Defined";
    row.price = row.price !== null ? row.price.toLocaleString() + " Toman" : "Not Defined";
    row.count = row.count !== null ? row.count : "Not Defined";
    row.description = row.description !== null ? row.description : "Not Defined";
    row.actions = `
      <button class="btn btn-sm btn-primary open-modal-edit-btn my-1" data-id="${row.id}">
        <i class="bi bi-pen h6"></i> Edit
      </button>
      <button class="btn btn-sm btn-danger open-modal-delete-btn my-1" data-id="${row.id}">
        <i class="bi bi-trash h6"></i> Delete
      </button>`;
    return row;
  };

  ajaxRequestList(endpoint, params, rowMapper);
}

function ajaxRequestGetOrderLock() {
  const url = prepend_url("/devops-tools/v1/order/lock");
  $.ajax({
    url,
    type: "GET",
    headers: { Authorization: token },
  })
    .done((res) => {
      $("#order-lock-in-days").val(res.lock);
      lastOrderLock = res.lock;
    })
    .fail((jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    });
}

function syncAggregationCreate(type) {
  const url = prepend_url("/devops-tools/v1/kubernetes/jobs/aggregation/create");
  if (!confirm("Are you sure you want to sync this table?")) return;

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: token,
    },
    body: JSON.stringify({ type }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.Status === "Created") {
        createOrUpdateToastTask("active", data.Job);
        checkJobStatus("/devops-tools/v1/kubernetes/jobs/aggregation/status/", data.Job);
      } else {
        console.error("Job creation failed:", data);
      }
    })
    .catch((error) => console.error("Error:", error));
}

function syncAccess() {
  const url = prepend_url("/devops-tools/v1/kubernetes/jobs/access/create");
  if (!confirm("Are you sure you want to sync this table?")) return;

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: token,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.Status === "Created") {
        createOrUpdateToastTask("active", data.Job);
        checkJobStatus("/devops-tools/v1/kubernetes/jobs/access/status/", data.Job);
      } else {
        console.error("Job creation failed:", data);
      }
    })
    .catch((error) => console.error("Error:", error));
}

function checkJobStatus(endpoint, jobName) {
  const statusUrl = prepend_url(endpoint) + jobName;
  
  fetch(statusUrl, { headers: { Authorization: token } })
    .then((response) => response.json())
    .then((data) => {
      if (data && data.status) {
        const status = data.status.toLowerCase();
        if (status === "pending") {
          createOrUpdateToastTask("pending", jobName);
        } else if (status === "succeeded") {
          createOrUpdateToastTask("succeeded", jobName, 5000);
          createToast(`Job ${jobName} finished with status Success.`, "success", "Task", 9999999999);
          console.log(`Job ${jobName} succeeded. Stopping further requests.`);
          return;
        } else if (status === "failed") {
          createOrUpdateToastTask("failed", jobName, 5000);
          createToast(`Job ${jobName} Failed.`, "error", data.error, 9999999999);
          console.log(`Job ${jobName} failed: ${data.error}. Stopping further requests.`);
          return;
        } else if (status === "unknown") {
          createOrUpdateToastTask("unknown", jobName, 5000);
          createToast(`Job ${jobName} finished with status Unknown.`, "warning", "Task", 9999999999);
          console.log(`Job ${jobName} is unknown. Stopping further requests.`);
          return;
        } else {
          createOrUpdateToastTask("active", jobName);
        }
      } else {
        console.error("Invalid response format or missing 'status' key.");
      }
      setTimeout(() => checkJobStatus(endpoint, jobName), 5000);
    })
    .catch((error) => {
      console.error("Error:", error);
      setTimeout(() => checkJobStatus(endpoint, jobName), 5000);
    });
}

const getCurrentDateTime = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${year}${month}${day}${hours}${minutes}`;
};

function getMonitorBoolMetrics(endpoint) {
  inProgress();
  const url = prepend_url("/devops-tools/v1/monitor/bool/") + endpoint;
  
  $.ajax({
    url,
    method: "GET",
    headers: { Authorization: token },
    success: (data, textStatus, jqXHR) => {
      const contentType = jqXHR.getResponseHeader("Content-Type");
      if (contentType && contentType.includes("application/json")) {
        const $target = $("#" + endpoint);
        $target.empty();
        Object.keys(data).forEach((key) => {
          const value = data[key];
          const colorClass = value ? "btn-success" : "btn-danger";
          const buttonHtml = `
            <div class="col-4 mb-3 px-1">
              <div class="row mx-1 h-100">
                <button class="btn btn-lg btn-not-clickable ${colorClass} col-12">${key}</button>
              </div>
            </div>
          `;
          $target.append(buttonHtml);
        });
      } else {
        handleErrors(406, { message: "Response is not in JSON format" });
      }
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: finishedProgress,
  });
}

function ImportCSV(url, checkJobStatusUrl) {
  inProgress();

  const file = csvFile && csvFile.files[0];
  const taskID = getCurrentDateTime();

  if (!file) {
    createToast("No CSV file selected!", "warning", 422);
    finishedProgress();
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const fullUrl = prepend_url(url + taskID);

  $.ajax({
    url: fullUrl,
    type: "POST",
    data: formData,
    contentType: false,
    processData: false,
    headers: { Authorization: token },
    statusCode: {
      200: (res) => {
        createToast("Product CSV file uploaded. Importing in process.", "success");
        checkJobStatus(checkJobStatusUrl, taskID);
      },
    },
    error: (jqXHR) => {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: () => {
      finishedProgress();
      if (fileInput) fileInput.value = "";
    },
  });
}

function ajaxRequestAceessListTable(params) {
  const url = prepend_url("/devops-tools/v1/access/endpoint/list")

  const pageNumber = (params.data.offset / params.data.limit) + 1;
  const pageSize = params.data.limit;
  const searchTerm = params.data.search;
  $.ajax({
      url: url,
      type: 'GET',
      headers: {
        Authorization: token,
      },
      data: {
          page: pageNumber,
          size: pageSize,
          search: searchTerm
      },
      success: function (res) {
          params.success({
              total: res.total,
              rows: res.items
          });
      },
      error: function (jqXHR, status, error) {
          console.error("Error loading data:", error);
          params.error(error);
      }
  });
}

function ajaxRequestPermissionTable(params) {
  const url = prepend_url("/devops-tools/v1/access/permissions/list")

  const pageNumber = (params.data.offset / params.data.limit) + 1;
  const pageSize = params.data.limit;
  const searchTerm = params.data.search;


  $.ajax({
      url: url,
      type: 'GET',
      headers: {
        Authorization: token,
      },
      data: {
          page: pageNumber,
          size: pageSize,
          search: searchTerm
      },
      success: function (res) {
          params.success({
              total: res.total,
              rows: res.items
          });
      },
      error: function (jqXHR, status, error) {
          console.error("Error loading data:", error);
          params.error(error);
      }
  });
}

function fetchAllPermissions(permissionSelect) {
  const url = prepend_url("/devops-tools/v1/access/permissions/list")
  const params = {
      page: 1,
      size: 100,
  };

  $.ajax({
      url: url,
      type: 'GET',
      headers: {
        Authorization: token,
      },
      data: params,
      success: function (res) {
          const permissions = res.items;

          permissionSelect.clearChoices();

          permissions.forEach(permission => {
              permissionSelect.setChoices([{
                  value: permission.id,
                  label: permission.label,
                  selected: false,
                  disabled: false,
              }], 'value', 'label', false);

          });

      },
      error: function (jqXHR, status, error) {
          console.error("Error loading data:", error);
      }
  });
}

function domLoaded() {
  const permissionSelect = new Choices('#editPermissionIdsAccessTable', {
      removeItemButton: true,
      searchEnabled: true,
      placeholderValue: 'Select permissions',
      noResultsText: 'No permissions found',
      noChoicesText: 'No more permissions to load',
  });

  fetchAllPermissions(permissionSelect);

  const searchInput = document.querySelector('.choices__input--cloned');
  searchInput.addEventListener('input', function (event) {
      const searchTerm = event.target.value.toLowerCase();
      const filteredChoices = permissionSelect.getChoices().filter(choice => {
          return choice.label.toLowerCase().includes(searchTerm);
      });

      permissionSelect.clearChoices();
      permissionSelect.setChoices(filteredChoices, 'value', 'label', true);
  });

  document.getElementById('saveChangesButtonAccessTable').addEventListener('click', function () {

    const mode = this.dataset.mode;
    const ruleId = document.getElementById('editIdAccessTable').value || null;
    const slug = document.getElementById('editSlugAccessTable').value;
    const path = document.getElementById('editPathAccessTable').value;
    const permissionIds = permissionSelect.getValue(true)
    const method = document.getElementById('editMethodAccessTable').value;
    const isPublic = document.getElementById('editPublicAccessTable').checked;
    create_url = prepend_url('/devops-tools/v1/access/endpoint/create')
    update_url = prepend_url(`/devops-tools/v1/access/endpoint/update/${ruleId}`)

    const url = mode === 'create' ? create_url : update_url;
    const methodType = mode === 'create' ? 'POST' : 'PUT';

    $.ajax({
        url: url,
        type: methodType,
        headers: {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            Authorization: token,
        },
        data: JSON.stringify({
            id: ruleId,
            slug: slug,
            path: path,
            method: method,
            permission_ids: permissionIds,
            public: isPublic
        }),
        success: function(response) {
            const action = mode === 'create' ? 'created' : 'updated';
            alert(`Access rule ${action} successfully!`);
            $('#accessListTable').bootstrapTable('refresh');
            $('#editModalAccessTable').modal('hide');
        },
        error: function() {
            alert(`Error ${mode === 'create' ? 'creating' : 'updating'} access rule.`);
        }
    });
});
};
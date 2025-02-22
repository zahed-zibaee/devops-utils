const toastLiveExample = document.getElementById("toast");

var token = "";
var hostname = "";

function prepend_url(url) {
  const notlocal = hostname.includes("staging-bo.snapp.supply") || hostname.includes("bo.snapp.supply");
  if (notlocal) {
    return "/api-bo" + url;
  } else {
    return url;
  }
}

function notEmpty(el) {
  return $.trim(el.html());
}

function createToast(message, severity, status = 500, delay = 5000) {
  const toastTemplate = document.getElementById("toastTemplate");
  const toastClone = toastTemplate.cloneNode(true);
  toastClone.id = ""; 

  
  const alertMessage = toastClone.querySelector(".alert-message");
  alertMessage.textContent =
    severity === "success" ? message : `Error ${status}: ${message}`;

  
  const severityConfig = {
    warning: {
      alertClass: "alert-warning",
      iconClass: "bi-exclamation-triangle-fill",
    },
    error: {
      alertClass: "alert-danger",
      iconClass: "bi-exclamation-triangle-fill",
      customDelay: 300000,
    },
    failed: {
      alertClass: "alert-danger",
      iconClass: "bi-exclamation-triangle-fill",
    },
    unknown: {
      alertClass: "alert-warning",
      iconClass: "bi-exclamation-triangle-fill",
    },
    success: {
      alertClass: "alert-success",
      iconClass: "bi-check-circle-fill",
    },
  };

  const config = severityConfig[severity];
  if (!config) {
    console.error(`Invalid severity: ${severity}`);
    return;
  }

  const alertElement = toastClone.querySelector(".alert");
  alertElement.classList.add(config.alertClass);
  toastClone.querySelector(".svg-icon").classList.add(config.iconClass);

  
  const effectiveDelay = config.customDelay || delay;

  
  const toastContainer = document.getElementById("toastContainer");
  toastContainer.appendChild(toastClone);

  const bsToast = new bootstrap.Toast(toastClone, { delay: effectiveDelay });
  bsToast.show();

  
  toastClone.addEventListener("hidden.bs.toast", () => toastClone.remove());
}

function createOrUpdateToastTask(status, jobName, autohide=false) {
  const toastId = `toast-${jobName}`;
  let existingToast = document.getElementById(toastId);

  
  if (!existingToast) {
    const toastTemplate = document.getElementById("toastTemplate");
    existingToast = toastTemplate.cloneNode(true);
    existingToast.id = toastId;

    const toastContainer = document.getElementById("toastContainer");
    toastContainer.appendChild(existingToast);
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

  
  const alertElement = existingToast.querySelector(".alert");
  alertElement.className = `alert me-auto d-flex align-items-center justify-content-between mb-0 ${config.alertClass}`;
  const iconElement = existingToast.querySelector(".svg-icon");
  iconElement.className = `svg-icon bi h4 me-2 my-auto ${config.iconClass}`;
  existingToast.querySelector(".alert-message").textContent = config.message;

  
  const bsToast = new bootstrap.Toast(existingToast, {
    autohide: config.autohide !== false,
  });
  bsToast.show();

  
  existingToast.addEventListener("hidden.bs.toast", () => existingToast.remove());
}

function inProgress() {
  const wrapper = $("#wrapper");
  const actionButtons = $(".btn");
  const loadOverlay = $("#loadOverlay");
  if (notEmpty(wrapper)) {
    wrapper.prop("style", "cursor: not-allowed; pointer-events: none;");
  }
  if (notEmpty(actionButtons)) {
    actionButtons.prop("disabled", true);
    actionButtons.addClass("disabled");
  }
  if (notEmpty(loadOverlay)) {
    loadOverlay.prop("style", "display:flex;")
  }
}

function finishedProgress() {
  const wrapper = $("#wrapper");
  const actionButtons = $(".btn");
  const loadOverlay = $("#loadOverlay");
  if (notEmpty(wrapper)) {
    wrapper.prop("style", "");
  }
  if (notEmpty(actionButtons)) {
    actionButtons.prop("disabled", false);
    actionButtons.removeClass("disabled");
  }
  if (notEmpty(loadOverlay)) {
    loadOverlay.prop("style", "display:none;");
  }
}

function isJSONObject(obj) {
  return obj !== null
      &&
      typeof obj === 'object'
      &&
      obj.constructor === Object;
}

function handleErrors(status, message) {
  if (isJSONObject(message)) {
    createToast(JSON.stringify(message), "error", status);
    console.error("Error :" + JSON.stringify(message));
  } else {
    createToast(message, "error", status);
    console.error("Error :" + message);
  }
}

function updateSettings() {
  inProgress();
  var orderLock = $("#order-lock-in-days").val();
  if (orderLock == lastOrderLock) {
    finishedProgress();
    return -1;
  }
  if (!orderLock || orderLock < 0 || orderLock > 1000) {
    createToast("Need to fill inputs!", "warning", 422);
    finishedProgress();
    return -1;
  }
  url = prepend_url("/devops-tools/v1/order/lock/edit");
  $.ajax(url, {
    type: "PUT",
    data: JSON.stringify({ lock: orderLock }),
    headers: {
      "Content-Type": "application/json",
      Authorization: token,
    },
    statusCode: {
      200: function (res) {
        createToast("Order lock Updated.", "success");
        lastOrderLock = orderLock;
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
      
    },
    complete: function () {
      finishedProgress();
    },
  });
}

function resetSettings() {
  $("#order-lock-in-days").val(lastOrderLock);
}

function responseHandler(res) {
  $.each(res.rows, function (i, row) {
    row.state = $.inArray(row.id, selections) !== -1;
  });
  return res;
}

function exportCSV(url) {
  var xhr = $.ajax({
    url: prepend_url(url),
    type: "GET",
    headers: { Authorization: token },
    responseType: "blob",
    success: function (data, status, xhr) {
      let filename = "";
      const disposition = xhr.getResponseHeader("Content-Disposition");
      if (disposition && disposition.indexOf("attachment") !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, "");
        }
      }

      if (!filename) {
        filename = "unknown.csv";
      }
      const bom = new Uint8Array([0xef, 0xbb, 0xbf]);
      const blob = new Blob([bom, data], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");

      a.href = url;
      a.download = filename;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
  });
}

function ajaxEditProductTaxAndMoadian(productID) {
  const url = prepend_url(
    "/devops-tools/v1/products/tax_and_moadian/" + productID
  );
  inProgress();
  const tax_rate = document.getElementById("editTaxRate").value;
  const moadian_product_id = document.getElementById("editMoadianProductId").value;
  const jsonData = JSON.stringify(
    tax_rate === ""
      ? { tax_rate: null, moadian_product_id: moadian_product_id }
      : { tax_rate: tax_rate, moadian_product_id: moadian_product_id }
  );
  $.ajax({
    url: url,
    type: "PUT",
    headers: { 
      Authorization: token,
      "Content-Type": "application/json",
    },
    data: jsonData,
    statusCode: {
      200: function (res) {
        
        createToast(
          "Product " + res.id + " updated.",
          "success",
          res.status
        );
        $("#table").bootstrapTable("refresh");
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: function () {
      finishedProgress();
    },
  });
}

function ajaxEditProductsDailyPurchased(ID) {
  const url = prepend_url(
    "/devops-tools/v1/products/products_daily_purchased/" + ID
  );
  inProgress();
  const productID = document.getElementById("editProductID").value;
  const date = document.getElementById("editDate").value;
  const price = document.getElementById("editPrice").value;
  const count = document.getElementById("editCount").value;
  const description = document.getElementById("editDescription").value;
  const jsonData = JSON.stringify(
      { product_id: productID, 
        date: date,
        price: price,
        count: count,
        description: description
      }
  );
  $.ajax({
    url: url,
    type: "PUT",
    headers: { 
      Authorization: token,
      "Content-Type": "application/json",
    },
    data: jsonData,
    statusCode: {
      200: function (res) {
        
        createToast(
          "Product Daily Purchased" + res.id + " updated.",
          "success",
          res.status
        );
        $("#table").bootstrapTable("refresh");
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: function () {
      finishedProgress();
    },
  });
}

function ajaxRequestProductTaxMoadian(params) {
  const url = prepend_url("/devops-tools/v1/products/tax_and_moadian/list");

  $.ajax({
    url: url + "?" + $.param(params.data),
    type: "GET",
    headers: { Authorization: token },
    statusCode: {
      200: function (res) {
        if (Array.isArray(res.rows)) {
          res.rows = res.rows.map((row) => {
            row.tax_rate = row.tax_rate !== null ? row.tax_rate + "%"  : "Not Defined";
            row.moadian_product_id = row.moadian_product_id !== "" ? row.moadian_product_id : "Not Defined";
            row.state = row.state === true ? "Online" : "Offline";

            row.actions = `
              <button class="btn btn-sm btn-primary open-modal-edit-btn" data-id="${row.id}">
                <i class="bi bi-pen h6"></i> Edit
              </button>`;
            return row;
          });
        } else {
          console.error("Response rows are missing or not an array");
        }

        params.success(res);
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
  });
}

function ajaxRequestProductsDailyPurchased(params) {
  const url = prepend_url("/devops-tools/v1/products/products_daily_purchased/list");

  $.ajax({
    url: url + "?" + $.param(params.data),
    type: "GET",
    headers: { Authorization: token },
    statusCode: {
      200: function (res) {
        if (Array.isArray(res.rows)) {
          res.rows = res.rows.map((row) => {
            row.product_id = row.product_id !== null ? row.product_id : "Not Defined";
            row.product_name = row.product_name !== null ? row.product_name : "Not Defined";
            row.date = row.date !== null ? row.date : "Not Defined";
            row.price = row.price !== null ? row.price.toLocaleString() + " Toman"  : "Not Defined";
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
          });
        } else {
          console.error("Response rows are missing or not an array");
        }

        params.success(res);
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
  });
}

function ajaxRequestGetOrderLock() {
  const url = prepend_url("/devops-tools/v1/order/lock");
  $.ajax({
    url: url,
    type: "GET",
    headers: { Authorization: token },
    statusCode: {
      200: function (res) {
        $("#order-lock-in-days").val(res.lock);
        lastOrderLock = res.lock;
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
  });
}

function syncAggregationCreate(type) {
  const url = prepend_url(
    "/devops-tools/v1/kubernetes/jobs/aggregation/create"
  );
  if (confirm('Are you sure you want to sync this table?')) {
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: token,
    },
    body: JSON.stringify({ type: type }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.Status === "Created") {
        createOrUpdateToastTask("active", data.Job);
        checkJobStatus("/devops-tools/v1/kubernetes/jobs/aggregation/status/", data.Job)
      } else {
        console.error("Job creation failed:", data);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
  }
}

function syncAccess() {
  const url = prepend_url(
    "/devops-tools/v1/kubernetes/jobs/access/create"
  );
  if (confirm('Are you sure you want to sync this table?')) {
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
      .catch((error) => {
        console.error("Error:", error);
      });
  }
}

function checkJobStatus(endpoint, jobName) {
  const statusUrl = prepend_url(endpoint);
  
  fetch(statusUrl + jobName, {
    headers: {
      Authorization: token,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data && data.status) {
        switch (data.status.toLowerCase()) {
          case "pending":
            createOrUpdateToastTask("pending", jobName);
            break;
          case "succeeded":
            createOrUpdateToastTask("succeeded", jobName, 5000);
            createToast(`Job ${jobName} finished with status Success.`, "success", "Task", 9999999999);
            console.log(`Job ${jobName} has status: Succeeded. Stopping further requests.`);
            return;
          case "failed":
            createOrUpdateToastTask("failed", jobName, 5000);
            createToast(`Job ${jobName} Failed.`, "error", data.error, 9999999999);
            console.log(`Job ${jobName} has status: Failed. Stopping further requests. error: ${data.error}`);
            return;
          case "unknown":
            createOrUpdateToastTask("warning", jobName, 5000);
            createToast(`Job ${jobName} finished with status Unknown.`, "warning", "Task", 9999999999);
            console.log(`Job ${jobName} has status: Unknown. Stopping further requests.`);
            return;
          default:
            createOrUpdateToastTask("active", jobName);
            break;
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

function formatTimestamp(timestamp) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString();
}

function getRandomLightColor() {
  const r = Math.floor(Math.random() * 156) + 100;
  const g = Math.floor(Math.random() * 156) + 100; 
  const b = Math.floor(Math.random() * 156) + 100;
  return `rgba(${r}, ${g}, ${b}, 1)`;
}

function getCurrentDateTime() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const formattedDateTime = `${year}${month}${day}${hours}${minutes}`;

    return formattedDateTime;
}

function getMonitorBoolMetrics(endpoint) {
  inProgress();
  $.ajax({
    url: prepend_url('/devops-tools/v1/monitor/bool/') + endpoint,
    method: 'GET',
    headers: {
      Authorization: token,
    },
    success: function(data, textStatus, jqXHR) {
      var contentType = jqXHR.getResponseHeader('Content-Type');
      if (contentType && contentType.includes('application/json')) {
        $('#' + endpoint).empty();
        for (var key in data) {
          if (data.hasOwnProperty(key)) {
            var value = data[key];
            var colorClass = value ? 'btn-success' : 'btn-danger'; 
            var buttonHtml = `
              <div class="col-4 mb-3 px-1">
                <div class="row mx-1 h-100">
                  <button class="btn btn-lg btn-not-clickable ${colorClass} col-12">${key}</button>
                </div>
              </div>
            `;
            $('#' + endpoint).append(buttonHtml);
          }
        }
      } else {
        handleErrors(406, { message: 'Response is not in JSON format' });
      }
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: function () {
      finishedProgress();
    }
  });
};

function ImportCSV(url, checkJobStatusUrl) {
  inProgress();
  var file = csvFile.files[0];
  var taskID = getCurrentDateTime();
  if (!file) {
    createToast("No csv file selected!", "warning", 422);
    finishedProgress();
    return -1;
  }
  var formData = new FormData();
  formData.append("file", file);
  url = prepend_url(url + taskID);
  $.ajax(url, {
    type: "POST",
    data: formData,
    contentType: false,
    processData: false,
    headers: {
      Authorization: token,
    },
    statusCode: {
      200: function (res) {
        createToast("Product CSV file uploaded. importing in process.", "success");
        checkJobStatus(checkJobStatusUrl, taskID);
      },
    },
    error: function (jqXHR, status, error) {
      handleErrors(jqXHR.status, jqXHR.responseJSON);
    },
    complete: function () {
      finishedProgress();
      csvFile.value = "";
    },
  });
};

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
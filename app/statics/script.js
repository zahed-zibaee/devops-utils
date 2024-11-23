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
      customDelay: 30000,
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

function createOrUpdateToastTask(status, jobName) {
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
      autohide: false,
    },
    pending: {
      alertClass: "alert-warning",
      iconClass: "bi-hourglass-split",
      message: `Job ${jobName} Status: Pending`,
      autohide: false,
    },
    succeeded: {
      alertClass: "alert-success",
      iconClass: "bi-check2-circle",
      message: `Job ${jobName} Status: Succeeded`,
      autohide: false,
    },
    failed: {
      alertClass: "alert-danger",
      iconClass: "bi-exclamation-triangle-fill",
      message: `Job ${jobName} Status: Failed`,
      autohide: false,
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

function exportProductTaxAndMoadian() {
  const url = prepend_url(
    "/devops-tools/v1/products/tax_and_moadian/export_csv"
  );
  var xhr = $.ajax({
    url: url,
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
        filename = "products.csv";
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
      ? { moadian_product_id: moadian_product_id }
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

function ajaxRequestProductTaxMoadian(params) {
  const url = prepend_url("/devops-tools/v1/products/tax_and_moadian/list");

  $.ajax({
    url: url + "?" + $.param(params.data),
    type: "GET",
    headers: { Authorization: token },
    statusCode: {
      200: function (res) {
        res.rows = res.rows.map((row) => {
          const normalizedId = row.id.replace(/<[^>]*>/g, "");
          row.actions = `
            <button class="btn btn-sm btn-primary open-modal-edit-btn" data-id="${normalizedId}">
              Edit
            </button>`;
          return row;
        });

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
        checkJobStatus("/devops-tools/v1/kubernetes/jobs/aggregation/status", data.Job)
      } else {
        console.error("Job creation failed:", data);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function syncAccess() {
  const url = prepend_url(
    "/devops-tools/v1/kubernetes/jobs/access/create"
  );
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
        checkJobStatus("/devops-tools/v1/kubernetes/jobs/access/status", data.Job);
      } else {
        console.error("Job creation failed:", data);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function checkJobStatus(endpoint, jobName) {
  const statusUrl = prepend_url(
    endpoint
  );
  fetch(statusUrl + `?job_name=${jobName}`, {
    headers: {
      Authorization: token,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data) {
        if (data.Pending) {
          createOrUpdateToastTask("pending", jobName);
        } else if (data.Succeeded) {
          createOrUpdateToastTask("succeeded", jobName);
        } else if (data.Failed) {
          createOrUpdateToastTask("failed", jobName);
        } else {
          createOrUpdateToastTask("active", jobName);
        }
        if (data.Succeeded) {
          console.log(
            `Job ${jobName} has status: Succeeded. Stopping further requests.`
          );
          return;
        }
        if (data.Failed) {
          console.log(
            `Job ${jobName} has status: Failed. Stopping further requests.`
          );
          return;
        }
      } else {
        console.error("Data is null or undefined");
      }
      setTimeout(() => checkJobStatus(endpoint, jobName), 5000);
    })
    .catch((error) => {
      console.error("Error:", error);
      setTimeout(() => checkJobStatus(endpoint, jobName), 5000);
    });
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

function uploadProductTaxAndMoadian() {
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
  url = prepend_url("/devops-tools/v1/products/tax_and_moadian/import_csv/" + taskID);
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
        createOrUpdateToastTask("active", taskID);
        checkJobStatusImportCSVTaxAndMoadian(taskID);
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

function checkJobStatusImportCSVTaxAndMoadian(jobName) {
    url = prepend_url("/devops-tools/v1/products/tax_and_moadian/import_csv/status/" + jobName);
    fetch(url, {
      headers: {
        Authorization: token,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data) {
          if (data.status == 'pending') {
            createOrUpdateToastTask("pending", jobName);
          } else if (data.status == 'succeeded') {
            $table.bootstrapTable("refresh");
            createOrUpdateToastTask("succeeded", jobName);
          } else if (data.status == 'failed') {
            createOrUpdateToastTask("failed", jobName);
            createToast(data.error, "error");
          } else {
            createOrUpdateToastTask("active", jobName);
          }
          if (data.status == 'failed') {
            console.log(
              `Job ${jobName} has status: Failed. Stopping further requests.`
            );
            return;
          }
          if (data.status == 'succeeded') {
            console.log(
              `Job ${jobName} has status: Succeeded. Stopping further requests.`
            );
            return;
          }
        } else {
          console.error("Data is null or undefined");
        }
        setTimeout(() => checkJobStatusImportCSVTaxAndMoadian(jobName), 5000);
      })
      .catch((error) => {
        console.error("Error:", error);
        setTimeout(() => checkJobStatusImportCSVTaxAndMoadian(jobName), 5000);
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
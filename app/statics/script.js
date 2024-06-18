const toastLiveExample = document.getElementById('toast');

var token = "";
var hostname = "";

function prepend_url(url) {
    const notlocal = hostname.includes('bo.snapp.supply');
    if (notlocal) {
        return "/api-bo" + url
    } else {
        return url
    }
}

function notEmpty( el ){
    return $.trim(el.html())
}

function createToast(message, severity, status = 500, delay = 5000) {
    const toastTemplate = document.getElementById('toastTemplate');
    const toastClone = toastTemplate.cloneNode(true);
    toastClone.id = '';

    if (severity != 'success') {
    toastClone.querySelector('.alert-message').textContent = "Error " + status + ": " + message;
    } else {
    toastClone.querySelector('.alert-message').textContent = message;

    }

    if (severity == 'warning') {
        toastClone.querySelector('.alert').classList.add("alert-warning");
        toastClone.querySelector('.svg-icon').classList.add('bi-exclamation-triangle-fill');
    } else if (severity == 'error') {
        toastClone.querySelector('.alert').classList.add("alert-danger");
        toastClone.querySelector('.svg-icon').classList.add('bi-exclamation-triangle-fill');
    } else if (severity == 'success') {
        toastClone.querySelector('.alert').classList.add("alert-success");
        toastClone.querySelector('.svg-icon').classList.add('bi-check-circle-fill');
    } else {
        return -1;
    }

    const toastContainer = document.getElementById('toastContainer');
    toastContainer.appendChild(toastClone);

    const bsToast = new bootstrap.Toast(toastClone, { delay });
    bsToast.show();

    toastClone.addEventListener('hidden.bs.toast', () => {
      toastClone.remove();
    });
}

function inProgress() {
    if (notEmpty($('#wrapper'))) {
        var wrapper = $("#wrapper");
        wrapper.prop('style', "cursor: not-allowed;");
    }
    if (notEmpty($('#upload-button'))) {
        var buttonUpdate = $("#upload-button");
        buttonUpdate.prop('disabled', true);
    }
    if (notEmpty($('#reset-button'))) {
        var buttonReset = $("#reset-button");
        buttonReset.prop('disabled', true);
    } 
}
function finishedProgress() {
    if (notEmpty($('#wrapper'))) {
        var wrapper = $("#wrapper");
        wrapper.prop('style', "");
    }
    if (notEmpty($('#upload-button'))) {
        var buttonUpdate = $("#upload-button");
        buttonUpdate.prop('disabled', false);
    }
    if (notEmpty($('#reset-button'))) {
        var buttonReset = $("#reset-button");
        buttonReset.prop('disabled', false);
    } 
}

function uploadProductTaxAndMoadian() {
    inProgress();
    var file = csvFile.files[0];
    if (!file) {
        createToast('No csv file selected!', "warning", 422);
        finishedProgress();
        return -1
    }
    var formData = new FormData();
    formData.append('file', file);
    url = prepend_url('/devops-tools/v1/products/tax_and_moadian/import_csv')
    $.ajax(url, {
    type: 'POST',
    data: formData,
    contentType: false,
    processData: false,
    headers: {
        "Authorization": token,
    },
    statusCode: {
        200: function (res) {
            createToast('Product CSV file imported.', "success");
            finishedProgress();
            $table.bootstrapTable('refresh'); 
        }
    },
    error: function (jqXHR, status, error) {
        var message;
        if (jqXHR.status == 422) {
            message = "Bad CSV file!";
        } else if (jqXHR.status == 404) {
            message = "Product not found!";
        } else if (jqXHR.status == 503) {
            message = "Can not access database!";
        } else {
            message = "Can not import CSV file! check console logs.";
        }
        createToast(message, "error", jqXHR.status);
        console.log(jqXHR.responseJSON);
        finishedProgress();
    }
    });
}

function updateSettings() {
    inProgress();
    var orderLock = $("#order-lock-in-days").val();
    if (orderLock == lastOrderLock) {
        finishedProgress();
        return -1
    }
    if (!orderLock || orderLock < 0 || orderLock > 1000) {
        createToast('Need to fill inputs!', "warning", 422);
        finishedProgress();
        return -1
    }
    url = prepend_url('/devops-tools/v1/order/lock/edit')
    $.ajax(url, {
    type: 'PUT',
    data: JSON.stringify({ "lock": orderLock }),
    headers: {
        "Content-Type": "application/json",
        "Authorization": token,
    },
    statusCode: {
        200: function (res) {
            createToast('Order lock Updated.', "success");
            finishedProgress();
            lastOrderLock = orderLock;
        }
    },
    error: function (jqXHR, status, error) {
        createToast('Can not update order lock, check console logs.', "error", jqXHR.status);
        console.log(jqXHR.responseJSON);
        finishedProgress();
    }
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

function exportProductTaxAndMoadian(){
    const url = prepend_url('/devops-tools/v1/products/tax_and_moadian/export_csv')
    var xhr = $.ajax({
        url: url,
        type: "GET",
        headers: { Authorization: token },
        responseType: 'blob', // Set the response type to 'blob'
        success: function (data, status, xhr) {
            let filename = '';
            const disposition = xhr.getResponseHeader('Content-Disposition');
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
    
            if (!filename) {
                filename = 'products.csv';
            }
    
            const blob = new Blob([data], { type: 'text/csv;charset=utf-8' }); // Create a Blob from the response data
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            
            a.href = url;
            a.download = filename;
    
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        },
        error: function (jqXHR, status, error) {
            createToast('Can not export product csv.', "error", jqXHR.status);
            console.log(jqXHR.responseJSON);
        }
    });
}

function ajaxRequestProductTaxMoadian(params) {
    const url = prepend_url('/devops-tools/v1/products/tax_and_moadian/list')
    $.ajax({
        url: url + '?' + $.param(params.data),
        type: "GET",
        headers: { Authorization: token },
        statusCode: {
            200: function (res) {
                params.success(res);
            }
        },
        error: function (jqXHR, status, error) {
            createToast('Can not get product data.', "error", jqXHR.status);
            console.log(jqXHR.responseJSON);
        }
    });
}

function ajaxRequestGetOrderLock() {
    const url = prepend_url('/devops-tools/v1/order/lock')
    $.ajax({
        url: url,
        type: "GET",
        headers: { Authorization: token },
        statusCode: {
            200: function (res) {
                $('#order-lock-in-days').val(res.lock);
                lastOrderLock = res.lock;
            },
            412: function (res) {
                createToast('Order lock is not equal as legacy lock.', "error", jqXHR.status);
                console.log(res);
            }
        },
        error: function (jqXHR, status, error) {
            var message;
            if (jqXHR.status == 412) {
                message = "Order lock is not equal as legacy lock!"
            } else {
                message = "Can not get product data."
            }
            createToast(message, "error", jqXHR.status);
            console.log(jqXHR.responseJSON);
        }
    });
}

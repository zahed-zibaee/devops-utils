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

function createToast(message, severity, delay = 5000) {
    const toastTemplate = document.getElementById('toastTemplate');
    const toastClone = toastTemplate.cloneNode(true);
    toastClone.id = '';

    toastClone.querySelector('.alert-message').textContent = message;

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
        createToast('No csv file selected!', "warning");
        finishedProgress();
        return -1
    }
    var formData = new FormData();
    formData.append('file', file);
    url = prepend_url('/devops-tools/v1/products/tax_and_moadian/import_csv')
    fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
        "Authorization": token,
        }
    })
    .then(response => {
    if (response.ok) {
        createToast('Product CSV file imported.', "success");
        console.log(response);
        finishedProgress();
        $table.bootstrapTable('refresh');
    } else if (response.status == 422) {
        createToast('Bad CSV file!', "error");
        console.log(response);
        finishedProgress();
    }else if (response.status == 404) {
        createToast('Product not found!', "error");
        console.log(response);
        finishedProgress();
    } else {
        createToast('Can not import CSV file! check console logs.', "error");
        console.log(response);
        finishedProgress();
    }
    })
    .catch(error => {
        createToast('Can not import CSV file! check console logs.', "error");
        finishedProgress();
        console.error(error);
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
        createToast('Need to fill inputs!', "warning");
        finishedProgress();
        return -1
    }
    url = prepend_url('/devops-tools/v1/order/lock/edit')
    fetch(url, {
    method: 'PUT',
    body: JSON.stringify({ "lock": orderLock }),
    headers: {
        "Content-Type": "application/json",
        "Authorization": token,
        }
    })
    .then(response => {
    if (response.ok) {
        createToast('Order lock Updated.', "success");
        console.log(response);
        finishedProgress();
        lastOrderLock = orderLock;
    }else {
        createToast('Can not update order lock, check console logs.', "error");
        console.log(response);
        finishedProgress();
    }
    })
    .catch(error => {
        createToast('Can not update order lock, check console logs.', "error");
        finishedProgress();
        console.error(error);
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

function ajaxRequestProductTaxMoadian(params) {
    const url = prepend_url('/devops-tools/v1/products/tax_and_moadian/list')
    $.ajax({
        url: url + '?' + $.param(params.data),
        type: "GET",
        headers: { Authorization: token }
    }).then(function (res) {
        console.log(res);
        params.success(res)
    }).catch(error => {
        createToast('Can not get product data.', "error");
    });
}

function ajaxRequestGetOrderLock() {
    const url = prepend_url('/devops-tools/v1/order/lock')
    $.ajax({
        url: url,
        type: "GET",
        headers: { Authorization: token }
    }).then(function (res) {
        console.log(res);
        $('#order-lock-in-days').val(res.lock);
        lastOrderLock = res.lock;
    }).catch(error => {
        createToast('Can not get order lock data.', "error");
    });
}

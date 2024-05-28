var $table = $("#table");
const csvFile = document.getElementById('csv-file');
const uploadButton = document.getElementById('upload-button');
const toastLiveExample = document.getElementById('toast');

var token = "";
var hostname = "";

function prepend_url(url) {
    const notlocal = hostname.includes('bo.snapp.supply')
    if (notlocal) {
        return "/api-bo" + url
    } else {
        return url
    }
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

uploadButton.addEventListener('click', () => {
    $("#upload-button").prop('disabled', true);
    var file = csvFile.files[0];
    if (!file) {
        createToast('No csv file selected!', "warning");
        $("#upload-button").prop('disabled', false);
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
        $("#upload-button").prop('disabled', false);
        $table.bootstrapTable('refresh')
    } else {
        createToast('Can not import CSV file check console logs.', "error");
        $("#upload-button").prop('disabled', false);
        console.error(response);
    }
    })
    .catch(error => {
        createToast('Can not import CSV file check console logs.', "error");
        $("#upload-button").prop('disabled', false);
        console.error(error);
    });
});

function responseHandler(res) {
  $.each(res.rows, function (i, row) {
    row.state = $.inArray(row.id, selections) !== -1;
  });
  return res;
}

function initTable() {
  $table.bootstrapTable("destroy").bootstrapTable({
    height: 600,
    locale: $("#locale").val(),
  });
}

window.addEventListener('message', function(event) {
    if(!!event.data) {
        hostname = event.data.hostname;
        console.log("Hostname received from the parent: " + hostname)
        token = event.data.token;
    }
    console.log("Message received from the parent: " + event.data);
});

function ajaxRequest(params) {
    const url = prepend_url('/devops-tools/v1/products/tax_and_moadian/list')
    $.ajax({
        url: url + '?' + $.param(params.data),
        type: "GET",
        headers: { Authorization: token }
    }).then(function (res) {
        params.success(res)
    })
}

$(function () {
    initTable();
    $("#locale").change(initTable);
});

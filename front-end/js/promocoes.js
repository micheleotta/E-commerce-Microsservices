(function () {
    var removeBtn = document.getElementById("remove-btn");
    var cancelButton = document.getElementById("cancel");
    var promoDialog = document.getElementById("promo-dialog");

    // O botão Update abre uma Dialog
    removeBtn.addEventListener("click", function () {
        promoDialog.showModal();
    });

    // O botão cancelButtom fecha uma Dialog
    cancelButton.addEventListener("click", function () {
        promoDialog.close();
    });
});
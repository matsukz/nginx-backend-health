document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("main-form");
    const submitButtons = form.querySelectorAll('button[type="submit"]');

    // 初期値を保存（リセットで戻す用）
    const ipTextarea = form.querySelector('textarea[name="ip_list"]');
    const successTextarea = form.querySelector('textarea[name="success_ip_list"]');
    const initialIpText = ipTextarea ? ipTextarea.value : "";
    const initialSuccessText = successTextarea ? successTextarea.value : "";

    // フォーム送信中はボタンを無効化
    form.addEventListener("submit", function () {
        submitButtons.forEach(function (btn) {
            btn.disabled = true;
            if (!btn.dataset.originalText) {
                btn.dataset.originalText = btn.textContent;
            }
            // すでに「中...」が付いていたら二重に付けない
            if (!btn.textContent.includes("中...")) {
                btn.textContent = btn.textContent + " 中...";
            }
        });
    });

    // リセットボタン：画面のテキストエリア内容を初期状態に戻す
    const resetButton = document.getElementById("reset-button");
    if (resetButton) {
        resetButton.addEventListener("click", function () {
            if (ipTextarea) {
                ipTextarea.value = initialIpText;
            }
            if (successTextarea) {
                successTextarea.value = initialSuccessText;
            }
        });
    }
});
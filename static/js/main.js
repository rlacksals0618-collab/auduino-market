// 알림 메시지는 4초 뒤 자동으로 사라집니다
document.querySelectorAll(".flash").forEach((el) => {
  setTimeout(() => el.remove(), 4000);
});

// data-confirm 이 붙은 폼은 제출 전에 한 번 더 물어봅니다 (예: 상품 삭제)
document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!confirm(form.dataset.confirm)) event.preventDefault();
  });
});

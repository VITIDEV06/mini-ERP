// Confirmación con modal para formularios con data-confirm="mensaje".
(function () {
  const modalEl = document.getElementById('confirmModal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  const body = document.getElementById('confirmModalBody');
  const ok = document.getElementById('confirmModalOk');
  let pendingForm = null;

  document.addEventListener('submit', function (ev) {
    const form = ev.target;
    if (!form.matches('form[data-confirm]') || form.dataset.confirmed === '1') return;
    ev.preventDefault();
    pendingForm = form;
    body.textContent = form.dataset.confirm;
    ok.className = 'btn ' + (form.dataset.confirmClass || 'btn-primary');
    ok.textContent = form.dataset.confirmText || 'Confirmar';
    modal.show();
  });

  ok.addEventListener('click', function () {
    if (!pendingForm) return;
    pendingForm.dataset.confirmed = '1';
    modal.hide();
    if (typeof pendingForm.requestSubmit === 'function') pendingForm.requestSubmit();
    else pendingForm.submit();
  });

  // Evita el doble envío de formularios.
  document.addEventListener('submit', function (ev) {
    if (ev.defaultPrevented) return;
    ev.target.querySelectorAll('button[type=submit]').forEach(function (b) {
      setTimeout(function () { b.disabled = true; }, 0);
    });
  });
})();

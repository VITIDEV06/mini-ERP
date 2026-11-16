// Formulario de venta: agrega/quita líneas y muestra una vista previa de importes.
// IMPORTANTE: estos cálculos son solo informativos. El backend recalcula precios,
// subtotales y total con los datos de la base de datos y valida el stock.
(function () {
  const tbody = document.getElementById('items-body');
  const template = document.getElementById('item-template');
  const totalForms = document.getElementById('id_items-TOTAL_FORMS');
  const totalEl = document.getElementById('venta-total');
  const btnAdd = document.getElementById('btn-agregar');
  if (!tbody || !template || !totalForms) return;

  const fmt = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function infoProducto(select) {
    const opt = select.options[select.selectedIndex];
    if (!opt || !opt.value) return null;
    const data = document.querySelector('#productos-data option[value="' + opt.value + '"]');
    if (!data) return null;
    return { precio: parseFloat(data.dataset.precio) || 0, stock: parseInt(data.dataset.stock, 10) || 0 };
  }

  function recalcular() {
    let total = 0;
    tbody.querySelectorAll('tr.venta-item').forEach(function (row) {
      const del = row.querySelector('input[name$="-DELETE"]');
      if (del && del.checked) return;
      const select = row.querySelector('select[name$="-producto"]');
      const qtyInput = row.querySelector('input[name$="-cantidad"]');
      const info = select ? infoProducto(select) : null;
      const qty = parseInt(qtyInput.value, 10) || 0;
      const precioEl = row.querySelector('.item-precio');
      const subEl = row.querySelector('.item-subtotal');
      const stockEl = row.querySelector('.item-stock');
      if (info) {
        const sub = info.precio * qty;
        total += sub;
        precioEl.textContent = '$ ' + fmt.format(info.precio);
        subEl.textContent = '$ ' + fmt.format(sub);
        stockEl.textContent = info.stock;
        qtyInput.max = info.stock;
        qtyInput.classList.toggle('is-invalid', qty > info.stock || qty < 1);
      } else {
        precioEl.textContent = subEl.textContent = '—';
        stockEl.textContent = '—';
      }
    });
    totalEl.textContent = '$ ' + fmt.format(total);
  }

  function agregarFila() {
    const index = parseInt(totalForms.value, 10);
    const html = template.innerHTML.replace(/__prefix__/g, index);
    tbody.insertAdjacentHTML('beforeend', html);
    totalForms.value = index + 1;
    recalcular();
  }

  btnAdd.addEventListener('click', agregarFila);

  tbody.addEventListener('change', recalcular);
  tbody.addEventListener('input', recalcular);
  tbody.addEventListener('click', function (ev) {
    const btn = ev.target.closest('.btn-quitar');
    if (!btn) return;
    const row = btn.closest('tr');
    const visibles = Array.from(tbody.querySelectorAll('tr.venta-item')).filter(function (r) {
      const d = r.querySelector('input[name$="-DELETE"]');
      return !(d && d.checked);
    });
    if (visibles.length <= 1) return; // siempre al menos una línea
    const del = row.querySelector('input[name$="-DELETE"]');
    del.checked = true;
    row.classList.add('d-none');
    recalcular();
  });

  if (!tbody.querySelector('tr.venta-item')) agregarFila();
  recalcular();
})();

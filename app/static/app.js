// Мінімальний фронтенд DSO-Shop: каталог, пошук, вхід, кошик.
(function () {
  "use strict";
  let token = null;

  function el(tag, text, cls) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  }

  async function api(path, options) {
    const opts = Object.assign({ headers: {} }, options || {});
    if (token) opts.headers["Authorization"] = "Bearer " + token;
    if (opts.body && typeof opts.body !== "string") {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const resp = await fetch(path, opts);
    const data = resp.status === 204 ? null : await resp.json();
    return { ok: resp.ok, status: resp.status, data: data };
  }

  function renderProducts(items) {
    const list = document.getElementById("products");
    list.replaceChildren();
    items.forEach(function (p) {
      const li = el("li");
      li.appendChild(el("strong", p.name));
      li.appendChild(el("div", p.price.toFixed(2) + " грн", "price"));
      const btn = el("button", "До кошика");
      btn.type = "button";
      btn.addEventListener("click", function () { addToCart(p.id); });
      li.appendChild(btn);
      list.appendChild(li);
    });
    if (items.length === 0) list.appendChild(el("li", "Нічого не знайдено"));
  }

  async function loadCatalog() {
    const r = await api("/api/products");
    if (r.ok) renderProducts(r.data.items);
  }

  async function search(event) {
    event.preventDefault();
    const q = document.getElementById("q").value;
    const r = await api("/api/products/search?q=" + encodeURIComponent(q));
    if (r.ok) renderProducts(r.data.items);
  }

  async function login(event) {
    event.preventDefault();
    const r = await api("/api/auth/login", {
      method: "POST",
      body: {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
      },
    });
    const status = document.getElementById("login-status");
    if (r.ok) {
      token = r.data.access_token;
      status.textContent = "Вхід виконано";
      loadCart();
    } else {
      status.textContent = "Невірний логін або пароль";
    }
  }

  async function loadCart() {
    if (!token) return;
    const r = await api("/api/cart");
    if (!r.ok) return;
    const list = document.getElementById("cart");
    list.replaceChildren();
    r.data.items.forEach(function (i) {
      list.appendChild(el("li", i.name + " × " + i.quantity));
    });
    document.getElementById("cart-total").textContent = "Разом: " + r.data.total.toFixed(2) + " грн";
  }

  async function addToCart(productId) {
    if (!token) {
      document.getElementById("login-status").textContent = "Спочатку увійдіть";
      return;
    }
    await api("/api/cart/items", { method: "POST", body: { product_id: productId, quantity: 1 } });
    loadCart();
  }

  async function checkout() {
    const status = document.getElementById("checkout-status");
    if (!token) { status.textContent = "Спочатку увійдіть"; return; }
    const r = await api("/api/orders", { method: "POST", body: {} });
    status.textContent = r.ok ? "Замовлення №" + r.data.order.id + " створено" : "Помилка: " + r.data.error;
    loadCart();
  }

  document.getElementById("search-form").addEventListener("submit", search);
  document.getElementById("login-form").addEventListener("submit", login);
  document.getElementById("checkout").addEventListener("click", checkout);
  loadCatalog();
})();

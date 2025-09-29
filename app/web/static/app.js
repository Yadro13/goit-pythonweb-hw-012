const $ = (sel) => document.querySelector(sel);
const baseUrl = window.location.origin;

const store = {
  get access() { return localStorage.getItem("access_token") || ""; },
  set access(v) { localStorage.setItem("access_token", v || ""); },
  get refresh() { return localStorage.getItem("refresh_token") || ""; },
  set refresh(v) { localStorage.setItem("refresh_token", v || ""); },
  clear() { localStorage.removeItem("access_token"); localStorage.removeItem("refresh_token"); }
};

function authHeaders() {
  const h = { "Accept": "application/json" };
  if (store.access) h["Authorization"] = "Bearer " + store.access;
  return h;
}

async function api(url, opts = {}) {
  const res = await fetch(url, opts);
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : await res.text();
  return { ok: res.ok, status: res.status, data };
}

function showSection(id) {
  document.querySelectorAll(".section").forEach(s => s.classList.add("hidden"));
  document.querySelectorAll(".nav a").forEach(a => a.classList.remove("active"));
  $("#" + id).classList.remove("hidden");
  document.querySelector(`.nav a[data-section="${id}"]`)?.classList.add("active");
}

document.querySelectorAll(".nav a").forEach(a => {
  a.addEventListener("click", e => {
    e.preventDefault();
    showSection(a.dataset.section);
  });
});

$("#btn-register").onclick = async () => {
  const email = $("#reg-email").value.trim();
  const password = $("#reg-pass").value;
  const { ok, status, data } = await api(baseUrl + "/auth/register", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  $("#auth-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-login").onclick = async () => {
  const email = $("#login-email").value.trim();
  const password = $("#login-pass").value;
  const body = new URLSearchParams({ username: email, password });
  const { ok, status, data } = await api(baseUrl + "/auth/login", {
    method: "POST",
    headers: { "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded" },
    body
  });
  if (ok) {
    store.access = data.access_token;
    store.refresh = data.refresh_token || "";
  }
  $("#auth-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-verify").onclick = async () => {
  const token = $("#verify-token").value.trim();
  const { ok, status, data } = await api(baseUrl + "/auth/verify-email?token=" + encodeURIComponent(token));
  $("#auth-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-forgot").onclick = async () => {
  const email = $("#forgot-email").value.trim();
  const { ok, status, data } = await api(baseUrl + "/auth/forgot-password?email=" + encodeURIComponent(email), {
    method: "POST", headers: authHeaders()
  });
  $("#auth-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-reset").onclick = async () => {
  const token = $("#reset-token").value.trim();
  const new_password = $("#new-pass").value;
  const { ok, status, data } = await api(baseUrl + "/auth/reset-password", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password })
  });
  $("#auth-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-refresh").onclick = async () => {
  const { ok, status, data } = await api(baseUrl + "/auth/refresh", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: store.refresh })
  });
  if (ok) store.access = data.access_token;
  $("#auth-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-logout").onclick = () => {
  store.clear();
  $("#auth-out").textContent = "Вихід виконано.";
};

$("#btn-create-contact").onclick = async () => {
  const body = {
    first_name: $("#c-first").value.trim(),
    last_name: $("#c-last").value.trim(),
    email: $("#c-email").value.trim(),
    phone: $("#c-phone").value.trim(),
    birthday: $("#c-bday").value,
    extra: $("#c-extra").value.trim() || null
  };
  await api(baseUrl + "/contacts", {
    method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  await loadContacts();
};

$("#btn-load-contacts").onclick = loadContacts;
async function loadContacts() {
  const q = new URLSearchParams();
  const f = $("#q-first").value.trim(); if (f) q.set("first_name", f);
  const l = $("#q-last").value.trim(); if (l) q.set("last_name", l);
  const e = $("#q-email").value.trim(); if (e) q.set("email", e);
  const url = baseUrl + "/contacts" + (q.toString() ? "?" + q.toString() : "");
  const { data } = await api(url, { headers: authHeaders() });
  const tbody = $("#contacts-table tbody"); tbody.innerHTML = "";
  (data || []).forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${c.id}</td>
      <td>${c.first_name}</td>
      <td>${c.last_name}</td>
      <td>${c.email}</td>
      <td><input value="${c.phone || ""}" data-id="${c.id}" class="cell-input"/></td>
      <td>${c.birthday || ""}</td>
      <td>
        <button class="btn-save" data-id="${c.id}">Зберегти</button>
        <button class="btn-del danger" data-id="${c.id}">Видалити</button>
      </td>`;
    tbody.appendChild(tr);
  });
  tbody.querySelectorAll(".btn-save").forEach(btn => btn.onclick = async () => {
    const id = btn.dataset.id;
    const phone = tbody.querySelector(`input[data-id="${id}"]`).value;
    await api(baseUrl + "/contacts/" + id, {
      method: "PUT", headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ phone })
    });
    await loadContacts();
  });
  tbody.querySelectorAll(".btn-del").forEach(btn => btn.onclick = async () => {
    const id = btn.dataset.id;
    await api(baseUrl + "/contacts/" + id, { method: "DELETE", headers: authHeaders() });
    await loadContacts();
  });
}

$("#btn-upcoming").onclick = async () => {
  const { data } = await api(baseUrl + "/contacts/birthdays/upcoming?days=7", { headers: authHeaders() });
  const ul = $("#upcoming-list"); ul.innerHTML = "";
  (data || []).forEach(c => {
    const li = document.createElement("li");
    li.textContent = `${c.first_name} ${c.last_name} — ${c.birthday}`;
    ul.appendChild(li);
  });
};

$("#btn-me").onclick = async () => {
  const { ok, status, data } = await api(baseUrl + "/users/me", { headers: authHeaders() });
  $("#me-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-upload-avatar").onclick = async () => {
  const f = $("#avatar-file").files[0];
  if (!f) return;
  const form = new FormData();
  form.append("file", f);
  const { ok, status, data } = await api(baseUrl + "/users/me/avatar", {
    method: "POST", headers: authHeaders(), body: form
  });
  $("#avatar-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-set-default-avatar").onclick = async () => {
  const url = $("#def-avatar-url").value.trim();
  const { ok, status, data } = await api(baseUrl + "/users/admin/default-avatar?url=" + encodeURIComponent(url), {
    method: "POST", headers: authHeaders()
  });
  $("#admin-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-get-default-avatar").onclick = async () => {
  const { ok, status, data } = await api(baseUrl + "/users/default-avatar", { headers: authHeaders() });
  $("#admin-out").textContent = JSON.stringify({ ok, status, data }, null, 2);
};

$("#btn-ping").onclick = async () => {
  const { ok, status } = await api(baseUrl + "/docs");
  $("#diag-out").textContent = JSON.stringify({ ok, status }, null, 2);
};

showSection("auth");
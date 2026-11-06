const categories = ["Access", "Hardware", "Software", "Microsoft 365", "Network", "Other"];
const priorities = ["Low", "Medium", "High", "Critical"];
let managerAuthenticated = false;
let managerReviewer = "";

const elements = {
  tabs: [...document.querySelectorAll(".tab")],
  intakeView: document.querySelector("#intake-view"),
  managerView: document.querySelector("#manager-view"),
  managerLoginPanel: document.querySelector("#manager-login-panel"),
  managerQueuePanel: document.querySelector("#manager-queue-panel"),
  managerLoginForm: document.querySelector("#manager-login-form"),
  managerLoginMessage: document.querySelector("#manager-login-message"),
  form: document.querySelector("#request-form"),
  formMessage: document.querySelector("#form-message"),
  queueMessage: document.querySelector("#queue-message"),
  requestList: document.querySelector("#request-list"),
  queueCount: document.querySelector("#queue-count"),
  statusFilter: document.querySelector("#status-filter"),
  refreshButton: document.querySelector("#refresh-button"),
  dialog: document.querySelector("#review-dialog"),
  reviewMessage: document.querySelector("#review-message"),
};

for (const tab of elements.tabs) {
  tab.addEventListener("click", () => showView(tab.dataset.view));
  tab.addEventListener("keydown", event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const current = elements.tabs.indexOf(tab);
    const offset = event.key === 'ArrowRight' ? 1 : -1;
    const next = elements.tabs[(current + offset + elements.tabs.length) % elements.tabs.length];
    next.focus();
    showView(next.dataset.view);
  });
}

document.querySelector("#title").addEventListener("input", event => {
  document.querySelector("#title-count").textContent = `${event.target.value.length} / 120`;
});
document.querySelector("#description").addEventListener("input", event => {
  document.querySelector("#description-count").textContent = `${event.target.value.length.toLocaleString()} / 2,000`;
});

elements.form.addEventListener("submit", async event => {
  event.preventDefault();
  const button = document.querySelector("#submit-button");
  button.disabled = true;
  setMessage(elements.formMessage, "");
  const data = Object.fromEntries(new FormData(elements.form));
  try {
    const created = await api("/api/requests", { method: "POST", body: data });
    elements.form.reset();
    document.querySelector("#title-count").textContent = "0 / 120";
    document.querySelector("#description-count").textContent = "0 / 2,000";
    setMessage(elements.formMessage, `Request #${created.id} was saved and classified for manager review.`, "success");
    await updateQueueCount();
  } catch (error) {
    setMessage(elements.formMessage, error.message, "error");
  } finally {
    button.disabled = false;
  }
});

elements.managerLoginForm.addEventListener("submit", async event => {
  event.preventDefault();
  const button = document.querySelector("#manager-login-button");
  button.disabled = true;
  setMessage(elements.managerLoginMessage, "");
  const body = Object.fromEntries(new FormData(elements.managerLoginForm));
  try {
    const session = await api("/api/manager/login", { method: "POST", body });
    managerAuthenticated = true;
    managerReviewer = session.reviewer;
    document.querySelector("#manager-passcode").value = "";
    showManagerQueue();
    await loadRequests();
    document.querySelector("#manager-heading").focus({ preventScroll: true });
  } catch (error) {
    setMessage(elements.managerLoginMessage, error.message, "error");
  } finally {
    button.disabled = false;
  }
});

elements.statusFilter.addEventListener("change", loadRequests);
elements.refreshButton.addEventListener("click", loadRequests);
document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    await api("/api/manager/logout", { method: "POST" });
  } finally {
    managerAuthenticated = false;
    managerReviewer = "";
    showManagerLogin();
  }
});
document.querySelector("#close-dialog").addEventListener("click", () => elements.dialog.close());
document.querySelector("#approve-button").addEventListener("click", () => submitDecision("approve"));
document.querySelector("#reject-button").addEventListener("click", () => submitDecision("reject"));
document.querySelector("#review-form").addEventListener("submit", event => event.preventDefault());

async function showView(name) {
  const manager = name === "manager";
  elements.intakeView.hidden = manager;
  elements.managerView.hidden = !manager;
  elements.intakeView.classList.toggle("active", !manager);
  elements.managerView.classList.toggle("active", manager);
  for (const tab of elements.tabs) {
    const active = tab.dataset.view === name;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  }
  history.replaceState(null, "", manager ? "/manager" : "/");
  if (manager) await loadRequests();
}

async function loadRequests() {
  if (!managerAuthenticated) {
    try {
      const session = await api("/api/manager/session");
      managerAuthenticated = true;
      managerReviewer = session.reviewer;
      showManagerQueue();
    } catch (error) {
      if (error.status === 401) {
        showManagerLogin();
        return;
      }
      setMessage(elements.managerLoginMessage, error.message, "error");
      return;
    }
  }
  elements.refreshButton.disabled = true;
  setMessage(elements.queueMessage, "");
  const status = elements.statusFilter.value;
  try {
    const response = await api(`/api/requests${status ? `?status=${encodeURIComponent(status)}` : ""}`);
    renderRequests(response.items);
    await updateQueueCount();
  } catch (error) {
    if (error.status === 401) {
      managerAuthenticated = false;
      managerReviewer = "";
      showManagerLogin();
      return;
    }
    setMessage(elements.queueMessage, error.message, "error");
  } finally {
    elements.refreshButton.disabled = false;
  }
}

function showManagerLogin() {
  elements.managerLoginPanel.hidden = false;
  elements.managerQueuePanel.hidden = true;
  elements.queueCount.textContent = "-";
  setMessage(elements.queueMessage, "");
  document.querySelector("#manager-name").focus({ preventScroll: true });
}

function showManagerQueue() {
  elements.managerLoginPanel.hidden = true;
  elements.managerQueuePanel.hidden = false;
  setMessage(elements.managerLoginMessage, "");
}

function renderRequests(requests) {
  elements.requestList.replaceChildren();
  if (!requests.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No requests match this filter.";
    elements.requestList.append(empty);
    return;
  }
  for (const request of requests) {
    const card = document.createElement("article");
    card.className = "request-card";
    const content = document.createElement("div");
    const kicker = document.createElement("p");
    kicker.className = "step";
    kicker.textContent = `Request #${request.id} · ${formatDate(request.created_at)}`;
    const title = document.createElement("h3");
    title.textContent = request.title;
    const summary = document.createElement("p");
    summary.textContent = request.ai_summary;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.append(tag(request.status), tag(request.category), tag(request.priority));
    content.append(kicker, title, summary, meta);
    const actions = document.createElement("div");
    actions.className = "card-actions";
    const open = document.createElement("button");
    open.type = "button";
    open.className = "secondary";
    open.textContent = request.status === "Awaiting review" ? "Review" : "View details";
    open.addEventListener("click", () => openReview(request.id));
    actions.append(open);
    card.append(content, actions);
    elements.requestList.append(card);
  }
}

function tag(value) {
  const element = document.createElement("span");
  element.className = `tag ${value.replaceAll(" ", "-")}`;
  element.textContent = value;
  return element;
}

async function openReview(id) {
  setMessage(elements.reviewMessage, "");
  try {
    const request = await api(`/api/requests/${id}`);
    document.querySelector("#review-id").value = request.id;
    const context = document.querySelector("#request-context");
    context.replaceChildren();
    const heading = document.createElement("strong");
    heading.textContent = `${request.title} — submitted by ${request.requester}`;
    const description = document.createElement("p");
    description.textContent = request.description;
    context.append(heading, description);
    populateSelect("#review-category", categories, request.category);
    populateSelect("#review-priority", priorities, request.priority);
    document.querySelector("#review-summary").value = request.ai_summary;
    document.querySelector("#review-reply").value = request.suggested_reply;
    document.querySelector("#reviewer").value = request.reviewed_by || managerReviewer;
    document.querySelector("#review-comment").value = request.review_comment || "";
    const isFinal = request.status !== "Awaiting review";
    for (const selector of ["#review-category", "#review-priority", "#review-summary", "#review-reply", "#review-comment", "#approve-button", "#reject-button"]) {
      document.querySelector(selector).disabled = isFinal;
    }
    document.querySelector("#review-heading").textContent = isFinal ? `${request.status} request #${request.id}` : `Review request #${request.id}`;
    elements.dialog.showModal();
  } catch (error) {
    setMessage(elements.queueMessage, error.message, "error");
  }
}

function populateSelect(selector, values, selected) {
  const select = document.querySelector(selector);
  select.replaceChildren(...values.map(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    option.selected = value === selected;
    return option;
  }));
}

async function submitDecision(decision) {
  const comment = document.querySelector("#review-comment").value.trim();
  if (decision === "reject" && !comment) {
    setMessage(elements.reviewMessage, "Enter a decision note before rejecting.", "error");
    return;
  }
  const buttons = [document.querySelector("#approve-button"), document.querySelector("#reject-button")];
  buttons.forEach(button => { button.disabled = true; });
  try {
    const id = document.querySelector("#review-id").value;
    await api(`/api/requests/${id}/decision`, {
      method: "POST",
      body: {
        decision,
        review_comment: comment,
        category: document.querySelector("#review-category").value,
        priority: document.querySelector("#review-priority").value,
        ai_summary: document.querySelector("#review-summary").value,
        suggested_reply: document.querySelector("#review-reply").value,
      },
    });
    elements.dialog.close();
    await loadRequests();
    setMessage(elements.queueMessage, `Request #${id} was ${decision === "approve" ? "approved" : "rejected"}.`, "success");
  } catch (error) {
    setMessage(elements.reviewMessage, error.message, "error");
    buttons.forEach(button => { button.disabled = false; });
  }
}

async function updateQueueCount() {
  if (!managerAuthenticated) {
    elements.queueCount.textContent = "-";
    return;
  }
  try {
    const response = await api("/api/requests?status=Awaiting%20review");
    elements.queueCount.textContent = response.items.length;
  } catch {
    elements.queueCount.textContent = "?";
  }
}

async function api(path, options = {}) {
  const request = { ...options, headers: { ...(options.headers || {}) } };
  if (options.body) {
    request.headers["Content-Type"] = "application/json";
    request.body = JSON.stringify(options.body);
  }
  const response = await fetch(path, request);
  const payload = await response.json().catch(() => ({ error: "The server returned an unreadable response." }));
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

function setMessage(element, text, type = "") {
  element.textContent = text;
  element.className = `message${text ? ` show ${type}` : ""}`;
  element.setAttribute("role", type === "error" ? "alert" : "status");
  element.setAttribute("aria-live", type === "error" ? "assertive" : "polite");
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

if (location.pathname === "/manager") showView("manager");

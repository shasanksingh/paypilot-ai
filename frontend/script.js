const API_BASE = window.location.protocol === "file:" ? "http://localhost:5000" : window.location.origin;

const sectionTitles = {
    dashboard: "Command Center",
    "metric-detail": "Metric Overview",
    "payment-detail": "Payment Intelligence",
    orchestrator: "AI Orchestrator",
    bills: "Bills",
    account: "My Account",
    subscriptions: "Subscriptions",
    approvals: "Approvals",
    transactions: "Transactions",
    logs: "Agent Logs",
    about: "About & Guide"
};

const sectionIcons = {
    dashboard: '<path d="M4 4h7v7H4zM13 4h7v5h-7zM13 11h7v9h-7zM4 13h7v7H4z"></path>',
    "metric-detail": '<path d="M4 18V9M10 18V5M16 18v-7M3 18h18"></path>',
    "payment-detail": '<path d="M4 7h16v10H4z"></path><path d="M7 10h2M15 14h2"></path><circle cx="12" cy="12" r="2"></circle>',
    orchestrator: '<path d="M12 3v4M12 17v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M3 12h4M17 12h4"></path><circle cx="12" cy="12" r="4"></circle>',
    bills: '<path d="M7 3h10l2 2v16l-3-1.5-2 1-2-1-2 1-2-1L5 21V5z"></path><path d="M8 8h8M8 12h8M8 16h5"></path>',
    account: '<path d="M3 10l9-6 9 6"></path><path d="M5 10h14v9H5z"></path><path d="M8 10v9M12 10v9M16 10v9"></path>',
    subscriptions: '<path d="M7 7h10v10H7z"></path><path d="M4 10V6a2 2 0 0 1 2-2h4M14 20h4a2 2 0 0 0 2-2v-4"></path>',
    approvals: '<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z"></path><path d="M8.5 12.5l2 2 5-5"></path>',
    transactions: '<path d="M4 7h16M7 11h10M9 15h6"></path><rect x="4" y="5" width="16" height="14" rx="2"></rect>',
    logs: '<path d="M6 4h12v16H6z"></path><path d="M9 8h6M9 12h6M9 16h4"></path>',
    about: '<circle cx="12" cy="12" r="9"></circle><path d="M12 10v7M12 7h.01"></path>'
};

const currencyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
});

let currentDetailBillId = null;
let dashboardCache = null;
let activeMetric = null;
let lastOrchestratorContext = null;

document.addEventListener("DOMContentLoaded", () => {
    restoreSidebarState();
    restoreTheme();
    setupCursorRobo();
    setupScrollReveal();
    decoratePageHeroes();
    loadAll();
    checkHealth(false);
});

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;"
    }[char]));
}

function formatCurrency(value) {
    return currencyFormatter.format(Number(value || 0));
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.innerText = value;
}

function getSectionIconSvg(sectionId, className = "") {
    const body = sectionIcons[sectionId] || sectionIcons.dashboard;
    return `<svg class="${className}" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
}

function updatePageChrome(sectionId) {
    setText("page-title", sectionTitles[sectionId] || "PayPilot AI");
    const pageIcon = document.getElementById("page-icon");
    if (pageIcon) pageIcon.innerHTML = getSectionIconSvg(sectionId);
}

function decoratePageHeroes() {
    document.querySelectorAll(".page-section > .page-hero").forEach(hero => {
        const section = hero.closest(".page-section");
        const sectionId = section ? section.id : "dashboard";
        if (hero.querySelector(".page-hero-icon")) return;

        const icon = document.createElement("span");
        icon.className = "page-hero-icon";
        icon.innerHTML = getSectionIconSvg(sectionId);
        hero.prepend(icon);
    });
}

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.className = `toast ${type} show`;
    toast.innerText = message;

    window.clearTimeout(showToast.timeout);
    showToast.timeout = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}

async function apiFetch(path, options = {}) {
    const { headers = {}, ...rest } = options;

    const response = await fetch(`${API_BASE}${path}`, {
        ...rest,
        headers: {
            "Content-Type": "application/json",
            ...headers
        }
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || data.message || "Request failed");
    return data;
}

function restoreTheme() {
    const savedTheme = window.localStorage.getItem("paypilot-theme") || "light";
    document.body.classList.toggle("dark-mode", savedTheme === "dark");
    updateThemeLabel();
}

function toggleTheme() {
    document.body.classList.toggle("dark-mode");
    window.localStorage.setItem("paypilot-theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
    updateThemeLabel();
}

function updateThemeLabel() {
    const toggle = document.querySelector(".theme-toggle");
    if (!toggle) return;

    const isDark = document.body.classList.contains("dark-mode");
    const label = isDark ? "Switch to light mode" : "Switch to dark mode";
    toggle.setAttribute("aria-label", label);
    toggle.setAttribute("title", label);
    toggle.innerHTML = isDark
        ? `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"></path></svg>`
        : `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z"></path></svg>`;
}

function restoreSidebarState() {
    const shell = document.getElementById("app-shell");
    if (!shell) return;

    if (window.localStorage.getItem("paypilot-sidebar") === "collapsed") {
        shell.classList.add("sidebar-collapsed");
    }

    updateSidebarToggleState();
}

function toggleSidebar() {
    const shell = document.getElementById("app-shell");
    if (!shell) return;

    shell.classList.toggle("sidebar-collapsed");
    window.localStorage.setItem(
        "paypilot-sidebar",
        shell.classList.contains("sidebar-collapsed") ? "collapsed" : "expanded"
    );
    updateSidebarToggleState();
}

function updateSidebarToggleState() {
    const shell = document.getElementById("app-shell");
    const toggle = document.querySelector(".sidebar-toggle");
    if (!shell || !toggle) return;

    const collapsed = shell.classList.contains("sidebar-collapsed");
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggle.setAttribute("title", collapsed ? "Open navigation" : "Collapse navigation");
}

function loadAll() {
    loadDashboard();
    loadBills();
    loadAccount();
    loadSubscriptions();
    loadApprovals();
    loadTransactions();
    loadLogs();
}

function switchSection(sectionId, element) {
    document.querySelectorAll(".page-section").forEach(section => {
        section.classList.remove("active-section");
    });

    const section = document.getElementById(sectionId);
    if (section) section.classList.add("active-section");

    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });

    if (element) {
        element.classList.add("active");
    } else {
        const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
        if (navItem) navItem.classList.add("active");
    }

    updatePageChrome(sectionId);
    document.querySelector(".main-content")?.scrollTo({ top: 0, behavior: "smooth" });
    window.scrollTo({ top: 0, behavior: "smooth" });

    if (sectionId === "orchestrator") {
        resetOrchestratorView();
    }

    revealActiveSectionContent();
}

function switchSectionFromCode(sectionId) {
    switchSection(sectionId);
}

function openGuideTarget(sectionId) {
    switchSectionFromCode(sectionId);
}

function openGuideTargetFromKey(event, sectionId) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openGuideTarget(sectionId);
}

async function checkHealth(showMessage = true) {
    try {
        const data = await apiFetch("/api/health");
        const label = data.remote_llm_enabled ? "AI routing active" : "Rule engine active";
        if (showMessage) showToast(`${label}. Safety checks are online.`);
    } catch (error) {
        if (showMessage) showToast(error.message, "error");
    }
}

async function setupDatabase() {
    try {
        const data = await apiFetch("/api/setup", { method: "POST" });
        showToast(data.message);
        currentDetailBillId = null;
        loadAll();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function loadDashboard() {
    try {
        const data = await apiFetch("/api/dashboard");
        dashboardCache = data;

        setText("balance", formatCurrency(data.user.balance));
        setText("orchestrator-balance", formatCurrency(data.user.balance));
        setText("pending-bills", data.stats.pending_bills);
        setText("risky-items", data.stats.risky_items);
        setText("transactions-count", data.stats.completed_transactions);
        setText("total-pending", formatCurrency(data.stats.total_pending_amount));

        renderList("dashboard-bills", data.bills.slice(0, 4), bill => renderBillCard(bill, false), "No pending bills.");
        renderList("dashboard-subscriptions", data.subscriptions.slice(0, 3), renderSubscriptionCard, "No subscriptions found.");
        renderRiskRadar(data);

        if (activeMetric && document.getElementById("metric-detail").classList.contains("active-section")) {
            renderMetricDetail(activeMetric);
        }
    } catch (error) {
        showToast(error.message, "error");
    }
}

function openDashboardMetric(metric) {
    activeMetric = metric;
    renderMetricDetail(metric);
    switchSectionFromCode("metric-detail");
}

function openDashboardMetricFromKey(event, metric) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openDashboardMetric(metric);
}

function getMetricConfig(metric) {
    const configs = {
        balance: {
            kicker: "Cash Safety",
            title: "Safe Balance Overview",
            copy: "See how the current wallet balance holds up against near-term payments and risk pressure.",
            heading: "Balance Impact Queue"
        },
        pending: {
            kicker: "Bills",
            title: "Pending Bills Overview",
            copy: "All unpaid bills sorted for quick review. Open any payment to inspect risk, policy, and method choice.",
            heading: "Pending Bills"
        },
        total: {
            kicker: "Exposure",
            title: "Total Pending Amount",
            copy: "A money-weighted view of pending obligations, with larger payments surfaced first.",
            heading: "Amount Exposure"
        },
        risk: {
            kicker: "Safety",
            title: "Risky Bills Overview",
            copy: "Payments with duplicate, suspicious, or waste signals that deserve extra attention.",
            heading: "Risk Review Queue"
        },
        completed: {
            kicker: "History",
            title: "Completed Transactions",
            copy: "Payments that cleared the human approval and mock execution flow.",
            heading: "Completed Payments"
        }
    };

    return configs[metric] || configs.pending;
}

function renderMetricDetail(metric) {
    if (!dashboardCache) {
        setText("metric-detail-title", "Loading overview...");
        return;
    }

    const bills = dashboardCache.bills || [];
    const transactions = dashboardCache.transactions || [];
    const config = getMetricConfig(metric);
    let items = bills;

    if (metric === "risk") {
        items = bills.filter(bill => getRiskClass(bill.risk_hint) !== "low");
    } else if (metric === "total") {
        items = [...bills].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0));
    } else if (metric === "balance") {
        items = [...bills].sort((a, b) => new Date(a.due_date) - new Date(b.due_date));
    } else if (metric === "completed") {
        items = transactions;
    }

    setText("metric-detail-kicker", config.kicker);
    setText("metric-detail-title", config.title);
    setText("metric-detail-copy", config.copy);
    setText("metric-primary-heading", config.heading);
    setText("metric-primary-count", `${items.length} ${items.length === 1 ? "item" : "items"}`);

    if (metric === "completed") {
        renderList("metric-detail-list", items, renderTransactionMetricCard, "No completed transactions yet.");
    } else {
        renderList("metric-detail-list", items, bill => renderMetricBillCard(bill, metric), "No related bills found.");
    }

    renderMetricInsights(metric, items);
}

function renderMetricBillCard(bill, metric) {
    const balance = Number((dashboardCache && dashboardCache.user && dashboardCache.user.balance) || 0);
    const afterPayment = balance - Number(bill.amount || 0);
    const amountNote = metric === "balance"
        ? `After payment ${formatCurrency(afterPayment)}`
        : `Share of pending ${getAmountShare(bill.amount)}%`;

    return `
        <div class="bill-card clickable metric-item" onclick="openPaymentPage(${Number(bill.id)})">
            <div class="card-header">
                <div>
                    <h4>${escapeHtml(bill.biller_name)}</h4>
                    <p>${escapeHtml(String(bill.category || "").replace("_", " "))}</p>
                </div>
                <span class="badge ${getRiskClass(bill.risk_hint)}">${getRiskLabel(bill.risk_hint)}</span>
            </div>
            <div class="metric-strip">
                <span>${formatCurrency(bill.amount)}</span>
                <span>Due ${escapeHtml(bill.due_date)}</span>
                <span>${amountNote}</span>
            </div>
        </div>
    `;
}

function renderTransactionMetricCard(item) {
    return `
        <div class="transaction-card">
            <div class="card-header">
                <div>
                    <h4>${escapeHtml(item.biller_name || "Unknown biller")}</h4>
                    <p>${escapeHtml(item.transaction_ref || "transaction")}</p>
                </div>
                <span class="badge ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span>
            </div>
            <div class="meta">${formatCurrency(item.amount)} · ${escapeHtml(item.payment_method)} · Risk score ${escapeHtml(item.risk_score)}</div>
        </div>
    `;
}

function getAmountShare(amount) {
    const total = Number((dashboardCache && dashboardCache.stats && dashboardCache.stats.total_pending_amount) || 0);
    if (!total) return 0;
    return Math.round((Number(amount || 0) / total) * 100);
}

function renderMetricInsights(metric, items) {
    const container = document.getElementById("metric-detail-insights");
    if (!container || !dashboardCache) return;

    const bills = dashboardCache.bills || [];
    const risky = bills.filter(bill => getRiskClass(bill.risk_hint) !== "low");
    const total = bills.reduce((sum, bill) => sum + Number(bill.amount || 0), 0);
    const selectedTotal = items.reduce((sum, item) => sum + Number(item.amount || 0), 0);
    const largest = bills.reduce((winner, bill) => Number(bill.amount || 0) > Number((winner || {}).amount || 0) ? bill : winner, null);
    const balanceAfterPending = Number(dashboardCache.user.balance || 0) - total;
    const categoryMap = bills.reduce((map, bill) => {
        const category = String(bill.category || "other").replace("_", " ");
        map[category] = (map[category] || 0) + Number(bill.amount || 0);
        return map;
    }, {});
    const topCategory = Object.entries(categoryMap).sort((a, b) => b[1] - a[1])[0];

    const insights = [
        ["Selected exposure", formatCurrency(selectedTotal)],
        ["Risk attention", `${risky.length} flagged ${risky.length === 1 ? "bill" : "bills"}`],
        ["Post-clearance balance", formatCurrency(balanceAfterPending)],
        ["Largest obligation", largest ? `${largest.biller_name} · ${formatCurrency(largest.amount)}` : "None"],
        ["Top category", topCategory ? `${topCategory[0]} · ${formatCurrency(topCategory[1])}` : "None"]
    ];

    if (metric === "completed") {
        insights[0] = ["Cleared value", formatCurrency(selectedTotal)];
        insights[2] = ["Approval discipline", "Human approved before execution"];
    }

    container.innerHTML = `
        <div class="insight-stack">
            ${insights.map(([label, value]) => `
                <div class="insight-row">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </div>
            `).join("")}
        </div>
        <div class="pilot-note">
            <strong>PayPilot Signal</strong>
            <p>${escapeHtml(getMetricSignal(metric, risky.length, balanceAfterPending))}</p>
        </div>
    `;
}

function getMetricSignal(metric, riskyCount, balanceAfterPending) {
    if (metric === "risk") return "Risk-first triage makes the demo feel less like a bill list and more like a payment command desk.";
    if (metric === "balance") return balanceAfterPending >= 0
        ? "Cash runway remains positive after clearing every pending bill."
        : "Clearing everything now would break the safe-balance boundary.";
    if (metric === "completed") return "Completed payments preserve an audit trail of risk score, method, and orchestration decision.";
    if (riskyCount > 0) return "Flagged bills should be reviewed before autopilot moves money.";
    return "No elevated risk signals are currently dominating the queue.";
}

function renderRiskRadar(data) {
    const radar = document.getElementById("risk-radar");
    const insights = document.getElementById("radar-insights");
    if (!radar || !insights) return;

    const bills = (data && data.bills) || [];
    if (!bills.length) {
        radar.innerHTML = '<div class="empty-state">No radar signals yet.</div>';
        insights.innerHTML = "";
        return;
    }

    const maxAmount = Math.max(...bills.map(bill => Number(bill.amount || 0)), 1);
    const today = new Date();
    const visibleBills = bills.slice(0, 10);
    const dueSortedIds = [...visibleBills]
        .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
        .map(bill => Number(bill.id));
    const amountSortedIds = [...visibleBills]
        .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
        .map(bill => Number(bill.id));
    const quadrantCounts = { safe: 0, watch: 0, urgent: 0, review: 0 };
    const quadrantSlots = {
        safe: { x: 24, y: 74, label: "Safe queue" },
        watch: { x: 74, y: 74, label: "Watch" },
        urgent: { x: 24, y: 26, label: "Act first" },
        review: { x: 74, y: 26, label: "Review" }
    };
    const maxPerQuadrant = Math.max(2, Math.ceil(visibleBills.length / 4) + 1);

    function rankedValue(ids, billId) {
        const index = ids.indexOf(Number(billId));
        if (ids.length <= 1 || index < 0) return 0.5;
        return 1 - (index / (ids.length - 1));
    }

    function chooseRadarQuadrant(riskClass, urgencyRank, amountRank) {
        let quadrant = "safe";
        if (riskClass === "high" || (riskClass === "medium" && urgencyRank >= 0.5)) {
            quadrant = "review";
        } else if (amountRank >= 0.58 || riskClass === "medium") {
            quadrant = "watch";
        } else if (urgencyRank >= 0.58) {
            quadrant = "urgent";
        }

        if (quadrantCounts[quadrant] < maxPerQuadrant) return quadrant;
        return Object.keys(quadrantCounts).sort((a, b) => quadrantCounts[a] - quadrantCounts[b])[0];
    }

    radar.innerHTML = visibleBills.map((bill, index) => {
        const daysUntilDue = Math.max(0, Math.ceil((new Date(bill.due_date) - today) / 86400000));
        const riskClass = getRiskClass(bill.risk_hint);
        const urgencyRank = rankedValue(dueSortedIds, bill.id);
        const amountRank = rankedValue(amountSortedIds, bill.id);
        const quadrant = chooseRadarQuadrant(riskClass, urgencyRank, amountRank);
        const slot = quadrantSlots[quadrant];
        quadrantCounts[quadrant] += 1;
        const spreadX = ((quadrantCounts[quadrant] - 1) % 3 - 1) * 8;
        const spreadY = (Math.floor((quadrantCounts[quadrant] - 1) / 3) - 0.5) * 8;
        const fineJitterX = ((index % 2) ? 3 : -3);
        const fineJitterY = ((index % 3) - 1) * 2;
        const amountPressure = Math.max(12, Math.min(88, slot.x + spreadX + fineJitterX));
        const urgency = Math.max(12, Math.min(88, slot.y + spreadY + fineJitterY));
        const dotSize = Math.round(26 + (Number(bill.amount || 0) / maxAmount) * 18);
        const dueLabel = daysUntilDue === 0 ? "due today" : `due in ${daysUntilDue}d`;

        return `
            <button class="radar-dot ${riskClass}" style="left:${amountPressure}%; top:${urgency}%; --dot-size:${dotSize}px;" onclick="openPaymentPage(${Number(bill.id)})" title="${escapeHtml(`${bill.biller_name} · ${formatCurrency(bill.amount)} · ${dueLabel} · ${slot.label}`)}">
                <span>${escapeHtml(bill.biller_name.slice(0, 1))}</span>
            </button>
        `;
    }).join("") + `
        <span class="radar-axis y-axis">Urgency</span>
        <span class="radar-axis x-axis">Amount pressure</span>
        <span class="radar-quadrant low-zone">Safe queue</span>
        <span class="radar-quadrant watch-zone">Watch</span>
        <span class="radar-quadrant urgent-zone">Act first</span>
        <span class="radar-quadrant danger-zone">Review</span>
    `;

    const riskyBills = bills.filter(bill => getRiskClass(bill.risk_hint) !== "low");
    const urgentBills = bills.filter(bill => {
        const daysUntilDue = Math.ceil((new Date(bill.due_date) - today) / 86400000);
        return daysUntilDue <= 3;
    });
    const totalExposure = bills.reduce((sum, bill) => sum + Number(bill.amount || 0), 0);
    const largestBill = bills.reduce((winner, bill) => Number(bill.amount || 0) > Number((winner || {}).amount || 0) ? bill : winner, null);
    const nextDue = [...bills].sort((a, b) => new Date(a.due_date) - new Date(b.due_date))[0];

    insights.innerHTML = `
        <div class="radar-stat"><span>Flagged</span><strong>${riskyBills.length}</strong></div>
        <div class="radar-stat"><span>Due soon</span><strong>${urgentBills.length}</strong></div>
        <div class="radar-stat"><span>Total exposure</span><strong>${formatCurrency(totalExposure)}</strong></div>
        <div class="radar-stat"><span>Largest</span><strong>${escapeHtml(largestBill ? largestBill.biller_name : "None")}</strong></div>
        <div class="radar-stat"><span>Next due</span><strong>${escapeHtml(nextDue ? nextDue.biller_name : "None")}</strong></div>
        <div class="radar-legend">
            <span><i class="low"></i>Normal</span>
            <span><i class="medium"></i>Medium</span>
            <span><i class="high"></i>High</span>
        </div>
        <p>Higher dots are more urgent. Dots farther right carry more amount pressure. Click any signal for full payment intelligence.</p>
    `;
}

async function loadBills() {
    try {
        const bills = await apiFetch("/api/bills");
        renderList("bills-list", bills, bill => renderBillCard(bill, true), "No pending bills.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function loadAccount() {
    try {
        const data = await apiFetch("/api/account");
        renderAccount(data);
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderAccount(data) {
    const summary = data.summary || {};
    const rules = data.rules || {};
    const methods = data.payment_methods || [];
    const autopayBills = data.autopay_ready_bills || [];
    const riskBills = data.risk_watchlist || [];

    setText("account-balance", formatCurrency((data.user && data.user.balance) || 0));
    setText("recommended-minimum-balance", formatCurrency(summary.recommended_minimum_balance));
    setText("minimum-balance", formatCurrency(summary.minimum_safe_balance));
    setText("safe-buffer", formatCurrency(summary.safe_buffer));
    setText("after-pending-balance", formatCurrency(summary.balance_after_all_pending));
    setText("autopay-count", `${autopayBills.length} ${autopayBills.length === 1 ? "item" : "items"}`);
    setText("watchlist-count", `${riskBills.length} ${riskBills.length === 1 ? "item" : "items"}`);

    const recommendedGap = Number((data.user && data.user.balance) || 0) - Number(summary.recommended_minimum_balance || 0);
    const afterPendingStatus = summary.balance_after_all_pending >= summary.minimum_safe_balance
        ? "Even after pending bills, the account stays above the safety floor."
        : "Paying every pending bill now would move the account below the safety floor.";
    setText(
        "balance-guidance",
        `Recommended minimum is based on your balance rule and pending exposure. Current gap: ${formatCurrency(recommendedGap)}. ${afterPendingStatus}`
    );

    document.getElementById("account-rules").innerHTML = `
        <div class="rule-tile"><span>Minimum safe balance</span><strong>${formatCurrency(rules.minimum_safe_balance)}</strong></div>
        <div class="rule-tile"><span>Review required above</span><strong>${formatCurrency(rules.approval_required_above)}</strong></div>
        <div class="rule-tile"><span>Low-risk autopay</span><strong>Enabled</strong></div>
        <div class="rule-tile"><span>High risk blocking</span><strong>${rules.block_high_risk ? "Enabled" : "Disabled"}</strong></div>
        <div class="rule-tile"><span>Cashback preference</span><strong>${rules.prefer_cashback ? "Preferred" : "Neutral"}</strong></div>
    `;

    renderList("account-methods", methods, renderAccountMethod, "No payment methods found.");
    renderList("account-autopay-list", autopayBills, bill => renderBillCard(bill, false), "No bills are autopay-ready right now.");
    renderList("account-risk-list", riskBills, bill => renderBillCard(bill, false), "No risk watchlist items.");
}

function renderAccountMethod(method) {
    return `
        <div class="method-card account-method">
            <div class="card-header">
                <div>
                    <h4>${escapeHtml(method.method_type)} via ${escapeHtml(method.provider)}</h4>
                    <p>${escapeHtml(method.masked_identifier)}</p>
                </div>
                <span class="badge ${method.is_default ? "low" : "pending"}">${method.is_default ? "Default" : "Available"}</span>
            </div>
            <div class="metric-strip">
                <span>Limit ${formatCurrency(method.available_balance)}</span>
                <span>Fee ${formatCurrency(method.fee)}</span>
                <span>Cashback ${formatCurrency(method.cashback)}</span>
            </div>
        </div>
    `;
}

async function addPaymentMethod(event) {
    event.preventDefault();

    const payload = {
        method_type: document.getElementById("new-method-type").value,
        provider: document.getElementById("new-method-provider").value.trim(),
        identifier: document.getElementById("new-method-identifier").value.trim(),
        available_balance: Number(document.getElementById("new-method-limit").value || 0),
        cashback: Number(document.getElementById("new-method-cashback").value || 0),
        fee: Number(document.getElementById("new-method-fee").value || 0)
    };

    try {
        const data = await apiFetch("/api/payment-methods", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        document.getElementById("add-method-form").reset();
        document.getElementById("new-method-cashback").value = "0";
        document.getElementById("new-method-fee").value = "0";
        showToast(data.message || "Payment method added.");
        loadAccount();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function loadSubscriptions() {
    try {
        const subscriptions = await apiFetch("/api/subscriptions");
        renderList("subscriptions-list", subscriptions, renderSubscriptionCard, "No subscriptions found.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderList(containerId, items, renderer, emptyText) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `<div class="empty-state">${escapeHtml(emptyText)}</div>`;
        return;
    }

    container.innerHTML = items.map(renderer).join("");
}

function renderSubscriptionCard(item) {
    const riskClass = item.waste_score >= 75 ? "high" : item.waste_score >= 40 ? "medium" : "low";

    return `
        <div class="subscription-card">
            <div class="card-header">
                <div>
                    <h4>${escapeHtml(item.merchant_name)}</h4>
                    <p>${escapeHtml(item.billing_cycle)} subscription</p>
                </div>
                <span class="badge ${riskClass}">${escapeHtml(item.waste_score)}% Waste</span>
            </div>
            <div class="meta">
                ${formatCurrency(item.amount)} · Last used ${escapeHtml(item.last_used_days_ago)} days ago
            </div>
        </div>
    `;
}

function renderBillCard(bill, showAction = false) {
    const riskClass = getRiskClass(bill.risk_hint);
    const riskLabel = getRiskLabel(bill.risk_hint);

    return `
        <div class="bill-card clickable" onclick="openPaymentPage(${Number(bill.id)})">
            <div class="card-header">
                <div>
                    <h4>${escapeHtml(bill.biller_name)}</h4>
                    <p>${escapeHtml(bill.category).replace("_", " ")}</p>
                </div>
                <span class="badge ${riskClass}">${riskLabel}</span>
            </div>
            <div class="meta">
                ${formatCurrency(bill.amount)} · Due ${escapeHtml(bill.due_date)} · ${escapeHtml(bill.status)}
            </div>
            ${
                showAction
                    ? `<button class="small-action" onclick="event.stopPropagation(); openPaymentPage(${Number(bill.id)})">Open Payment</button>`
                    : ""
            }
        </div>
    `;
}

function getRiskClass(riskHint) {
    if (riskHint === "suspicious") return "high";
    if (riskHint === "geo_mismatch") return "high";
    if (riskHint === "vendor_change") return "high";
    if (riskHint === "possible_duplicate") return "high";
    if (riskHint === "invoice_spike") return "medium";
    if (riskHint === "cashflow_pressure") return "medium";
    if (riskHint === "trial_renewal") return "medium";
    if (riskHint === "unused_subscription") return "medium";
    return "low";
}

function getRiskLabel(riskHint) {
    if (riskHint === "suspicious") return "High Risk";
    if (riskHint === "geo_mismatch") return "Geo Mismatch";
    if (riskHint === "vendor_change") return "New Vendor";
    if (riskHint === "invoice_spike") return "Invoice Spike";
    if (riskHint === "cashflow_pressure") return "Cashflow Risk";
    if (riskHint === "trial_renewal") return "Trial Renewal";
    if (riskHint === "unused_subscription") return "Waste Risk";
    if (riskHint === "possible_duplicate") return "Duplicate Block";
    return "Normal";
}

function getStatusClass(status) {
    if (status === "approved" || status === "success" || status === "paid") return "low";
    if (status === "blocked" || status === "blocked_review" || status === "rejected" || status === "failed") return "high";
    return "pending";
}

async function openPaymentPage(billId) {
    currentDetailBillId = billId;
    switchSectionFromCode("payment-detail");

    setText("detail-biller", "Loading payment...");
    setText("detail-meta", "Running bill selector, risk, optimizer, compliance, and explainability agents.");
    document.getElementById("detail-summary").innerHTML = '<div class="empty-state">Loading payment intelligence...</div>';
    document.getElementById("detail-risk-box").innerHTML = '<div class="empty-state">Calculating risk...</div>';
    document.getElementById("detail-method-box").innerHTML = '<div class="empty-state">Optimizing method...</div>';
    document.getElementById("detail-timeline").innerHTML = '<div class="empty-state">Waiting for agents...</div>';

    try {
        const data = await apiFetch(`/api/bills/${billId}/analysis`);
        renderPaymentDetail(data);
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderPaymentDetail(data) {
    const bill = data.bill || {};
    const risk = data.risk || {};
    const compliance = data.compliance || {};
    const optimizer = data.optimizer || {};
    const method = optimizer.selected_method;
    const blockedReasons = [
        ...(risk.risk_reasons || []),
        ...(compliance.checks || [])
    ];

    currentDetailBillId = bill.id;

    setText("detail-biller", bill.biller_name || "Selected Payment");
    setText(
        "detail-meta",
        `${formatCurrency(bill.amount)} · Due ${bill.due_date || "n/a"} · ${String(bill.category || "payment").replace("_", " ")}`
    );

    const status = document.getElementById("detail-status");
    status.className = `badge ${data.status === "blocked" ? "high" : data.status === "auto_approved" || data.status === "override_approved" ? "low" : "pending"}`;
    status.innerText = data.status === "blocked"
        ? "Blocked"
        : data.status === "auto_approved"
            ? "Auto Executed"
            : data.status === "override_approved"
                ? "Paid by Override"
            : compliance.approval_required
                ? "Review Ready"
                : "Autopay Ready";

    const approvalButton = document.getElementById("detail-approval-button");
    const cancelButton = document.getElementById("detail-cancel-button");
    if (cancelButton) cancelButton.classList.add("hidden");

    if (data.status === "auto_approved" || data.status === "override_approved") {
        approvalButton.disabled = true;
        approvalButton.innerText = data.status === "override_approved" ? "Paid by Override" : "Paid by Orchestrator";
    } else if (bill.status !== "pending") {
        approvalButton.disabled = true;
        approvalButton.innerText = "Already Paid";
    } else if (data.status === "blocked" && data.review) {
        approvalButton.disabled = false;
        approvalButton.innerText = "Pay at Own Risk";
        approvalButton.onclick = payAtOwnRiskFromDetail;
        if (cancelButton) cancelButton.classList.remove("hidden");
    } else if (data.status === "blocked") {
        approvalButton.disabled = false;
        approvalButton.innerText = "Review Risk";
        approvalButton.onclick = prepareApprovalFromDetail;
        if (cancelButton) cancelButton.classList.remove("hidden");
    } else if (data.approval && data.approval.status === "pending") {
        approvalButton.disabled = false;
        approvalButton.innerText = "Open Approval";
        approvalButton.onclick = () => openApprovalFromChat(Number(data.approval.approval_id || 0));
    } else {
        approvalButton.disabled = false;
        approvalButton.innerText = compliance.approval_required ? "Prepare Approval" : "Pay Safely";
        approvalButton.onclick = prepareApprovalFromDetail;
    }

    document.getElementById("detail-summary").innerHTML = `
        <div><span>Amount</span><strong>${formatCurrency(bill.amount)}</strong></div>
        <div><span>Status</span><strong>${escapeHtml(bill.status || "n/a")}</strong></div>
        <div><span>Category</span><strong>${escapeHtml(String(bill.category || "n/a").replace("_", " "))}</strong></div>
        <div><span>After Payment</span><strong>${formatCurrency(compliance.after_payment_balance)}</strong></div>
    `;

    document.getElementById("detail-risk-box").innerHTML = `
        ${
            data.status === "blocked"
                ? `<div class="blocked-note">
                    <strong>${escapeHtml(data.message || "This payment is blocked by policy.")}</strong>
                    <span>Review the risk reasons below. If you still want to continue, use Pay at Own Risk after acknowledging the warning, or cancel the payment.</span>
                    <ul>${blockedReasons.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
                </div>`
                : ""
        }
        <div class="risk-meter">
            <div class="risk-score">${escapeHtml(risk.risk_score || 0)}</div>
            <div>
                <span class="badge ${risk.risk_level === "high" ? "high" : risk.risk_level === "medium" ? "medium" : "low"}">
                    ${escapeHtml(risk.risk_level || "low")} risk
                </span>
                <p>${escapeHtml(risk.risk_summary || "Risk assessment completed.")}</p>
            </div>
        </div>
        <ul class="detail-list">
            ${(risk.risk_reasons || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
    `;

    document.getElementById("detail-method-box").innerHTML = method ? `
        <div class="method-card">
            <h4>${escapeHtml(method.method_type)} via ${escapeHtml(method.provider)}</h4>
            <p>${escapeHtml(method.masked_identifier || "")}</p>
            <div class="method-stats">
                <span>Score ${escapeHtml(method.final_score)}</span>
                <span>Fee ${formatCurrency(method.fee)}</span>
                <span>Cashback ${formatCurrency(method.cashback)}</span>
            </div>
        </div>
    ` : '<div class="empty-state">No suitable payment method found.</div>';

    renderExplanation(data.explanation, data, "detail-explanation-box");
    renderTimeline(data.timeline, "detail-timeline");
}

async function payAtOwnRiskFromDetail() {
    if (!currentDetailBillId) return;

    const accepted = window.confirm(
        "This payment is blocked because it is risky. If you continue, you accept the risk and PayPilot will execute it as your override. Continue?"
    );

    if (!accepted) return;

    const approvalButton = document.getElementById("detail-approval-button");

    try {
        if (approvalButton) {
            approvalButton.disabled = true;
            approvalButton.innerText = "Paying at own risk...";
        }

        const data = await apiFetch(`/api/bills/${currentDetailBillId}/override-pay`, {
            method: "POST",
            body: JSON.stringify({ confirm_risk: true })
        });

        renderPaymentDetail(data);
        syncBalanceFromExecution(data);
        loadAll();
        showToast(data.message || "Payment executed after risk acknowledgement.");
    } catch (error) {
        if (approvalButton) {
            approvalButton.disabled = false;
            approvalButton.innerText = "Pay at Own Risk";
        }
        showToast(error.message, "error");
    }
}

async function cancelRiskPaymentFromDetail() {
    if (!currentDetailBillId) return;

    try {
        const data = await apiFetch(`/api/bills/${currentDetailBillId}/cancel-risk-payment`, { method: "POST" });
        showToast(data.message || "Payment cancelled.");
        switchSectionFromCode("bills");
        loadAll();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function prepareApprovalFromDetail() {
    if (!currentDetailBillId) return;

    const approvalButton = document.getElementById("detail-approval-button");
    const previousLabel = approvalButton ? approvalButton.innerText : "";

    try {
        if (approvalButton) {
            approvalButton.disabled = true;
            approvalButton.innerText = previousLabel === "Pay Safely" ? "Paying..." : "Preparing...";
        }

        const data = await apiFetch(`/api/bills/${currentDetailBillId}/prepare-approval`, { method: "POST" });

        renderPaymentDetail(data);
        syncBalanceFromExecution(data);
        loadAll();
        showToast(
            data.status === "auto_approved"
                ? "Safe payment executed by orchestration."
                : data.status === "blocked"
                    ? "Payment is blocked. Review record is ready."
                : data.approval && data.approval.reused_existing
                    ? "Existing approval is ready."
                    : "Approval request prepared."
        );
    } catch (error) {
        if (approvalButton) {
            approvalButton.disabled = false;
            approvalButton.innerText = previousLabel || "Prepare Approval";
        }
        showToast(error.message, "error");
    }
}

function usePrompt(prompt) {
    setText("prompt-hint", prompt);
    document.getElementById("user-message").value = prompt;
}

async function runPrompt(prompt) {
    switchSectionFromCode("orchestrator");
    document.getElementById("user-message").value = prompt;
    await sendMessage();
}

function resetOrchestratorView() {
    const orchestrator = document.getElementById("orchestrator");
    if (!orchestrator) return;

    orchestrator.classList.remove("orchestrator-running", "orchestrator-active");
    orchestrator.classList.add("orchestrator-idle");
    setText("prompt-hint", "Ready for a payment request.");

    const chatBox = document.getElementById("chat-box");
    if (chatBox) {
        chatBox.innerHTML = `
            <div class="bot-message">
                Hi, I am PayPilot AI. I auto-clear safe payments and ask for approval when risk or policy requires it.
            </div>
        `;
    }

    const explanationBox = document.getElementById("explanation-box");
    if (explanationBox) {
        explanationBox.innerHTML = '<div class="empty-state">No decision yet.</div>';
    }

    const timeline = document.getElementById("agent-timeline");
    if (timeline) {
        timeline.innerHTML = '<div class="empty-state">No timeline available.</div>';
    }

    const plan = document.getElementById("plan-box");
    if (plan) {
        plan.innerHTML = '<div class="empty-state">No payment plan generated yet.</div>';
    }

    const suggestions = document.getElementById("context-suggestions");
    if (suggestions) suggestions.innerHTML = "";
}

async function sendMessage() {
    const input = document.getElementById("user-message");
    const message = input.value.trim();
    if (!message) return;

    startOrchestratorRun();
    appendChatMessage(message, "user-message");
    input.value = "";
    setText("prompt-hint", "Agents are evaluating intent, plan, risk, method, policy, and smart approval.");

    await callAgent({ message, context: lastOrchestratorContext });
}

async function callAgent(payload) {
    const loadingMessage = appendChatMessage("Running multi-agent payment orchestration...", "bot-message muted");

    try {
        const data = await apiFetch("/api/agent/chat", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        loadingMessage.remove();
        appendChatMessage(buildAgentResponse(data), "bot-message");
        if (data.status === "approval_required") {
            appendApprovalFollowUp(data);
        } else if (data.status === "blocked") {
            appendBlockedReviewFollowUp(data);
        }
        updateContextSuggestions(data);
        syncBalanceFromExecution(data);
        revealOrchestratorResults();

        if (data.status === "subscription_analysis" || data.status === "subscription_review") {
            renderSubscriptionAnalysis(data);
            renderPlan([]);
        } else {
            renderExplanation(data.explanation, data);
            renderPlan(data.plan || []);
        }

        renderTimeline(data.timeline);
        await loadDashboard();
        loadBills();
        loadAccount();
        loadApprovals();
        loadTransactions();
        loadLogs();
    } catch (error) {
        loadingMessage.remove();
        appendChatMessage(error.message, "bot-message error");
        showToast(error.message, "error");
    }
}

function startOrchestratorRun() {
    const orchestrator = document.getElementById("orchestrator");
    if (!orchestrator) return;

    orchestrator.classList.remove("orchestrator-idle", "orchestrator-active");
    orchestrator.classList.add("orchestrator-running");
}

function revealOrchestratorResults() {
    const orchestrator = document.getElementById("orchestrator");
    if (!orchestrator) return;

    orchestrator.classList.remove("orchestrator-idle", "orchestrator-running");
    orchestrator.classList.add("orchestrator-active");
}

function syncBalanceFromExecution(data) {
    const remaining = data && data.execution && data.execution.execution_result
        ? data.execution.execution_result.remaining_balance
        : null;

    if (remaining === null || remaining === undefined) return;

    const formattedBalance = formatCurrency(remaining);
    setText("balance", formattedBalance);
    setText("orchestrator-balance", formattedBalance);
    setText("account-balance", formattedBalance);
}

function setupCursorRobo() {
    const cursorRobo = document.getElementById("cursor-robo");
    if (!cursorRobo || window.matchMedia("(pointer: coarse)").matches) return;

    let targetX = window.innerWidth - 80;
    let targetY = 140;
    let currentX = targetX;
    let currentY = targetY;
    let idleTimer = null;
    let eyeDirection = 0;
    let tiltX = 8;
    let tiltY = -10;

    window.addEventListener("mousemove", event => {
        const previousTargetX = targetX;
        const previousTargetY = targetY;
        targetX = event.clientX + 18;
        targetY = event.clientY + 18;
        tiltY = Math.max(-18, Math.min(18, (targetX - previousTargetX) * 0.24));
        tiltX = Math.max(-12, Math.min(14, -(targetY - previousTargetY) * 0.18));
        cursorRobo.classList.add("is-awake");
        cursorRobo.classList.remove("is-thinking");
        cursorRobo.style.setProperty("--eye-x", "0px");
        cursorRobo.style.setProperty("--eye-y", "0px");

        window.clearTimeout(idleTimer);
        idleTimer = window.setTimeout(() => {
            cursorRobo.classList.add("is-thinking");
        }, 420);
    });

    function animateCursorRobo() {
        currentX += (targetX - currentX) * 0.12;
        currentY += (targetY - currentY) * 0.12;
        tiltX += (8 - tiltX) * 0.05;
        tiltY += (-10 - tiltY) * 0.05;
        if (cursorRobo.classList.contains("is-thinking")) {
            eyeDirection += 0.045;
            cursorRobo.style.setProperty("--eye-x", `${Math.sin(eyeDirection) * 2.2}px`);
            cursorRobo.style.setProperty("--eye-y", `${Math.cos(eyeDirection * 0.7) * 1.1}px`);
        }

        cursorRobo.style.transform = `translate3d(${currentX}px, ${currentY}px, 0) rotateX(${tiltX}deg) rotateY(${tiltY}deg) rotateZ(${tiltY * 0.15}deg)`;
        window.requestAnimationFrame(animateCursorRobo);
    }

    animateCursorRobo();
}

function setupScrollReveal() {
    const revealItems = document.querySelectorAll(
        ".hero-panel, .stats-grid, .pilot-lab, .grid-two, .panel, .page-hero, .account-hero, .account-grid, .orchestrator-hero, .automation-strip, .orchestrator-workspace, .orchestrator-results, .guide-card"
    );

    revealItems.forEach(item => item.classList.add("reveal-on-scroll"));

    if (!("IntersectionObserver" in window)) {
        revealItems.forEach(item => item.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.16 });

    revealItems.forEach(item => observer.observe(item));
}

function revealActiveSectionContent() {
    const activeSection = document.querySelector(".active-section");
    if (!activeSection) return;

    activeSection.querySelectorAll(".reveal-on-scroll").forEach((item, index) => {
        window.setTimeout(() => item.classList.add("is-visible"), index * 45);
    });
}

function appendChatMessage(message, className) {
    const chatBox = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.className = className;
    div.innerText = message;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

function appendApprovalFollowUp(data) {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;

    const bill = data.bill || {};
    const approval = data.approval || {};
    const div = document.createElement("div");
    div.className = "bot-message approval-follow-up";
    div.innerHTML = `
        <strong>Approval needed before execution.</strong>
        <span>Do you want to approve ${escapeHtml(bill.biller_name || "this payment")} for ${formatCurrency(bill.amount)}?</span>
        <button onclick="openApprovalFromChat(${Number(approval.approval_id || 0)})">Yes, open approval</button>
    `;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function appendBlockedReviewFollowUp(data) {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;

    const bill = data.bill || {};
    const review = data.review || {};
    const div = document.createElement("div");
    div.className = "bot-message approval-follow-up";
    div.innerHTML = `
        <strong>Blocked payment needs review.</strong>
        <span>${escapeHtml(bill.biller_name || "This payment")} was not executed. Review the risk details before deciding what to do next.</span>
        <button onclick="openApprovalFromChat(${Number(review.approval_id || 0)})">Open review</button>
    `;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function openApprovalFromChat(approvalId = 0) {
    switchSectionFromCode("approvals");
    loadApprovals();

    window.setTimeout(() => {
        const target = approvalId ? document.querySelector(`[data-approval-id="${approvalId}"]`) : null;
        if (target) {
            target.classList.add("highlight-approval");
            target.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }, 180);
}

function updateContextSuggestions(data) {
    const container = document.getElementById("context-suggestions");
    if (!container) return;

    const renderPills = suggestions => {
        container.innerHTML = `
            <span>Suggestions</span>
            ${suggestions.map(buildSuggestionPill).join("")}
        `;
    };

    if (data.status === "subscription_analysis") {
        const subscriptions = data.subscriptions || [];
        lastOrchestratorContext = { type: "subscriptions", items: subscriptions };
        const topItems = subscriptions.slice(0, 4);

        renderPills([
            ...topItems.map(item => ({
                label: `Review ${item.merchant_name}`,
                prompt: `Review ${item.merchant_name} subscription`
            })),
            { label: "Show pending bills", prompt: "Show pending bills" }
        ]);
        return;
    }

    if (data.status === "subscription_review") {
        const subscription = data.subscription || (data.subscriptions || [])[0] || {};
        lastOrchestratorContext = {
            type: "subscription_review",
            subscription
        };

        renderPills([
            { label: `Yes, pay ${subscription.merchant_name || "this subscription"}`, prompt: "yes" },
            { label: "No, don't pay", prompt: "no" },
            { label: "Review another", prompt: "Analyze my subscriptions and waste" }
        ]);
        return;
    }

    if (data.status === "subscription_declined") {
        lastOrchestratorContext = null;
        renderPills([
            { label: "Waste scan", prompt: "Analyze my subscriptions and waste" },
            { label: "Show pending bills", prompt: "Show pending bills" },
            { label: "Pay safe bill", prompt: "Pay my most urgent safe bill" }
        ]);
        return;
    }

    if (data.status === "no_bill_selected" && data.matched_subscription) {
        lastOrchestratorContext = null;
        renderPills([
            { label: "Open Subscriptions", section: "subscriptions" },
            { label: "Show pending bills", prompt: "Show pending bills" },
            { label: "Pay safe bill", prompt: "Pay my most urgent safe bill" }
        ]);
        return;
    }

    lastOrchestratorContext = null;
    renderPills(getTransactionSuggestions(data));
}

function buildSuggestionPill(item) {
    const label = escapeHtml(item.label || item.prompt || "Continue");
    let action = item.action;

    if (!action && item.section) {
        action = `switchSectionFromCode('${escapeJsString(item.section)}')`;
    }

    if (!action) {
        action = `runSuggestedPrompt('${escapeJsString(item.prompt || item.label)}')`;
    }

    return `<button onclick="${action}">${label}</button>`;
}

function getTransactionSuggestions(data) {
    const status = data.status;
    const bill = data.bill || {};
    const billName = bill.biller_name || "this bill";
    const approvalId = Number((data.approval && data.approval.approval_id) || 0);
    const reviewId = Number((data.review && data.review.approval_id) || 0);

    if (status === "approval_required") {
        return [
            { label: "Open approval", action: `openApprovalFromChat(${approvalId})` },
            { label: `Review ${billName}`, action: `openPaymentPage(${Number(bill.id || 0)})` },
            { label: "Find risky payments", prompt: "Find risky payments and explain why" }
        ];
    }

    if (status === "blocked") {
        return [
            reviewId
                ? { label: "Open blocked review", action: `openApprovalFromChat(${reviewId})` }
                : { label: `Review ${billName}`, action: `openPaymentPage(${Number(bill.id || 0)})` },
            { label: "Pay safe bill", prompt: "Pay my most urgent safe bill" },
            { label: "Show pending bills", prompt: "Show pending bills" }
        ];
    }

    if (status === "auto_approved" || status === "override_approved") {
        return [
            { label: "View transactions", section: "transactions" },
            { label: "Check balance", section: "account" },
            { label: "Pay next safe bill", prompt: "Pay my most urgent safe bill" }
        ];
    }

    if (status === "pending_bills") {
        return [
            { label: "Pay safe bill", prompt: "Pay my most urgent safe bill" },
            { label: "Risk scan", prompt: "Find risky payments and explain why" },
            { label: "Check account", section: "account" }
        ];
    }

    if (status === "no_bill_selected") {
        const backendSuggestions = (data.suggestions || []).slice(0, 3).map(prompt => ({
            label: prompt,
            prompt
        }));
        return backendSuggestions.length ? backendSuggestions : [
            { label: "Show pending bills", prompt: "Show pending bills" },
            { label: "Waste scan", prompt: "Analyze my subscriptions and waste" },
            { label: "Pay safe bill", prompt: "Pay my most urgent safe bill" }
        ];
    }

    if (status === "failed") {
        return [
            { label: "Show pending bills", prompt: "Show pending bills" },
            { label: "Check account", section: "account" },
            { label: "Try safe bill", prompt: "Pay my most urgent safe bill" }
        ];
    }

    return [
        { label: "Autopilot", prompt: "Manage my payments this week safely" },
        { label: "Risk scan", prompt: "Find risky payments and explain why" },
        { label: "Waste scan", prompt: "Analyze my subscriptions and waste" }
    ];
}

async function runSuggestedPrompt(prompt) {
    const input = document.getElementById("user-message");
    if (input) input.value = prompt;
    await sendMessage();
}

function escapeJsString(value) {
    return String(value ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

function buildAgentResponse(data) {
    if (data.status === "blocked") return `Blocked by Financial Safety Firewall: ${data.message}`;
    if (data.status === "auto_approved") {
        const remaining = data.execution && data.execution.execution_result
            ? data.execution.execution_result.remaining_balance
            : null;
        const balanceText = remaining === null ? "" : ` New balance: ${formatCurrency(remaining)}.`;
        return `Auto-approved and executed: ${formatCurrency(data.bill.amount)} to ${data.bill.biller_name}. Risk level: ${data.risk.risk_level}.${balanceText}`;
    }
    if (data.status === "override_approved") {
        const result = data.execution && data.execution.execution_result ? data.execution.execution_result : {};
        return `Paid after risk acknowledgement: ${formatCurrency(data.bill.amount)} to ${data.bill.biller_name}. Cashback credited: ${formatCurrency(result.cashback || 0)}. New balance: ${formatCurrency(result.remaining_balance)}.`;
    }
    if (data.status === "approval_required") return `Ready for approval: ${formatCurrency(data.bill.amount)} to ${data.bill.biller_name}. Risk level: ${data.risk.risk_level}. Do you want to continue? Click the approval button below.`;
    if (data.status === "subscription_analysis") return "Subscription waste analysis completed.";
    if (data.status === "subscription_review") return data.message || "Subscription reviewed. Reply yes to pay this reviewed subscription.";
    if (data.status === "subscription_declined") return data.message || "Payment cancelled. No payment was made.";
    if (data.status === "no_bill_selected" && data.matched_subscription) {
        return `${data.message} I will not pay a different bill automatically. Use the suggestions below to review subscriptions or choose a pending bill.`;
    }
    if (data.status === "failed" || data.status === "no_bill_selected") return data.message;
    return data.message || "Agent workflow completed.";
}

function renderSubscriptionAnalysis(data) {
    const box = document.getElementById("explanation-box");
    const isSingleReview = data.status === "subscription_review";
    const subscriptions = data.subscriptions || [];
    box.innerHTML = `
        <div class="decision-summary">
            <span class="badge medium">${isSingleReview ? "Focused Review" : "Waste Scan"}</span>
            <h4>${isSingleReview ? "Subscription Review" : "Subscription Waste Analysis"}</h4>
            <p>${escapeHtml(isSingleReview ? data.message : "PayPilot found subscriptions with elevated waste scores based on usage recency.")}</p>
        </div>
        ${subscriptions.map(renderSubscriptionCard).join("")}
    `;
}

function renderExplanation(explanation, data = {}, targetId = "explanation-box") {
    const box = document.getElementById(targetId);
    if (!box) return;

    if (!explanation) {
        box.innerHTML = '<div class="empty-state">No explanation available.</div>';
        return;
    }

    const bill = data.bill || {};
    const compliance = data.compliance || {};
    const optimizer = data.optimizer || {};
    const selectedMethod = optimizer.selected_method;
    const finalDecision = explanation.final_decision || "unknown";

    box.innerHTML = `
        <div class="decision-summary">
            <span class="badge ${finalDecision === "blocked" ? "high" : finalDecision === "allowed" ? "low" : "pending"}">
                ${escapeHtml(finalDecision).replace("_", " ").toUpperCase()}
            </span>
            <h4>${escapeHtml(explanation.summary || "Payment decision ready.")}</h4>
            <p>${escapeHtml(explanation.user_friendly_message || "")}</p>
        </div>

        <div class="decision-metrics">
            <div><span>Amount</span><strong>${formatCurrency(bill.amount)}</strong></div>
            <div><span>Risk</span><strong>${escapeHtml((data.risk && data.risk.risk_level) || "n/a")}</strong></div>
            <div><span>After Payment</span><strong>${formatCurrency(compliance.after_payment_balance)}</strong></div>
        </div>

        <div class="explanation-section">
            <h4>Why This Payment</h4>
            <ul>${(explanation.why_this_payment || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>

        <div class="explanation-section">
            <h4>Risk Explanation</h4>
            <ul>${(explanation.risk_explanation || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>

        <div class="explanation-section">
            <h4>Payment Method</h4>
            <p>${escapeHtml(explanation.method_explanation || "")}</p>
            ${selectedMethod ? `<p class="method-chip">${escapeHtml(selectedMethod.method_type)} · ${escapeHtml(selectedMethod.provider)} · score ${escapeHtml(selectedMethod.final_score)}</p>` : ""}
        </div>

        <div class="explanation-section">
            <h4>Policy Checks</h4>
            <ul>${(explanation.policy_explanation || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
    `;
}

function renderPlan(plan) {
    const container = document.getElementById("plan-box");
    if (!container) return;

    if (!plan || plan.length === 0) {
        container.innerHTML = '<div class="empty-state">No payment plan generated yet.</div>';
        return;
    }

    container.innerHTML = plan.slice(0, 8).map(item => `
        <div class="plan-row">
            <div>
                <strong>${escapeHtml(item.biller_name)}</strong>
                <span>${formatCurrency(item.amount)} · ${escapeHtml(item.due_date)}</span>
            </div>
            <span class="badge ${getRiskClass(item.risk_hint)}">${escapeHtml(item.priority).replace(/_/g, " ")}</span>
        </div>
    `).join("");
}

function renderTimeline(timeline, targetId = "agent-timeline") {
    const container = document.getElementById(targetId);
    if (!container) return;

    if (!timeline || timeline.length === 0) {
        container.innerHTML = '<div class="empty-state">No timeline available.</div>';
        return;
    }

    container.innerHTML = `<div class="workflow-timeline">${timeline.map((item, index) => `
        <div class="timeline-item" style="--step-index:${index}">
            <span>${index + 1}</span>
            <div>
                <h4>${escapeHtml(item.agent || "Agent")}</h4>
                <p>${escapeHtml(item.reasoning || "Agent completed its task.")}</p>
            </div>
        </div>
    `).join("")}</div>`;
}

async function loadApprovals() {
    try {
        const approvals = await apiFetch("/api/approvals");
        renderList("approvals-list", approvals, item => `
            <div class="approval-card" data-approval-id="${Number(item.id)}">
                <div class="card-header">
                    <div>
                        <h4>${escapeHtml(item.payee)}</h4>
                        <p>${formatCurrency(item.amount)}</p>
                    </div>
                    <span class="badge ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span>
                </div>
                <div class="meta">${escapeHtml(item.recommendation)}</div>
                ${
                    item.status === "pending"
                        ? `<div class="approval-actions"><button onclick="approvePayment(${Number(item.id)})">Approve & Execute</button><button class="reject" onclick="rejectPayment(${Number(item.id)})">Reject</button></div>`
                        : item.status === "blocked_review"
                            ? `<div class="approval-actions"><button onclick="openPaymentPage(${Number(item.bill_id)})">Review in Bills</button><span class="review-only-note">Decide from the payment review page.</span></div>`
                            : ""
                }
            </div>
        `, "No approval requests yet.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function approvePayment(approvalId) {
    try {
        const data = await apiFetch(`/api/approvals/${approvalId}/approve`, { method: "POST" });
        syncBalanceFromExecution(data);
        showToast(data.message || "Payment executed.");
        loadAll();
    } catch (error) {
        showToast(error.message, "error");
        loadAll();
    }
}

async function rejectPayment(approvalId) {
    try {
        const data = await apiFetch(`/api/approvals/${approvalId}/reject`, { method: "POST" });
        showToast(data.message || "Payment rejected.");
        loadApprovals();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function loadTransactions() {
    try {
        const transactions = await apiFetch("/api/transactions");
        renderList("transactions-list", transactions, item => `
            <div class="transaction-card">
                <div class="card-header">
                    <div>
                        <h4>${escapeHtml(item.biller_name || "Unknown biller")}</h4>
                        <p>${escapeHtml(item.transaction_ref)}</p>
                    </div>
                    <span class="badge ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span>
                </div>
                <div class="meta">${formatCurrency(item.amount)} · ${escapeHtml(item.payment_method)} · Risk score ${escapeHtml(item.risk_score)}</div>
            </div>
        `, "No transactions completed yet.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function loadLogs() {
    try {
        const logs = await apiFetch("/api/agent/logs");
        renderList("logs-list", logs, log => `
            <div class="log-card">
                <div class="card-header">
                    <div>
                        <h4>${escapeHtml(log.agent_name)}</h4>
                        <p>${escapeHtml(log.created_at)}</p>
                    </div>
                </div>
                <div class="meta">${escapeHtml(log.reasoning)}</div>
            </div>
        `, "No agent logs yet.");
    } catch (error) {
        showToast(error.message, "error");
    }
}

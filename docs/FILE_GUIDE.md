# PayPilot AI File Guide

Use this document to explain the project file by file during evaluation. The main idea is that PayPilot AI is not just a payment list; it is an agentic payment orchestration demo where multiple agents inspect a payment, decide whether it is safe, ask for approval when needed, execute safe payments, and keep an audit trail.

## Main User Flow

1. The user opens the frontend from `frontend/index.html`.
2. `frontend/script.js` calls backend APIs such as `/api/dashboard`, `/api/agent/chat`, `/api/approvals`, and `/api/transactions`.
3. `backend/app.py` receives the API request and calls the correct service or agent.
4. The main orchestration path runs through `backend/agents/orchestrator.py`.
5. The orchestrator calls specialist agents for intent, planning, bill selection, risk, reinforcement feedback, optimization, compliance, approval, execution, monitoring, and explanation.
6. Safe payments are executed automatically through a mock gateway.
7. Risky or policy-sensitive payments create an approval request and the frontend asks the user to open the Approval Queue.
8. Blocked payments create a `blocked_review` item so the user can inspect the review details.
9. After approval, the backend performs final checks and executes the payment.

## Frontend Files

### `frontend/index.html`

This is the main single-page application layout.

Important sections:
- Sidebar navigation: Command Center, AI Orchestrator, Bills, Account, Subscriptions, Approvals, Transactions, Agent Logs, and About.
- Command Center: dashboard cards, payment safety radar, upcoming payments, and subscription waste watch.
- Payment Detail: shows selected bill risk, method choice, explanation, and timeline.
- AI Orchestrator: chat console where the user asks PayPilot to pay or analyze bills.
- Approvals: human approval queue for payments that cannot execute automatically.
- About: explains the system, approval routing, explainability, learning signal, account rules, and demo flow.

### `frontend/script.js`

This contains almost all frontend logic.

Important sections:
- API helper: `apiFetch()` sends requests to Flask.
- Dashboard loaders: `loadDashboard()`, `loadBills()`, `loadAccount()`, `loadSubscriptions()`, `loadApprovals()`, `loadTransactions()`, and `loadLogs()`.
- Navigation: `switchSection()` changes visible app sections.
- Payment detail: `openPaymentPage()` and `renderPaymentDetail()` show bill intelligence.
- Orchestrator chat: `sendMessage()`, `callAgent()`, `buildAgentResponse()`, and `appendApprovalFollowUp()`.
- Follow-up safety: `appendBlockedReviewFollowUp()` and `updateContextSuggestions()` show review buttons and Copilot-style suggestion chips after risky or subscription-related prompts.
- Subscription context: `lastOrchestratorContext` remembers the focused subscription review, so replying `yes` pays that reviewed subscription only.
- Approval flow: `openApprovalFromChat()`, `approvePayment()`, and `rejectPayment()`.
- Rendering helpers: bill cards, transaction cards, risk labels, timelines, plans, and explanations.

### `frontend/styles.css`

This is the full visual styling for the app.

Important sections:
- CSS variables and theme colors.
- Sidebar, topbar, panels, cards, buttons, and badges.
- Dashboard hero, stats cards, and safety radar.
- Orchestrator workspace, chat messages, XAI panel, timeline, and plan.
- Approval cards and the highlighted approval follow-up state.
- Responsive layout for smaller screens.

## Backend Entry Point

### `backend/app.py`

This is the Flask API server.

Important routes:
- `/`: serves the frontend.
- `/api/health`: returns backend and model status.
- `/api/setup`: resets and seeds demo data.
- `/api/dashboard`: returns dashboard summary, bills, transactions, and subscriptions.
- `/api/account`: returns balance, rules, payment methods, autopay-ready bills, and watchlist.
- `/api/bills/<bill_id>/analysis`: runs instant payment detail analysis.
- `/api/bills/<bill_id>/prepare-approval`: prepares approval or executes safe payment from the detail page.
- `/api/agent/chat`: sends a user prompt to the orchestrator.
- `/api/approvals`: returns approval queue.
- `/api/approvals/<id>/approve`: approves and executes a pending payment.
- `/api/approvals/<id>/reject`: rejects a pending approval.
- `/api/transactions`: returns completed payments.
- `/api/agent/logs`: returns stored agent decisions.

## Agent Files

### `backend/agents/orchestrator.py`

This is the main brain of the backend workflow. It runs the agents in order and decides the final route.

Main sequence:
- Detect intent.
- Build a payment plan.
- Select the bill.
- Calculate risk.
- Add reinforcement feedback from previous approvals/rejections.
- Select best payment method.
- Check compliance rules.
- Generate explanation.
- Auto-execute safe payments.
- Create approval request for payments that need human approval.
- Create blocked review records for payments stopped by the firewall.
- Return the timeline to the frontend.

### `backend/agents/intent_agent.py`

Detects what the user wants from their message.

Example intents:
- Show pending bills.
- Analyze subscriptions.
- Autopilot payments.
- Pay a selected or urgent bill.

### `backend/agents/planning_agent.py`

Creates a safety-first plan from pending bills. It scores bills based on risk hints, amount, and payment safety.

Main idea:
- Normal low-value bills get higher priority.
- Suspicious, duplicate, vendor-change, geo-mismatch, and waste-risk bills get lower priority.
- High-value bills are marked for approval-style handling.

### `backend/agents/bill_selector_agent.py`

Chooses the bill that matches the user request. It can use a selected bill id or infer from the user message and current pending bills.

Important behavior:
- It matches biller names using exact text and meaningful name tokens.
- It recognizes subscription merchant names from the waste scan.
- If a specific name is requested but no pending bill matches, it refuses to pay an unrelated fallback bill.
- Focused subscription reviews return only the requested subscription, not the full subscription list.

### `backend/agents/risk_agent.py`

Calculates risk score and risk reasons.

Main checks:
- Suspicious merchant.
- Possible duplicate.
- Unused subscription.
- Vendor change.
- Invoice spike.
- Trial renewal.
- Geography mismatch.
- Cashflow pressure.
- High amount.

It can also ask the LLM for additional reasoning if remote LLM mode is configured.

### `backend/agents/reinforcement_agent.py`

Adds a lightweight reinforcement-learning style signal. It looks at previous human approval and rejection outcomes for similar categories or risk hints.

How to explain it:
- Approval is treated as positive reward.
- Rejection is treated as negative reward.
- The agent calculates approval confidence.
- Risky payments still stay in the approval loop, so learning does not bypass safety.

### `backend/agents/optimizer_agent.py`

Selects the best payment method. It considers method availability, fees, cashback, success rate, and suitability for the bill amount.

### `backend/agents/compliance_agent.py`

Checks payment safety rules.

Main rules:
- Do not go below minimum safe balance.
- Block high-risk payments when high-risk blocking is enabled.
- Require approval for elevated risk.
- Mark high-value payments for enhanced monitoring.

### `backend/agents/approval_agent.py`

Creates or reuses a human approval request. It prevents duplicate pending approvals for the same bill.

It can also create `blocked_review` records for payments that were stopped by the Financial Safety Firewall.

### `backend/agents/execution_agent.py`

Executes a payment through the mock gateway after orchestration or approval.

### `backend/agents/monitoring_agent.py`

Summarizes the result after execution. It records whether the payment succeeded and what should be monitored.

### `backend/agents/explainability_agent.py`

Creates user-facing explanations for why a payment was selected, what risks were found, which method was selected, and why the final decision was made.

## Service Files

### `backend/services/bill_service.py`

Reads pending bills, selected bills, creates subscription-payment bills when a reviewed subscription is approved, marks bills paid, and returns subscriptions.

### `backend/services/payment_service.py`

Reads payment methods, user balance, and user rules.

### `backend/services/approval_service.py`

Reads approval requests, finds pending approvals for a bill, and updates approval status.

### `backend/services/transaction_service.py`

Stores agent decision logs and reads transactions and logs for the frontend.

### `backend/services/mock_gateway.py`

Simulates real payment execution. It creates a transaction record, marks the bill as paid, reduces balance, and reduces the selected payment method's available limit.

## LLM Files

### `backend/llm/llm_client.py`

Contains helper functions for calling a remote LLM. If remote LLM configuration is missing, the app uses fallback JSON so the demo still works.

### `backend/llm/prompts.py`

Stores prompts for intent detection, risk reasoning, and explanation generation.

## Database Files

### `backend/database.py`

Creates SQLite connections and initializes the database from the schema file.

### `backend/models/schema.sql`

Defines all database tables:
- `users`
- `user_rules`
- `bills`
- `subscriptions`
- `payment_methods`
- `transactions`
- `agent_logs`
- `approvals`

### `backend/seed_data.py`

Resets and fills the database with demo data: one user, rules, pending bills, paid bills, subscriptions, payment methods, and seed transactions.

### `backend/paypilot.db`

SQLite database file used by the running app.

## Utility And Config Files

### `backend/config.py`

Reads environment variables for remote LLM settings and model names.

### `backend/utils/json_utils.py`

Utility helpers for JSON parsing or cleanup.

### `backend/utils/response_utils.py`

Utility helpers for consistent response handling.

### `backend/requirements.txt`

Lists Python dependencies required by the backend.

## Documentation Files

### `README.md`

Main project overview and setup instructions.

### `docs/WHAT_WE_BUILT.md`

Explains the overall product and what was implemented.

### `docs/PPT_STEPS.md`

Presentation steps for explaining or demonstrating the project.

### `docs/FILE_GUIDE.md`

This document. Use it when the invigilator asks what each file does.

## Best Demo Script

1. Open Command Center and explain the dashboard.
2. Open AI Orchestrator and run `Pay my most urgent safe bill`.
3. Show the Agent Timeline and XAI Decision Core.
4. Run a risky or duplicate bill prompt.
5. Show that PayPilot asks for approval instead of directly executing.
6. Click `Yes, open approval`.
7. Approve the payment in Approval Queue.
8. Open Transactions and Agent Logs to prove the payment and reasoning were recorded.
9. Open About and explain the agent architecture plus the reinforcement feedback signal.

# What We Built: PayPilot AI

PayPilot AI is an agentic payment orchestration demo that turns a user's natural-language payment request into a safe, explainable payment workflow. It can inspect pending bills, select the right bill, score risk, choose the best payment method, apply compliance rules, explain the decision, execute safe payments through a mock gateway, and route risky payments for human approval.

The project is built as a Flask backend with a vanilla HTML/CSS/JavaScript frontend and a SQLite database.

## Core Idea

Traditional bill payment tools usually show bills and let the user manually decide what to pay. PayPilot AI adds an intelligent orchestration layer on top of that process.

The user can ask things like:

- `Manage my payments this week safely`
- `Pay my most urgent safe bill`
- `Find risky payments and explain why`
- `Analyze my subscriptions and waste`
- `Make payment for HDFC Credit Card`
- `Review Notion Plus subscription`
- `yes`

The system then breaks the task into smaller decisions handled by specialized agents. Each agent returns structured output and reasoning, which is shown in the UI and stored in agent logs.

## Main Capabilities

### Natural-Language Payment Orchestration

The AI Orchestrator accepts user instructions in plain language. The backend detects the intent, builds a payment plan, selects a bill, checks risk and compliance, and decides whether to auto-pay, block, or request approval. When approval is required, the chat asks the user to open the approval record instead of silently executing.

### Safety-First Autopay

Low-risk payments can be executed automatically when they satisfy all safety rules:

- The payment is allowed by compliance policy.
- The risk score is below the medium-risk threshold.
- The user's balance remains above the configured minimum safe balance.
- A valid payment method has enough available balance.

This means routine payments such as normal utility or internet bills can be cleared without unnecessary manual approval.

### Human Approval For Risky Payments

Payments are paused for human review when risk or policy requires it. Examples include:

- Suspicious merchants
- Possible duplicate bills
- Vendor changes
- Invoice spikes
- Geo mismatch signals
- Subscription waste
- Trial renewals
- Cashflow pressure
- Medium or high risk scores

Approval requests are created in the `approvals` table and surfaced in the Approvals page.

If a payment is blocked by the Financial Safety Firewall, PayPilot creates a `blocked_review` record in the Approvals page. This lets the user review the blocked payment details and risk explanation, while still preventing automatic execution.

### Follow-Up Safety

The Bill Selector Agent uses strict matching for named payment requests. If the user asks to pay a specific name and no pending bill matches it, PayPilot refuses to fall back to another safe bill. For example, if the user scans subscription waste and then asks to pay `Notion Plus`, the system recognizes it as a subscription record instead of paying `Airtel Fiber`.

Focused subscription review keeps context. If the user clicks `Review Notion Plus`, the XAI panel shows only Notion Plus. If the next message is `yes`, PayPilot creates or reuses a pending bill for Notion Plus and pays that exact reviewed subscription.

### Financial Safety Firewall

Compliance rules protect the user before payment execution. The system blocks payments when:

- The payment would reduce balance below the minimum safe balance.
- The payment is high risk and high-risk blocking is enabled.
- No eligible payment method can execute it.

The compliance result includes policy checks, the projected after-payment balance, approval status, and reasoning.

### Explainable AI Decisions

Every payment analysis includes an explanation that answers:

- Why this bill was selected
- What risk signals were found
- Which payment method was recommended
- What policy checks were applied
- Whether the final decision is allowed, blocked, or approval-required

The app can use a remote LLM when configured, but it also has deterministic fallback logic so the demo works locally without remote AI access.

### Payment Method Optimization

The Optimizer Agent ranks payment methods using:

- Available balance
- Fee
- Cashback
- Success rate
- Payment-type safety rules

For example, credit card bills are not paid using another credit card. Methods without enough available balance are skipped with a clear reason.

### Mock Payment Execution

Payments are executed through a mock gateway, not a real payment processor. On successful execution, the gateway:

- Creates a transaction reference
- Inserts a transaction record
- Marks the bill as paid
- Deducts the amount from the user's balance
- Deducts from the selected payment method's available balance

This gives the demo realistic end-to-end behavior while staying safe.

### Subscription Waste Analysis

The app includes subscription records with last-used data and waste scores. The frontend highlights subscriptions that may be unused, expensive, or worth reviewing before renewal.

After a waste scan, Copilot-style suggestion chips let the user review one subscription at a time. A focused review does not load the full subscription list into the XAI panel.

### Audit Logs

Agent decisions are stored in the `agent_logs` table. The Agent Logs page lets users inspect the reasoning trail behind orchestrated actions.

## User Interface

The frontend is a single-page dashboard served by Flask from the `frontend/` directory.

### Command Center

The Command Center is the landing dashboard. It shows:

- Available safe balance
- Pending bill count
- Total pending amount
- Risky item count
- Completed transaction count
- Payment Safety Radar
- Upcoming payments
- Subscription waste watch

Dashboard metrics are clickable and open a detail view for deeper inspection.

### AI Orchestrator

The AI Orchestrator is the main task console. It includes:

- Natural-language input
- Quick prompts
- Live available balance
- Explainable decision panel
- Agent timeline
- Safety-first payment plan

When a payment is auto-executed or approved, the frontend refreshes dashboard, bills, account, approvals, transactions, and logs.

### Bills

The Bills page lists pending bills. Opening a bill shows payment intelligence:

- Payment snapshot
- Risk analysis
- Recommended method
- Compliance result
- XAI explanation
- Agent timeline

The user can prepare an approval or allow the system to auto-execute if the bill is safe.

### My Account

The Account page summarizes:

- Available balance
- Recommended minimum balance
- Configured minimum safe balance
- Safe buffer
- Projected balance after all pending bills
- Account rules
- Payment methods
- Autopay candidates
- Risk watchlist

### Subscriptions

The Subscriptions page displays recurring payments ordered by waste score so the user can quickly see which subscriptions may need attention.

### Approvals

The Approvals page shows pending, approved, rejected, or blocked approval requests. Approving a request triggers one final safety check before execution.

### Transactions

The Transactions page shows completed mock payment transactions, including biller, amount, method, status, risk score, reference, and explanation.

### Agent Logs

The Agent Logs page shows the audit trail of agent decisions produced during orchestration.

## Backend Architecture

The backend is organized around routes, agents, services, and database helpers.

### Flask API

Main file: `backend/app.py`

Important routes:

- `GET /` serves the frontend.
- `GET /api/health` reports backend and model configuration status.
- `POST /api/setup` initializes and seeds the database.
- `GET /api/dashboard` returns dashboard metrics and data.
- `GET /api/account` returns balance, rules, payment methods, autopay candidates, and risk watchlist.
- `GET /api/bills` returns pending bills.
- `GET /api/bills/<id>/analysis` returns instant bill-level analysis.
- `POST /api/bills/<id>/prepare-approval` prepares approval or auto-executes a safe bill.
- `POST /api/agent/chat` runs the full natural-language orchestration flow.
- `GET /api/approvals` returns approval requests.
- `POST /api/approvals/<id>/approve` approves and executes a pending request after a final safety check.
- `POST /api/approvals/<id>/reject` rejects a pending request.
- `GET /api/subscriptions` returns subscription data.
- `GET /api/transactions` returns transaction history.
- `GET /api/agent/logs` returns agent decision logs.

### Agent Layer

The agent layer lives in `backend/agents/`.

#### Intent Agent

File: `backend/agents/intent_agent.py`

Detects the user's intent from a natural-language message. Supported intents include autopilot payments, paying a bill, analyzing risk, analyzing subscriptions, showing pending bills, and general payment advice.

It can call a remote LLM, but falls back to keyword-based rules if the LLM is disabled or unavailable.

#### Planning Agent

File: `backend/agents/planning_agent.py`

Builds a safety-first payment plan from pending bills. It assigns each bill a priority and score based on risk hints, due date, and amount.

Safe bills are favored. Suspicious, duplicate, vendor-change, geo-mismatch, subscription-waste, invoice-spike, trial-renewal, and cashflow-pressure bills are pushed into review-style priorities.

#### Bill Selector Agent

File: `backend/agents/bill_selector_agent.py`

Selects the most relevant bill for the user request. It supports:

- Direct selection from the UI
- Category and biller-name matching
- Keyword matching
- Risk-focused selection for risk scans
- Safe-bill preference for payment execution requests
- Due-date fallback

This prevents the system from blindly selecting suspicious bills when the user wants safe autopay.

#### Risk Agent

File: `backend/agents/risk_agent.py`

Calculates risk score and risk level. The deterministic scoring rules consider:

- Suspicious merchant signals
- Duplicate payment signals
- Unused subscription risk
- Vendor change
- Invoice spike
- Trial renewal
- Geo mismatch
- Cashflow pressure
- High payment amount
- One-time shopping payment behavior

The risk score maps to:

- Low risk: below 40
- Medium risk: 40 to 69
- High risk: 70 and above

Optional LLM reasoning can adjust the score, but the deterministic score is always available.

#### Optimizer Agent

File: `backend/agents/optimizer_agent.py`

Ranks payment methods and selects the best one. It skips invalid methods and provides reasons for skipping them.

The final method score combines method reliability and net benefit:

```text
final_score = success_rate * 100 + cashback - fee
```

#### Compliance Agent

File: `backend/agents/compliance_agent.py`

Applies safety and policy rules. It decides:

- Whether the payment is allowed
- Whether human approval is required
- Whether enhanced review is required
- What the user's balance would be after payment

This is the core safety firewall.

#### Explainability Agent

File: `backend/agents/explainability_agent.py`

Creates user-facing explanations from the agent decisions. It explains the bill choice, risk, method selection, policy checks, and final outcome.

It can use a remote LLM for richer phrasing, with deterministic fallback output if remote AI is unavailable.

#### Approval Agent

File: `backend/agents/approval_agent.py`

Creates approval requests for payments that need human review. If an approval already exists for the same bill, it reuses the pending request instead of creating duplicates.

#### Execution Agent

File: `backend/agents/execution_agent.py`

Executes an approved payment through the mock gateway.

#### Monitoring Agent

File: `backend/agents/monitoring_agent.py`

Confirms payment status and receipt readiness after execution.

#### Orchestrator

File: `backend/agents/orchestrator.py`

Coordinates the full workflow:

1. Detect intent.
2. Handle direct requests like showing pending bills or analyzing subscriptions.
3. Create a payment plan.
4. Select a bill.
5. Score risk.
6. Optimize the payment method.
7. Run compliance checks.
8. Generate explanation.
9. Block, auto-execute, or create approval.
10. Monitor executed payments.
11. Log each agent decision.

## Service Layer

The service layer lives in `backend/services/` and isolates database operations from the agents and routes.

- `bill_service.py` reads pending bills, bill details, and subscriptions.
- `payment_service.py` reads payment methods, user rules, and balance.
- `transaction_service.py` writes agent logs and reads transaction/log history.
- `approval_service.py` reads and updates approval requests.
- `mock_gateway.py` performs atomic mock payment execution.

## Database Design

The SQLite schema is defined in `backend/models/schema.sql`.

Main tables:

- `users`: demo user profile and balance.
- `user_rules`: minimum safe balance, approval threshold, autopay limit, high-risk blocking, and cashback preference.
- `bills`: pending and paid bills with category, amount, due date, status, recurrence, and risk hint.
- `subscriptions`: recurring subscriptions with usage and waste score.
- `payment_methods`: available payment rails, fees, cashback, success rate, and balance.
- `transactions`: executed mock payments.
- `approvals`: human approval workflow records.
- `agent_logs`: auditable agent reasoning.

The seed data creates one demo user, several realistic bills, active subscriptions, payment methods, and past transactions.

## LLM And Fallback Behavior

The project can run in two modes:

### Local Rule-Based Mode

This is the default mode when no remote LLM configuration is provided. Intent, risk, and explanations use deterministic fallback logic.

### Remote LLM Mode

Remote LLM usage can be enabled with environment variables:

- `USE_REMOTE_LLM`
- `GENAI_BASE_URL`
- `GENAI_API_KEY`
- `PAYPILOT_MAIN_MODEL`
- `PAYPILOT_FAST_MODEL`
- `PAYPILOT_REASONING_MODEL`
- `PAYPILOT_EMBEDDING_MODEL`

The LLM client has safeguards:

- It expects JSON where needed.
- It falls back to deterministic outputs on failures.
- It disables a failing model type for the current process after an error.
- It handles model temperature differences.

## End-To-End Flow Example

When the user says `Pay my most urgent safe bill`, the flow is:

1. Intent Agent classifies the request as a payment intent.
2. Planning Agent sorts bills with safety-first priorities.
3. Bill Selector Agent chooses an early safe payable bill.
4. Risk Agent calculates a risk score.
5. Optimizer Agent selects the best valid payment method.
6. Compliance Agent checks safe balance and approval policy.
7. Explainability Agent prepares a readable explanation.
8. If approval is not required, Execution Agent pays through the mock gateway.
9. Monitoring Agent confirms the transaction.
10. The frontend refreshes balance, bill status, transactions, approvals, and logs.

If any safety condition fails, the same flow stops before execution and returns a blocked or approval-required result.

## Why This Build Matters

PayPilot AI demonstrates an agentic finance workflow where automation is useful but controlled. The system does not simply "auto-pay everything." It separates low-risk routine payments from risky or sensitive payments, keeps a human in the loop when needed, and explains every decision in a way the user can inspect.

The result is a working prototype of safe autonomous payment orchestration with:

- Natural-language control
- Multi-agent reasoning
- Policy-based safety
- Payment-method optimization
- Human approval routing
- Mock execution
- Transaction history
- Agent audit logs
- Explainable decision output

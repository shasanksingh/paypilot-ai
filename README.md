# PayPilot AI

PayPilot AI is an agentic payment orchestration demo. A user can ask for a payment task in natural language, and the system routes the request through intent detection, planning, bill selection, risk scoring, payment-method optimization, compliance, explainability, execution, monitoring, and audit logging.

For the full build explanation, architecture, workflow, UI walkthrough, data model, and demo behavior, read [What We Built](docs/WHAT_WE_BUILT.md).

## What It Does

- Lets users manage and pay bills using natural-language prompts.
- Builds a safety-first payment plan from pending bills.
- Auto-executes low-risk, policy-allowed payments through a mock gateway.
- Routes risky, duplicate, suspicious, high-value, or cashflow-sensitive payments to human approval.
- Creates a review item for blocked payments so the user can inspect the risk details instead of losing the decision.
- Avoids paying an unrelated bill when a named payment, such as a subscription merchant, does not match a pending bill.
- Keeps focused subscription review context, so reviewing `Notion Plus` and replying `yes` pays `Notion Plus` only.
- Explains every decision with risk reasons, method choice, policy checks, and final outcome.
- Tracks transactions, approvals, subscriptions, payment methods, and agent logs.

## Automation Logic

PayPilot uses compliance rules to decide whether a payment can be executed automatically, needs human review, or must be blocked.

Safe automatic execution happens when:

- The bill is allowed by compliance.
- Risk score is below the medium-risk threshold.
- The payment keeps the user above the minimum safe balance.
- A valid payment method is available.

Human review is still required when:

- Risk score is elevated.
- Risk score is medium or high.
- The payment has suspicious, duplicate, vendor-change, geo-mismatch, invoice-spike, subscription-waste, trial-renewal, or cashflow-pressure signals.

Payment is blocked when:

- It would reduce the balance below the safe minimum.
- It is high-risk and high-risk blocking is enabled.
- No valid payment method can execute it.

Blocked payments are also added to the Approval Queue as `blocked_review` records. They do not execute automatically; the user can open the review details and inspect why the payment was stopped.

## Project Structure

```text
backend/
  agents/       Multi-agent payment workflow
  services/     Database and gateway service layer
  llm/          LLM prompts, client, and deterministic fallbacks
  models/       SQLite schema
  app.py        Flask API and static frontend serving
  seed_data.py  Demo data setup
frontend/
  index.html    Single-page app structure
  styles.css    UI styling and responsive layout
  script.js     API calls, rendering, and interactions
docs/
  WHAT_WE_BUILT.md  Full project explanation
  PPT_STEPS.md      Presentation notes
```

## Running The App

Start the Flask backend:

```bash
python3 backend/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

If port `5000` is busy, run from the backend folder on another port:

```bash
flask --app app run --port 5001
```

Then open:

```text
http://127.0.0.1:5001
```

To reset demo data from the UI, use the reset button in the top bar. It calls `POST /api/setup`.

## Main Files

- `frontend/index.html` - page structure and UI sections
- `frontend/styles.css` - visual system, responsive layout, and page polish
- `frontend/script.js` - API calls, rendering, balance refresh, and user interactions
- `backend/agents/orchestrator.py` - end-to-end agent workflow and auto-execution route
- `backend/agents/bill_selector_agent.py` - strict bill matching so named follow-ups do not pay the wrong bill
- `backend/agents/reinforcement_agent.py` - approval/rejection feedback signal for RL-style learning
- `backend/agents/compliance_agent.py` - autopay, review, and blocking policy
- `backend/app.py` - Flask API routes
- `backend/services/mock_gateway.py` - mock payment execution and balance updates

## Documentation

- [What We Built](docs/WHAT_WE_BUILT.md) - complete explanation of the product, architecture, workflow, agents, UI, API, and data model.
- [PPT Steps](docs/PPT_STEPS.md) - short presentation notes.
- [File Guide](docs/FILE_GUIDE.md) - file-by-file explanation for evaluation.

## Verification

Checks performed:

- Python compile check for backend files.
- Flask test-client health check.
- Bill analysis check confirmed low-risk bills return `approval_required: false`.
- Temporary database smoke test confirmed a safe low-risk bill returns `auto_approved` and mock execution `success`.

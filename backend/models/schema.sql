DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS bills;
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS agent_logs;
DROP TABLE IF EXISTS approvals;
DROP TABLE IF EXISTS user_rules;
DROP TABLE IF EXISTS subscriptions;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    balance REAL DEFAULT 50000,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    minimum_safe_balance REAL DEFAULT 10000,
    approval_required_above REAL DEFAULT 5000,
    autopay_limit REAL DEFAULT 2000,
    block_high_risk INTEGER DEFAULT 1,
    prefer_cashback INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    biller_name TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    is_recurring INTEGER DEFAULT 0,
    risk_hint TEXT DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    merchant_name TEXT,
    amount REAL,
    billing_cycle TEXT,
    last_used_days_ago INTEGER,
    waste_score INTEGER,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    method_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    masked_identifier TEXT NOT NULL,
    fee REAL DEFAULT 0,
    cashback REAL DEFAULT 0,
    success_rate REAL DEFAULT 0.95,
    available_balance REAL DEFAULT 50000,
    is_default INTEGER DEFAULT 0
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    bill_id INTEGER,
    amount REAL,
    payment_method TEXT,
    status TEXT,
    risk_score INTEGER,
    transaction_ref TEXT,
    explanation TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    agent_name TEXT,
    input_summary TEXT,
    output_summary TEXT,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    bill_id INTEGER,
    amount REAL,
    payee TEXT,
    recommendation TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bills_user_status_due ON bills(user_id, status, due_date);
CREATE INDEX idx_bills_user_risk ON bills(user_id, risk_hint);
CREATE INDEX idx_subscriptions_user_waste ON subscriptions(user_id, waste_score DESC);
CREATE INDEX idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX idx_approvals_user_status ON approvals(user_id, status);
CREATE INDEX idx_agent_logs_user_created ON agent_logs(user_id, created_at DESC);

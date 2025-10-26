# DATA CONTRACT — Idilio TV

## 1. Keys

| Dataset | Field | Type | Description | Uniqueness | Nulls |
|----------|--------|------|--------------|-------------|--------|
| users | user_id | string/int | Unique user identifier | Yes | No |
| events | event_uuid | string | Unique event identifier | Yes | No |
| events | user_id | string/int | Foreign key to users.user_id | 🔁 | No |

---

## 2. Temporal fields

| Field | Dataset | Type | Description | Expected range | Notes |
|--------|----------|------|--------------|----------------|--------|
| signup_date | users | datetime | Date when the user registered | 2020–2025 | Must be ≤ last_active_date |
| last_active_date | users | datetime | Last day the user was active | 2020–2025 | Must be ≥ signup_date |
| event_timestamp | events | datetime | Timestamp when event happened in app | 2020–2025 | Primary temporal field |
| received_at | events | datetime | Time when backend received the event | 2020–2025 | Should be ≥ event_timestamp |
| created_at | events | datetime | Time when record was persisted | 2020–2025 | Should be ≥ received_at |

---

## 3. Critical business variables

| Field | Dataset | Type | Description / Use | Valid values / Example |
|--------|----------|------|--------------------|-------------------------|
| churned_30d | users | bool/int | Churn label in 30 days | 0 / 1 |
| subscription_type | users | string | Subscription type | free / premium / trial |
| country | users / events | string | Country of user or event | MX / CO / US |
| device, os, app_version | users / events | string | Device context | Android / iOS / v1.2.3 |
| event_type | events | string | Type of event | play / pause / next / open / exit |
| credits_purchased, credits_spent | users | int | Monetization metrics | 0+ |
| episodes_completed | users | int | Completed episodes | 0+ |
| views, likes | users | int | Engagement indicators | 0+ |
| avg_watch_time_sec | users | float | Average watch time per session | ≥ 0 |

---

## 4. Referential integrity and consistency

- `events.user_id` must exist in `users.user_id`
- `event_uuid` must be unique
- Temporal consistency rules:
- Categorical values (`subscription_type`, `device`, `event_type`, `language`) must belong to controlled vocabularies.

---

## 5. Conventions

| Aspect | Rule |
|--------|------|
| Timestamp format | UTC, ISO8601 |
| Encoding | UTF-8 |
| CSV separator | , |
| Decimal separator | . |
| Identifier format | snake_case |
| Currency | USD |

---

## 6. Quality rules

| Dimension | Rule | Target |
|------------|------|--------|
| Completeness | No nulls in user_id / event_uuid | 0% nulls |
| Temporal | signup_date ≤ last_active_date | <0.1% violations |
| Integrity | events.user_id must exist in users | <0.5% orphans |
| Range | event_timestamp in 2020–2025 | <0.1% out of range |
| Duplicates | event_uuid unique | 0 duplicates |

---

## 7. Version and ownership

| Field | Value |
|--------|--------|
| Version | 0.1 (Oct 2025) |
| Data Owner | Head of Data & AI – Idilio TV |
| Data Engineer | TBD |
| Data Scientist | TBD |

---

## 8. Valid value domains (to update after profiling)

Once the data audit (phase 1) is executed, this section will contain valid lists extracted directly from the data:

- **subscription_type:** TBD (from `users.subscription_type`)
- **device:** TBD (from `users.device`)
- **event_type:** TBD (from `events.event_type`)
- **language:** TBD (from `users.language`)

---


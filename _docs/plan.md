# Hidden B2B Subscriptions & Auto-Charge Tracker

## Product brainstorming and MVP implementation notes

**Status:** Early build / MVP planning\
**Last updated:** 19 October 2026\
**Founder context:** Solo founder building a custom web app\
**Initial target customer:** Freelancers and solo business owners\
**Initial market:** International (not yet narrowed to one launch
country)\
**Primary user outcome:** Find waste from unnecessary or forgotten
business subscriptions

------------------------------------------------------------------------

## 1. Product concept

Build a tool that helps freelancers and solo business owners discover
recurring business expenses they may have forgotten about, understand
what they are paying for, and identify subscriptions that may be
unnecessary.

The product should connect to financial and email data, identify
recurring charges and subscription evidence, then present a reviewable
list of possible waste. It should help users make informed decisions
rather than automatically cancel services.

### Core user journey

1.  **Connect data** --- connect a bank account and Gmail, with clear
    permissions and privacy disclosures.
2.  **Discover recurring expenses** --- identify repeat payments and
    subscription-related emails or invoices.
3.  **Review possible waste** --- highlight forgotten tools, duplicate
    services, price increases, unused-looking subscriptions, and
    upcoming renewals where evidence exists.
4.  **Confirm and act** --- let the user confirm whether a finding is
    waste, mark it as useful, or record that they cancelled it.
5.  **Measure savings** --- show estimated potential savings separately
    from confirmed savings.

A key product principle: do not claim that a subscription is unused
solely because the system sees recurring charges. The app may not know
actual product usage. Phrase findings as hypotheses and explain the
evidence.

------------------------------------------------------------------------

## 2. Target customer and positioning

### Initial customer

-   Freelancers
-   Independent consultants
-   Solo business owners
-   Small service businesses with a relatively simple set of business
    expenses

### Main pain point

**Waste:** paying for tools that are no longer needed, forgotten trials
that converted to paid plans, duplicate services, or recurring charges
that have quietly increased.

### Possible positioning

> Find the business subscriptions you forgot about --- and see where you
> could stop wasting money.

Avoid promising guaranteed savings. The app identifies likely
opportunities; the user confirms whether they are real.

------------------------------------------------------------------------

## 3. Potential features

### MVP essentials

-   Bank transaction connection
-   Gmail connection for subscription emails and invoices
-   Recurring-payment detection
-   Vendor matching and merchant-name normalization
-   Subscription list with amount, currency, cadence, last charge, and
    next expected charge where estimable
-   Waste Finder with evidence and confidence level
-   Mark a finding as useful, review later, or confirmed waste
-   Estimated potential savings and user-confirmed savings
-   Disconnect and delete-data controls

### Candidate findings

1.  **Forgotten recurring charge** --- a merchant has charged
    repeatedly, but the user has not reviewed it.
2.  **Trial conversion** --- email evidence suggests a trial or
    introductory period ended and payment began.
3.  **Price increase** --- recurring charge amount increased.
4.  **Possible duplicate** --- two services may serve a similar purpose.
    Treat this as a suggestion, not a definitive conclusion.
5.  **Unusual amount or cadence** --- a charge differs from the
    established pattern.
6.  **Renewal approaching** --- an upcoming renewal date is supported by
    transaction or email evidence.
7.  **Unclear merchant** --- the transaction descriptor is hard to
    recognize and needs user confirmation.
8.  **Potentially dormant subscription** --- only make this claim if
    there is reliable usage evidence; bank and email data alone
    generally cannot establish actual usage.

### Features to defer

-   Automatic cancellation
-   Direct vendor-account integrations for many SaaS products
-   Team approvals and complex spend management
-   Full accounting and bookkeeping
-   Broad AI summaries of all email
-   Multi-bank support across every country before validating one launch
    market

------------------------------------------------------------------------

## 4. Suggested web dashboard

### 1. Overview

-   Monthly recurring spend
-   Number of identified subscriptions
-   Potential savings to review
-   Upcoming renewals
-   Recently detected changes

### 2. Subscriptions

A table/list with: - Vendor - Amount and currency - Billing cadence -
Last charge - Next expected charge, if confidence is sufficient - Source
of evidence: bank, Gmail, or both - Confidence level - User status:
needs review, useful, potential waste, cancelled

### 3. Waste Finder

Each finding should explain: - What was detected - Why it may matter -
Supporting evidence - Confidence level - Estimated savings and
assumptions - Actions: confirm waste, mark useful, snooze, or dismiss

### 4. Connections

-   Bank connection status
-   Gmail connection status
-   Last successful sync
-   Permission summary
-   Disconnect / delete controls

### 5. Renewals

-   Upcoming expected charges
-   Email-supported renewal dates
-   Reminders, once the core detection is reliable

### 6. Savings report

Separate: - **Potential savings:** estimates based on findings not yet
confirmed - **Confirmed savings:** amounts the user says they stopped
paying - **Realized savings:** savings supported by subsequent
transactions, where possible

Do not combine these numbers into one misleading total.

------------------------------------------------------------------------

## 5. Integration provider comparison

Provider coverage and eligibility depend on the user's country, bank,
product, and commercial agreement. "International" is not a single
coverage area. Confirm the exact country and institutions before
committing to a provider.

  --------------------------------------------------------------------------------------------
  Provider        Best-fit        Coverage /          Implementation   Main considerations
                  starting point  capabilities to     complexity       
                                  investigate                          
  --------------- --------------- ------------------- ---------------- -----------------------
  **Plaid**       US-first        Transactions API;   Medium           Check country/product
                  product, with   recurring                            availability and
                  some            transaction                          pricing. Plaid's Trial
                  international   features are                         availability has
                  options         documented. Country                  historically been
                                  and institution                      restricted to
                                  coverage vary.                       developers in the
                                                                       US/Canada and
                                                                       US/Canadian
                                                                       institutions, so it may
                                                                       not be suitable for
                                                                       every founder or launch
                                                                       market.

  **TrueLayer**   UK and selected Data API for        Medium           Confirm the specific
                  European        account and                          bank, data fields,
                  markets         transaction data;                    commercial access, and
                                  available                            onboarding requirements
                                  institutions and                     for the target country.
                                  products vary by                     
                                  market.                              

  **Tink**        European        Broad European      Medium to high   Enterprise/commercial
                  account         bank-connectivity                    onboarding and terms
                  aggregation     offering; Tink has                   may be a hurdle for a
                                  advertised                           solo founder. Verify
                                  thousands of                         current availability
                                  institutions across                  and access.
                                  multiple European                    
                                  markets.                             

  **GoCardless    EEA-oriented    Bank-account data   Low to medium    Not a global solution.
  Bank Account    prototype or    and transaction     for a prototype  Verify supported
  Data**          product         history for                          institutions, data
                                  supported                            refresh limits, terms,
                                  institutions;                        and production
                                  access duration and                  suitability for the
                                  refresh behavior                     chosen country.
                                  are constrained by                   
                                  the relevant                         
                                  connection and                       
                                  market.                              

  **Gmail API**   Email and       Gmail messages and  Medium to high   `gmail.readonly` is a
                  invoice         metadata, subject   because of       restricted scope.
                  evidence        to OAuth scopes and Google           Verification and
                                  user consent.       verification     potentially a
                                                      requirements     third-party security
                                                                       assessment may apply if
                                                                       restricted-scope data
                                                                       is stored or
                                                                       transmitted through a
                                                                       server. Minimize data
                                                                       access and retention.
  --------------------------------------------------------------------------------------------

### Practical interpretation

-   **Plaid:** a strong candidate if you choose a US launch market and
    can meet its developer and commercial requirements.
-   **TrueLayer:** worth evaluating if your first market is the UK or a
    supported European country.
-   **Tink:** potentially broad European coverage, but confirm whether
    its onboarding and commercial model fit a solo-founder MVP.
-   **GoCardless Bank Account Data:** may be useful for a constrained
    EEA prototype, but do not assume it is suitable for an international
    production launch.
-   **Gmail:** useful as a second evidence source, but its compliance
    work may be significant. Start with a narrow, explicit use case.

### Best first connector

**Do not choose the bank connector until you choose one launch country
and verify coverage for the banks your target users actually use.** Bank
data is central to recurring-charge discovery, so a working connector in
one market is more valuable than nominal global coverage.

Recommended decision process: 1. Choose one initial country or market
cluster. 2. List the top banks used by likely target customers. 3. Check
each provider's live coverage and transaction access for those banks. 4.
Confirm onboarding, pricing, data-refresh behavior, commercial terms,
and production approval. 5. Select the provider that covers the target
users with the least operational burden. 6. Keep the app's internal data
model independent of the provider.

If you need to test the product before provider approval, use synthetic
transactions or a clearly labeled manual CSV import. Do not make the
architecture depend on one provider's proprietary response format.

------------------------------------------------------------------------

## 6. Gmail integration and privacy

Gmail can provide invoice, trial, renewal, cancellation, and
price-change evidence. It can also expose highly sensitive information,
so the integration should be narrowly scoped.

### Safer design principles

-   Request only the minimum OAuth scopes needed for the specific
    feature.
-   Clearly explain what email information is read and why.
-   Use a focused search and parsing strategy for likely billing-related
    messages rather than processing all mail without a clear need.
-   Prefer extracting only necessary fields: vendor, amount, currency,
    invoice date, renewal date, and evidence reference.
-   Avoid storing full email bodies or attachments unless strictly
    necessary.
-   Encrypt access and refresh tokens at rest; restrict internal access.
-   Use secure OAuth flows and protect secrets.
-   Offer a clear disconnect flow and a way to delete imported data.
-   Define retention periods and delete raw data when no longer needed.
-   Avoid using email data for unrelated purposes.
-   Review Google's current OAuth verification and restricted-scope
    policies before launch. A third-party security assessment may be
    required for certain restricted-scope data handling.

**Important:** Compliance requirements can change and depend on the
exact implementation. Treat this as a design checklist, not legal
advice. Review current Google documentation and, if needed, consult a
qualified security/compliance professional before production.

------------------------------------------------------------------------

## 7. Suggested technical architecture

A practical solo-founder stack:

-   **Frontend:** Next.js + TypeScript
-   **Backend:** Next.js server-side routes or a separate API service
-   **Database:** PostgreSQL
-   **Background work:** a queue or scheduled job runner for sync and
    analysis
-   **Authentication:** a well-supported authentication provider or
    secure managed implementation
-   **Secrets:** managed secret storage and encryption key management
-   **Observability:** structured logs, error monitoring, and
    sync-health monitoring

Keep the detection engine separate from provider-specific integration
code.

### Provider adapter pattern

Create an internal interface such as:

-   `connect()`
-   `syncAccounts()`
-   `syncTransactions()`
-   `getConnectionStatus()`
-   `disconnect()`

Each provider adapter maps its data into the same internal schema. This
makes it easier to add or replace providers without rewriting the
product logic.

------------------------------------------------------------------------

## 8. Suggested database model

A starting model might include:

### `users`

-   `id`
-   `email`
-   `created_at`

### `connections`

-   `id`
-   `user_id`
-   `provider`
-   `connection_type` (bank or Gmail)
-   `provider_connection_id`
-   `status`
-   `last_synced_at`
-   `created_at`
-   `disconnected_at`

Store credentials/tokens securely, not as ordinary unprotected fields.

### `transactions`

-   `id`
-   `user_id`
-   `connection_id`
-   `provider_transaction_id`
-   `merchant_raw`
-   `merchant_normalized`
-   `amount`
-   `currency`
-   `transaction_date`
-   `pending`
-   `category`
-   `raw_payload_reference` (optional, access-controlled, and
    short-lived if retained)
-   `created_at`

Use a unique constraint to prevent duplicate imports, such as provider
connection plus provider transaction ID.

### `billing_evidence`

-   `id`
-   `user_id`
-   `connection_id`
-   `source_message_id`
-   `vendor_normalized`
-   `evidence_type` (invoice, trial, renewal, cancellation, price
    change)
-   `amount`
-   `currency`
-   `event_date`
-   `renewal_date`
-   `extracted_fields`
-   `created_at`

Store minimal extracted data and a message reference where possible, not
full message content by default.

### `subscriptions`

-   `id`
-   `user_id`
-   `vendor_normalized`
-   `display_name`
-   `amount_estimate`
-   `currency`
-   `cadence`
-   `last_charge_date`
-   `next_charge_estimate`
-   `confidence`
-   `status`
-   `created_at`
-   `updated_at`

### `findings`

-   `id`
-   `user_id`
-   `subscription_id`
-   `finding_type`
-   `title`
-   `explanation`
-   `confidence`
-   `estimated_monthly_savings`
-   `estimated_annual_savings`
-   `evidence_references`
-   `user_decision`
-   `created_at`
-   `resolved_at`

### `actions`

-   `id`
-   `user_id`
-   `finding_id`
-   `action_type`
-   `notes`
-   `created_at`

Use user-level access controls and ensure every query is scoped to the
authenticated user.

------------------------------------------------------------------------

## 9. Recurring-payment detection

Start with explainable rules before adding complex machine learning.

### Signals to consider

-   Same or similar merchant descriptor
-   Similar amount
-   Repeated transaction intervals
-   Monthly, annual, weekly, or other regular cadence
-   Multiple consecutive occurrences
-   Vendor name or amount found in an invoice or billing email
-   Evidence of a trial, renewal, or price change

### Basic process

1.  Normalize merchant descriptors.
2.  Group likely transactions by vendor.
3.  Identify repeated transactions and plausible intervals.
4.  Estimate cadence and amount stability.
5.  Match bank evidence with Gmail evidence when possible.
6.  Assign confidence based on the strength and consistency of evidence.
7.  Create a subscription candidate only when the evidence passes a
    threshold.
8.  Let the user correct the vendor, cadence, or classification.

Do not assume every repeated payment is a subscription. Payroll,
transfers, utilities, taxes, and one-off installments can look
recurring.

### Confidence and explanation

For every finding, show a human-readable reason, for example:

> "This vendor charged a similar amount on three occasions at roughly
> monthly intervals. A matching invoice email was also found."

Avoid opaque labels like "AI says this is waste."

------------------------------------------------------------------------

## 10. MVP implementation plan

### Phase 1 --- Validate the market and scope

-   Pick one launch country.
-   Interview 5--10 freelancers or solo business owners.
-   Ask how they currently find forgotten subscriptions.
-   Collect examples of anonymized merchant descriptors and billing
    emails.
-   Define what "waste" means to the user.
-   Confirm willingness to connect a bank and Gmail.

**Deliverable:** a narrow user profile, prioritized use cases, and
launch-market choice.

### Phase 2 --- Foundation

-   Set up the web app and authentication.
-   Create PostgreSQL schema and migrations.
-   Add user-scoped authorization.
-   Build Connections and Subscriptions screens.
-   Create a synthetic-data mode for development and demos.

**Deliverable:** a usable dashboard with sample data.

### Phase 3 --- Bank data

-   Choose the provider after checking launch-country coverage.
-   Implement OAuth/consent and connection lifecycle.
-   Sync accounts and transactions.
-   Add incremental sync, retries, and duplicate prevention.
-   Handle revoked consent, expired connections, and provider errors.

**Deliverable:** reliable, read-only transaction ingestion for the
chosen market.

### Phase 4 --- Detection engine

-   Normalize merchant names.
-   Detect repeated payments and likely cadence.
-   Add confidence scoring and explanation text.
-   Let users correct mistakes.
-   Test against false positives, non-subscription recurring
    transactions, and variable amounts.

**Deliverable:** subscription candidates with evidence and confidence.

### Phase 5 --- Gmail evidence

-   Review OAuth scope and verification requirements.
-   Implement consent and restricted-scope handling.
-   Detect billing-related emails with minimal data collection.
-   Extract vendor, amount, invoice date, trial/renewal details where
    available.
-   Match email evidence to bank transactions.
-   Add disconnect and deletion workflows.

**Deliverable:** cross-source subscription evidence.

### Phase 6 --- Waste Finder and savings

-   Add findings for forgotten recurring charges, price increases,
    possible duplicates, and trial conversions.
-   Explain each finding with evidence.
-   Let users confirm, dismiss, or mark useful.
-   Separate potential from confirmed savings.

**Deliverable:** the core user outcome --- finding and reviewing likely
waste.

### Phase 7 --- Pilot and hardening

-   Invite a small number of users.
-   Measure connection success, detection precision, false positives,
    and user-confirmed findings.
-   Improve merchant matching and onboarding.
-   Test deletion, disconnect, access controls, and sync failures.
-   Add monitoring and support workflows.

**Deliverable:** a limited pilot with evidence about usefulness and
reliability.

------------------------------------------------------------------------

## 11. Solo-founder prioritization

Keep the first release small. The highest-risk work is likely not the
dashboard; it is integration access, data quality, privacy, and whether
the findings are accurate enough to earn trust.

Recommended order:

1.  Market and bank coverage validation
2.  Synthetic-data prototype
3.  One bank connector
4.  Explainable recurring-charge detection
5.  User review workflow
6.  Gmail integration, once the Google requirements are understood
7.  Better findings and savings reporting
8.  Additional countries and providers

Do not integrate several bank providers simultaneously before validating
one launch market.

------------------------------------------------------------------------

## 12. Success metrics

Track product quality as well as engagement.

-   Bank connection completion rate
-   Gmail connection completion rate
-   Successful sync rate
-   Time from connection to first useful finding
-   Share of subscription candidates confirmed by users
-   False-positive rate
-   Number of findings users mark as genuinely wasteful
-   Potential savings identified
-   Confirmed savings recorded
-   User trust signals: corrections, dismissals, and disconnects
-   User retention after the first review

A particularly useful early metric is: **How often does a first-time
user find at least one genuinely useful, previously overlooked recurring
expense?**

------------------------------------------------------------------------

## 13. Decisions still open

These are the main questions to resolve next:

1.  **First country:** Which country will the first users live in?
    "International" is too broad for selecting a bank connector.
2.  **Target segment:** Freelancers only, or also small businesses with
    employees?
3.  **Gmail scope:** Is Gmail essential on day one, or can the first
    prototype prove value with bank data alone?
4.  **Onboarding:** Should users connect accounts immediately, or first
    try a demo with synthetic data?
5.  **Waste definition:** Which findings matter most: forgotten charges,
    trial conversions, price increases, duplicates, or renewals?
6.  **Trust model:** What evidence should be shown before the app labels
    something "potential waste"?
7.  **Pricing:** Free report, paid subscription, or a one-time audit?
8.  **Savings tracking:** Should users manually confirm cancellation, or
    should later transactions help validate realized savings?
9.  **Data retention:** How long should imported transactions and
    extracted billing evidence be kept?
10. **First connector:** Which banks are most common among the first
    target users?

------------------------------------------------------------------------

## 14. Official documentation to verify before implementation

Provider coverage, prices, eligibility, and compliance requirements
change. Use official documentation and confirm details for the intended
country before choosing a provider.

-   Plaid Transactions: https://plaid.com/docs/transactions/
-   Plaid global coverage: https://plaid.com/global/
-   Plaid Trial documentation: https://plaid.com/docs/
-   TrueLayer Data API: https://docs.truelayer.com/
-   TrueLayer supported providers: https://docs.truelayer.com/
-   Tink developer documentation: https://docs.tink.com/
-   GoCardless Bank Account Data:
    https://developer.gocardless.com/bank-account-data/overview/
-   Gmail API scopes:
    https://developers.google.com/workspace/gmail/api/auth/scopes
-   Google API Services User Data Policy:
    https://developers.google.com/terms/api-services-user-data-policy
-   Google OAuth verification:
    https://support.google.com/cloud/answer/9110914

The URLs above are starting points. Re-check current documentation,
country coverage, product availability, pricing, commercial terms, and
security requirements before implementation.

------------------------------------------------------------------------

## 15. Current recommendation

Build a **web dashboard for freelancers and solo business owners** that
discovers likely recurring business expenses from **bank transactions
first**, then enriches findings with **Gmail invoices and billing
emails**.

Keep the architecture provider-independent, start with synthetic data,
and choose a single launch country before selecting the first bank
integration. Make every waste finding explainable and reviewable. The
product's promise should be to reveal possible waste with evidence, not
to claim certainty about whether a tool is used.

**Immediate next step:** choose the first country to support, then
compare real bank coverage and onboarding requirements for Plaid,
TrueLayer, Tink, and GoCardless Bank Account Data in that market.

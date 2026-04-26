# Requirements Document

## Introduction

Delhivery Commerce AI is a merchant-facing intelligence layer built on top of Delhivery's existing RTO Predictor. It helps brands acquire healthier demand and handle risky orders more effectively, with the goal of increasing realized commerce and Delhivery's share of merchant shipping volume. The product has two connected modules: a Demand Mix Advisor (benchmarking merchant cohorts against network peers to surface high-confidence demand suggestions) and an Order Action Engine (recommending or executing the lowest-regret intervention for each risky order).

## Technology Stack and AI Delineation

### Data Layer (No AI — deterministic)
- **SQLite**: Local database storing 6–9 months of real order data from hundreds of shippers. Contains order attributes (category, price band, payment mode, origin node, destination pincode, address quality), delivery outcomes (delivered, RTO, pending), intervention history, and merchant metadata.
- **Why no AI**: Data storage, retrieval, aggregation, and cohort grouping are standard SQL operations. Peer benchmarks are computed as statistical aggregates (means, percentiles, confidence intervals) — no model needed.

### Cohort Scoring and Peer Benchmarking (AI — gradient-boosted model)
- **scikit-learn / XGBoost**: Train a Realized Commerce Score model on historical order features (category, price band, payment mode, origin node, destination cluster, address quality) predicting delivery success probability.
- **Why AI is needed**: The interaction effects between 6+ categorical and continuous features across thousands of pincode-category combinations cannot be captured by static rules. A learned model generalizes across sparse cohorts where simple averages would be unreliable.
- **Why AI is the right fit**: This is a classic tabular classification problem — gradient-boosted trees are the proven best approach for structured/tabular data with mixed feature types.

### RTO Risk Reasoning and Tagging (AI — Knowledge Graph + LLM explanation)
- **NetworkX**: Build a knowledge graph modeling relationships between merchants, warehouse nodes, destination clusters, customers, categories, and price bands. Edge weights represent delivery rates, RTO rates, and cohort performance. Graph traversal identifies the specific risk path for each order.
- **LangChain + open-source LLM (e.g., Llama 3, Mistral via Ollama)**: Takes the structured risk path from the knowledge graph and generates a human-readable explanation.
- **Why a knowledge graph is needed**: A black-box RTO score (0.82) tells you nothing about why. The graph makes the reasoning auditable: "Customer C has 3 prior RTOs → shipping from Node N1 to Cluster X which has 45% COD-RTO rate → category electronics in price band 2000+ underperforms peers by 12pp." This structured path is what differentiates Commerce AI from any other RTO predictor.
- **Why the LLM is still needed on top**: The graph produces a structured risk path (a list of contributing factors with weights). The LLM converts this into a merchant-readable sentence. Without the LLM, you'd show raw graph edges — useful for engineers, not for merchants.
- **Why this combination is the right fit**: Graph gives you auditable, queryable structure. LLM gives you readability. Neither alone is sufficient.

### Next-Best-Action Selection (AI — contextual bandit / learned policy)
- **scikit-learn or Vowpal Wabbit**: Learn which intervention (verification, cancellation, masked calling, COD-to-prepaid nudge, premium courier, merchant confirmation, no action) historically produced the best outcome for similar order cohorts.
- **Why AI is needed**: The optimal intervention depends on the interaction of order risk level, category, payment mode, destination, and the merchant's historical response patterns. A static decision tree would either over-intervene (wasting merchant trust) or under-intervene (missing salvageable orders).
- **Why AI is the right fit**: This is a contextual decision problem where the "right" action depends on high-dimensional context. Historical intervention-outcome data provides the training signal for a learned policy.

### Natural-Language Insights for Demand Mix Advisor (AI — LLM-based summarization)
- **LangChain + open-source LLM**: Convert peer benchmark comparisons and cohort performance gaps into plain-language merchant-facing suggestions.
- **Why AI is needed**: Each suggestion involves a unique combination of cohort dimensions, score deltas, and peer reference points. Generating readable, non-repetitive explanations that reference specific data points requires language generation, not templating.

### Outbound Customer Communication (AI for voice calls — deterministic for WhatsApp)
- **WhatsApp Business API (or mock for hackathon)**: Send templated messages to customers based on the identified issue — address confirmation, prepaid payment link, order confirmation, delivery slot preference, or alternate delivery point suggestion.
- **Voice AI (e.g., Bland.ai, Retell, or open-source Vocode)**: Escalation channel when WhatsApp gets no response. Voice AI conducts a contextual conversation with the customer about the same issue.
- **Why WhatsApp doesn't need AI**: Messages are templated per issue type with dynamic fields (order ID, address, payment link URL). The routing logic (which template for which issue) is a deterministic mapping from the Risk_Tag.
- **Why voice AI needs AI**: A voice call must handle free-form customer responses, confirm understanding, and adapt the conversation based on what the customer says. This is a real-time dialogue problem that cannot be scripted with static IVR trees.
- **Escalation flow**: WhatsApp first → configurable wait window (default 2 hours) → voice AI call if no response → update order status based on outcome.

### Dashboard, Workflow Execution, Guardrails (No AI — deterministic)
- **FastAPI**: Backend API serving dashboard data, executing intervention workflows, enforcing rate limits and permissions.
- **React or Streamlit**: Frontend for the hackathon MVP (merchant snapshot, demand advisor, order feed, action console).
- **Why no AI**: Rendering charts, triggering workflows, enforcing caps, logging actions, and checking permissions are all deterministic operations that should be auditable and predictable. Putting AI here would add complexity without value.

### Summary: Where AI Adds Real Value vs Where It Doesn't

| Component | AI? | Technology | Rationale |
|---|---|---|---|
| Data storage and retrieval | No | SQLite | Standard SQL aggregation |
| Cohort statistical benchmarks | No | SQL + Python (pandas) | Means, percentiles, confidence intervals |
| Realized Commerce Score model | **Yes** | scikit-learn / XGBoost | Tabular classification with interaction effects |
| RTO risk reasoning and tagging | **Yes** | NetworkX (graph) + LangChain + Llama 3 / Mistral | Knowledge graph for auditable risk path + LLM for readable explanation |
| Next-best-action selection | **Yes** | scikit-learn / Vowpal Wabbit | Learned intervention policy from outcomes |
| Demand Mix Advisor insights | **Yes** | LangChain + Llama 3 / Mistral | Data-grounded NL summarization |
| WhatsApp outbound messages | No | WhatsApp Business API + templates | Deterministic template selection from Risk_Tag |
| Voice AI escalation calls | **Yes** | Bland.ai / Retell / Vocode | Real-time dialogue handling with free-form customer responses |
| Communication orchestration | No | FastAPI + SQLite | Deterministic escalation flow (WA → wait → voice) |
| Auto-cancel on fraud/extreme risk | No | FastAPI + SQLite | Rule-based: rto_score > cancel_threshold + merchant config enabled |
| Express upgrade for impulsive orders | No | FastAPI + SQLite | Rule-based: late-night + COD + first-time buyer + elevated risk |
| Dashboard and visualization | No | React / Streamlit | Deterministic rendering |
| Workflow execution | No | FastAPI | Deterministic, auditable triggers |
| Guardrails and rate limits | No | FastAPI + SQLite | Rule-based safety checks |
| Permissions and eligibility | No | FastAPI + SQLite | Explicit merchant config |

## Glossary

- **Commerce_AI**: The overall merchant-facing intelligence product comprising the Demand Mix Advisor and Order Action Engine.
- **Demand_Mix_Advisor**: Module that benchmarks a merchant's observed shipping cohorts against peer cohorts on the Delhivery network and surfaces high-confidence suggestions for healthier demand acquisition.
- **Order_Action_Engine**: Module that consumes the existing RTO score, enriches it with merchant context and peer analogs, and recommends or executes the lowest-regret intervention for risky orders.
- **RTO_Score**: The existing Delhivery RTO Predictor output that classifies order-level return-to-origin risk on a numeric scale.
- **Merchant**: A brand or seller that ships orders through the Delhivery network.
- **Cohort**: A group of orders sharing common attributes such as category, price band, payment mode, origin node, and destination cluster.
- **Peer_Benchmark**: A statistical comparison of a merchant's cohort performance against similar merchants on the Delhivery network, matched by category, price band, payment mode, origin node, and destination cluster.
- **Intervention**: An operational action taken on a risky order, such as verification, cancellation, masked calling, COD-to-prepaid nudge, premium courier assignment, or merchant confirmation request.
- **Realized_Commerce_Score**: A probabilistic score (0–1) representing the likelihood that an order in a given cohort will be successfully delivered, produced by a trained gradient-boosted model.
- **Confidence_Gate**: A mechanism that suppresses recommendations when sample size or signal quality falls below defined thresholds. Rule-based, not AI.
- **Destination_Cluster**: A geographic grouping of pincodes with similar delivery performance characteristics.
- **Action_Console**: The UI component that displays executable actions, distinguishing between Delhivery-owned and merchant-owned actions.
- **Merchant_Snapshot**: The dashboard view showing a merchant's warehouse nodes, category-price mix, and peer benchmark gaps.
- **Next_Best_Action**: The recommended intervention for a risky order, selected by a learned policy trained on historical intervention performance across similar cohorts.
- **Dashboard**: The reporting and visualization layer that presents benchmark comparisons, cohort trends, and merchant insights.
- **Risk_Tag**: A human-readable label generated by the LLM explaining why a specific order is flagged as high-RTO-risk.
- **Outbound_Communication**: A customer-facing message (WhatsApp or voice AI call) triggered by the Order_Action_Engine to resolve a specific issue identified on a risky order.
- **Communication_Issue_Type**: The specific problem identified on a risky COD order that determines the outbound message content. Types: address_enrichment (COD order with address quality below threshold), cod_to_prepaid (COD order in high-RTO cluster with acceptable address quality).
- **Escalation_Window**: The configurable time period (default 2 hours) after a WhatsApp message is sent, after which the system escalates to a voice AI call if no customer response is received.
- **Voice_AI_Call**: An AI-powered outbound phone call that conducts a contextual conversation with the customer about the identified issue, handling free-form responses.
- **Auto_Cancel_Threshold**: A configurable RTO_Score threshold per Merchant (default 0.9), above which orders are automatically cancelled if the Merchant has opted in. Higher than the general risk threshold.
- **Impulse_Signal**: A deterministic indicator of impulsive buying behavior. Four signals: late-night ordering (23:00–04:00), COD payment, first-time buyer (no prior delivered orders), high-impulse category (fashion, beauty).
- **Express_Upgrade**: Automatic upgrade of shipping mode from Surface to Express for orders flagged as impulsive, to reduce buyer's remorse window.

## Requirements

### Requirement 1: Merchant Snapshot Display

**User Story:** As a Merchant, I want to see a snapshot of my warehouse nodes, category-price mix, and peer benchmark gaps, so that I can understand how my shipping profile compares to similar merchants on the Delhivery network.

**Technology:** No AI. SQL aggregation from SQLite + deterministic dashboard rendering.

#### Acceptance Criteria

1. WHEN a Merchant opens Commerce_AI, THE Merchant_Snapshot SHALL display the Merchant's active warehouse nodes, category-price band distribution, and payment mode breakdown.
2. WHEN a Merchant opens Commerce_AI, THE Merchant_Snapshot SHALL display Peer_Benchmark gaps for each Cohort dimension (category, price band, payment mode, origin node, Destination_Cluster).
3. IF the Merchant has insufficient order volume (fewer than 100 orders in a Cohort) for a statistically meaningful comparison, THEN THE Merchant_Snapshot SHALL display a notice indicating that benchmark data is not yet available for that Cohort.
4. THE Merchant_Snapshot SHALL refresh benchmark data at least once every 24 hours.

### Requirement 2: Cohort-Based Realized Commerce Scoring

**User Story:** As a Merchant, I want each of my shipping cohorts scored for realized commerce probability, so that I can identify which segments of my demand are structurally healthy and which are underperforming.

**Technology:** AI — scikit-learn / XGBoost gradient-boosted model trained on historical order features predicting delivery success. This cannot be done with rules because the interaction effects between 6+ features across thousands of pincode-category combinations require a learned model.

#### Acceptance Criteria

1. Commerce_AI SHALL compute a Realized_Commerce_Score for each Cohort by combining category, price band, payment mode, origin node, Destination_Cluster, address quality, and historical delivery outcomes using a trained gradient-boosted classification model.
2. WHEN a new Cohort score is computed, Commerce_AI SHALL rank Cohorts from highest to lowest Realized_Commerce_Score within the Merchant's profile.
3. Commerce_AI SHALL recompute Realized_Commerce_Scores at least once every 24 hours using the latest available order and delivery data.
4. IF a Cohort has fewer than 50 historical orders on the Delhivery network, THEN Commerce_AI SHALL flag that Cohort's score as low-confidence.

### Requirement 3: Demand Mix Advisor Suggestions

**User Story:** As a Merchant, I want to receive high-confidence suggestions on which destination clusters, payment mixes, and pincode groups offer structurally stronger delivery realization, so that I can adjust my demand acquisition strategy.

**Technology:** Peer benchmarks computed via SQL aggregation (no AI). Suggestion ranking uses the Realized_Commerce_Score model output (AI). Natural-language explanation of each suggestion uses LangChain + open-source LLM (AI).

#### Acceptance Criteria

1. THE Demand_Mix_Advisor SHALL surface between 1 and 5 high-confidence suggestions per Merchant, ranked by expected improvement in Realized_Commerce_Score.
2. WHEN generating suggestions, THE Demand_Mix_Advisor SHALL compare the Merchant's observed Cohort performance against Peer_Benchmark data from similar merchants by category and price band.
3. EACH suggestion from the Demand_Mix_Advisor SHALL include the specific Cohort dimension being recommended (Destination_Cluster, payment mode, or pincode group), the expected Realized_Commerce_Score improvement, and the Peer_Benchmark reference.
4. THE Demand_Mix_Advisor SHALL apply a Confidence_Gate that suppresses suggestions where the supporting Peer_Benchmark sample size is fewer than 200 peer orders or where the statistical confidence interval exceeds 15 percentage points.
5. IF no suggestions pass the Confidence_Gate, THEN THE Demand_Mix_Advisor SHALL display a message indicating that no high-confidence suggestions are available at this time.

### Requirement 4: Natural-Language Merchant Insights

**User Story:** As a Merchant, I want benchmark comparisons and order signals explained in plain language, so that I can understand the reasoning behind each recommendation without needing to interpret raw data.

**Technology:** AI — LangChain + open-source LLM (Llama 3 or Mistral via Ollama). This cannot be done with templates because each insight involves a unique combination of cohort dimensions, score deltas, and peer reference points that would require maintaining hundreds of condition-explanation mappings.

#### Acceptance Criteria

1. WHEN the Demand_Mix_Advisor generates a suggestion, Commerce_AI SHALL produce a natural-language explanation summarizing the Peer_Benchmark comparison, the Cohort performance gap, and the recommended action.
2. WHEN the Order_Action_Engine recommends a Next_Best_Action, Commerce_AI SHALL produce a natural-language explanation stating the RTO_Score, the contributing risk factors, and the rationale for the recommended Intervention.
3. Commerce_AI SHALL generate natural-language insights using LangChain with an open-source LLM served locally via Ollama.
4. EACH natural-language insight SHALL reference specific data points (Cohort dimensions, score values, sample sizes) rather than generic statements.

### Requirement 5: RTO Score Integration, Risk Display, and Risk Tagging

**User Story:** As a Merchant, I want to see the RTO score for each live order alongside an AI-generated explanation of why this order is risky and what risk tag applies, so that I can understand the risk profile of my current order feed.

**Technology:** RTO score consumption is deterministic (existing system). Risk enrichment uses SQL lookups for historical analogs (no AI). Risk reasoning and tagging uses LangChain + open-source LLM (AI) — because translating a numeric score + multi-dimensional features into a coherent merchant-readable reason requires natural language generation.

#### Acceptance Criteria

1. THE Order_Action_Engine SHALL consume the existing RTO_Score for each order as the primary risk input.
2. WHEN an order is created, THE Order_Action_Engine SHALL enrich the RTO_Score with merchant-specific context including category, price band, payment mode, origin node, Destination_Cluster, and historical outcome analogs from similar Cohorts.
3. WHEN an order's RTO_Score exceeds the configurable risk threshold, Commerce_AI SHALL generate a Risk_Tag using the LLM that explains in one sentence why this order is flagged as high-risk, referencing the specific contributing factors.
4. Commerce_AI SHALL display each order's RTO_Score, Risk_Tag, and enriched risk context in a live order feed, updated within 60 seconds of order creation.
5. WHILE the live order feed is active, Commerce_AI SHALL sort orders by RTO_Score in descending order (highest risk first) by default.

### Requirement 6: Next-Best-Action Recommendation

**User Story:** As a Merchant, I want the system to recommend the lowest-regret intervention for each risky order, so that I can reduce RTO rates without over-intervening on healthy orders.

**Technology:** AI — scikit-learn or Vowpal Wabbit contextual bandit / learned policy. This cannot be done with static rules because the optimal intervention depends on the interaction of order risk level, category, payment mode, destination, and merchant response patterns. A static decision tree would either over-intervene (wasting merchant trust) or under-intervene (missing salvageable orders).

#### Acceptance Criteria

1. WHEN an order's RTO_Score exceeds a configurable risk threshold, THE Order_Action_Engine SHALL generate a Next_Best_Action recommendation from the set of available Interventions (verification, cancellation, masked calling, premium courier assignment, merchant confirmation request, address enrichment outreach, COD-to-prepaid outreach, auto-cancel, express upgrade, or no action).
2. THE Order_Action_Engine SHALL select the Next_Best_Action using a learned policy trained on historical Intervention performance across similar Cohorts (matching on category, price band, payment mode, origin node, and Destination_Cluster).
3. EACH Next_Best_Action recommendation SHALL include a confidence score between 0 and 1 representing the model's certainty in the recommendation.
4. IF the confidence score for a Next_Best_Action is below 0.6, THEN THE Order_Action_Engine SHALL default to recommending "no action" rather than a low-confidence Intervention.
5. THE Order_Action_Engine SHALL generate a Next_Best_Action recommendation within 5 seconds of receiving an enriched order.

### Requirement 7: Action Console and Execution

**User Story:** As a Merchant, I want a console that clearly separates Delhivery-executable actions from merchant-owned actions, so that I know which interventions are handled automatically and which require my involvement.

**Technology:** No AI. Deterministic workflow execution via FastAPI. Action categorization is a static mapping. Workflow triggers, logging, and retry logic are rule-based.

#### Acceptance Criteria

1. THE Action_Console SHALL categorize each recommended Intervention as either "Delhivery-executable" or "Merchant-owned".
2. WHEN a Delhivery-executable Intervention is approved (or auto-approved per merchant policy), THE Action_Console SHALL trigger the corresponding Delhivery workflow (verification, cancellation, masked calling, or premium courier assignment) within 10 seconds.
3. WHEN a Merchant-owned Intervention is recommended (COD-to-prepaid nudge or merchant confirmation request), THE Action_Console SHALL notify the Merchant through the configured communication channel and display the pending action status.
4. THE Action_Console SHALL log every Intervention execution with a timestamp, the order identifier, the Intervention type, the initiating party (Delhivery or Merchant), and the outcome.
5. IF a Delhivery-executable Intervention fails during execution, THEN THE Action_Console SHALL display an error status for that order and retry the Intervention once within 30 seconds.

### Requirement 8: Guardrails and Eligibility Checks

**User Story:** As a Merchant, I want the system to enforce safety limits on automated interventions, so that I can trust that the system will not take excessive or unauthorized actions on my orders.

**Technology:** No AI. Rule-based rate limiting, permission checks, and cap enforcement via FastAPI + SQLite. These must be deterministic and auditable — AI would add unpredictability to safety-critical controls.

#### Acceptance Criteria

1. Commerce_AI SHALL enforce a configurable maximum number of automated Interventions per Merchant per day (default: 500).
2. Commerce_AI SHALL enforce a configurable maximum Intervention rate per hour per Merchant (default: 100 Interventions per hour).
3. WHEN the daily or hourly Intervention cap is reached, Commerce_AI SHALL queue remaining recommended Interventions and notify the Merchant that the cap has been reached.
4. Commerce_AI SHALL require explicit Merchant permission before enabling any automated Delhivery-executable Intervention type.
5. IF a Merchant has not granted permission for a specific Intervention type, THEN Commerce_AI SHALL present the recommendation as a suggestion only, without executing the Intervention.

### Requirement 9: Confidence-Aware Recommendation Gating

**User Story:** As a Merchant, I want the system to suppress weak or low-sample recommendations, so that I only see suggestions backed by sufficient data.

**Technology:** No AI. Statistical threshold checks (sample size, confidence interval width) are deterministic comparisons. This is intentionally rule-based for transparency and auditability.

#### Acceptance Criteria

1. THE Confidence_Gate SHALL evaluate each recommendation (both Demand_Mix_Advisor suggestions and Next_Best_Action recommendations) against minimum sample size and signal quality thresholds before surfacing the recommendation to the Merchant.
2. THE Confidence_Gate SHALL require a minimum of 200 peer orders for Demand_Mix_Advisor suggestions and a minimum of 50 historical analog orders for Next_Best_Action recommendations.
3. IF a recommendation fails the Confidence_Gate, THEN Commerce_AI SHALL suppress the recommendation from the Merchant-facing interface.
4. THE Confidence_Gate SHALL log all suppressed recommendations with the reason for suppression (insufficient sample size or low signal quality) for internal audit.

### Requirement 10: Dashboard and Benchmark Presentation

**User Story:** As a Merchant, I want dashboard views showing cohort comparisons and trend visualizations, so that I can track how my shipping performance evolves over time relative to peers.

**Technology:** No AI. SQL aggregation for metrics, deterministic chart rendering via React/Streamlit. Filtering and time-period selection are standard query parameters.

#### Acceptance Criteria

1. THE Dashboard SHALL display Cohort-level Realized_Commerce_Score trends over configurable time periods (7 days, 30 days, 90 days).
2. THE Dashboard SHALL display side-by-side comparisons of the Merchant's Cohort performance against Peer_Benchmark averages for each Cohort dimension.
3. WHEN a Merchant applies a filter (by category, price band, payment mode, origin node, or Destination_Cluster), THE Dashboard SHALL update all displayed metrics and visualizations to reflect the filtered Cohort within 3 seconds.
4. THE Dashboard SHALL display the total number of Interventions executed, grouped by Intervention type and outcome (successful delivery, RTO, pending), for the selected time period.

### Requirement 11: Local Backend with Historical Order Data

**User Story:** As a demo operator, I want the system to run locally with a SQLite database pre-loaded with real order data from hundreds of shippers over the last 6–9 months, so that all AI models and benchmarks operate on realistic data.

**Technology:** No AI. SQLite database with Python data loading scripts.

#### Acceptance Criteria

1. Commerce_AI SHALL include a local SQLite database pre-loaded with anonymized order data spanning at least 6 months from at least 100 distinct shippers.
2. THE database SHALL contain for each order: merchant identifier, customer UCID (unique identifier for phone number), category, price band, payment mode, origin node (warehouse), destination pincode, address quality indicator, RTO score, delivery outcome (delivered, RTO, or pending), intervention history (type, timestamp, outcome), and order creation timestamp.
3. Commerce_AI SHALL provide a data loading script that populates the SQLite database from CSV or JSON source files.
4. THE backend API (FastAPI) SHALL serve all dashboard, scoring, and recommendation endpoints from this local SQLite database without requiring external service dependencies.

### Requirement 12: Outbound Customer Communication (WhatsApp + Voice AI Escalation)

**User Story:** As a Merchant, I want the system to automatically reach out to customers on risky orders via WhatsApp first and then voice AI call if needed, with the message tailored to the specific issue identified, so that addressable problems are resolved before the order ships and RTO rates decrease.

**Technology:** WhatsApp messages are deterministic (templated per issue type, no AI needed — the routing from Risk_Tag to template is a static mapping). Voice AI calls require AI because the system must handle free-form customer responses in real-time dialogue. Communication orchestration (WA → wait → voice escalation) is deterministic workflow logic.

#### Communication Issue Types and Actions

| Issue Type | Risk_Tag Trigger | Why We Can Detect This | WhatsApp Action | Voice AI Action |
|---|---|---|---|---|
| Address enrichment | COD order + address quality score < threshold | `address_quality` field in order data directly measures this; only COD orders because prepaid RTO from bad address is the customer's loss, not ours | Send address confirmation/correction request with current address displayed | Ask customer to confirm or dictate correct address |
| COD-to-prepaid conversion | COD order + high-RTO destination cluster + address quality is fine | System knows `payment_mode` + historical RTO rates by `destination_cluster` from 6-9 months of data; address is fine so the risk is payment-mode-driven | Send prepaid payment link with order summary and incentive (if configured) | Explain benefits of prepaid, guide through payment |

**Routing logic (deterministic, no AI):**
- Only COD orders are eligible for outbound communication (prepaid orders are not targeted)
- IF `address_quality < threshold` → address_enrichment (fix the address first, higher priority)
- ELIF `destination_cluster` COD-RTO rate > cluster threshold → cod_to_prepaid (address is fine, risk is payment-mode-driven)
- Address enrichment takes precedence when both conditions are true (no point converting payment if the address is wrong)

#### Acceptance Criteria

1. WHEN the Order_Action_Engine generates a Next_Best_Action that maps to an outbound communication issue type (address_enrichment or cod_to_prepaid), Commerce_AI SHALL send a WhatsApp message to the customer within 60 seconds of the recommendation.
2. THE WhatsApp message SHALL be selected from a pre-defined template corresponding to the Communication_Issue_Type, populated with order-specific dynamic fields (order ID, current address, payment link URL, delivery options).
3. IF the customer does not respond to the WhatsApp message within the configurable Escalation_Window (default: 2 hours), Commerce_AI SHALL initiate a Voice_AI_Call to the customer with the same issue context.
4. THE Voice_AI_Call SHALL be contextually aware of the Communication_Issue_Type and SHALL handle free-form customer responses to resolve the identified issue (e.g., capture corrected address, confirm payment, confirm order, select delivery slot, choose pickup point).
5. WHEN a customer responds to either the WhatsApp message or the Voice_AI_Call, Commerce_AI SHALL update the order record with the resolution (address_updated, payment_converted, or no_resolution) and log the communication outcome.
6. IF the customer does not respond to both the WhatsApp message and the Voice_AI_Call, Commerce_AI SHALL mark the communication as "no_response" and the Order_Action_Engine SHALL fall back to the next-best non-communication Intervention (e.g., cancellation or merchant confirmation).
7. Commerce_AI SHALL enforce a maximum of 1 WhatsApp message and 1 Voice_AI_Call per order per Communication_Issue_Type to prevent customer harassment.
8. Commerce_AI SHALL require explicit Merchant permission before enabling outbound customer communication for each Communication_Issue_Type.
9. THE Action_Console SHALL display the communication status for each order (WhatsApp sent, awaiting response, voice call scheduled, voice call completed, resolved, no response) in real time.
10. Commerce_AI SHALL log every outbound communication with: order ID, Communication_Issue_Type, channel (WhatsApp or voice), timestamp sent, customer response (if any), resolution outcome, and time to resolution.

### Requirement 13: Auto-Cancel on High RTO Score (Fraud/Extreme Risk)

**User Story:** As a Merchant, I want orders with extremely high RTO scores to be automatically cancelled when I've opted in, so that clearly fraudulent or undeliverable orders are stopped before they enter the logistics pipeline.

**Technology:** No AI. Pure rule-based threshold check + merchant config flag. The RTO score already captures fraud/risk signal — we just need a higher threshold for auto-cancel vs the general risk threshold used for interventions.

#### Acceptance Criteria

1. Commerce_AI SHALL support a configurable auto-cancel threshold per Merchant (default: 0.9), separate from and higher than the general risk threshold used for Next_Best_Action recommendations.
2. WHEN an order's RTO_Score exceeds the Merchant's auto-cancel threshold AND the Merchant has enabled auto-cancel in their configuration, Commerce_AI SHALL automatically cancel the order without requiring further approval.
3. IF the Merchant has NOT enabled auto-cancel in their configuration, Commerce_AI SHALL NOT auto-cancel any order regardless of RTO_Score, and SHALL instead route the order through the standard Next_Best_Action flow.
4. Commerce_AI SHALL log every auto-cancelled order with: order ID, merchant ID, RTO_Score, the auto-cancel threshold that was exceeded, and the cancellation timestamp.
5. THE Action_Console SHALL display auto-cancelled orders in a distinct "Auto-Cancelled" status with the RTO_Score and Risk_Tag visible.
6. Commerce_AI SHALL include auto-cancel as a configurable toggle in the Merchant permissions (disabled by default), with the threshold value editable by the Merchant.

### Requirement 14: Express Upgrade for Impulsive Orders

**User Story:** As a Merchant, I want orders that show impulsive buying patterns to be automatically upgraded from Surface to Express shipping, so that faster delivery reduces the window for buyer's remorse and lowers RTO rates.

**Technology:** No AI. Deterministic rule-based identification of impulsive orders using signals already present in the order data and SQLite history. The impulse signals are:
- **Late-night ordering**: Order placed between 11 PM and 4 AM (order `created_at` timestamp) — impulse buying peaks during these hours.
- **COD payment**: `payment_mode = COD` — removes payment friction, making impulse purchases easier.
- **First-time buyer**: `customer_ucid` has zero prior delivered orders with this merchant in the database — no established purchase relationship.
- **Category signal**: Category is in a high-impulse set (fashion, beauty) — these categories have structurally higher impulse-driven RTO rates.

An order is flagged as impulsive when it meets at least 3 of the 4 signals above AND has an elevated RTO score (above the general risk threshold but below the auto-cancel threshold).

#### Acceptance Criteria

1. Commerce_AI SHALL evaluate each order against 4 impulse signals: late-night ordering (created_at between 23:00 and 04:00), COD payment mode, first-time buyer (no prior delivered orders from this customer_ucid to this merchant), and high-impulse category (fashion, beauty).
2. WHEN an order matches at least 3 of the 4 impulse signals AND the order's RTO_Score is above the general risk threshold but below the auto-cancel threshold, Commerce_AI SHALL flag the order as impulsive.
3. WHEN an order is flagged as impulsive AND the Merchant has enabled express upgrade in their configuration, Commerce_AI SHALL automatically upgrade the shipping mode from Surface to Express for that order.
4. IF the Merchant has NOT enabled express upgrade in their configuration, Commerce_AI SHALL NOT upgrade any order, and SHALL instead display the impulsive flag as an informational tag in the live order feed.
5. Commerce_AI SHALL log every express upgrade with: order ID, merchant ID, RTO_Score, the impulse signals that matched, the original shipping mode, and the upgrade timestamp.
6. THE Action_Console SHALL display express-upgraded orders with an "Express Upgrade (Impulse)" status showing which impulse signals were detected.
7. Commerce_AI SHALL include express upgrade as a configurable toggle in the Merchant permissions (disabled by default), with the high-impulse category list editable by the Merchant.
8. THE first-time buyer check SHALL query the orders table for any prior order from the same customer_ucid to the same merchant_id with delivery_outcome = "delivered".

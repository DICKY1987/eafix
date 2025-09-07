# Agentic AI Modernization Plan for the eafix Trading System

## Overview and Scope

This document defines the tasks for an agentic AI acting as a
**Modernization Architect & Implementer**. The goal is to convert the
existing **eafix** trading system (repository: `DICKY1987/eafix`) from a
single‑codebase application into a set of modular, containerized
services. The repository combines trading utilities, economic calendar
processing and a unified GUI for MetaTrader 4
integration[\[1\]](https://raw.githubusercontent.com/DICKY1987/eafix/master/README.md#:~:text=This%20repository%20contains%20a%20comprehensive,interface%20for%20MetaTrader%204%20integration).
Existing documentation identifies processes such as calendar intake,
matrix mapping, re‑entry decisioning, transport/router, EA bridge,
telemetry daemon and
GUI[\[2\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_runtime_architecture.md#:~:text=,UX%3B%20System%20Status%3B%20Signals%2FHistory%2FConfig%2FDiagnostics%20tabs).
Risk and portfolio
limits[\[3\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md#:~:text=%23%23%201.%20Per%E2%80%91Symbol%20Limits%20,broker%E2%80%91aware),
calendar
ingestion[\[4\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md#:~:text=,11%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81),
signal
mapping[\[5\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md#:~:text=,%28Master%20%C2%A75.1%E2%80%93%C2%A75.6%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
and
observability[\[6\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md#:~:text=%23%23%201.%20Acceptance%20%28Selected%29%20,100%20Acceptance%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
are all critical aspects of the system. The modernization process must
preserve these features while improving reliability and maintainability.

**Terminology:** In this plan, "decomposition" means breaking the
monolith into services, "modularization" means restructuring code into
well‑bounded modules, and "containerization" means packaging each
service into a Docker image and defining orchestration manifests.

## Phase 1 -- Decompose the Monolith

### Objectives

1.  **Identify Service Boundaries.** Use documentation to define
    distinct responsibilities. The Scope Overview outlines subsystems
    such as calendar, matrix, re‑entry, transport/communication, EA
    bridge, observability and
    GUI[\[7\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_overview.md#:~:text=,panels%2C%20controls%20tied%20to%20contracts).
    The runtime architecture lists individual processes: calendar
    intake, matrix mapper, reentry engine, transport router, EA bridge,
    telemetry daemon and
    gui_app[\[2\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_runtime_architecture.md#:~:text=,UX%3B%20System%20Status%3B%20Signals%2FHistory%2FConfig%2FDiagnostics%20tabs).
2.  **Create a Service Catalog.** For each service, specify its purpose,
    inputs, outputs, dependencies, scaling profile and service‑level
    objectives. A short table summarizing recommended services is below.
    Additional services (e.g. reporter and GUI gateway) may be added to
    meet observability and user interface requirements.

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Service                  Purpose (short phrase)  Inputs / Outputs (short)
  ------------------------ ----------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **data‑ingestor**        Normalize broker price  Receives MT4/DDE/bridge feed; publishes `PriceTick@1.0` events
                           feed                    

  **indicator‑engine**     Compute technical       Consumes `prices.raw` stream; emits `IndicatorVector@1.1` events
                           indicators              

  **signal‑generator**     Apply rules &           Consumes `IndicatorVector` and calendar events; produces `Signal@1.0` events
                           thresholds              

  **risk‑manager**         Position sizing & risk  Accepts signals via HTTP; returns `OrderIntent@1.2`
                           checks                  

  **execution‑engine**     Send orders to broker   Accepts `OrderIntent`; returns `ExecutionReport@1.0`

  **calendar‑ingestor**    Weekly economic         Discovers vendor CSV and normalizes
                           calendar intake         events[\[4\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md#:~:text=,11%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81);
                                                   emits `CalendarEvent@1.0` data

  **reentry‑matrix‑svc**   Manage re‑entry         Uses matrix and outcome state to produce `ReentryDecision@1.0`
                           decisions               

  **reporter**             Metrics & P&L reporting Reads trade and metrics tables; outputs reports

  **gui‑gateway**          Serve operator UI       Provides thin API for GUI; aggregates status
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Use the service catalog to create
`docs/modernization/01_service_catalog.md` describing each service, its
dependencies and SLOs.

1.  **Define Boundaries & Events.** Draw a diagram (Mermaid or PlantUML)
    illustrating event flows and synchronous calls. Use the provided
    example (data‑ingestor → indicator‑engine → signal‑generator →
    risk‑manager → execution‑engine) and include calendar and re‑entry
    services. Capture relationships such as PriceTick → IndicatorVector
    → Signal, and note synchronous HTTP calls from signal to risk and
    from risk to execution.

2.  **Specify Contracts.** For every event and API, create versioned
    schemas. Use OpenAPI for synchronous endpoints (e.g. `/position` and
    `/orders`) and JSON Schema for event payloads. The initial set
    includes:

3.  **PriceTick@1.0** -- timestamp, symbol, bid, ask.

4.  **IndicatorVector@1.1** -- timestamp, symbol, feature dictionary,
    window version.

5.  **Signal@1.0** -- id, timestamp, symbol, side (BUY/SELL),
    confidence, optional explanation.

6.  **OrderIntent@1.2** -- id, symbol, side, quantity, stop loss, take
    profit, timeInForce.

7.  **ExecutionReport@1.0** -- order_id, broker_order_id, status,
    filled_qty, avg_price, timestamp.

8.  **CalendarEvent@1.0** -- id, start_ts, currency, impact
    (LOW/MED/HIGH), title, forecast, actual,
    previous[\[8\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md#:~:text=,8%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).

9.  **ReentryDecision@1.0** -- state, action (ENTER/WAIT/EXIT/ADJUST),
    rationale.

Place API definitions under `contracts/openapi/` and event schemas under
`contracts/events/`.

1.  **Write an Architectural Decision Record (ADR).** Summarize why
    services were decomposed in a certain way, reference docs (e.g.,
    determinism & idempotence[\[9\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=,identical%20artifacts%20for%20identical%20inputs),
    single source of
    truth[\[10\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=,validate%20against%20the%20same%20definitions),
    defensive
    posture[\[11\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=%23%23%203.%20Defensive%20Posture%20,clock%E2%80%91skew%3B%20suppress%20decisions%20until%20healthy),
    and explicit
    fallbacks[\[12\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=%23%23%204.%20Explicit%20Fallbacks%20,audit%20trails%20and%20coverage%20metrics))
    and outline risks. Save this as
    `docs/adr/ADR-0001-service-decomposition.md`.

### Acceptance Criteria for Phase 1

-   All capabilities from the monolith are mapped to exactly one
    service.
-   Service catalog and boundaries diagrams are complete and reflect
    current documentation.
-   Every contract is versioned and machine‑validates via JSON Schema or
    OpenAPI.
-   ADR captures rationale and cross‑references relevant documentation.

## Phase 2 -- Modularize the Codebase

### Objectives

1.  **Create Module Directories.** For each service, create
    `services/<name>/` with sub‑directories:

2.  `src/<name>/` -- core logic

3.  `adapters/` -- external IO (database, broker, network)

4.  `tests/` -- unit tests and contract tests

5.  **Implement Adapters.** Build thin wrappers around external systems.
    For example, a `BrokerAdapter` hides MT4 socket and file‑based
    communications (CSV or socket) described in the
    Integration & Communication
    layer[\[13\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_integration_comm.md#:~:text=%23%23%201.%20Adapters%20,7%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).
    A `CalendarAdapter` encapsulates vendor CSV discovery and
    normalization
    rules[\[4\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md#:~:text=,11%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).

6.  **Create Contract Tests.** Under `tests/contracts/`, add tests
    ensuring that each API endpoint conforms to its OpenAPI schema and
    each event published matches its JSON Schema. Use mocking to isolate
    external dependencies.

7.  **Update Build System.** Consolidate service dependencies into a
    top‑level workspace (e.g. `pyproject.toml` with `[tool.poetry]` and
    multiple packages) or similar. Ensure each module can be installed
    in editable mode for local development.

8.  **Continuous Integration (CI).** Add a GitHub Actions workflow
    (`.github/workflows/ci.yml`) that runs unit tests, schema validation
    and contract tests on push/pull requests.

### Acceptance Criteria for Phase 2

-   Each service builds and runs independently with mocked adapters.
-   Cross‑service communication occurs only through defined contracts.
-   Module boundaries enforce single source of truth (schemas in
    `contracts` are canonical).
-   CI passes with no failing tests.

## Phase 3 -- Containerize and Orchestrate

### Objectives

1.  **Write Dockerfiles.** For each service, create
    `services/<name>/Dockerfile` that:

2.  Uses an official Python base image (e.g., `python:3.11-slim`).

3.  Adds a non‑root user and installs dependencies using Poetry or pip.

4.  Copies only the relevant service code.

5.  Exposes a port (e.g. 8080) and defines a health‑check endpoint
    (`/healthz`).

6.  Uses `USER appuser` and `CMD ["python","-m", "<name>.main"]`.

7.  **Define Local Compose.** Create `deploy/compose/docker-compose.yml`
    that brings up all services with dependencies (Postgres, Redis or
    file‑based message bus). Respect existing infrastructure: CSV and
    socket adapters may remain for EA
    interactions[\[13\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_integration_comm.md#:~:text=%23%23%201.%20Adapters%20,7%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81),
    but within the containerized microservices use a message broker
    (e.g. Redis pub/sub) for internal events. Map volumes for shared
    files if necessary.

8.  **Prepare K8s Manifests (optional).** Under `deploy/k8s/`, provide
    `namespace.yaml`, `deployment.yaml`, `service.yaml`, `hpa.yaml`,
    `configmap.yaml` and `secret.yaml` templates for each service. These
    should implement readiness and liveness probes, resource
    requests/limits and Horizontal Pod Autoscaler based on CPU
    utilization.

9.  **Observability.** Include structured JSON logging and metrics
    endpoints for each service. Support metrics and health telemetry
    described in the QC & acceptance
    documentation[\[14\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md#:~:text=Emit%20to%20DB%20%2B%20,3%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).
    Provide runbooks summarizing how to operate each service under
    `docs/runbooks/`.

### Acceptance Criteria for Phase 3

-   `docker compose up` launches the full stack locally. All services
    start, health checks succeed, and events flow end‑to‑end
    (price → indicators → signals → orders).
-   Each Docker image passes a vulnerability scan.
-   K8s manifests are syntactically valid and support scaling up/down of
    stateless services.
-   Logs and metrics expose latency, coverage and error rates as defined
    in the system
    documentation[\[14\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md#:~:text=Emit%20to%20DB%20%2B%20,3%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).

## Guardrails & Best Practices

-   **Determinism and Idempotence.** All emitters should write files or
    publish events atomically and
    idempotently[\[9\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=,identical%20artifacts%20for%20identical%20inputs).
-   **Single Source of Truth.** Treat CSV contracts and schemas as
    canonical[\[10\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=,validate%20against%20the%20same%20definitions).
    Validate incoming data against schemas before processing.
-   **Defensive Posture & Observability.** Fail closed on integrity
    errors and degrade gracefully when brokers or transports are
    unhealthy[\[11\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=%23%23%203.%20Defensive%20Posture%20,clock%E2%80%91skew%3B%20suppress%20decisions%20until%20healthy).
    Provide health metrics and alerts for coverage, latency, slippage,
    fallback rates and integrity
    checks[\[14\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md#:~:text=Emit%20to%20DB%20%2B%20,3%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).
-   **Explicit Fallbacks & Tiering.** Implement tiered parameter
    resolution for signals as described in the Signal Model & Matrix
    Mapping
    specification[\[15\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md#:~:text=,%28Master%20%C2%A75.8%E2%80%93%C2%A75.9%2C%20%C2%A76.8%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81).
    Maintain audit logs for mapping
    decisions[\[16\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md#:~:text=,2).
-   **Risk & Governance.** Enforce per‑symbol and portfolio caps,
    performance overlays and circuit
    breakers[\[3\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md#:~:text=%23%23%201.%20Per%E2%80%91Symbol%20Limits%20,broker%E2%80%91aware).
    Maintain an append‑only Risk Decisions Log with change
    control[\[17\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md#:~:text=%23%23%205.%20Governance%20,linked%20acceptance%20evidence%20and%20sign%E2%80%91off).
-   **Time and Locale.** Align schedulers to America/Chicago time zone
    and store timestamps in
    UTC[\[18\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_overview.md#:~:text=,fail%20closed%20on%20checksum%20mismatch).

By following this plan, the agentic AI will produce a modular, reliable
and observable version of the eafix trading system. The process yields
clear documentation, versioned contracts, independently deployable
services and container orchestration files. These artefacts enable safer
iteration, easier testing, and future scalability.

[\[1\]](https://raw.githubusercontent.com/DICKY1987/eafix/master/README.md#:~:text=This%20repository%20contains%20a%20comprehensive,interface%20for%20MetaTrader%204%20integration)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/master/README.md>

[\[2\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_runtime_architecture.md#:~:text=,UX%3B%20System%20Status%3B%20Signals%2FHistory%2FConfig%2FDiagnostics%20tabs)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/02_runtime_architecture.md>

[\[3\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md#:~:text=%23%23%201.%20Per%E2%80%91Symbol%20Limits%20,broker%E2%80%91aware)
[\[17\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md#:~:text=%23%23%205.%20Governance%20,linked%20acceptance%20evidence%20and%20sign%E2%80%91off)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md>

[\[4\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md#:~:text=,11%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
[\[8\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md#:~:text=,8%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/05_calendar_ingest_transform.md>

[\[5\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md#:~:text=,%28Master%20%C2%A75.1%E2%80%93%C2%A75.6%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
[\[15\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md#:~:text=,%28Master%20%C2%A75.8%E2%80%93%C2%A75.9%2C%20%C2%A76.8%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
[\[16\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md#:~:text=,2)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/06_signal_model_mapping.md>

[\[6\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md#:~:text=%23%23%201.%20Acceptance%20%28Selected%29%20,100%20Acceptance%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
[\[14\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md#:~:text=Emit%20to%20DB%20%2B%20,3%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md>

[\[7\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_overview.md#:~:text=,panels%2C%20controls%20tied%20to%20contracts)
[\[18\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_overview.md#:~:text=,fail%20closed%20on%20checksum%20mismatch)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_overview.md>

[\[9\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=,identical%20artifacts%20for%20identical%20inputs)
[\[10\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=,validate%20against%20the%20same%20definitions)
[\[11\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=%23%23%203.%20Defensive%20Posture%20,clock%E2%80%91skew%3B%20suppress%20decisions%20until%20healthy)
[\[12\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md#:~:text=%23%23%204.%20Explicit%20Fallbacks%20,audit%20trails%20and%20coverage%20metrics)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md>

[\[13\]](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_integration_comm.md#:~:text=%23%23%201.%20Adapters%20,7%29%20%EE%88%80filecite%EE%88%82turn2file0%EE%88%81)
raw.githubusercontent.com

<https://raw.githubusercontent.com/DICKY1987/eafix/main/02_integration_comm.md>

# Service Catalog

This catalog summarizes the proposed services for the modernized **eafix** trading system.
Each service includes its responsibility, key dependencies and service level objectives (SLOs).

| Service | Purpose | Inputs | Outputs | Dependencies | SLOs |
| --- | --- | --- | --- | --- | --- |
| data-ingestor | Normalize broker price feed | MT4/DDE/bridge feed | `PriceTick@1.0` events | connection to price feed | 99.9% availability, <50ms publish latency |
| indicator-engine | Compute technical indicators | `PriceTick` stream | `IndicatorVector@1.1` events | data-ingestor | process tick within 100ms |
| signal-generator | Apply rules and thresholds | `IndicatorVector`, `CalendarEvent`, `ReentryDecision` | `Signal@1.0` events and HTTP calls to risk-manager | indicator-engine, calendar-ingestor, reentry-matrix-svc | generate signals within 100ms of indicators |
| risk-manager | Position sizing & risk checks | `Signal` via HTTP `/position` | `OrderIntent@1.2` | signal-generator | respond within 200ms |
| execution-engine | Send orders to broker | `OrderIntent` via HTTP `/orders` | `ExecutionReport@1.0` | risk-manager, broker API | 99.9% availability, <250ms to broker |
| calendar-ingestor | Weekly economic calendar intake | Vendor CSV | `CalendarEvent@1.0` | external calendar source | complete ingest within 5min of availability |
| reentry-matrix-svc | Manage re-entry decisions | matrix & outcome state | `ReentryDecision@1.0` | trading DB | compute decision within 100ms |
| reporter | Metrics & P&L reporting | trades and metrics tables | reports | DB access | daily report by 01:00 UTC |
| gui-gateway | Serve operator UI | status from services | aggregated status API | all services | 99% availability |


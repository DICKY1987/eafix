# Event Flow

```mermaid
flowchart LR
    price[(Price Feed)] -->|PriceTick@1.0| DI[data-ingestor]
    DI -->|PriceTick@1.0| IE[indicator-engine]
    IE -->|IndicatorVector@1.1| SG[signal-generator]
    cal[calendar-ingestor] -->|CalendarEvent@1.0| SG
    re[reentry-matrix-svc] -->|ReentryDecision@1.0| SG
    SG -- POST /position --> RM[risk-manager]
    RM -- POST /orders --> EE[execution-engine]
    EE -->|ExecutionReport@1.0| RM
```

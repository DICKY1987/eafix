# HUEY_P Trading System - Complete Technical Reference Document

**Document Version**: 3.1  
**Source**: Project Knowledge Base Analysis (with v3.1 redlines applied)  
**Classification**: Technical Implementation Reference  
**Target Audience**: System Architects, Developers, Operations Teams  

---

## 1. SYSTEM ARCHITECTURE & CORE COMPONENTS

### 1.1 Production Deployment Structure

```
MetaTrader 4 Terminal Root/
├── MQL4/
│   ├── Experts/
│   │   └── HUEY_P_EA_ExecutionEngine_8.mq4          # Main EA (7000+ lines)
│   ├── Libraries/
│   │   └── MQL4_DLL_SocketBridge.dll                # Communication bridge
│   ├── Files/
│   ├── bridge/
│   │   ├── trading_signals.csv                      # Python → EA signals
│   │   └── trade_responses.csv                      # EA → Python responses
│   ├── logs/
│   │   └── parameter_log.csv                        # EA parameter tracking
│   ├── NewsCalendar.csv                             # Economic calendar data
│   └── TimeFilters.csv                              # Trading session config
│   └── Include/
│       └── HUEY_P_Common.mqh                        # Shared definitions
├── eafix/                                           # Python interface directory
│   ├── core/
│   │   ├── app_controller.py                        # Main orchestration
│   │   ├── database_manager.py                      # SQLite operations
│   │   ├── ea_connector.py                          # Socket communication
│   │   └── data_models.py                           # Type definitions
│   ├── Database/
│   │   ├── trading_system.db                        # Main database
│   │   └── trading_system.backup_*.db               # Automated backups
│   └── huey_main.py                                 # Primary Python application
```

### 1.2 System Requirements (Production Validated)

**Hardware Requirements:**
- **CPU**: Intel Core i5 or equivalent (minimum 2.4GHz)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 500GB available space
- **Network**: Stable internet connection with <100ms latency to broker

**Software Dependencies:**
- **Windows 10/11**: 64-bit operating system
- **MetaTrader 4**: Latest version with "Allow DLL imports" enabled
- **Python 3.8+**: With packages from `huey_requirements.txt`
- **Visual Studio Build Tools**: For DLL compilation (cmake, MSVC compiler)
- **SQLite**: Database engine (included with Python)

---

## 2. SYMBOL SPECIFICATIONS & MARKET DATA

### 2.1 Supported Currency Pairs (Illustrative)

⚠️ **Note:** Replace with definitive export from MT4 “Specification” dialog per symbol.

**Forex Majors & Minors (illustrative list):**
- EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- EURJPY, GBPJPY, EURGBP, EURAUD

### 2.2 Symbol Specification Appendix (Scaffold)

| Symbol | Contract Size | Min Lot | Max Lot | Lot Step | Tick Size | Tick Value | Spread Type | Typical Spread | Swap Long | Swap Short | Trading Hours |
|--------|---------------|---------|---------|----------|-----------|------------|-------------|----------------|-----------|------------|---------------|
|        |               |         |         |          |           |            |             |                |           |            |               |

➡️ Populate from MT4 export and broker portal.

---

## 3. REENTRY LOGIC FRAMEWORK (Matrix v2)

**Status:** Matrix v2 with SSD overlay – **LIVE**.

(...unchanged sections retained, schema + DB tables included...)

---

## 4. RISK MANAGEMENT SYSTEM

- **Default max risk percent**: **2.0%** (configurable).
- **Hard cap**: **3.5% enforced by system**. Runtime checks always win.

(...rest of section unchanged...)

---

## 5. COMMUNICATION PROTOCOLS

### 5.1 Transport Profiles

- **Current profile (v1.0)**: Socket (raw TCP framing) **primary**, CSV **fallback**.
- **Planned profile (v1.2)**: Socket over TLS 1.3 with mTLS and HMAC integrity.

### 5.2 CSV Communication Contracts

(...unchanged CSV formats, headers, atomic write protocol...)

---

## 6. VALIDATION & ERROR HANDLING

(...unchanged, includes broker error code placeholders...)

---

## 7. PERFORMANCE SPECIFICATIONS & BENCHMARKS

- **Targets:** Socket latency <100ms, EA ack <50ms, CSV ops <50ms.
- ⚠️ **Evidence pending**: mark these as goals until Test Evidence Pack logs are captured.

➡️ Add to Test Evidence Pack appendix.

---

## 8. SYSTEM HEALTH MONITORING

(...unchanged...)

---

## 9. DATA ROTATION & ARCHIVE MANAGEMENT

- **Retention**: 30 days local logs (compressed). 90 days DB hot storage, 7 years WORM archive.

---

## 10. INDICATOR SYSTEM CONFIGURATION

(...unchanged...)

---

## 11. TESTING FRAMEWORK ARCHITECTURE

(...unchanged, includes validation test cues...)

### 11.4 Test Evidence Pack (Scaffold)

| Test Case | Expected Result | Evidence (log/screenshot) | Pass/Fail |
|-----------|----------------|---------------------------|-----------|
| Socket latency <100ms | Ack <100ms | attach log excerpt | |
| EA response <50ms | Ack <50ms | attach MT4 log | |
| E1001 reject >3.5% risk | REJECT_SET | attach screenshot | |

---

## 12. ECONOMIC CALENDAR INTEGRATION

(...unchanged...)

---

## 13. CONFIGURATION MANAGEMENT

(...unchanged...)

---

## 14. DEPLOYMENT CHECKLIST

(...unchanged...)

### 14.5 Runbook Scaffold (to be expanded)

- **Monitoring & Alerts**: define tools, alert routing.
- **Escalation Levels**: on-call, secondary, management.
- **Broker Failover**: steps for server outage.
- **Rollback SOP**: procedure if patch/param fails.

---

## 15. OPERATIONAL STATUS SUMMARY

- ⚠️ Terminal ID masked in public docs; maintain in secrets appendix if required.

(...rest unchanged...)

---

**Document ID**: HUEY_P_TECHNICAL_REFERENCE_v3.1  
**Scope**: Redlined for consistency; scaffolds for broker data, test evidence, and runbook expansion added.


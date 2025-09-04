"""Combined gate engine placeholder."""

from . import market_quality, risk_management, system_health, broker_connectivity


def all_checks(context=None) -> bool:
    return all(
        gate.check(context)
        for gate in (market_quality, risk_management, system_health, broker_connectivity)
    )

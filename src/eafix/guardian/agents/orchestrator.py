"""Guardian agent orchestrator placeholder."""

from dataclasses import dataclass
from typing import List

from .risk_agent import RiskAgent
from .market_agent import MarketAgent


@dataclass
class AgentOrchestrator:
    risk: RiskAgent
    market: MarketAgent

    def run_all(self) -> List[bool]:
        return [self.risk.assess(), bool(self.market.snapshot())]

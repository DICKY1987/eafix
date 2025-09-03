"""Currency Strength Indicator

Calculates relative strength for each currency by aggregating percent
changes across provided currency pairs. Each pair contributes its percent
change positively to the base currency and negatively to the quote
currency. Strength for each currency is the average of its contributions.

This indicator returns a dictionary mapping currency codes to strength
values (as decimal percent change). It requires access to a
``PriceManager`` instance to obtain historical prices for each pair.
"""

from collections import defaultdict
from typing import Dict, List

from .base_indicator import MultiValueIndicator, IndicatorConfig, IndicatorFactory


class CurrencyStrengthIndicator(MultiValueIndicator):
    """Aggregate percent-change based currency strength indicator."""

    def __init__(self, name: str, config: IndicatorConfig):
        super().__init__(name, config)
        self.price_manager = config.get("price_manager")
        if self.price_manager is None:
            raise ValueError("price_manager is required for CurrencyStrengthIndicator")

        # List of currency pairs to include. If not provided, we'll query
        # the price manager when calculating values.
        self.symbols: List[str] = config.get("symbols", [])
        self.window: int = config.get("window", 10)

    def get_required_periods(self) -> int:
        # This indicator recalculates on every tick and does not depend on
        # its own history buffer.
        return 1

    def calculate_values(self, price_data) -> Dict[str, float]:
        symbols = self.symbols or self.price_manager.get_all_symbols()
        strengths: Dict[str, List[float]] = defaultdict(list)

        for symbol in symbols:
            prices = self.price_manager.get_price_array(symbol, "mid", self.window)
            if len(prices) < 2:
                continue
            change = (prices[-1] - prices[0]) / prices[0]
            base, quote = symbol[:3], symbol[3:]
            strengths[base].append(change)
            strengths[quote].append(-change)

        # Average contributions per currency
        return {
            ccy: float(sum(vals) / len(vals))
            for ccy, vals in strengths.items()
            if vals
        }


# Register indicator with factory so it can be constructed dynamically
IndicatorFactory.register("CurrencyStrength", CurrencyStrengthIndicator)


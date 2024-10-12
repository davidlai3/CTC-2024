from datetime import datetime
from backtester import Backtester
from example_strategy import Strategy

start = datetime(2024, 1, 1)
end = datetime(2024, 1, 15)
s = Strategy()
b = Backtester(start, end, s)

b.calculate_pnl()
from datetime import datetime
from backtester import Backtester
from starter_code import Strategy

start = datetime(2024, 1, 1)
end = datetime(2024, 3, 30)
s = Strategy()
b = Backtester(start, end, s)

# print( s.parse_symbol( "SPX   240216C05020000" ) )

b.calculate_pnl()
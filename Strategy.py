import pandas as pd
from collections import deque
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import norm

class pricing:

    @staticmethod
    def black_scholes_call(S, K, T, r=0.03, sigma=0.15):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price

    @staticmethod
    def black_scholes_put(S, K, T, r=0.03, sigma=0.15):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price

    @staticmethod
    def implied_volatility(option_price, S, K, T, r=0.01, option_type="call", tol=1e-8, max_iterations=100):
        # Initial guess for volatility
        sigma = 0.2
        for i in range(max_iterations):
            if option_type == "call":
                price = pricing.black_scholes_call(S, K, T, r, sigma)
            else:
                price = pricing.black_scholes_put(S, K, T, r, sigma)

            # Vega: sensitivity of the option price to changes in volatility
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T)  # Vega is the partial derivative of option price w.r.t. sigma

            # Price difference
            price_diff = price - option_price

            # Check if the difference is small enough
            if abs(price_diff) < tol:
                return sigma

            # Update volatility estimate using Newton-Raphson
            sigma = sigma - price_diff / vega

        # If no convergence, return the last value of sigma
        return sigma

class helper:

    # timestamp_1 is the order timestamp
    # timestamp_2 is the underlying timestamp
    # returns true if order timestamp is after underlying timestamp 

    @staticmethod
    def generate_datetime(ms: int, date: str) -> datetime:
        hour = ms // 3600000
        ms = ms % 3600000
        minute = ms // 60000

        base = datetime.strptime(date, "%Y%m%d")
        compiled_datetime = base.replace(hour=hour, minute=minute)

        return compiled_datetime


    # timestamp_1 is the order timestamp
    # timestamp_2 is the underlying timestamp
    @staticmethod
    def compare_times(timestamp_1: str, timestamp_2ms: int, timestamp_2day: str) -> bool:
        timestamp_1 = timestamp_1[:26] + 'Z'
        dt1 = datetime.strptime(timestamp_1, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt2 = helper.generate_datetime(timestamp_2ms, timestamp_2day)

        return dt1 > dt2 


    @staticmethod
    def time_difference_in_years(date1: str, date2: datetime) -> float:
        # Parse the first date formatted as "yyyy-mm-dd"
        date1_parsed = datetime.strptime(date1, "%Y-%m-%d")
        
        # Calculate the difference in days
        difference_in_days = abs((date1_parsed - date2).days)
        
        # Convert days to years
        difference_in_years = difference_in_days / 365.25  # Considering leap years
        
        return difference_in_years

    @staticmethod
    def parse_option_symbol(symbol) -> dict:
        """
        EXAMPLE: SPX 20230120P2800000
        """
        numbers : str = symbol.split(" ")[1]
        date : str = numbers[:8]
        date_yymmdd : str = date[0:4] + "-" + date[4:6] + "-" + date[6:8]
        action : str = numbers[8]
        strike_price : float = int(numbers[9:])/1000
        return {
            "expiry": datetime.strptime(date_yymmdd, "%Y-%m-%d"),
            "action": action,
            "strike": strike_price
        }

    """
    def parse_order(row) -> dict:
            "instrument" : row["instrument_id"],
            "bid_size" : row["bid_sz_00"],
            "ask_size" : row["ask_sz_00"],
        data = {
            "bid_price" : row.bid_px_00,
            "ask_price" : row.ask_px_00,
            "date" : row.ts_recv,
            "expiry" : row.symbol[6:12],
            "order_type" : row.symbol[12],
            "strike" : float(row.symbol[13:20])/10000
        }

        return data
    """

class Strategy:
  
    def __init__(self, start_date, end_date, options_data, underlying) -> None:
        self.capital : float = 100_000_000
        self.portfolio_value : float = 0

        self.start_date : datetime = start_date
        self.end_date : datetime = end_date
      
        self.options : pd.DataFrame = pd.read_csv(options_data)
        self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])

        self.underlying = pd.read_csv(underlying)
        self.underlying.columns = self.underlying.columns.str.lower()
        self.size = len(self.underlying)

        # earliest possible hour
        self.minute_ptr = 5
        self.ctr = 0


    def generate_orders(self) -> pd.DataFrame:

        orders = []
        for row in self.options.itertuples():

            if (self.ctr == 5000):
                break
            
            if (self.minute_ptr > self.size - 50):
                break

            """
            # if the minute ptr is ahead, wait until orders catch up
            while not (helper.compare_times(row.ts_recv, int(self.underlying.iloc[self.minute_ptr]["ms_of_day"]), self.underlying.iloc[self.minute_ptr]["date"])):
                continue

            # bring minute ptr to most recent time before order
            while (self.minute_ptr < self.size - 50) and row.ts_recv, int(self.underlying.iloc[self.minute_ptr]["ms_of_day"]), self.underlying.iloc[self.minute_ptr]["date"]:
                self.minute_ptr += 1
            self.minute_ptr -= 1

            mid = float(self.underlying.iloc[self.minute_ptr]["price"])
            """
            
            mid = 5000
            
            if (mid == 0.0):
                mid = float(self.underlying.iloc[self.minute_ptr-1]["price"])

            symbol_data = helper.parse_option_symbol(row.symbol)

            if (row.ask_px_00 < 25):
                continue

            order = {}

            # If the order is an overvalued call then we can sell it
            if (symbol_data["action"] == 'C'):
                time_to_expiry = helper.time_difference_in_years(row.ts_recv[:10], symbol_data["expiry"])
                expected = pricing.black_scholes_call(mid, symbol_data["strike"], time_to_expiry)

                if (expected < row.bid_px_00 - 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "S",
                        "order_size" : max(int(row.bid_sz_00)//4, 1)
                    }
                    orders.append(order)
            # If the order is an overvalued put then we can sell it
            else:
                time_to_expiry = helper.time_difference_in_years(row.ts_recv[:10], symbol_data["expiry"])
                expected = pricing.black_scholes_call(mid, symbol_data["strike"], time_to_expiry)

                if (expected < row.bid_px_00 - 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "S",
                        "order_size" : max(int(row.bid_sz_00)//4, 1)
                    }
                    orders.append(order)

        return pd.DataFrame(orders)


if __name__ == "__main__":
    strategy = Strategy("2024-01-02", "2024-01-03", "data/cleaned_options_data.csv", "data/underlying_data_hour.csv")
    """

    orders = strategy.generate_orders()
    orders.to_csv("orders.csv", index=False)
    print(orders)
    """

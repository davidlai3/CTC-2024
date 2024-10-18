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
    def compare_times(timestamp_1: str, timestamp_2: int) -> bool:
        timestamp_1 = timestamp_1[:26] + 'Z'
        timestamp = datetime.strptime(timestamp_1, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Get the hour part of the timestamp
        hour = timestamp.hour
        # Get the minute part of the timestamp
        minutes = timestamp.minute

        adjusted = (hour * 60 + minutes) * 60000

        return adjusted > timestamp_2


    @staticmethod
    def time_difference_in_years(date1: str, date2: str) -> float:
        # Parse the first date formatted as "yyyy-mm-dd"
        date1_parsed = datetime.strptime(date1, "%Y-%m-%d")
        
        # Parse the second date formatted as "yymmdd"
        date2_parsed = datetime.strptime(date2, "%y%m%d")
        
        # Calculate the difference in days
        difference_in_days = abs((date1_parsed - date2_parsed).days)
        
        # Convert days to years
        difference_in_years = difference_in_days / 365.25  # Considering leap years
        
        return difference_in_years

    @staticmethod
    def parse_order(row) -> dict:
        """
            "instrument" : row["instrument_id"],
            "bid_size" : row["bid_sz_00"],
            "ask_size" : row["ask_sz_00"],
        """
        data = {
            "bid_price" : row.bid_px_00,
            "ask_price" : row.ask_px_00,
            "date" : row.ts_recv,
            "expiry" : row.symbol[6:12],
            "order_type" : row.symbol[12],
            "strike" : float(row.symbol[13:20])/10000
        }

        return data

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

        # earliest possible hour
        self.minute_ptr = 5


    def generate_orders(self) -> pd.DataFrame:

        orders = []
        for row in self.options.itertuples():

            # if the minute ptr is ahead, wait until orders catch up
            while not helper.compare_times(row.ts_recv, self.underlying.iloc[self.minute_ptr]["ms_of_day"]):
                continue;

            # bring minute ptr to most recent time before order
            while helper.compare_times(row.ts_recv, self.underlying.iloc[self.minute_ptr]["ms_of_day"]):
                self.minute_ptr += 1
            self.minute_ptr -= 1
            
            mid = float(self.underlying.iloc[self.minute_ptr]["price"])
            if (mid == 0.0):
                mid = float(self.underlying.iloc[self.minute_ptr-1]["price"])

            order_data = helper.parse_order(row);

            if (order_data["ask_price"] < 25):
                continue

            order = {}

            if (order_data["order_type"] == 'C'):
                time_to_expiry = helper.time_difference_in_years(order_data["date"][:10], order_data["expiry"])
                expected = pricing.black_scholes_call(mid, order_data["strike"], time_to_expiry)

                if (expected < order_data["bid_price"] - 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "S",
                        "order_size" : max(int(row.bid_sz_00)//4, 1)
                    }
                    orders.append(order)

            else:
                time_to_expiry = helper.time_difference_in_years(order_data["date"][:10], order_data["expiry"])
                expected = pricing.black_scholes_put(mid, order_data["strike"], time_to_expiry)

                if (expected < order_data["bid_price"] - 10):
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

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

    @staticmethod
    def update_hour(timestamp_str: str) -> str:
        timestamp_str = timestamp_str[:26] + 'Z'
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Get the minute part of the timestamp
        minutes = timestamp.minute
        

        # Determine if it should be rounded down to :00 or :30
        if minutes < 30:
            # Round down to :00
            rounded_timestamp = timestamp.replace(minute=30, second=0, microsecond=0)
            rounded_timestamp -= timedelta(hours=1)
            if (rounded_timestamp.hour >= 16):
                rounded_timestamp = rounded_timestamp.replace(hour=15)
        else:
            # Round down to :30
            rounded_timestamp = timestamp.replace(minute=30, second=0, microsecond=0)
            if (rounded_timestamp.hour >= 16):
                rounded_timestamp = rounded_timestamp.replace(hour=15)
        
        formatted_date = rounded_timestamp.strftime("%Y-%m-%d %H:%M:%S-05:00")
        return formatted_date

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
            "strike" : float(row.symbol[13:18])
        }

        for i in range(3):
            data["strike"] += float(row.symbol[18+i]) / 10**(i+1)

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

        self.hour_data = {}
        for row in self.underlying.itertuples():
            self.hour_data[row.date] = {"open" : row.open, "high" : row.high, "low" : row.low, "close" : row.close, "volume" : row.volume}
        self.underlying = self.hour_data

        # earliest possible hour
        self.prev_hour = "2024-01-02 09:30:00-05:00";

        # moving average of s&p data
        self.moving_avg = deque()


    def generate_orders(self) -> pd.DataFrame:

        orders = []
        for row in self.options.itertuples():

            prev_hour = helper.update_hour(row.ts_recv)
            if (prev_hour not in self.underlying):
                orders = pd.DataFrame(orders)
                orders.to_csv("orders.csv", index=False)
                return orders
            prev_hour_data = self.underlying[prev_hour]
            mid = (prev_hour_data["high"] + prev_hour_data["low"])/2

            self.moving_avg.append(mid)
            if (len(self.moving_avg) > 10):
                self.moving_avg.popleft()

            mid = sum(self.moving_avg)/len(self.moving_avg)
            
            order_data = helper.parse_order(row);

            if (order_data["ask_price"] < 25):
                continue

            order = {}

            if (order_data["order_type"] == 'C'):
                time_to_expiry = helper.time_difference_in_years(order_data["date"][:10], order_data["expiry"])
                expected = pricing.black_scholes_call(mid, order_data["strike"], time_to_expiry)
                """
                print(f"Current time: {row.ts_recv}, Expiration: {order_data['expiry']}, Years to expiry: {time_to_expiry}")
                print(f"Stock price: {mid}, Strike price: {order_data['strike']}")
                print(f"Expected: {expected}, Actual: {order_data['ask_price']}")
                """
                """
                if (expected > order_data["ask_price"] + 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "B",
                        "order_size" : int(row.ask_sz_00)//4
                    }
                    orders.append(order)
                """

                if (expected < order_data["bid_price"] - 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "S",
                        "order_size" : int(row.bid_sz_00)//4
                    }
                    orders.append(order)

            else:
                time_to_expiry = helper.time_difference_in_years(order_data["date"][:10], order_data["expiry"])
                expected = pricing.black_scholes_put(mid, order_data["strike"], time_to_expiry)

                """
                print(f"Current time: {row.ts_recv}, Expiration: {order_data['expiry']}, Years to expiry: {time_to_expiry}")
                print(f"Stock price: {mid}, Strike price: {order_data['strike']}")
                print(f"Expected: {expected}, Actual: {order_data['ask_price']}")

                if (expected > order_data["ask_price"] + 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "B",
                        "order_size" : int(row.ask_sz_00)//4
                    }
                    orders.append(order)
                """
                if (expected < order_data["bid_price"] - 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "S",
                        "order_size" : int(row.bid_sz_00)//4
                    }
                    orders.append(order)

        return pd.DataFrame(orders)


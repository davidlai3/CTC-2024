import pandas as pd
import helper
import pricing
from collections import deque
from datetime import datetime

class Strategy:
  
    def __init__(self) -> None:
        self.capital : float = 100_000_000
        self.portfolio_value : float = 0

        self.start_date : datetime = datetime(2024, 1, 1)
        self.end_date : datetime = datetime(2024, 3, 30)

        self.options : pd.DataFrame = pd.read_csv("data/cleaned_options_data.csv")
        self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])

        self.underlying = pd.read_csv("data/underlying_data_hour.csv")
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
        prev_time = ""
        print("Generating orders...")
        c = 0
        for row in self.options.itertuples():

            prev_hour = helper.update_hour(row.ts_recv)
            if (prev_hour not in self.underlying or c >= 20000):
                orders = pd.DataFrame(orders)
                orders.to_csv("orders.csv", index=False)
                print("Orders generated 1")
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
            c += 1


        print("Orders generated 2")
        return pd.DataFrame(orders)


if __name__ == "__main__":
    s = Strategy()

import pandas as pd
import helper
import pricing
from heapq import heappush, heappop
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

        self.open_orders = {}


    def generate_orders(self) -> pd.DataFrame:

        orders = []
        print("Generating orders...")
        c = 0
        for row in self.options.itertuples():

            # update moving average of underlying hourly data
            prev_hour = helper.update_hour(row.ts_recv)

            # TODO: Change c when submitting
            # if (prev_hour not in self.underlying or prev_hour == "2024-03-01 09:30:00-05:00"):
            if (prev_hour not in self.underlying or c == 20000):
                orders = pd.DataFrame(orders)
                orders.to_csv("orders.csv", index=False)
                print("Orders generated 1")
                return orders

            # Update moving average
            prev_hour_data = self.underlying[prev_hour]
            mid = (prev_hour_data["high"] + prev_hour_data["low"])/2
            self.moving_avg.append(mid)
            if (len(self.moving_avg) > 10):
                self.moving_avg.popleft()

            # Check if any call options are in the money
            # tuple: (total size, total price)

            if (row.symbol in self.open_orders and self.open_orders[row.symbol][0] > 0):
                avg_price = self.open_orders[row.symbol][1]/self.open_orders[row.symbol][0]
                if (row.bid_px_00 > avg_price):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "S",
                        "order_size" : min(row.bid_sz_00, self.open_orders[row.symbol][0])
                    }
                    print(f"Selling {row.symbol} at {row.bid_px_00} with average price {avg_price} for {order['order_size']})
                    orders.append(order)
                    new_size = self.open_orders[row.symbol][0] - min(order["order_size"], self.open_orders[row.symbol][0])
                    new_price = self.open_orders[row.symbol][1] - min(order["order_size"], self.open_orders[row.symbol][0])*avg_price
                    self.open_orders[row.symbol] = (new_size, new_price)

                if (self.open_orders[row.symbol][0] == 0):
                    del self.open_orders[row.symbol]

            # Update moving
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
                if (expected > order_data["ask_price"] + 10):
                    order = {
                        "datetime" : row.ts_recv,
                        "option_symbol" : row.symbol,
                        "action" : "B",
                        "order_size" : int(row.ask_sz_00)//4
                    }
                    print(f"Buying {row.symbol} at {row.ask_px_00} with expected price {expected} for {order['order_size']}")
                    if (row.symbol in self.open_orders):
                        new_size = self.open_orders[row.symbol][0] + order["order_size"]
                        new_price = self.open_orders[row.symbol][1] + (order_data["ask_price"] * order["order_size"])
                        self.open_orders[row.symbol] = (new_size, new_price)
                    else:
                        self.open_orders[row.symbol] = (order["order_size"], order_data["ask_price"] * order["order_size"])
                    orders.append(order)

            c += 1


        print("Orders generated 2")
        return pd.DataFrame(orders)

 

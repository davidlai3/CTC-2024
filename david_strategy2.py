import pandas as pd
import helper
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


    def generate_orders(self) -> pd.DataFrame:

        orders = []
        prev_time = ""
        print("Generating orders...")
        for row in self.options.itertuples():

            prev_hour = helper.update_hour(row.ts_recv)
            if (prev_hour not in self.underlying):
                orders = pd.DataFrame(orders)
                orders.to_csv("orders.csv", index=False)
                print("Orders generated 1")
                return orders
            prev_hour_data = self.underlying[prev_hour]
            mid = (prev_hour_data["high"] + prev_hour_data["low"])/2

            
            order_data = helper.parse_order(row);

            order = {}
            if (order_data["strike"] < mid - 7 and order_data["order_type"] == 'C'):
                order = {
                    "datetime" : str(row.ts_recv),
                    "option_symbol" : str(row.symbol),
                    "action" : "B",
                    "order_size" : min(row.ask_sz_00//2, 100)
                }
                orders.append(order)
            elif (order_data["strike"] > mid - 7 and order_data["order_type"] == 'C'):
                order = {
                    "datetime" : str(row.ts_recv),
                    "option_symbol" : str(row.symbol),
                    "action" : "S",
                    "order_size" : min(row.bid_sz_00//2, 100)
                }
                orders.append(order)

            elif (order_data["strike"] > mid + 7 and order_data["order_type"] == 'P'):
                order = {
                    "datetime" : str(row.ts_recv),
                    "option_symbol" : str(row.symbol),
                    "action" : "B",
                    "order_size" : min(row.ask_sz_00//2, 100)
                }
                orders.append(order)
            elif (order_data["strike"] < mid + 7 and order_data["order_type"] == 'P'):
                order = {
                    "datetime" : str(row.ts_recv),
                    "option_symbol" : str(row.symbol),
                    "action" : "S",
                    "order_size" : min(row.bid_sz_00//2, 100)
                }
                orders.append(order)



        print("Orders generated 2")
        return pd.DataFrame(orders)


if __name__ == "__main__":
    s = Strategy()

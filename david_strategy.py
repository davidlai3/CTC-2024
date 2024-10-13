import pandas as pd
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
        self.underlying.columns = self.underlying.columns.str.lower()

    def parse_order(self, row) -> dict:
        data = {
            "date" : row["ts_recv"],
            "instrument" : row["instrument_id"],
            "bid_price" : row["bid_px_00"],
            "ask_price" : row["ask_px_00"],
            "bid_size" : row["bid_sz_00"],
            "ask_size" : row["ask_sz_00"],
            "expiry" : row["symbol"][6:12],
            "order_type" : row["symbol"][12],
            "strike" : float(row["symbol"][13:17])
        }

        for i in range(4):
            data["strike"] += float(row["symbol"][17+i]) / 10**(i+1)

        return data;

    def generate_orders(self) -> pd.DataFrame:

        orders = []
        prev_time = "";
        # simple strategy:
        print(self.parse_order(self.options.iloc[0]))
        for i in range(0, 100):
            row = self.options.iloc[i];
            order = {};

            if (i < 50):
                order = {
                    "datetime" : row["ts_recv"],
                    "option_symbol" : row["symbol"],
                    "action" : "B",
                    "order_size" : max(int(row["ask_sz_00"])//2, 1)
                }
                print(f"Order {i} size: {order['order_size']}")
            else:
                order = {
                    "datetime" : row["ts_recv"],
                    "option_symbol" : row["symbol"],
                    "action" : "S",
                    "order_size" : int(row["bid_sz_00"])//2
                }

            if (order["datetime"] == prev_time):
                continue;
            else:
                orders.append(order)
                prev_time = order["datetime"]

        return pd.DataFrame(orders);


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
  
  def calculate_fair_value():
    # use a typical size-weighted mid between Best Bid and Best Offer at a given time
    pass

  def find_best_bid():
    pass 

  def find_best_offer():
    pass

  def generate_orders(self) -> pd.DataFrame:
    # implement me!
    example_orders = pd.read_csv("data/example_orders.csv")
    return example_orders

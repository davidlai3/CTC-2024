import pandas as pd
from datetime import datetime
from collections import defaultdict, deque

class Strategy:
  
  def __init__(self) -> None:
    self.capital : float = 100_000_000
    self.portfolio_value : float = 0

    self.start_date : datetime = datetime(2024, 1, 1)
    self.end_date : datetime = datetime(2024, 3, 30)
  
    self.options : pd.DataFrame = pd.read_csv("data/cleaned_options_data.csv")
    self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])

    # appends a fair_value column to the pandas dataframe
    self.options = self.calculate_fair_value( self.options )
    self.moving_averages = defaultdict(deque)
    self.positions = defaultdict(int)

    self.underlying = pd.read_csv("data/underlying_data_hour.csv")
    self.underlying.columns = self.underlying.columns.str.lower()
  

  # helper function
  def find_size_weighted_mid(self, bid_price : float, bid_size : int, ask_price : float, ask_size : int ) -> float:
    # will find the average of all of the best bids and offers
    # this can serve as a reasonable fair value estimate
    num_orders = bid_size + ask_size
    total_price = (bid_price * bid_size) + (ask_price * ask_size)
    return total_price / num_orders

  # helper function
  def calculate_fair_value( self, order_book : pd.DataFrame ) -> pd.DataFrame :
    # use a size-weighted mid between Best Bid and Best Offer at a given time
    # for each order in the order_book, store the fair value for future computations
    order_book[ "fair_value" ] =  self.find_size_wegihted_mid( 
      float(order_book["bid_px_00"]), int(order_book["bid_sz_00"]), 
      float(order_book["ask_px_00"], int(order_book["ask_sz_00"]) ))
    return order_book
  

  # helper function
  # given a symbol, will parse and return a dictionary with more friendly formatting of data
  def parse_symbol( symbol : str ) -> dict:
    _ , data = symbol.split(" ")
    parsed_symbol = {}

    # check for the type
    if "C" in data:
      parsed_symbol["option_type"] = "C"
    else:
      parsed_symbol["option_type"] = "P" 
    
    # read in the date
    expiration_date = data[:8]
    parsed_symbol["expiration_date"] = expiration_date 
    
    # read in the strike price
    strike_price = data[9:]
    parsed_symbol["strike_price"] = strike_price

    return parsed_symbol


  def generate_orders(self) -> pd.DataFrame:
    # # implement me!
    # moving avg strategy --> NOT FULLY FUNCTIONAL

    try:
      my_orders = pd.read_csv("data/example_orders.csv")
      
      my_orders = pd.DataFrame(columns=['datetime', 'option_symbol', 'action', 'size'])
      for row in self.options.itertuples:
        # employ a moving averages strategy: if fair_value above the moving average sell
        # if fair_value below the moving average, buy
        self.moving_averages[ row.symbol ].append( row.fair_value )
        curr_moving_average = sum(self.moving_averages[ row.symbol ]) / len(self.moving_averages[ row.symbol ])
        if len(self.moving_averages[row.symbol]) > 10:
          self.moving_averages[row.symbol].popleft()

        if curr_moving_average > row.fair_value+5:
          buy_order = [ row.ts_recv, row.symbol, "B", row.bid_sz_00 ]
          my_orders = my_orders.concat( buy_order, ignore_index=True )
          self.positions += (int(row.bid_sz_00))
        elif curr_moving_average < row.fair_value-5:
          sell_order = [ row.ts_recv, row.symbol, "S", row.ask_sz_00 ]
          my_orders = my_orders.concat( sell_order, ignore_index=True )
          self.positions -= (int(row.ask_sz_00))


    except:
      with open("errors.txt", "a") as file:
        file.write("we just had an error")
      

    return my_orders


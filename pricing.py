import numpy as np
from scipy.stats import norm

def black_scholes_call(S, K, T, r=0.01, sigma=0.15):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return call_price

def black_scholes_put(S, K, T, r=0.01, sigma=0.15):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return put_price

def implied_volatility(option_price, S, K, T, r=0.01, option_type="call", tol=1e-8, max_iterations=100):
    # Initial guess for volatility
    sigma = 0.2
    for i in range(max_iterations):
        if option_type == "call":
            price = black_scholes_call(S, K, T, r, sigma)
        else:
            price = black_scholes_put(S, K, T, r, sigma)

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

import yfinance as yf

msft = yf.Ticker("MSFT")

# get stock info
msft.info

msft
# get historical market data
hist = msft.history(period="max")

# show actions (dividends, splits)
print(msft.actions)

# show dividends
print(msft.dividends)

# show splits
msft.splits

# show financials
msft.financials
msft.quarterly_financials


# show balance heet
msft.balance_sheet
msft.quarterly_balance_sheet

# show cashflow
msft.cashflow
msft.quarterly_cashflow

# show earnings
msft.earnings
msft.quarterly_earnings

# show sustainability
msft.sustainability

# show analysts recommendations
msft.recommendations

# show next event (earnings, etc)
msft.calendar

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
msft.isin

# show options expirations
msft.options

# get option chain for specific expiration
#opt = msft.option_chain('YYYY-MM-DD')
# data available via: opt.calls, opt.puts

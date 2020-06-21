# Original Source: https://www.freecodecamp.org/news/auto-updating-excel-python-aws/
# This version will upload content to google sheets instead of AWS.
# Must have an API key in api.txt and credentials in creds.json in the same directory as the script.
# Date Tested: 6/20/2020
import pandas as pd
import xlsxwriter
from oauth2client.service_account import ServiceAccountCredentials
import csv
import os
import gspread
import time
import numpy as np

# Change to current working directory to pull files from same directory as script.
cwd = os.getcwd()
os.chdir(cwd)

# Read API Key
ApiKey = open("api.txt", "r")
IEX_API_Key = ApiKey.read()

# Authorize api scopes based on creds file.
def AuthorizeApi():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    return client

# Define ticker symbols
tickers = [
            'MSFT',
            'AAPL',
            'AMZN',
            'GOOG',
            'FB',
            'BRK.B',
            'JNJ',
            'WMT',
            'V',
            'PG',
            'TDS',
            'DX',
            'AES',
            'AMKR',
            'AGO',
            'CAH',
            'CVS'
            ]

# Create an empty string called `ticker_string` that we'll add tickers and commas.
ticker_string = ''

# Loop through every element of `tickers` and add them and a comma to ticker_string.
for ticker in tickers:
    ticker_string += ticker
    ticker_string += ','
# Drop the last comma from `ticker_string`.
ticker_string = ticker_string[:-1]

#Create the endpoint strings
endpoints = 'price,stats'

# Interpolate the endpoint strings into the HTTP_request string.
HTTP_request = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={ticker_string}&types={endpoints}&range=1y&token={IEX_API_Key}'

raw_data = pd.read_json(HTTP_request)

output_data = pd.DataFrame(np.empty((0,4)))

for ticker in raw_data.columns:

    company_name = raw_data[ticker]['stats']['companyName']
    
    stock_price = raw_data[ticker]['price']
    
    dividend_yield = raw_data[ticker]['stats']['dividendYield']
    new_column = pd.Series([ticker, company_name, stock_price, dividend_yield])
    output_data = output_data.append(new_column, ignore_index = True)

# Change the column names of output_data.
output_data.columns = ['Ticker', 'Company Name', 'Stock Price', 'Dividend Yield']
# Change the index of output_data.
output_data.set_index('Ticker', inplace=True)
# Replace the missing values of the 'Dividend Yield' column with 0.
output_data['Dividend Yield'].fillna(0,inplace=True)

# Create Excel Sheets writer.
writer = pd.ExcelWriter('stock_market_data.xlsx', engine='xlsxwriter')
output_data.to_excel(writer, sheet_name='Stock Market Data')
# Specify all column widths.
writer.sheets['Stock Market Data'].set_column('B:B', 32)
writer.sheets['Stock Market Data'].set_column('C:C', 18)
writer.sheets['Stock Market Data'].set_column('D:D', 20)

header_template = writer.book.add_format(
        {
            'font_color': '#ffffff',
            'bg_color': '#135485',
            'border': 1
        }
    )

string_template = writer.book.add_format(
        {
            'bg_color': '#DADADA',
            'border': 1
        }
    )

dollar_template = writer.book.add_format(
        {
            'num_format':'$0.00',
            'bg_color': '#DADADA',
            'border': 1
        }
    )

percent_template = writer.book.add_format(
        {
            'num_format':'0.0%',
            'bg_color': '#DADADA',
            'border': 1
        }
    )

# Format the header of the spreadsheet.
writer.sheets['Stock Market Data'].conditional_format('A1:D1', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   header_template
                                }
                            )

# Format the 'Ticker' and 'Company Name' columns.
writer.sheets['Stock Market Data'].conditional_format('A2:B18', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   string_template
                                }
                            )

# Format the 'Stock Price' column.
writer.sheets['Stock Market Data'].conditional_format('C2:C18', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   dollar_template
                                }
                            )

# Format the 'Dividend Yield' column.
writer.sheets['Stock Market Data'].conditional_format('D2:D18', 
                             {
                                'type':     'cell',
                                'criteria': '<>',
                                'value':    '"None"',
                                'format':   percent_template
                                }
                            )

# Write Excel File.
writer.save()

# Now that xls is made, start importing to sheets.

def UpdateExcel():
    client = AuthorizeApi()
    sh = client.open_by_key("1g7yBvtpXMtP4Xr6RnK8A7OiBr5M848K5ClrV3p3kTqc")
    worksheet = sh.worksheet("Stock Market Data")
    worksheet.clear()
    file = 'stock_market_data.xlsx'
    xl = pd.ExcelFile(file)
    dataframe = xl.parse('Stock Market Data')
    worksheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())

time.sleep(5)
UpdateExcel()

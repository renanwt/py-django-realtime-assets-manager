#STOCKS and REITS
#user: renanwt; pass: Tiingo****(o que só eu sei)
# import requests
#
# headers = {
#         'Content-Type': 'application/json',
#         'Authorization' : 'Token 2ca2a5fb00a371874b9f6ba681cd27a55d3cf205'
#         }
# requestResponse = requests.get("https://api.tiingo.com/iex/?tickers=USDBRL",
#                                     headers=headers)
# print(requestResponse.json())

# STOCKS BR + FIIS
## Alpha
# api_key = "8QU6ELEHQEM8383U"
# api_key2 = "J4ZSRVVHMVS5PEAR"
# url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={nome}&interval=1min&apikey={api_key}&outputsize=compact'
# r = requests.get(url)
# last_busday = r.json()['Meta Data']['3. Last Refreshed'][:10]
# data = r.json()['Time Series (Daily)'][last_busday]['5. adjusted close']
# float_data = float(data)
# return round(float_data, 2)
# Yahoo Finance
# import yfinance as yf
# ticker = yf.Ticker("USDBRL")
# cotacao = ticker.history_metadata['regularMarketPrice']
import yfinance as yf


nome = 'NVDA'
ticker = yf.Ticker(nome)
cotacao = ticker.history_metadata['regularMarketPrice']


def quotation_brl(classe, nome):
    if classe in ['ações', 'fiis', 'etf_br']:
        ticker = yf.Ticker(nome+".SA")
        cotacao = ticker.history_metadata['regularMarketPrice']
        return round(cotacao, 2)


print(quotation_brl('ações', 'CPLE3'))

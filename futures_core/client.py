from futures_core.marke_data.market_data import MarketData
from futures_core.trade.trade import TradeData
from futures_core.user.user import UserData
from futures_core.ws_token.token import GetToken


class Market(MarketData):
    pass


class User(UserData):
    pass


class Trade(TradeData):
    pass


class WsToken(GetToken):
    pass



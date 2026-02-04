from spot_core.earn.earn import EarnData
from spot_core.lending.lending import LendingData
from spot_core.margin.margin import MarginData
from spot_core.market.market import MarketData
from spot_core.trade.trade import TradeData
from spot_core.user.user import UserData
from spot_core.ws_token.token import GetToken


class User(UserData):
    pass


class Trade(TradeData):
    pass


class Market(MarketData):
    pass


class Lending(LendingData):
    pass

class Earn(EarnData):
    pass


class Margin(MarginData):
    pass


class WsToken(GetToken):
    pass

from enum import Enum
import json
import logging
import random

from rauth import OAuth1Service

from broker import Broker

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.etrade.com"


class ETrade(Broker):
    # TODO add in remaining options
    class OrderType(Enum):
        EQUITY = "EQ"
        OPTION = "OPTN"

    class OrderTerm(Enum):
        GOOD_UNTIL_CANCEL = "GOOD_UNTIL_CANCEL"
        GOOD_FOR_DAY = "GOOD_FOR_DAY"
        GOOD_TILL_DATE = "GOOD_TILL_DATE"
        IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
        FILL_OR_KILL = "FILL_OR_KILL"

    class PriceType(Enum):
        MARKET = "MARKET"
        LIMIT = "LIMIT"
        STOP = "STOP"
        STOP_LIMIT = "STOP_LIMIT"

    class MarketSession(Enum):
        REGULAR = "REGULAR"
        EXTENDED = "EXTENDED"

    class QuoteDetail(Enum):
        ALL = "ALL"
        FUNDAMENTAL = "FUNDAMENTAL"
        INTRADAY = "INTRADAY"
        OPTIONS = "OPTIONS"
        WEEK_52 = "WEEK_52"
        MF_DETAIL = "MF_DETAIL"

    # ETrade definition
    def __init__(self):
        super().__init__()
        self.oauth = None
        self.request_token = None
        self.request_token_secret = None
        self.session = None
        self.key = None
        self.selected_account = None

    def oauth_part1(self, token_key, token_secret) -> str:
        self.key = token_key
        self.oauth = OAuth1Service(
            name="etrade",
            consumer_key=self.key,
            consumer_secret=token_secret,
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url="https://api.etrade.com",
        )

        # OAuth1 rev. A - leg 1
        self.request_token, self.request_token_secret = self.oauth.get_request_token(
            params={"oauth_callback": "oob", "format": "json"}
        )

        # OAuth1 rev. A - leg 2
        authorize_url = self.oauth.authorize_url.format(self.oauth.consumer_key, self.request_token)

        return authorize_url

    def oauth_part2(self, text_code):
        # OAuth1 rev. A - leg 3
        self.session = self.oauth.get_auth_session(
            self.request_token, self.request_token_secret, params={"oauth_verifier": text_code}
        )

    def choose_account(self, account_id):
        url = f"{_BASE_URL}/v1/accounts/list.json"
        response = self.session.get(url)

        if response.status_code != 200:
            return False

        processed = json.loads(response.content)
        account_choices = (
            processed.get("AccountListResponse", {})
            .get("Accounts", {})
            .get("Account", [])
        )

        # discard dashes in account_id
        account_id = account_id.replace("-", "")

        # account_id -> account_id_key
        accounts = {account["accountId"]: account["accountIdKey"] for account in account_choices}
        if account_id not in accounts:
            return False

        # selected account := account_id_key
        self.selected_account = accounts[account_id]
        return True

    def cash_available(self):
        params = {"instType": "BROKERAGE", "realTimeNAV": "true"}
        headers = {"consumerkey": self.key}

        url = f"{_BASE_URL}/v1/accounts/{self.selected_account}/balance.json"

        response = self.session.get(
            url, header_auth=True, params=params, headers=headers
        )

        if response.status_code != 200:
            return False

        resp = json.loads(response.content)

        return resp["BalanceResponse"]["Computed"]["cashAvailableForInvestment"]

    def positions(self) -> json:
        url = f"{_BASE_URL}/v1/accounts/{self.selected_account}/portfolio.json"
        response = self.session.get(url, header_auth=True)

        if response.status_code != 200:
            return None

        content = json.loads(response.content)

        print(content)

        return response.content

    def quote(self, symbol: str, detail: QuoteDetail = None) -> json:
        if detail is None:
            url = f"{_BASE_URL}/v1/market/quote/{symbol}"
        else:
            url = f"{_BASE_URL}/v1/market/quote/{symbol}?detailFlag={detail.value}"

        headers = {"consumerkey": self.key}
        response = self.session.get(url, header_auth=True, headers=headers)
        if response.status_code != 200:
            return None

        processed = json.loads(response.detail)
        return processed

    def order_stock(
        self,
        symbol: str,
        quantity: int,
        side,
        limit_price: float = None,
        price_type: PriceType = PriceType.MARKET,
        order_term: OrderTerm = OrderTerm.GOOD_UNTIL_CANCEL,
        market_session: MarketSession = MarketSession.REGULAR,
    ):
        preview_url = (
            _BASE_URL + "/v1/accounts/" + self.selected_account + "/orders/preview.json"
        )
        headers = {"Content-Type": "application/json", "consumerKey": self.key}

        client_order_id: int = random.randint(1000000000, 9999999999)

        preview_payload = {
            "PreviewOrderRequest": {
                "orderType": "EQ",
                "clientOrderId": client_order_id,
                "Order": [
                    {
                        "allOrNone": "false",
                        "priceType": price_type.value,
                        "orderTerm": order_term.value,
                        "marketSession": market_session.value,
                        "stopPrice": "",
                        "Instrument": [
                            {
                                "Product": {"securityType": "EQ", "symbol": symbol},
                                "orderAction": side.value,
                                "quantityType": "QUANTITY",
                                "quantity": quantity,
                            }
                        ],
                    }
                ],
            }
        }

        if limit_price is not None:
            preview_payload["PlaceOrderRequest"]["Order"]["limitPrice"] = limit_price

        response = self.session.post(
            preview_url,
            header_auth=True,
            headers=headers,
            data=json.dumps(preview_payload),
        )
        if response.status_code != 200:
            return False

        processed = json.loads(response.content)

        order_payload = {
            "PlaceOrderRequest": {
                "orderType": "EQ",
                "clientOrderId": client_order_id,
                "PreviewIds": [
                    {
                        "previewId": processed["PreviewOrderResponse"]["PreviewIds"][0][
                            "previewId"
                        ]
                    }
                ],
                "Order": [
                    {
                        "allOrNone": "false",
                        "priceType": price_type.value,
                        "orderTerm": order_term.value,
                        "marketSession": market_session.value,
                        "stopPrice": "",
                        "Instrument": [
                            {
                                "Product": {"securityType": "EQ", "symbol": symbol},
                                "orderAction": side.value,
                                "quantityType": "QUANTITY",
                                "quantity": quantity,
                            }
                        ],
                    }
                ],
            }
        }

        if limit_price is not None:
            order_payload["PlaceOrderRequest"]["Order"]["limitPrice"] = limit_price

        order_url = f"{_BASE_URL}/v1/accounts/{self.selected_account}/orders/place.json"
        response = self.session.post(
            order_url, header_auth=True, headers=headers, data=json.dumps(order_payload)
        )
        if response.status_code != 200:
            return False

        processed = json.loads(response.content)

        return processed


    def order(self):
        pass

    def order_target(self):
        pass

    def order_target_portfolio(self):
        pass

    def account_value(self) -> float:
        params = {"instType": "BROKERAGE", "realTimeNAV": "true"}
        headers = {"consumerkey": self.key}

        url = f"{_BASE_URL}/v1/accounts/{self.selected_account}/balance.json"

        response = self.session.get(
            url, header_auth=True, params=params, headers=headers
        )

        if response.status_code != 200:
            return False

        resp = json.loads(response.content)

        return resp["BalanceResponse"]["Computed"]["RealTimeValues"]["totalAccountValue"]

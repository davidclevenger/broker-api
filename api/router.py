import uuid
import logging
from typing import Dict

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from broker.etrade import ETrade
from models import Target, TargetPortfolio
import globals

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/new", tags=["auth"])
def new_broker_instance(broker: str, resp: Response):
    obj = {
        "etrade": ETrade()
    }.get(broker, None)

    if obj is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = f"{broker} is not a known broker option."
        return resp

    session_id = str(uuid.uuid4())
    globals.SESSIONS[session_id] = obj

    logger.debug(f"created session: {{{session_id}->{obj.__class__}}}")

    return {"session_id": session_id}

@router.get("/choose_account", tags=["auth"])
def choose_account(session_id: str, account_id: str, resp: Response):
    broker: ETrade = None
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    valid_account = broker.choose_account(account_id)

    if not valid_account:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = f"ETrade account \"{account_id}\" not found."
        return resp

    resp.status_code = status.HTTP_200_OK
    return resp

@router.get("/account_value", tags=["account"])
def account_value(session_id: str, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    value = broker.account_value()
    # resp.status_code = status.HTTP_200_OK
    # resp.content = value
    return Response(content=str(value), status_code=status.HTTP_200_OK)

@router.get("/cash_available", tags=["account"])
def cash_available(session_id: str, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    cash = broker.cash_available()
    # resp.status_code = status.HTTP_200_OK
    # resp.content = cash
    return Response(content=str(cash), status_code=status.HTTP_200_OK)

@router.get("/positions", tags=["account"])
def positions(session_id: str, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    positionz = broker.positions()
    if positionz is None:
        resp.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        resp.content = "Error getting positions"
        return resp

    resp.status_code = status.HTTP_200_OK
    resp.content = positionz
    return resp

@router.get("/order_target", tags=["order"])
def order_target(session_id: str, target: Target, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    result = broker.order_target(target)
    if result is None:
        resp.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        resp.content = "error ordering target"
        return resp

    resp.status_code = status.HTTP_200_OK
    resp.content = result

@router.get("/order_target_portfolio", tags=["order"])
def order_target_porfolio(session_id: str, target_portfolio: TargetPortfolio, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    result = broker.order_target_portfolio(target_portfolio)
    if result is None:
        resp.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        resp.content = "error ordering target portfolio"
        return resp

    resp.status_code = status.HTTP_200_OK
    resp.content = result

"""
ETrade-specific Authorization (OAuth Core 1.0 Rev. A)
"""

@router.get("/etrade/oauth_part1", tags=["etrade"])
def etrade_oauth_part1(session_id: str, token_key: str, token_secret: str, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    authorize_url = broker.oauth_part1(token_key, token_secret)
    return {"authorize_url": authorize_url}

@router.get("/etrade/oauth_part2", tags=["etrade"])
def etrade_oauth_part2(session_id: str, response_code: str, resp: Response):
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    broker.oauth_part2(response_code)
    resp.status_code = status.HTTP_200_OK
    resp.content = "Successfully established ETrade conneection"
    return resp

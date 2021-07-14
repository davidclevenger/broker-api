import uuid
import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from broker import Broker
from broker.etrade import ETrade
from models import Target, TargetPortfolio
import globals

logger = logging.getLogger(__name__)

router = APIRouter()

def session_exists(session_id: str = Query(...)):
    if session_id not in globals.SESSIONS:
        raise HTTPException(status_code=404, detail="session not found!!!")


@router.get("/new", tags=["auth"])
def new_broker_instance(broker: str, resp: Response):
    obj: Broker = {
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

@router.get("/choose_account", dependencies=[Depends(session_exists)], tags=["auth"])
def choose_account(session_id: str, account_id: str, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    valid_account = broker.choose_account(account_id)

    if not valid_account:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = f"ETrade account \"{account_id}\" not found."
        return resp

    resp.status_code = status.HTTP_200_OK
    return resp

@router.get("/account_value", dependencies=[Depends(session_exists)], tags=["account"])
def account_value(session_id: str, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    value = broker.account_value()
    return Response(content=str(value), status_code=status.HTTP_200_OK)

@router.get("/cash_available", dependencies=[Depends(session_exists)], tags=["account"])
def cash_available(session_id: str, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    cash = broker.cash_available()
    return Response(content=str(cash), status_code=status.HTTP_200_OK)

@router.get("/positions", dependencies=[Depends(session_exists)], tags=["account"])
def positions(session_id: str, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    positionz = broker.positions()
    if positionz is None:
        resp.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        resp.content = "Error getting positions"
        return resp

    resp.status_code = status.HTTP_200_OK
    resp.content = positionz
    return resp

@router.get("/order_target", dependencies=[Depends(session_exists)], tags=["order"])
def order_target(session_id: str, target: Target, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    result = broker.order_target(target)
    if result is None:
        resp.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        resp.content = "error ordering target"
        return resp

    resp.status_code = status.HTTP_200_OK
    resp.content = result

@router.get("/order_target_portfolio", dependencies=[Depends(session_exists)], tags=["order"])
def order_target_porfolio(session_id: str, target_portfolio: TargetPortfolio, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
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

@router.get("/etrade/oauth_part1", dependencies=[Depends(session_exists)], tags=["etrade"])
def etrade_oauth_part1(session_id: str, token_key: str, token_secret: str, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    authorize_url = broker.oauth_part1(token_key, token_secret)
    return {"authorize_url": authorize_url}

@router.get("/etrade/oauth_part2", dependencies=[Depends(session_exists)], tags=["etrade"])
def etrade_oauth_part2(session_id: str, response_code: str, resp: Response):
    broker: Broker = globals.SESSIONS[session_id]
    broker.oauth_part2(response_code)
    return Response(status_code=status.HTTP_200_OK, content="Successfully established ETrade conneection")

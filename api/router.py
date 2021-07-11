import uuid
import logging

from fastapi import APIRouter, Response, status

from broker.etrade import ETrade
import globals

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/new")
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

@router.get("/etrade/oauth_part1")
def etrade_oauth_part1(session_id: str, token_key: str, token_secret: str, resp: Response):
    broker: ETrade = None
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    authorize_url = broker.oauth_part1(token_key, token_secret)
    return {"authorize_url": authorize_url}

@router.get("/etrade/oauth_part2")
def etrade_oauth_part2(session_id: str, response_code: str, resp: Response):
    broker: ETrade = None
    if (broker := globals.SESSIONS.get(session_id, None)) is None:
        resp.status_code = status.HTTP_404_NOT_FOUND
        resp.content = "session not found"
        return resp

    broker.oauth_part2(response_code)
    resp.status_code = status.HTTP_200_OK
    resp.content = "Successfully established ETrade conneection"
    return resp

@router.get("/choose_account")
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






@router.get("/order_portfolio")
def order_portfolio():
    pass
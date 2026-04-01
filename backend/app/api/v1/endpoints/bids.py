from fastapi import APIRouter, HTTPException

from app.schemas.bid import AuctionStateOut, BidRequest, CloseAuctionOut, ResetAuctionOut
from app.services.bidding_service import bidding_service

router = APIRouter(prefix="/auction", tags=["auction"])


@router.get("/state", response_model=AuctionStateOut)
def get_auction_state() -> AuctionStateOut:
	return bidding_service.get_state()


@router.post("/bid", response_model=AuctionStateOut)
def place_bid(payload: BidRequest) -> AuctionStateOut:
	try:
		return bidding_service.place_bid(payload.team_name, payload.amount)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/close", response_model=CloseAuctionOut)
def close_auction() -> CloseAuctionOut:
	return bidding_service.close_current_auction()


@router.post("/reset", response_model=ResetAuctionOut)
def reset_auction() -> ResetAuctionOut:
	return ResetAuctionOut(status="ok", state=bidding_service.reset())

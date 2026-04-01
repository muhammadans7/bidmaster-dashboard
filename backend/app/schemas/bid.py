from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.player import PlayerOut
from app.schemas.team import TeamOut


class BidRequest(BaseModel):
	team_name: str = Field(min_length=1)
	amount: int = Field(gt=0)


class BidEventOut(BaseModel):
	team_name: str
	amount: int
	timestamp: str


class AuctionStateOut(BaseModel):
	current_player: PlayerOut | None
	total_players: int
	current_player_number: int | None
	current_bid: int | None
	leading_team: str | None
	min_increment: int
	bid_window_seconds: int
	bid_window_remaining_seconds: int | None
	bid_window_ends_at: str | None
	bid_timer_paused: bool
	squad_min_players: int
	squad_max_players: int
	bid_options: list[int]
	teams: list[TeamOut]
	recent_bids: list[BidEventOut]
	message: str | None = None


class CloseAuctionOut(BaseModel):
	sold: bool
	winner: str | None
	amount: int | None
	next_player: PlayerOut | None
	state: AuctionStateOut


class ResetAuctionOut(BaseModel):
	status: Literal["ok"]
	state: AuctionStateOut

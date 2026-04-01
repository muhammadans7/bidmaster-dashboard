from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import floor
from threading import RLock

from app.schemas.bid import AuctionStateOut, BidEventOut, CloseAuctionOut
from app.schemas.player import PlayerOut
from app.schemas.team import TeamOut


TEAM_PURSE = 1_000_000
TEAM_MIN_PLAYERS = 10
TEAM_MAX_PLAYERS = 12
BASE_PRICE = 30_000
MIN_INCREMENT = 5_000
BID_WINDOW_SECONDS = 60


@dataclass(frozen=True)
class TeamConfig:
	name: str
	captain: str
	mentor: str


TEAM_CONFIGS = [
	TeamConfig(name="strikers", captain="Saib", mentor="Sumbal"),
	TeamConfig(name="thunders", captain="Haiders", mentor="Usman"),
	TeamConfig(name="stallion", captain="Sharjeel", mentor="Akhtar"),
	TeamConfig(name="vanguardian", captain="Ans", mentor="Khurram"),
]

PLAYER_QUEUE: list[tuple[str, list[str]]] = [
	("Abdullah Tariq", ["Cards", "Tekken", "Foosball"]),
	("Abrar", ["Cricket", "Badminton", "Ludo"]),
	("Hamza", ["Foosball", "Ludo", "Cricket"]),
	("Zaki", ["Cricket", "Tekken", "Foosball"]),
	("Shehzar", ["Cricket", "Tekken", "Table Tennis"]),
	("Murtaza Jaffer", ["Table Tennis", "Cricket", "Foosball"]),
	("Zunair Shafiq", ["Cricket", "Tekken", "Cards"]),
	("Najullah", ["Cricket", "Tekken", "Foosball"]),
	("Salman Tariq", ["Cricket", "Badminton", "Table Tennis"]),
	("Afnan Azir", ["Cricket", "Carrom", "Ludo"]),
	("Adeel", ["Foosball", "Table Tennis", "Cricket"]),
	("Hussain", ["Tekken", "Cards", "Ludo"]),
	("Tayyab", ["Cards", "Ludo", "Cricket"]),
	("Umair", ["Foosball", "Cards", "Ludo"]),
	("Usman Altaf", ["Foosball", "Cards", "Cricket"]),
	("Rehan", ["Chess", "Badminton", "Cards"]),
	("Ali Khan", ["Cricket", "Cards", "Ludo"]),
	("Shoaib", ["Cricket", "Badminton", "Ludo"]),
	("Usama", ["Tekken", "Chess", "Cricket"]),
	("Ali Shan", ["Foosball", "Cricket", "Tekken"]),
	("Shahzman", ["Cricket", "Ludo", "Badminton"]),
	("Ruhan", ["Ludo", "Badminton", "Foosball"]),
	("Rizwan", ["Chess", "Cricket", "Badminton"]),
	("Taha", ["Cricket", "Badminton", "Ludo"]),
	("Hamza", ["Cricket", "Badminton", "Tekken"]),
	("Zia", ["Badminton", "Tekken", "Cricket"]),
	("Zeesha", ["Cricket", "Tekken", "Cards"]),
	("Riaz", ["Badminton", "Carrom", "Ludo"]),
	("Meerab", ["Badminton", "Carrom", "Ludo"]),
	("Ayesha", ["Ludo", "Badminton", "Carrom"]),
	("Minahil Hameed", ["Ludo", "Badminton", "Cricket"]),
	("Esha", ["Ludo", "Badminton", "Cricket"]),
	("Minahil Javed", ["Ludo", "Badminton", "Carrom"]),
	("Maryam Iftikhar", ["Ludo", "Cards", "Badminton"]),
	("Fatima", ["Cards", "Ludo", "Cricket"]),
	("Nimra", ["Ludo", "Carrom", "Cards"]),
	("Tabinda", ["Ludo", "Foosball", "Tekken"]),
	("Laiba", ["Ludo", "Cards", "Carrom"]),
	("Sana Yousaf", ["Ludo", "Cards", "Badminton"]),
	("Kinza", ["Ludo", "Carrom", "Cards"]),
]


@dataclass
class TeamState:
	name: str
	captain: str
	mentor: str
	purse_total: int = TEAM_PURSE
	spent: int = 0
	squad_size: int = 0

	@property
	def remaining_purse(self) -> int:
		return self.purse_total - self.spent


@dataclass
class AuctionState:
	player: PlayerOut | None = None
	player_started_at: datetime | None = None
	current_bid: int | None = None
	leading_team: str | None = None
	recent_bids: list[BidEventOut] = field(default_factory=list)


class BiddingService:
	def __init__(self) -> None:
		self._lock = RLock()
		self._players = [
			PlayerOut(
				id=index + 1,
				name=name,
				profile="Sports Week auction player",
				favorite_games=favorite_games,
				base_price=BASE_PRICE,
			)
			for index, (name, favorite_games) in enumerate(PLAYER_QUEUE)
		]
		self._player_index = 0
		self._teams: dict[str, TeamState] = {}
		self._state = AuctionState()
		self.reset()

	def _build_team_views(self) -> list[TeamOut]:
		return [
			TeamOut(
				name=team.name,
				captain=team.captain,
				mentor=team.mentor,
				purse_total=team.purse_total,
				spent=team.spent,
				squad_size=team.squad_size,
				remaining_purse=team.remaining_purse,
			)
			for team in self._teams.values()
		]

	def _current_player(self) -> PlayerOut | None:
		if self._player_index >= len(self._players):
			return None
		return self._players[self._player_index]

	def _current_player_number(self) -> int | None:
		if self._state.player is None:
			return None
		return self._player_index + 1

	def _bid_window_remaining_seconds(self) -> int | None:
		if self._state.player is None or self._state.player_started_at is None:
			return None

		elapsed = (datetime.now(timezone.utc) - self._state.player_started_at).total_seconds()
		remaining = BID_WINDOW_SECONDS - floor(elapsed)
		return max(0, remaining)

	def _bid_window_ends_at(self) -> str | None:
		if self._state.player is None or self._state.player_started_at is None:
			return None
		window_end = self._state.player_started_at + timedelta(seconds=BID_WINDOW_SECONDS)
		return window_end.isoformat()

	def _bid_window_closed(self) -> bool:
		remaining = self._bid_window_remaining_seconds()
		return remaining == 0 if remaining is not None else False

	def _next_bid_options(self) -> list[int]:
		if self._state.player is None:
			return []

		anchor = (
			self._state.current_bid
			if self._state.current_bid is not None
			else self._state.player.base_price - MIN_INCREMENT
		)
		return [anchor + (MIN_INCREMENT * i) for i in range(1, 5)]

	def get_state(self, message: str | None = None) -> AuctionStateOut:
		with self._lock:
			return AuctionStateOut(
				current_player=self._state.player,
				total_players=len(self._players),
				current_player_number=self._current_player_number(),
				current_bid=self._state.current_bid,
				leading_team=self._state.leading_team,
				min_increment=MIN_INCREMENT,
				bid_window_seconds=BID_WINDOW_SECONDS,
				bid_window_remaining_seconds=self._bid_window_remaining_seconds(),
				bid_window_ends_at=self._bid_window_ends_at(),
				squad_min_players=TEAM_MIN_PLAYERS,
				squad_max_players=TEAM_MAX_PLAYERS,
				bid_options=self._next_bid_options(),
				teams=self._build_team_views(),
				recent_bids=list(self._state.recent_bids),
				message=message,
			)

	def _set_active_player(self) -> None:
		current_player = self._current_player()
		started_at = datetime.now(timezone.utc) if current_player is not None else None
		self._state = AuctionState(player=current_player, player_started_at=started_at)

	def _queue_finished_message(self) -> str:
		short_teams = [
			f"{team.name} ({team.squad_size}/{TEAM_MIN_PLAYERS})"
			for team in self._teams.values()
			if team.squad_size < TEAM_MIN_PLAYERS
		]
		if not short_teams:
			return "Auction queue finished"
		return "Auction queue finished. Teams below minimum squad: " + ", ".join(short_teams)

	def reset(self) -> AuctionStateOut:
		with self._lock:
			self._player_index = 0
			self._teams = {
				team_config.name: TeamState(
					name=team_config.name,
					captain=team_config.captain,
					mentor=team_config.mentor,
				)
				for team_config in TEAM_CONFIGS
			}
			self._set_active_player()
			return self.get_state(message="Auction reset")

	def place_bid(self, team_name: str, amount: int) -> AuctionStateOut:
		with self._lock:
			normalized_team = team_name.strip().lower()
			if normalized_team not in self._teams:
				raise ValueError("Invalid team name")

			if self._state.player is None:
				raise ValueError("No active player left to bid on")

			if self._bid_window_closed():
				raise ValueError(
					f"{BID_WINDOW_SECONDS}-second bid window ended. Close current player to move next"
				)

			team = self._teams[normalized_team]
			if team.squad_size >= TEAM_MAX_PLAYERS:
				raise ValueError(f"{team.name} already reached max squad size")

			floor_bid = (
				self._state.player.base_price
				if self._state.current_bid is None
				else self._state.current_bid + MIN_INCREMENT
			)
			if amount < floor_bid:
				raise ValueError(f"Bid must be at least PKR {floor_bid:,}")

			anchor = (
				self._state.player.base_price
				if self._state.current_bid is None
				else self._state.current_bid
			)
			if (amount - anchor) % MIN_INCREMENT != 0:
				raise ValueError(f"Bid increment must be in PKR {MIN_INCREMENT:,} steps")

			if team.remaining_purse < amount:
				raise ValueError(f"{team.name} does not have enough purse for this bid")

			self._state.current_bid = amount
			self._state.leading_team = team.name
			self._state.recent_bids.insert(
				0,
				BidEventOut(
					team_name=team.name,
					amount=amount,
					timestamp=datetime.now(timezone.utc).isoformat(),
				),
			)
			self._state.recent_bids = self._state.recent_bids[:10]

			return self.get_state(message=f"Bid accepted from {team.name}")

	def close_current_auction(self) -> CloseAuctionOut:
		with self._lock:
			if self._state.player is None:
				state = self.get_state(message=self._queue_finished_message())
				return CloseAuctionOut(
					sold=False,
					winner=None,
					amount=None,
					next_player=None,
					state=state,
				)

			sold = self._state.leading_team is not None and self._state.current_bid is not None
			winner: str | None = None
			amount: int | None = None

			if sold:
				winner = self._state.leading_team
				amount = self._state.current_bid
				winning_team = self._teams[winner]
				winning_team.spent += amount
				winning_team.squad_size += 1

			self._player_index += 1
			self._set_active_player()
			next_player = self._state.player
			if next_player is None:
				state_message = self._queue_finished_message()
			else:
				state_message = "Player sold" if sold else "Player marked unsold"

			return CloseAuctionOut(
				sold=sold,
				winner=winner,
				amount=amount,
				next_player=next_player,
				state=self.get_state(message=state_message),
			)


bidding_service = BiddingService()

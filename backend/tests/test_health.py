from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services.bidding_service import BID_WINDOW_SECONDS, bidding_service


client = TestClient(app)


def reset_auction() -> dict:
	response = client.post("/api/v1/auction/reset")
	assert response.status_code == 200
	return response.json()["state"]


def test_players_follow_prompt_order_with_manual_advance() -> None:
	state = reset_auction()
	assert state["current_player"]["name"] == "Abdullah Tariq"
	assert state["current_player_number"] == 1

	close_response = client.post("/api/v1/auction/close")
	assert close_response.status_code == 200
	close_payload = close_response.json()

	assert close_payload["state"]["current_player"]["name"] == "Abrar"
	assert close_payload["state"]["current_player_number"] == 2


def test_team_metadata_and_rules_are_in_state() -> None:
	state = reset_auction()
	assert state["squad_min_players"] == 10
	assert state["squad_max_players"] == 12
	assert state["bid_window_seconds"] == 30
	assert state["total_players"] == 40

	strikers = next(team for team in state["teams"] if team["name"] == "strikers")
	assert strikers["captain"] == "Saib"
	assert strikers["mentor"] == "Sumbal"


def test_bid_rejected_after_bid_window_timeout() -> None:
	reset_auction()
	bidding_service._state.player_started_at = datetime.now(timezone.utc) - timedelta(
		seconds=BID_WINDOW_SECONDS + 1
	)

	response = client.post(
		"/api/v1/auction/bid",
		json={"team_name": "thunders", "amount": 30_000},
	)

	assert response.status_code == 400
	assert "30-second bid window ended" in response.json()["detail"]


def test_queue_completion_message_mentions_underfilled_teams() -> None:
	state = reset_auction()
	for _ in range(state["total_players"]):
		close_response = client.post("/api/v1/auction/close")
		assert close_response.status_code == 200

	final_state = close_response.json()["state"]
	assert final_state["current_player"] is None
	assert "Teams below minimum squad" in final_state["message"]

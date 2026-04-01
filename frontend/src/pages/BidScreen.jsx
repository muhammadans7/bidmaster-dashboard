import { useEffect, useMemo, useState } from "react";

import BidOptions from "../components/bidding/BidOptions";
import PlayerCard from "../components/player/PlayerCard";
import {
	closeAuction,
	fetchAuctionState,
	pauseAuctionTimer,
	resetAuction,
	resumeAuctionTimer,
	submitBid,
} from "../services/bidService";

function BidScreen() {
	const [state, setState] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [notice, setNotice] = useState("");
	const [displayRemainingSeconds, setDisplayRemainingSeconds] = useState(0);

	const hasActivePlayer = Boolean(state?.current_player);

	useEffect(() => {
		void loadState();
	}, []);

	useEffect(() => {
		if (!state?.current_player || state.bid_window_remaining_seconds == null) {
			setDisplayRemainingSeconds(0);
			return;
		}
		setDisplayRemainingSeconds(state.bid_window_remaining_seconds);
	}, [state?.current_player?.id, state?.bid_window_remaining_seconds, state?.bid_window_ends_at]);

	useEffect(() => {
		if (!state?.current_player) {
			return undefined;
		}

		if (state.bid_timer_paused) {
			return undefined;
		}

		const timerId = window.setInterval(() => {
			setDisplayRemainingSeconds((previous) => (previous > 0 ? previous - 1 : 0));
		}, 1000);

		return () => {
			window.clearInterval(timerId);
		};
	}, [state?.current_player?.id, state?.bid_timer_paused]);

	async function loadState() {
		setLoading(true);
		setError("");
		try {
			const data = await fetchAuctionState();
			setState(data);
			setNotice(data.message || "");
		} catch (err) {
			setError(err?.response?.data?.detail || "Failed to load auction state");
		} finally {
			setLoading(false);
		}
	}

	async function handleBid(teamName, amount) {
		if (!teamName) {
			setNotice(`Selected amount PKR ${amount.toLocaleString()}. Click team button to place bid.`);
			return;
		}

		setLoading(true);
		setError("");
		setNotice("");
		try {
			const data = await submitBid(teamName, amount);
			setState(data);
			setNotice(data.message || `Bid accepted from ${teamName}`);
		} catch (err) {
			setError(err?.response?.data?.detail || "Bid failed");
		} finally {
			setLoading(false);
		}
	}

	async function handleCloseAuction() {
		setLoading(true);
		setError("");
		try {
			const data = await closeAuction();
			setState(data.state);
			if (data.sold) {
				setNotice(`Sold to ${data.winner} for PKR ${data.amount.toLocaleString()}`);
			} else {
				setNotice("Player marked unsold.");
			}
		} catch (err) {
			setError(err?.response?.data?.detail || "Failed to close auction");
		} finally {
			setLoading(false);
		}
	}

	async function handleReset() {
		setLoading(true);
		setError("");
		try {
			const data = await resetAuction();
			setState(data.state);
			setNotice(data.state.message || "Auction reset");
		} catch (err) {
			setError(err?.response?.data?.detail || "Failed to reset auction");
		} finally {
			setLoading(false);
		}
	}

	async function handlePauseTimer() {
		setLoading(true);
		setError("");
		try {
			const data = await pauseAuctionTimer();
			setState(data);
			setNotice(data.message || "Bid timer paused");
		} catch (err) {
			setError(err?.response?.data?.detail || "Failed to pause timer");
		} finally {
			setLoading(false);
		}
	}

	async function handleResumeTimer() {
		setLoading(true);
		setError("");
		try {
			const data = await resumeAuctionTimer();
			setState(data);
			setNotice(data.message || "Bid timer resumed");
		} catch (err) {
			setError(err?.response?.data?.detail || "Failed to resume timer");
		} finally {
			setLoading(false);
		}
	}

	const summary = useMemo(() => {
		if (!state) {
			return "Loading...";
		}
		if (!state.current_bid) {
			return "No bids yet";
		}
		return `Leading: ${state.leading_team} at PKR ${state.current_bid.toLocaleString()}`;
	}, [state]);

	const queueInfo = useMemo(() => {
		if (!state) {
			return "Loading queue...";
		}
		if (!state.current_player) {
			return `All ${state.total_players} players are completed.`;
		}
		return `Player ${state.current_player_number} of ${state.total_players}`;
	}, [state]);

	const timerInfo = useMemo(() => {
		if (!state?.current_player) {
			return "No active bid window";
		}

		const remaining = displayRemainingSeconds;
		const total = state.bid_window_seconds ?? 0;
		const remainingFormatted = String(remaining).padStart(2, "0");
		const totalFormatted = String(total).padStart(2, "0");

		if (state.bid_timer_paused) {
			return `Bid window paused at 00:${remainingFormatted}`;
		}

		if (remaining === 0) {
			return "Bid window ended. Close current player to move next.";
		}

		return `Bid window: 00:${remainingFormatted} / 00:${totalFormatted}`;
	}, [state, displayRemainingSeconds]);

	const timerCritical = Boolean(
		state?.current_player &&
			!state?.bid_timer_paused &&
			displayRemainingSeconds <= 5,
	);

	return (
		<main className="page">
			<header className="topbar">
				<div>
					<p className="label">Sports Week Auction</p>
					<h1>Live Bidding Dashboard</h1>
					<p>{queueInfo}</p>
					<p className={`timer-copy ${timerCritical ? "timer-critical" : ""}`}>{timerInfo}</p>
					<p>{summary}</p>
				</div>
				<div className="header-actions">
					{state?.bid_timer_paused ? (
						<button
							type="button"
							onClick={handleResumeTimer}
							disabled={loading || !hasActivePlayer}
						>
							Resume Timer
						</button>
					) : (
						<button
							type="button"
							className="ghost"
							onClick={handlePauseTimer}
							disabled={loading || !hasActivePlayer}
						>
							Pause Timer
						</button>
					)}
					<button type="button" onClick={handleCloseAuction} disabled={loading || !hasActivePlayer}>
						Close Current Player
					</button>
					<button type="button" className="ghost" onClick={handleReset} disabled={loading}>
						Reset Auction
					</button>
				</div>
			</header>

			{error ? <p className="alert error">{error}</p> : null}
			{notice ? <p className="alert notice">{notice}</p> : null}

			{state ? (
				<div className="screen-grid">
					<PlayerCard player={state.current_player} />
					<BidOptions
						teams={state.teams}
						bidOptions={state.bid_options}
						minIncrement={state.min_increment}
						onBid={handleBid}
						loading={loading}
						disabled={!hasActivePlayer || state.bid_timer_paused}
						squadMaxPlayers={state.squad_max_players}
					/>
				</div>
			) : (
				<p>Loading screen...</p>
			)}

			<section className="card recent-card">
				<h3>Recent Bids</h3>
				{state?.recent_bids?.length ? (
					<ul>
						{state.recent_bids.map((item, index) => (
							<li key={`${item.timestamp}-${index}`}>
								<strong>{item.team_name}</strong> bid PKR {item.amount.toLocaleString()}
							</li>
						))}
					</ul>
				) : (
					<p>No bids placed yet.</p>
				)}
			</section>
		</main>
	);
}

export default BidScreen;

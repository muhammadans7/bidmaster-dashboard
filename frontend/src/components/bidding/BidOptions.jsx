import { useMemo, useState } from "react";

function BidOptions({ teams, bidOptions, onBid, loading, disabled, squadMaxPlayers, minIncrement }) {
	const [customAmount, setCustomAmount] = useState("");
	const [showAmountError, setShowAmountError] = useState(false);

	const minimumBid = bidOptions[0] ?? 0;
	const parsedAmount = useMemo(() => Number.parseInt(customAmount, 10), [customAmount]);
	const hasValidNumber = Number.isFinite(parsedAmount) && parsedAmount > 0;
	const hasMinimumError = hasValidNumber && parsedAmount < minimumBid;
	const hasIncrementError = hasValidNumber && parsedAmount % minIncrement !== 0;
	const hasAmountError = !hasValidNumber || hasMinimumError || hasIncrementError;

	const showMinimumError = showAmountError && hasMinimumError;
	const showIncrementError = showAmountError && hasIncrementError;
	const showInvalidNumberError = showAmountError && !hasValidNumber;

	function handleCustomBid(teamName) {
		if (hasAmountError) {
			setShowAmountError(true);
			return;
		}
		setShowAmountError(false);
		onBid(teamName, parsedAmount);
	}

	function handleAmountChange(event) {
		setCustomAmount(event.target.value);
		setShowAmountError(false);
	}

	return (
		<section className="card bid-card">
			<h3>Team Bidding Controls</h3>
			<p className="hint">Host can type any amount and place bid for any team.</p>

			<div className="custom-bid-wrap">
				<label htmlFor="custom-amount" className="label">
					Bid Amount (PKR)
				</label>
				<input
					id="custom-amount"
					type="number"
					className="custom-bid-input"
					min={minimumBid || 0}
					step={minIncrement}
					placeholder="Enter amount"
					value={customAmount}
					onChange={handleAmountChange}
					disabled={disabled || loading}
				/>
				<p className="custom-bid-help">
					Minimum: PKR {minimumBid.toLocaleString()} | Increment: PKR {minIncrement.toLocaleString()}
				</p>
				{showInvalidNumberError ? (
					<p className="custom-bid-error">Enter a valid bid amount first.</p>
				) : null}
				{showMinimumError ? (
					<p className="custom-bid-error">Amount must be at least PKR {minimumBid.toLocaleString()}.</p>
				) : null}
				{showIncrementError ? (
					<p className="custom-bid-error">
						Amount must be in PKR {minIncrement.toLocaleString()} increments.
					</p>
				) : null}
			</div>

			<div className="team-grid">
				{teams.map((team) => (
					<div key={team.name} className="team-box">
						<p className="team-name">{team.name}</p>
						<p className="team-meta">Captain: {team.captain}</p>
						<p className="team-meta">Mentor: {team.mentor}</p>
						<p>Remaining: PKR {team.remaining_purse.toLocaleString()}</p>
						<p>Squad: {team.squad_size}</p>
						{team.squad_size >= squadMaxPlayers ? (
							<p className="team-full">Squad limit reached</p>
						) : null}
						<div className="team-actions">
							<button
								type="button"
								className="team-bid-btn"
								onClick={() => handleCustomBid(team.name)}
								disabled={disabled || loading || team.squad_size >= squadMaxPlayers || hasAmountError}
							>
								Place Bid
							</button>
						</div>
					</div>
				))}
			</div>
		</section>
	);
}

export default BidOptions;

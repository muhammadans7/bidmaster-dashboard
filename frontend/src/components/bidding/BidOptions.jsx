function BidOptions({ teams, bidOptions, onBid, loading, disabled, squadMaxPlayers }) {
	return (
		<section className="card bid-card">
			<h3>Team Bidding Controls</h3>
			<p className="hint">Pick one amount, then click the team to place bid.</p>

			<div className="options-grid">
				{bidOptions.map((amount) => (
					<button
						key={amount}
						className="price-tag"
						type="button"
						onClick={() => onBid(null, amount)}
						disabled={disabled || loading}
					>
						PKR {amount.toLocaleString()}
					</button>
				))}
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
							{bidOptions.map((amount) => (
								<button
									key={`${team.name}-${amount}`}
									type="button"
									className="team-bid-btn"
									onClick={() => onBid(team.name, amount)}
									disabled={disabled || loading || team.squad_size >= squadMaxPlayers}
								>
									Bid {amount.toLocaleString()}
								</button>
							))}
						</div>
					</div>
				))}
			</div>
		</section>
	);
}

export default BidOptions;

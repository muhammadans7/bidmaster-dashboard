function PlayerCard({ player }) {
	if (!player) {
		return (
			<section className="card player-card">
				<h2>No active player</h2>
				<p>All players in the current queue are completed.</p>
			</section>
		);
	}

	return (
		<section className="card player-card">
			<p className="label">Now on screen</p>
			<h2>{player.name}</h2>
			<p>{player.profile}</p>
			<p className="base-price">Base Price: PKR {player.base_price.toLocaleString()}</p>
			<div className="games-wrap">
				{player.favorite_games.map((game) => (
					<span key={game} className="chip">
						{game}
					</span>
				))}
			</div>
		</section>
	);
}

export default PlayerCard;

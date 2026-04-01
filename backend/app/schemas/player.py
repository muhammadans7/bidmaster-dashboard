from pydantic import BaseModel


class PlayerOut(BaseModel):
	id: int
	name: str
	profile: str
	favorite_games: list[str]
	base_price: int

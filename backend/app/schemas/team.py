from pydantic import BaseModel


class TeamOut(BaseModel):
	name: str
	captain: str
	mentor: str
	purse_total: int
	spent: int
	squad_size: int
	remaining_purse: int

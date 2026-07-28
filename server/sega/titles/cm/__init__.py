from server.sega.titles.cm.index import CardMakerServlet
from server.sega.titles.cm.const import CardMakerConstants
from server.sega.titles.cm.read import CardMakerReader
from server.sega.titles.cm.database import CardMakerData

index = CardMakerServlet
reader = CardMakerReader
database = CardMakerData
game_codes = [CardMakerConstants.GAME_CODE]

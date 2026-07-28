from server.sega.titles.idz.index import IDZServlet
from server.sega.titles.idz.const import IDZConstants
from server.sega.titles.idz.database import IDZData

index = IDZServlet
database = IDZData
game_codes = [IDZConstants.GAME_CODE]

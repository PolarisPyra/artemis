from server.sega.titles.idac.index import IDACServlet
from server.sega.titles.idac.const import IDACConstants
from server.sega.titles.idac.database import IDACData
from server.sega.titles.idac.read import IDACReader
from server.sega.titles.idac.frontend import IDACFrontend

index = IDACServlet
database = IDACData
reader = IDACReader
frontend = IDACFrontend
game_codes = [IDACConstants.GAME_CODE]

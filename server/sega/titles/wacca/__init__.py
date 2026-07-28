from server.sega.titles.wacca.const import WaccaConstants
from server.sega.titles.wacca.index import WaccaServlet
from server.sega.titles.wacca.read import WaccaReader
from server.sega.titles.wacca.database import WaccaData
from server.sega.titles.wacca.frontend import WaccaFrontend

index = WaccaServlet
database = WaccaData
reader = WaccaReader
frontend = WaccaFrontend
game_codes = [WaccaConstants.GAME_CODE]

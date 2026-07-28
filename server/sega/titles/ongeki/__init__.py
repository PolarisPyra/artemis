from server.sega.titles.ongeki.index import OngekiServlet
from server.sega.titles.ongeki.const import OngekiConstants
from server.sega.titles.ongeki.database import OngekiData
from server.sega.titles.ongeki.read import OngekiReader
from server.sega.titles.ongeki.frontend import OngekiFrontend

index = OngekiServlet
database = OngekiData
reader = OngekiReader
frontend = OngekiFrontend
game_codes = [OngekiConstants.GAME_CODE]

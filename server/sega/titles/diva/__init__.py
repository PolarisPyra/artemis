from server.sega.titles.diva.index import DivaServlet
from server.sega.titles.diva.const import DivaConstants
from server.sega.titles.diva.database import DivaData
from server.sega.titles.diva.read import DivaReader
from .frontend import DivaFrontend

index = DivaServlet
database = DivaData
reader = DivaReader
frontend = DivaFrontend
game_codes = [DivaConstants.GAME_CODE]

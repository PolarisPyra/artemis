from server.sega.titles.cxb.index import CxbServlet
from server.sega.titles.cxb.const import CxbConstants
from server.sega.titles.cxb.database import CxbData
from server.sega.titles.cxb.read import CxbReader

index = CxbServlet
database = CxbData
reader = CxbReader
game_codes = [CxbConstants.GAME_CODE]

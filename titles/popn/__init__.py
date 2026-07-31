from .index import PopnDispatch
from .database import PopnData
from .const import PopnConstants
from .read import PopnReader

database = PopnData
reader = PopnReader
index = PopnDispatch
is_eamuse = True
game_codes = [PopnConstants.GAME_CODE]

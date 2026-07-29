from core.eamuse import BaseHandler
from core.config import CoreConfig
from core.eamuse import EAProtocol
from core.eaapi import XMLNode, Type
import logging

from .const import PopnConstants
from .config import PopnConfig
from .database import PopnData


class PopnBase(BaseHandler):
    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, protocol)
        self.game_config = game_config
        self.game = PopnConstants.GAME_CODE
        self.version = PopnConstants.VER_BASE
        self.logger = logging.getLogger("popn")
        self.data = PopnData(core_config)
        self.extra_services = {"local": "", "lobby": ""}

    def decode_pcbevent(self, event: str, value: int) -> str:
        evt_split = event.split(".")
        ret = None

        if len(evt_split) >= 2:
            if evt_split[0] == "M39":
                if evt_split[1] == "light":
                    ret = "Pop'n Light Start"
                
                elif evt_split[1] == "first":
                    if evt_split[2] == "free":
                        ret = "Pop'n First Play Free"

                elif evt_split[1] == "standard":
                    if evt_split[2] == "ec":
                        ret = "Pop'n Standard Start w/ Paseli"

                elif evt_split[1] == "pdata":
                    if evt_split[2] == "w":
                        ret = f"Pop'n Player Data Write Failed"

                    elif evt_split[2] == "r":
                        ret = f"Pop'n Player Data Read Failed"

                elif evt_split[1] == "mode":
                    if evt_split[2] == "o":
                        ret = f"Pop'n Online Mode"

                    elif evt_split[2] == "l":
                        ret = f"Pop'n Local Mode"

                elif evt_split[1] == "match":
                    if evt_split[2] == "o":
                        ret = f"Pop'n Online Match"

                    elif evt_split[2] == "l":
                        ret = f"Pop'n Local Match"

                elif evt_split[1] == "single":
                    if evt_split[2] == "o":
                        ret = f"Pop'n Online Solo"

                    elif evt_split[2] == "l":
                        ret = f"Pop'n Local Solo"

                elif evt_split[1] == "tutorial":
                    if evt_split[2] == "o":
                        ret = f"Pop'n Online Tutorial"

                    elif evt_split[2] == "l":
                        ret = f"Pop'n Local Tutorial"

                    elif evt_split[2] == "skip":
                        ret = f"Pop'n Tutorial Skip"
            
            elif evt_split[0] == "pp":
                if evt_split[1] == "M39":
                    if evt_split[2] == "c":
                        if evt_split[3] == "play":
                            ret = "Pop'n Participation Credit Play"
                    
                    elif evt_split[2] == "p":
                        if evt_split[3] == "play":
                            ret = "Pop'n Participation Paseli Play"
                        
                        elif evt_split[3] == "premiumplay":
                            ret = "Pop'n Participation Paseli Premium Play"
                        
                        elif evt_split[3] == "option":
                            ret = "Pop'n Participation Paseli Beast Play"
                
                elif evt_split[1] == "M39A":
                    if evt_split[2] == "c":
                        if evt_split[3] == "play":
                            ret = "Pop'n (A) Participation Credit Play"
                    
                    elif evt_split[2] == "p":
                        if evt_split[3] == "play":
                            ret = "Pop'n (A) Participation Paseli Play"
                        
                        elif evt_split[3] == "premiumplay":
                            ret = "Pop'n (A) Participation Paseli Premium Play"
                        
                        elif evt_split[3] == "option":
                            ret = "Pop'n (A) Participation Paseli Beast Play"
            
            elif evt_split[0] == "pt":
                if evt_split[1] == "M39":
                    if evt_split[2] == "play":
                        ret = "Pop'n PT Credit Play"

        if ret is None:
            return super().decode_pcbevent(event, value)
        return ret
    
    def decode_paseli_item(self, event: str) -> str:
        if not event: return "Unknown"
        event_spt = event.split("/")
        if not event_spt[0]:
            event_spt.pop(0)
        
        ret = None
        
        if event_spt[0] == "eacoin":
            if event_spt[1] == "start":
                ret = "4-Stage Start"
            if event_spt[1] == "start_c":
                ret = "4-Stage Continue"
            
            # Unused?
            if event_spt[1] == "pstart":
                ret = "Premium Start"
            if event_spt[1] == "pstart_c":
                ret = "Premium Continue"
            
            elif event_spt[1] == "normal_start":
                ret = "3-Stage Start"
            elif event_spt[1] == "normal_start_c":
                return "3-Stage Continue"
            
            elif event_spt[1] == "pbstart":
                ret = "Beast Start"
            elif event_spt[1] == "pbstart_c":
                ret = "Beast Continue"

            # Unused?
            elif event_spt[1] == "option":
                ret = "Option Start"
            elif event_spt[1] == "option_c":
                ret = "Option Continue"

        if not ret:
            return super().decode_paseli_item(event)
        return ret

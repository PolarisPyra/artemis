#!/usr/bin/env 
from typing import Optional, List
import asyncio
import argparse
from os import path, mkdir, W_OK, access
import yaml
import bcrypt
import secrets
import string
from sqlalchemy.engine import Row
import inflection

from core.data import Data
from core.config import CoreConfig
from core.const import AllnetCountryCode

try:
    from asciimatics.widgets import Frame, Layout, Text, Button, RadioButtons, CheckBox, Divider, Label
    from asciimatics.scene import Scene
    from asciimatics.screen import Screen
    from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
except:
    print("Artemis TUI requires asciimatics, please install it using pip")
    exit(1)


class State:   
    class SelectedUser:
        def __init__(self, id: Optional[int] = None, name: Optional[str] = None):
            self.id = id
            self.name = name

        def __str__(self):
            if self.id is not None:
                return f"{self.name} ({self.id})" if self.name else f"User{self.id:04d}"
            return "None"

        def __int__(self):
            return self.id if self.id else 0

    class SelectedCard:
        def __init__(self, id: Optional[int] = None, access_code: Optional[str] = None):
            self.id = id
            self.access_code = access_code
        
        def __str__(self):
            if self.id is not None and self.access_code:
                return f"{self.access_code} ({self.id})"
            return "None"

        def __int__(self):
            return self.id if self.id else 0

    class SelectedArcade:
        def __init__(self, id: Optional[int] = None, country: Optional[str] = None, name: Optional[str] = None):
            self.id = id
            self.country = country
            self.name = name
        
        def __str__(self):
            if self.id is not None:
                return f"{self.name} ({self.country}{self.id:05d})" if self.name else f"{self.country}{self.id:05d}"
            return "None"
        
        def __int__(self):
            return self.id if self.id else 0

    class SelectedMachine:
        def __init__(self, id: Optional[int] = None, serial: Optional[str] = None):
            self.id = id
            self.serial = serial
        
        def __str__(self):
            if self.id is not None:
                return f"{self.serial} ({self.id})"
            return "None"
        
        def __int__(self):
            return self.id if self.id else 0

    def __init__(self):
        self.selected_user = self.SelectedUser()
        self.selected_card = self.SelectedCard()
        self.selected_arcade = self.SelectedArcade()
        self.selected_machine = self.SelectedMachine()
        self.last_err: str = ""
        self.search_results: List[Row] = []
        self.search_type: str = ""

    def set_user(self, id: int, username: Optional[str]) -> None:
        self.selected_user = self.SelectedUser(id, username)

    def clear_user(self) -> None:
        print(self.selected_user)
        self.selected_user = self.SelectedUser()

    def set_card(self, id: int, access_code: Optional[str]) -> None:
        self.selected_card = self.SelectedCard(id, access_code)

    def clear_card(self) -> None:
        self.selected_card = self.SelectedCard()

    def set_arcade(self, id: int, country: str = "JPN", name: Optional[str] = None) -> None:
        self.selected_arcade = self.SelectedArcade(id, country, name)

    def clear_arcade(self) -> None:
        self.selected_arcade = self.SelectedArcade()

    def set_machine(self, id: int, serial: Optional[str]) -> None:
        self.selected_machine = self.SelectedMachine(id, serial)

    def clear_machine(self) -> None:
        self.selected_machine = self.SelectedMachine()

    def set_last_err(self, err: str) -> None:
        self.last_err = err

    def clear_last_err(self) -> None:
        self.last_err = ""
    
    def clear_search_results(self) -> None:
        self.search_results = []

state = State()
data: Data = None
loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

class MainView(Frame):
    def __init__(self, screen: Screen):
        super(MainView, self).__init__(
            screen, 
            screen.height * 2 // 3, 
            screen.width * 2 // 3, 
            hover_focus=True, 
            can_scroll=False, 
            title="ARTEMiS TUI"
        )

        layout = Layout([100], True)
        self.add_layout(layout)
        layout.add_widget(Button("User Management", self._user_mgmt))
        layout.add_widget(Button("Card Management", self._card_mgmt))
        layout.add_widget(Button("Arcade Management", self._arcade_mgmt))
        layout.add_widget(Button("Machine Management", self._machine_mgmt))
        layout.add_widget(Button("Quit", self._quit))
        
        self.fix()
    
    def _user_mgmt(self):
        self.save()
        raise NextScene("User Management")
    
    def _card_mgmt(self):
        self.save()
        raise NextScene("Card Management")
    
    def _arcade_mgmt(self):
        self.save()
        raise NextScene("Arcade Management")
    
    def _machine_mgmt(self):
        self.save()
        raise NextScene("Machine Management")
    
    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

class ManageUserView(Frame):
    def __init__(self, screen: Screen):
        super(ManageUserView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="User Management",
            on_load=self._redraw
        )

        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Create User", self._create_user))
        layout.add_widget(Button("Lookup User", self._lookup))
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        
        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Edit User", self._edit_user, disabled=state.selected_user.id == 0 or state.selected_user.id is None))
        layout.add_widget(Button("Delete User", self._del_user, disabled=state.selected_user.id == 0 or state.selected_user.id is None))
        layout.add_widget((Divider()))
        
        usr_cards = []
        if state.selected_user.id != 0:
            cards = loop.run_until_complete(data.card.get_user_cards(state.selected_user.id))
            for card in cards or []:
                usr_cards.append(card._asdict())

        if len(usr_cards) > 0:
            layout3 = Layout([100], True)
            self.add_layout(layout3)
            
            card_status = "Available"
            if card['is_locked'] and card['is_banned']:
                card_status = "Locked and Banned"
            if card['is_locked']:
                card_status = "Locked"
            if card['is_banned']:
                card_status = "Banned"

            layout3.add_widget(RadioButtons(
                [(f"{card['id']} | {card['access_code']} | {card_status} | {card['memo'] if card['memo'] else '-'}", state.SelectedCard(card['id'], card['access_code'])) for card in usr_cards],
                "Cards:",
                "usr_cards"
            ))
            layout3.add_widget(Button('Select Card', self._sel_card))
            layout3.add_widget(Divider())

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        a = Text("", f"status", readonly=True, disabled=True)
        a.value = f"Selected User: {state.selected_user}"
        layout2.add_widget(a)
        layout2.add_widget(Button("Back", self._back), 2)
        
        self.fix()
    
    def _sel_card(self):
        self.save()
        a = self.data.get('usr_cards')
        state.set_card(a.id, a.access_code)
        raise NextScene("Card Management")
    
    def _create_user(self):
        self.save()
        raise NextScene("Create User")
    
    def _lookup(self):
        self.save()
        raise NextScene("Lookup User")
    
    def _edit_user(self):
        self.save()
        raise NextScene("Edit User")
    
    def _del_user(self):
        self.save()
        raise NextScene("Delete User")

    def _back(self):
        self.save()
        raise NextScene("Main")

class ManageCardView(Frame):
    def __init__(self, screen: Screen):
        super(ManageCardView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Card Management",
            on_load=self._redraw
        )

        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Create Card", self._create_card))
        layout.add_widget(Button("Lookup Card", self._lookup))
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        
        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Edit Card", self._edit_card, disabled=state.selected_card.id == 0 or state.selected_card.id is None))
        layout.add_widget(Button("Reassign Card", self._edit_card, disabled=state.selected_card.id == 0 or state.selected_card.id is None))
        layout.add_widget(Button("Delete Card", self._del_card, disabled=state.selected_card.id == 0 or state.selected_card.id is None))
        layout.add_widget((Divider()))

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        a = Text("", f"status", readonly=True, disabled=True)
        a.value = f"Selected Card: {state.selected_card}"
        layout2.add_widget(a)
        layout2.add_widget(Button("Back", self._back), 2)
        
        self.fix()
    
    def _create_card(self):
        self.save()
        raise NextScene("Create Card")
    
    def _lookup(self):
        self.save()
        raise NextScene("Lookup Card")
    
    def _edit_card(self):
        self.save()
        raise NextScene("Edit Card")
    
    def _del_card(self):
        self.save()
        raise NextScene("Delete Card")

    def _back(self):
        self.save()
        raise NextScene("Main")

class CreateUserView(Frame):
    def __init__(self, screen: Screen):
        super(CreateUserView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Create User"
        )

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Username:", "username"))
        layout.add_widget(Text("Email:", "email"))
        layout.add_widget(Text("Password:", "passwd"))
        layout.add_widget(CheckBox("", "Add Card:", "is_add_card", ))
        layout.add_widget(RadioButtons([
            ("User", "1"),
            ("User Manager", "2"),
            ("Arcde Manager", "4"),
            ("Sysadmin", "8"),
            ("Owner", "255"),
        ], "Role:", "role"))

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()

    def _ok(self):
        self.save()
        if not self.data.get("username"):
            state.set_last_err("Username cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        if not self.data.get("passwd"):
            pw = "".join(
                secrets.choice(string.ascii_letters + string.digits) for i in range(20)
            )
        else:
            pw = self.data.get("passwd")
        
        hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

        loop.run_until_complete(self._create_user_async(self.data.get("username"), hash.decode(), self.data.get("email"), self.data.get('role')))

        raise NextScene("User Management")
    
    async def _create_user_async(self, username: str, password: str, email: Optional[str], role: str):
        usr_id = await data.user.create_user(
            username=username,
            email=email if email else None,
            password=password,
            permission=int(role)
        )

        state.set_user(usr_id, username)

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("User Management")

class SearchResultsView(Frame):
    def __init__(self, screen: Screen):
        super(SearchResultsView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Search Results",
            on_load=self._redraw
        )
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Select", self._select_current), 2)
        layout2.add_widget(Button("Cancel", self._cancel), 2)
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        opts = []
        if state.search_type == "user":
            layout.add_widget(Label("      ID   | Username |   Role   | Email"))
            layout.add_widget(Divider())
            
            for usr in state.search_results:
                name = str(usr['username'])
                if len(name) < 8:
                    name = str(usr['username']) + ' ' * (8 - len(name))
                elif len(name) > 8:
                    name = usr['username'][:5] + "..."
                
                opts.append((f"{usr['id']:05d} | {name} | {usr['permissions']:08b} | {usr['email']}", state.SelectedUser(usr["id"], str(usr['username']))))
        
        elif state.search_type == "arcade":
            layout.add_widget(Label("      ID   | Name | Country | # Machines "))
            layout.add_widget(Divider())
            
            for ac in state.search_results:
                name = str(ac['name'])
                if len(name) < 8:
                    name = str(ac['name']) + ' ' * (8 - len(name))
                elif len(name) > 8:
                    name = ac['name'][:5] + "..."
                
                opts.append((f"{ac['id']:04X} | {name} | {ac['country']} | {usr['mech_ct']}", state.SelectedArcade(ac["id"], ac['country'], str(ac['name']))))
            
        layout.add_widget(RadioButtons(opts, "", "selopt"))
        
        self.fix()

    def _select_current(self):
        self.save()
        a = self.data.get('selopt')
        if state.search_type == "user":
            state.set_user(a.id, a.name)
            raise NextScene("User Management")
        
        elif state.search_type == "arcade":
            state.set_arcade(a.id, a.country, a.name)
            raise NextScene("Arcade Management")

    def _cancel(self):
        state.clear_last_err()
        if state.search_type == "user":
            raise NextScene("User Management")
        
        elif state.search_type == "arcade":
            raise NextScene("Arcade Management")

    def _back(self):
        self.save()
        raise NextScene("Main")

class LookupUserView(Frame):
    def __init__(self, screen):
        super(LookupUserView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Lookup User"
        )
        
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(RadioButtons([
            ("Username", "1"),
            ("Email", "2"),
            ("Access Code", "3"),
            ("User ID", "4"),
        ], "Search By:", "search_type"))
        layout.add_widget(Text("Search:", "search_str"), 1)

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Search", self._lookup), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()
    
    def _lookup(self):
        self.save()
        if not self.data.get("search_str"):
            state.set_last_err("Search cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        search_type = self.data.get("search_type")
        if search_type == "1":
            loop.run_until_complete(self._lookup_user_by_username(self.data.get("search_str")))
        elif search_type == "2":
            loop.run_until_complete(self._lookup_user_by_email(self.data.get("search_str")))
        elif search_type == "3":
            loop.run_until_complete(self._lookup_user_by_access_code(self.data.get("search_str")))
        elif search_type == "4":
            loop.run_until_complete(self._lookup_user_by_id(self.data.get("search_str")))
        else:
            state.set_last_err("Unknown search type")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        if len(state.search_results) < 1:
            state.set_last_err("Search returned no results")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.search_type = "user"
        raise NextScene("Search Results")

    async def _lookup_user_by_id(self, user_id: str):
        usr = await data.user.get_user(user_id)

        if usr is not None:
            state.search_results = [usr]

    async def _lookup_user_by_username(self, username: str):
        usr = await data.user.find_user_by_username(username)

        if usr is not None:
            state.search_results = usr

    async def _lookup_user_by_email(self, email: str):
        usr = await data.user.find_user_by_email(email)

        if usr is not None:
            state.search_results = usr

    async def _lookup_user_by_access_code(self, access_code: str):
        card = await data.card.get_card_by_access_code(access_code)

        if card is not None:
            usr = await data.user.get_user(card['user'])
            if usr is not None:
                state.search_results = [usr]

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("User Management")

class EditUserView(Frame):
    def __init__(self, screen):
        super(EditUserView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Edit User",
            on_load=self._redraw
        )

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Username:", "username"))
        layout.add_widget(Text("Email:", "email"))
        layout.add_widget(Text("Password:", "passwd"))
        layout.add_widget(RadioButtons([
            ("User", "1"),
            ("User Manager", "2"),
            ("Arcde Manager", "4"),
            ("Sysadmin", "8"),
            ("Owner", "255"),
        ], "Role:", "role"))

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Save", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()
    
    def _redraw(self):
        uinfo = loop.run_until_complete(data.user.get_user(state.selected_user.id))
        self.find_widget('username').value = uinfo['username']
        self.find_widget('email').value = uinfo['email']
        self.find_widget('role').value = str(uinfo['permissions'])

    def _ok(self):
        self.save()
        if not self.data.get("username"):
            state.set_last_err("Username cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        pw = self.data.get("passwd")
        hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

        is_good = loop.run_until_complete(self._update_user_async(self.data.get("username"), hash.decode(), self.data.get("email"), self.data.get('role')))
        
        self.find_widget('status').value = "User Updated" if is_good else "User update failed"

        raise NextScene("User Management")

    async def _update_user_async(self, username: Optional[str], password: Optional[str], email: Optional[str], role: Optional[str]) -> bool:
        if username: namechange_ok = await data.user.change_username(state.selected_user.id, username)
        else: namechange_ok = True
        
        if password: pw_ok = await data.user.change_password(state.selected_user.id, password)
        else: pw_ok = True
        
        if role: role_ok = await data.user.change_permission(state.selected_user.id, role)
        else: role_ok = True
        
        if email: email_ok = await data.user.change_email(state.selected_user.id, email)
        else: email_ok = True

        state.set_user(state.selected_user.id, username if username and namechange_ok else state.selected_user.name)
        return namechange_ok and pw_ok and role_ok and email_ok
    
    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("User Management")

class ManageArcadeView(Frame):
    def __init__(self, screen: Screen):
        super(ManageArcadeView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Arcade Management",
            on_load=self._redraw
        )

        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Create Arcade", self._create_arcade))
        layout.add_widget(Button("Lookup Arcade", self._lookup))
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        
        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Edit Arcade", self._edit_arcade, disabled=state.selected_arcade.id == 0 or state.selected_arcade.id is None))
        layout.add_widget(Button("Delete Arcade", self._del_arcade, disabled=state.selected_arcade.id == 0 or state.selected_arcade.id is None))
        layout.add_widget((Divider()))

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        a = Text("", f"status", readonly=True, disabled=True)
        a.value = f"Selected Arcade: {state.selected_arcade}"
        layout2.add_widget(a)
        layout2.add_widget(Button("Back", self._back), 2)
        
        self.fix()

    def _create_arcade(self):
        self.save()
        raise NextScene("Create Arcade")
    
    def _lookup(self):
        self.save()
        raise NextScene("Lookup Arcade")
    
    def _edit_arcade(self):
        self.save()
        raise NextScene("Edit Arcade")
    
    def _del_arcade(self):
        self.save()
        raise NextScene("Delete Arcade")

    def _back(self):
        self.save()
        raise NextScene("Main")

class CreateArcadeView(Frame):
    def __init__(self, screen: Screen):
        super(CreateArcadeView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Create Arcade"
        )

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Nickname:", "nickname"))
        layout.add_widget(Text("Timezone:", "timezone"))
        layout.add_widget(Text("VPN IP:", "ip"))
        layout.add_widget(CheckBox("", "Add Machine:", "is_add_machine", ))
        layout.add_widget(RadioButtons([
            (inflection.titleize(x.name), x.value) for x in AllnetCountryCode
        ], "Country:", "country"))

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()

    def _ok(self):
        self.save()
        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        loop.run_until_complete(self._create_arcade_async(self.data.get("name"), self.data.get("nickname"), self.data.get("country"), self.data.get('timezone'), self.data.get('ip')))

        raise NextScene("Create Machine" if self.data.get("is_add_machine") else "Arcade Management") 

    async def _create_arcade_async(self, name: str, nickname: Optional[str], country: str, timezone: Optional[str], ip: Optional[str]):
        arcade_id = await data.arcade.create_arcade(name, nickname if nickname != "" else None, country)

        if timezone:
            data.arcade.set_arcade_timezone(arcade_id, timezone)
        
        if ip:
            data.arcade.set_arcade_vpn_ip(arcade_id, ip)

        if arcade_id:
            state.set_arcade(arcade_id, country, name)

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("Arcade Management")

class LookupArcadeView(Frame):
    def __init__(self, screen):
        super(LookupArcadeView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Lookup Arcade"
        )
        
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(RadioButtons([
            ("Name", "1"),
            ("Serial", "2"),
            ("Place ID", "3"),
            ("Arcade ID", "4"),
        ], "Search By:", "search_type"))
        layout.add_widget(Text("Search:", "search_str"), 1)

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Search", self._lookup), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()
    
    def _lookup(self):
        self.save()
        if not self.data.get("search_str"):
            state.set_last_err("Search cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        search_type = self.data.get("search_type")
        if search_type == "1":
            loop.run_until_complete(self._lookup_arcade_by_name(self.data.get("search_str")))
        elif search_type == "2":
            loop.run_until_complete(self._lookup_arcade_by_serial(self.data.get("search_str")))
        elif search_type == "3":
            real_id = int(self.data.get("search_str"), 16)
            loop.run_until_complete(self._lookup_arcade_by_id(real_id))
        elif search_type == "4":
            loop.run_until_complete(self._lookup_arcade_by_id(self.data.get("search_str")))
        else:
            state.set_last_err("Unknown search type")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        if len(state.search_results) < 1:
            state.set_last_err("Search returned no results")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.search_type = "user"
        raise NextScene("Search Results")

    async def _lookup_arcade_by_id(self, ac_id: str):
        ac = await data.arcade.get_arcade(ac_id)

        if ac is not None:
            res = ac._asdict()
            num_cabs = await data.arcade.get_arcade_machines(ac_id)
            res['mech_ct'] = len(num_cabs) if num_cabs else 0
            state.search_results = [res]

    async def _lookup_arcade_by_name(self, name: str):
        ac = await data.arcade.get_arcade_by_name(name)

        if ac is not None:
            res = []
            for ac_res in ac:
                t = ac_res._asdict()
                num_cabs = await data.arcade.get_arcade_machines(t['id'])
                t['mech_ct'] = len(num_cabs) if num_cabs else 0
                res.append(t)
            
            state.search_results = res

    async def _lookup_arcade_by_serial(self, serial: str):
        mech = await data.arcade.get_machine(serial)

        if mech is not None:
            ac = await data.arcade.get_arcade(mech['arcade'])

            if ac is not None:
                res = ac._asdict()
                num_cabs = await data.arcade.get_arcade_machines(mech['arcade'])
                res['mech_ct'] = len(num_cabs) if num_cabs else 0
                state.search_results = [res]

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("Arcade Management")

class ManageMachineView(Frame):
    def __init__(self, screen: Screen):
        super(ManageMachineView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Machine Management",
            on_load=self._redraw
        )

        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Create Machine", self._create))
        layout.add_widget(Button("Lookup Machine", self._lookup))
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        
        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Reassign Machine", self._reassign, disabled=state.selected_machine.id == 0 or state.selected_machine.id is None))
        layout.add_widget(Button("Edit Machine", self._edit, disabled=state.selected_machine.id == 0 or state.selected_machine.id is None))
        layout.add_widget(Button("Delete Machine", self._del, disabled=state.selected_machine.id == 0 or state.selected_machine.id is None))
        layout.add_widget((Divider()))

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        a = Text("", f"status", readonly=True, disabled=True)
        a.value = f"Selected Machine: {state.selected_arcade}"
        layout2.add_widget(a)
        layout2.add_widget(Button("Back", self._back), 2)
        
        self.fix()

    def _create(self):
        self.save()
        raise NextScene("Create Machine")
    
    def _lookup(self):
        self.save()
        raise NextScene("Lookup Machine")
    
    def _reassign(self):
        self.save()
        raise NextScene("Reassign Machine")
    
    def _edit(self):
        self.save()
        raise NextScene("Edit Machine")
    
    def _del(self):
        self.save()
        raise NextScene("Delete Machine")

    def _back(self):
        self.save()
        raise NextScene("Main")

class CreateMachineView(Frame):
    def __init__(self, screen: Screen):
        super(CreateMachineView, self).__init__(
            screen,
            screen.height - 10,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Create Machine"
        )

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Arcade:", "arcade_id"))
        layout.add_widget(Text("Serial:", "serial"))
        layout.add_widget(Text("Game:", "game_id"))
        layout.add_widget(CheckBox("", "Real Cabinet:", "is_cab", ))
        layout.add_widget(RadioButtons([("Not Set", None)] + [
            (inflection.titleize(x.name), x.value) for x in AllnetCountryCode
        ], "Country Override:", "country"))

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()
    
    def _redraw(self):
        self.find_widget("arcade_id").value = state.selected_arcade.id

    def _ok(self):
        self.save()
        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        loop.run_until_complete(self._create_arcade_async(self.data.get("name"), self.data.get("nickname"), self.data.get("country"), self.data.get('timezone'), self.data.get('ip')))

        raise NextScene("Arcade Management") 

    async def _create_arcade_async(self, arcade_id: int, serial: str, game: Optional[str], is_cab: bool, country: Optional[str]):
        machine_id = await data.arcade.create_machine(arcade_id, serial, None, game, is_cab)

        if country:
            data.arcade.set_machine_country(machine_id, country)

        if machine_id:
            state.set_machine(machine_id, serial)

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("Machine Management")

class LookupMachineView(Frame):
    def __init__(self, screen):
        super(LookupMachineView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Lookup Machine"
        )
        
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(RadioButtons([
            ("Name", "1"),
            ("Serial", "2"),
            ("Arcade ID", "3"),
            ("Machine ID", "4"),
        ], "Search By:", "search_type"))
        layout.add_widget(Text("Search:", "search_str"), 1)

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Search", self._lookup), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()
    
    def _lookup(self):
        self.save()
        if not self.data.get("search_str"):
            state.set_last_err("Search cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        search_type = self.data.get("search_type")
        if search_type == "1":
            loop.run_until_complete(self._lookup_arcade_by_name(self.data.get("search_str")))
        elif search_type == "2":
            loop.run_until_complete(self._lookup_arcade_by_serial(self.data.get("search_str")))
        elif search_type == "3":
            real_id = int(self.data.get("search_str"), 16)
            loop.run_until_complete(self._lookup_arcade_by_id(real_id))
        elif search_type == "4":
            loop.run_until_complete(self._lookup_arcade_by_id(self.data.get("search_str")))
        else:
            state.set_last_err("Unknown search type")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        if len(state.search_results) < 1:
            state.set_last_err("Search returned no results")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.search_type = "user"
        raise NextScene("Search Results")

    async def _lookup_arcade_by_id(self, ac_id: str):
        ac = await data.arcade.get_arcade(ac_id)

        if ac is not None:
            res = ac._asdict()
            num_cabs = await data.arcade.get_arcade_machines(ac_id)
            res['mech_ct'] = len(num_cabs) if num_cabs else 0
            state.search_results = [res]

    async def _lookup_arcade_by_name(self, name: str):
        ac = await data.arcade.get_arcade_by_name(name)

        if ac is not None:
            res = []
            for ac_res in ac:
                t = ac_res._asdict()
                num_cabs = await data.arcade.get_arcade_machines(t['id'])
                t['mech_ct'] = len(num_cabs) if num_cabs else 0
                res.append(t)
            
            state.search_results = res

    async def _lookup_arcade_by_serial(self, serial: str):
        mech = await data.arcade.get_machine(serial)

        if mech is not None:
            ac = await data.arcade.get_arcade(mech['arcade'])

            if ac is not None:
                res = ac._asdict()
                num_cabs = await data.arcade.get_arcade_machines(mech['arcade'])
                res['mech_ct'] = len(num_cabs) if num_cabs else 0
                state.search_results = [res]

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("Machine Management")

def demo(screen:Screen, scene: Scene):
    scenes = [
        Scene([MainView(screen)], -1, name="Main"),
        Scene([ManageUserView(screen)], -1, name="User Management"),
        Scene([CreateUserView(screen)], -1, name="Create User"),
        Scene([LookupUserView(screen)], -1, name="Lookup User"),
        Scene([SearchResultsView(screen)], -1, name="Search Results"),
        Scene([ManageCardView(screen)], -1, name="Card Management"),
        Scene([EditUserView(screen)], -1, name="Edit User"),
        Scene([ManageArcadeView(screen)], -1, name="Arcade Management"),
        Scene([CreateArcadeView(screen)], -1, name="Create Arcade"),
        Scene([LookupArcadeView(screen)], -1, name="Lookup Arcade"),
        Scene([ManageMachineView(screen)], -1, name="Machine Management"),
        Scene([LookupMachineView(screen)], -1, name="Lookup Machine"),
        Scene([CreateMachineView(screen)], -1, name="Create Machine"),
    ]

    screen.play(scenes, stop_on_resize=False, start_scene=scene, allow_int=True)

last_scene = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database utilities")
    parser.add_argument(
        "--config", "-c", type=str, help="Config folder to use", default="config"
    )
    args = parser.parse_args()
    
    cfg = CoreConfig()
    if path.exists(f"{args.config}/core.yaml"):
        cfg_dict = yaml.safe_load(open(f"{args.config}/core.yaml"))
        cfg_dict.get("database", {})["loglevel"] = "info"
        cfg.update(cfg_dict)

    if not path.exists(cfg.server.log_dir):
        mkdir(cfg.server.log_dir)

    if not access(cfg.server.log_dir, W_OK):
        print(
            f"Log directory {cfg.server.log_dir} NOT writable, please check permissions"
        )
        exit(1)

    data = Data(cfg)

    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
            exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene

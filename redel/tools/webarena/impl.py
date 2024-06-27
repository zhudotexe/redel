import enum

from browser_env import (
    Action,
    create_click_action,
    create_go_back_action,
    create_go_forward_action,
    create_goto_url_action,
    create_hover_action,
    create_key_press_action,
    create_new_tab_action,
    create_page_close_action,
    create_page_focus_action,
    create_scroll_action,
    create_type_action,
)
from kani import ChatMessage, ChatRole, ai_function

from redel.base_kani import BaseKani
from .harness import WebArenaHarness


class ScrollDirection(enum.Enum):
    up = "up"
    down = "down"


class WebArenaMixin(BaseKani):
    def __init__(self, *args, webarena_harness: WebArenaHarness, **kwargs):
        super().__init__(*args, **kwargs)
        self.webarena = webarena_harness

    def take_action(self, action: Action):
        """Send the action to the WA harness and return the updated state."""
        obs, success, info = self.webarena.action(action)
        if not success:
            error = info["fail_error"]
            return self.webarena.get_prompt(task=self.last_user_message.text, error=error)
        return self.webarena.get_prompt(task=self.last_user_message.text)

    def add_to_history(self, message: ChatMessage):
        # HACK: if the message is a USER message and does not contain the webarena state prompt,
        # prepend it here
        # this is used to ensure that messages sent to the delegates allow them to see the state
        if message.role == ChatRole.USER and not message.text.startswith("BROWSER STATE:"):
            message.content = self.webarena.get_prompt(task=message.text)
        return super().add_to_history(message)

    # action definitions taken from
    # https://github.com/web-arena-x/webarena/blob/4c741b4b20a3e183836e58f383f9be1785248160/agent/prompts/raw/p_cot_id_actree_2s.py#L14
    # and implementations adapted from
    # https://github.com/web-arena-x/webarena/blob/4c741b4b20a3e183836e58f383f9be1785248160/browser_env/actions.py#L1502

    @ai_function()
    def click(self, id: int):
        """Click on an element with a specific id on the current webpage."""
        action = create_click_action(element_id=str(id))
        return self.take_action(action)

    @ai_function()
    def type(self, id: int, content: str, press_enter_after: bool = True):
        """Type the content into the field with the given id. By default, the "Enter" key is pressed after typing unless press_enter_after is set to false."""
        text = content if not press_enter_after else f"{content}\n"
        action = create_type_action(text=text, element_id=str(id))
        return self.take_action(action)

    @ai_function()
    def hover(self, id: int):
        """Hover over an element with the given id."""
        action = create_hover_action(element_id=str(id))
        return self.take_action(action)

    @ai_function()
    def press(self, key_comb: str):
        """Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v)."""
        action = create_key_press_action(key_comb=key_comb)
        return self.take_action(action)

    @ai_function()
    def scroll(self, direction: ScrollDirection):
        """Scroll the page up or down."""
        action = create_scroll_action(direction=direction.value)
        return self.take_action(action)

    @ai_function()
    def new_tab(self):
        """Open a new, empty browser tab."""
        action = create_new_tab_action()
        return self.take_action(action)

    @ai_function()
    def tab_focus(self, tab_index: int):
        """Switch the browser's focus to a specific tab using its index."""
        action = create_page_focus_action(tab_index)
        return self.take_action(action)

    @ai_function()
    def close_tab(self):
        """Close the currently active tab."""
        action = create_page_close_action()
        return self.take_action(action)

    @ai_function()
    def goto(self, url: str):
        """Navigate to a specific URL."""
        url = self.webarena.map_url_to_local(url)
        action = create_goto_url_action(url=url)
        return self.take_action(action)

    @ai_function()
    def go_back(self):
        """Navigate to the previously viewed page."""
        action = create_go_back_action()
        return self.take_action(action)

    @ai_function()
    def go_forward(self):
        """Navigate to the next page (if a previous 'go_back' action was performed)."""
        action = create_go_forward_action()
        return self.take_action(action)

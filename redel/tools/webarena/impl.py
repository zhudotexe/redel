import enum

from browser_env import Action, create_goto_url_action
from kani import ai_function

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

    # actions taken from
    # https://github.com/web-arena-x/webarena/blob/4c741b4b20a3e183836e58f383f9be1785248160/agent/prompts/raw/p_cot_id_actree_2s.py#L14

    @ai_function()
    def click(self, id: int):
        """Click on an element with a specific id on the current webpage."""
        pass

    @ai_function()
    def type(self, id: int, content: str, press_enter_after: bool = True):
        """Type the content into the field with the given id. By default, the "Enter" key is pressed after typing unless press_enter_after is set to false."""
        pass

    @ai_function()
    def hover(self, id: int):
        """Hover over an element with the given id."""
        pass

    @ai_function()
    def press(self, key_comb: str):
        """Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v)."""
        pass

    @ai_function()
    def scroll(self, direction: ScrollDirection):
        """Scroll the page up or down."""
        pass

    @ai_function()
    def new_tab(self):
        """Open a new, empty browser tab."""
        pass

    @ai_function()
    def tab_focus(self, tab_index: int):
        """Switch the browser's focus to a specific tab using its index."""
        pass

    @ai_function()
    def close_tab(self):
        """Close the currently active tab."""
        pass

    @ai_function()
    def goto(self, url: str):
        """Navigate to a specific URL."""
        url = self.webarena.map_url_to_local(url)
        action = create_goto_url_action(url=url)
        return self.take_action(action)

    @ai_function()
    def go_back(self):
        """Navigate to the previously viewed page."""
        pass

    @ai_function()
    def go_forward(self):
        """Navigate to the next page (if a previous 'go_back' action was performed)."""
        pass

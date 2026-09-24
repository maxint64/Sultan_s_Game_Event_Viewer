import tempfile
import unittest

import tkinter as tk

from event_viewer import EventViewer


class FakeVariable:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class FakeButton:
    def __init__(self):
        self.states = []

    def config(self, *, state):
        self.states.append(state)


class LoadEventFilesTests(unittest.TestCase):
    def test_character_update_failure_restores_buttons_and_reports_error(self):
        viewer = EventViewer.__new__(EventViewer)
        viewer.data_source_var = FakeVariable()
        viewer.folder_path = FakeVariable()
        viewer.load_button = FakeButton()
        viewer.reset_button = FakeButton()
        viewer.status_messages = []
        viewer.dialog_messages = []
        viewer.set_status = viewer.status_messages.append
        viewer.show_message = lambda title, message, kind="info": (
            viewer.dialog_messages.append((title, message, kind))
        )

        def raise_character_error(folder):
            raise RuntimeError("测试异常")

        viewer.update_characters_from_cards = raise_character_error
        viewer.clear_event_display = lambda: None
        viewer.show_empty_state = lambda message: None

        with tempfile.TemporaryDirectory() as temp_dir:
            viewer.custom_data_folder = temp_dir
            viewer.selected_game_directory = temp_dir
            viewer.load_event_files()

        self.assertEqual(
            viewer.load_button.states,
            [tk.DISABLED, tk.NORMAL],
        )
        self.assertEqual(
            viewer.reset_button.states,
            [tk.DISABLED, tk.NORMAL],
        )
        self.assertEqual(
            viewer.status_messages[-1],
            "加载失败：读取事件文件时出错：测试异常",
        )
        self.assertEqual(
            viewer.dialog_messages[-1],
            ("加载失败", "读取事件文件时出错：测试异常", "error"),
        )


if __name__ == "__main__":
    unittest.main()

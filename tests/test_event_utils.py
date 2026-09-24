import json
import os
import tempfile
import unittest

from event_utils import (
    group_settlements,
    player_name_segments,
    resolve_event_folder,
    strip_json_comments,
)


class ResolveEventFolderTests(unittest.TestCase):
    def test_config_directory_prefers_nested_rite_over_cards_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = os.path.join(temp_dir, "config")
            rite_dir = os.path.join(config_dir, "rite")
            os.makedirs(rite_dir)
            open(os.path.join(config_dir, "cards.json"), "w").close()
            open(os.path.join(rite_dir, "event.json"), "w").close()

            self.assertEqual(resolve_event_folder(config_dir), rite_dir)

    def test_accepts_a_rite_directory_directly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rite_dir = os.path.join(temp_dir, "rite")
            os.makedirs(rite_dir)
            open(os.path.join(rite_dir, "event.json"), "w").close()

            self.assertEqual(resolve_event_folder(rite_dir), rite_dir)

    def test_resolves_game_root(self):
        with tempfile.TemporaryDirectory() as game_dir:
            rite_dir = os.path.join(
                game_dir,
                "Sultan's Game_Data",
                "StreamingAssets",
                "config",
                "rite",
            )
            os.makedirs(rite_dir)
            open(os.path.join(rite_dir, "event.json"), "w").close()

            self.assertEqual(resolve_event_folder(game_dir), rite_dir)


class StripJsonCommentsTests(unittest.TestCase):
    def test_preserves_double_slashes_inside_strings(self):
        content = r'''
        {
          "url": "https://example.com/path",
          "text": "保留 // 字符",
          "value": 1, // 删除这条注释
        }
        '''

        self.assertEqual(
            json.loads(strip_json_comments(content)),
            {
                "url": "https://example.com/path",
                "text": "保留 // 字符",
                "value": 1,
            },
        )

    def test_handles_escaped_quotes_and_trailing_commas(self):
        content = r'{"text": "他说：\"//不是注释\"", "items": [1, 2,],}'

        self.assertEqual(
            json.loads(strip_json_comments(content)),
            {"text": '他说："//不是注释"', "items": [1, 2]},
        )


class PlayerNameSegmentsTests(unittest.TestCase):
    def test_adds_spaces_next_to_text(self):
        segments = player_name_segments("你好[player.name]今天", "Hugo")

        self.assertEqual("".join(text for text, _ in segments), "你好 Hugo 今天")
        self.assertIn(("Hugo", True), segments)

    def test_does_not_add_spaces_next_to_punctuation(self):
        segments = player_name_segments("“[player.name]！”", "Hugo")

        self.assertEqual("".join(text for text, _ in segments), "“Hugo！”")


class GroupSettlementsTests(unittest.TestCase):
    def test_groups_equivalent_conditions_across_sections(self):
        event_data = {
            "settlement": [
                {"condition": {"s1": 1, "s2": 2}, "result_text": "普通"},
                {"result_text": "无条件"},
            ],
            "settlement_prior": [
                {"condition": {"s2": 2, "s1": 1}, "result_text": "优先"}
            ],
            "settlement_extre": [
                {"condition": {"s3": 3}, "result_text": "额外"}
            ],
        }

        groups = list(group_settlements(event_data).values())

        self.assertEqual(len(groups), 2)
        self.assertEqual(
            [(item_type, index) for item_type, index, _ in groups[0]],
            [("settlement", 0), ("prior", 0)],
        )
        self.assertEqual(groups[1][0][:2], ("extre", 0))


if __name__ == "__main__":
    unittest.main()

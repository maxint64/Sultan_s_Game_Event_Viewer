"""与 Tkinter 控件无关的事件数据处理函数。"""

import glob
import json
import os
import re


def strip_json_comments(content):
    """移除 JSON 字符串外的 ``//`` 注释，并清理尾随逗号。"""
    result = []
    index = 0
    in_string = False
    escaped = False

    while index < len(content):
        char = content[index]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
        elif char == '"':
            in_string = True
            result.append(char)
            index += 1
        elif char == "/" and index + 1 < len(content) and content[index + 1] == "/":
            index += 2
            while index < len(content) and content[index] not in "\r\n":
                index += 1
        else:
            result.append(char)
            index += 1

    return re.sub(r",\s*([}\]])", r"\1", "".join(result))


def resolve_event_folder(selected_folder):
    """从游戏根目录、config 或 rite 目录中定位事件 JSON 目录。"""
    selected_folder = os.path.normpath(selected_folder)
    nested_candidates = [
        os.path.join(selected_folder, "rite"),
        os.path.join(selected_folder, "config", "rite"),
        os.path.join(
            selected_folder,
            "Sultan's Game_Data",
            "StreamingAssets",
            "config",
            "rite",
        ),
    ]
    candidates = (
        [selected_folder, *nested_candidates]
        if os.path.basename(selected_folder).lower() == "rite"
        else [*nested_candidates, selected_folder]
    )

    seen = set()
    for candidate in candidates:
        normalized = os.path.normcase(os.path.abspath(candidate))
        if normalized in seen:
            continue
        seen.add(normalized)
        if os.path.isdir(candidate) and glob.glob(os.path.join(candidate, "*.json")):
            return candidate
    return selected_folder


def player_name_segments(text, player_name, placeholder="[player.name]"):
    """拆分玩家名占位符，并仅在相邻字符为文字或数字时补空格。"""
    segments = []
    cursor = 0

    while True:
        index = text.find(placeholder, cursor)
        if index < 0:
            if cursor < len(text):
                segments.append((text[cursor:], False))
            break

        if index > cursor:
            segments.append((text[cursor:index], False))
        if index > 0 and text[index - 1].isalnum():
            segments.append((" ", False))

        segments.append((player_name, True))
        end = index + len(placeholder)
        if end < len(text) and text[end].isalnum():
            segments.append((" ", False))
        cursor = end

    return segments


def group_settlements(event_data):
    """按条件合并普通、优先和额外结算分支，并保持原有顺序。"""
    groups = {}
    sections = (
        ("settlement", "settlement"),
        ("prior", "settlement_prior"),
        ("extre", "settlement_extre"),
    )

    for item_type, field_name in sections:
        settlements = event_data.get(field_name, [])
        if not isinstance(settlements, list):
            continue
        for index, settlement in enumerate(settlements):
            if not isinstance(settlement, dict) or "condition" not in settlement:
                continue
            condition_key = json.dumps(
                settlement["condition"], ensure_ascii=False, sort_keys=True
            )
            groups.setdefault(condition_key, []).append(
                (item_type, index, settlement)
            )

    return groups

# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 19:49:39 2025

@author: 阿赤
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font as tkfont
import glob
import re
import copy

class EventViewer:
    CHARACTER_DEFAULT_SELECTION = "所有人"
    CHARACTER_PLACEHOLDER = "输入角色ID、名称、别称、或关键词"
    EVENT_DEFAULT_SELECTION = "输入事件ID、标题或关键词"
    NOT_LOADED_TEXT = "正在加载内置数据..."
    NO_EVENT_TEXT = "请先选择角色和事件"

    def __init__(self, root):
        self.root = root
        self.root.title("事件分支查看器")
        self.configure_initial_geometry()
        
        # 全局排版：11pt 在 96 DPI 下约为 14.7px，不低于 12px。
        self.font_family = "Microsoft YaHei UI" if os.name == "nt" else tkfont.nametofont("TkDefaultFont").actual("family")
        self.font = (self.font_family, 11)
        self.heading_font = (self.font_family, 11, "bold")
        self.title_font = (self.font_family, 13, "bold")
        self.dialog_icon_font = (self.font_family, 22, "bold")
        self.configure_global_fonts()
        
        # 数据
        self.event_files = []
        self.event_data = {}
        self.current_event = None
        self.current_settlement = None
        self.current_detail = None
        self.comments_data = {}  # 存储注释信息
        self.all_event_names = []  # 存储所有事件名称
        self.available_event_names = []  # 当前人物筛选后的事件名称
        self.event_name_to_file = {}
        self.event_card_ids = {}
        self.custom_data_folder = None
        self.selected_game_directory = None
        self.default_characters = self.load_default_characters()
        self.characters = copy.deepcopy(self.default_characters)
        self.character_display_map = {}
        
        # 跟随系统的应用主题
        self.system_dark_mode = self.is_system_dark_mode()
        self.colors = self.apply_theme(self.system_dark_mode)

        # 创建UI
        self.create_ui()
        self.apply_theme(self.system_dark_mode)
        self.show_empty_state(self.NOT_LOADED_TEXT)
        self.root.after(0, self.load_event_files)
        if os.name == "nt":
            self.root.after(2000, self.check_system_theme)

    def configure_initial_geometry(self):
        """窗口占满屏幕可用高度，并保持适合阅读的常规宽度。"""
        left = top = 0
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        work_width = screen_width
        work_height = screen_height

        if os.name == "nt":
            try:
                import ctypes

                class Rect(ctypes.Structure):
                    _fields_ = [
                        ("left", ctypes.c_long),
                        ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long),
                    ]

                rect = Rect()
                if ctypes.windll.user32.SystemParametersInfoW(
                    0x0030, 0, ctypes.byref(rect), 0
                ):
                    left, top = rect.left, rect.top
                    work_width = rect.right - rect.left
                    work_height = rect.bottom - rect.top
            except (AttributeError, OSError):
                pass

        taskbar_height = max(0, screen_height - work_height)
        window_height = max(1, int(screen_height * 0.9) - taskbar_height)
        window_height = min(window_height, work_height)
        window_width = min(1200, work_width)
        x = left + max(0, (work_width - window_width) // 2)
        y = top + max(0, (work_height - window_height) // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(min(1000, work_width), min(700, window_height))

    def configure_global_fonts(self):
        """统一 Tk/ttk 和传统 Tk 控件使用的命名字体。"""
        for font_name in (
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkIconFont",
            "TkTooltipFont",
        ):
            try:
                tkfont.nametofont(font_name).configure(family=self.font_family, size=11)
            except tk.TclError:
                pass
        try:
            tkfont.nametofont("TkHeadingFont").configure(
                family=self.font_family,
                size=11,
                weight="bold",
            )
        except tk.TclError:
            pass
        self.root.option_add("*Font", self.font)

    def is_system_dark_mode(self):
        """读取 Windows 当前的应用主题；其他平台默认使用亮色。"""
        if os.name != "nt":
            return False
        try:
            import winreg
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
                apps_use_light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return apps_use_light_theme == 0
        except OSError:
            return getattr(self, "system_dark_mode", False)

    def apply_theme(self, dark_mode):
        """根据系统模式配置 ttk 和文本控件颜色。"""
        if dark_mode:
            colors = {
                "bg": "#1e1e1e",
                "fg": "#d4d4d4",
                "select_bg": "#264f78",
                "select_fg": "#ffffff",
                "input_bg": "#3c3c3c",
                "border": "#555555",
                "comment": "#6a9955",
                "info": "#75b7ff",
                "error": "#ff6b6b",
                "hover": "#4a4a4a",
                "player_name": "#ffd24a",
            }
        else:
            colors = {
                "bg": "#f0f0f0",
                "fg": "#202020",
                "select_bg": "#0078d4",
                "select_fg": "#ffffff",
                "input_bg": "#ffffff",
                "border": "#a0a0a0",
                "comment": "#008000",
                "info": "#0067c0",
                "error": "#c42b1c",
                "hover": "#e5f1fb",
                "player_name": "#a66f00",
            }

        bg_color = colors["bg"]
        fg_color = colors["fg"]
        select_bg = colors["select_bg"]
        select_fg = colors["select_fg"]
        input_bg = colors["input_bg"]
        border_color = colors["border"]

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=self.font)
        style.configure(
            "TButton",
            background=input_bg,
            foreground=fg_color,
            font=self.font,
            padding=(16, 4),
            bordercolor=border_color,
            lightcolor=input_bg,
            darkcolor=input_bg,
        )
        style.map("TButton", background=[("active", select_bg)], foreground=[("active", select_fg)])
        style.configure(
            "TEntry",
            fieldbackground=input_bg,
            foreground=fg_color,
            font=self.font,
            padding=(8, 5),
            bordercolor=border_color,
            lightcolor=input_bg,
            darkcolor=input_bg,
        )
        style.configure(
            "TCombobox",
            background=input_bg,
            fieldbackground=input_bg,
            foreground=fg_color,
            arrowcolor=fg_color,
            font=self.font,
            padding=(8, 5),
            bordercolor=border_color,
            lightcolor=input_bg,
            darkcolor=input_bg,
        )
        style.map("TCombobox", fieldbackground=[("readonly", input_bg)], foreground=[("readonly", fg_color)])

        style.configure(
            "Treeview",
            background=input_bg,
            foreground=fg_color,
            fieldbackground=input_bg,
            font=self.font,
            rowheight=32,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Treeview.Heading",
            background=fg_color,
            foreground=input_bg,
            font=self.heading_font,
            padding=(8, 5),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[("active", fg_color), ("pressed", fg_color)],
            foreground=[("active", input_bg), ("pressed", input_bg)],
            relief=[("active", "flat"), ("pressed", "flat")],
        )
        style.map("Treeview",
                  background=[("selected", select_bg)],
                  foreground=[("selected", select_fg)])

        style.configure(
            "TLabelframe",
            background=bg_color,
            foreground=fg_color,
            borderwidth=0,
            relief="flat",
            bordercolor=bg_color,
            lightcolor=bg_color,
            darkcolor=bg_color,
        )
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color, font=self.heading_font)
        style.configure("Status.TLabel", background=input_bg, foreground=fg_color, padding=(10, 6))
        style.configure("ColumnSeparator.TSeparator", background=border_color)
        style.configure(
            "TScrollbar",
            background=input_bg,
            troughcolor=bg_color,
            bordercolor=border_color,
            arrowcolor=fg_color,
            lightcolor=input_bg,
            darkcolor=input_bg,
            borderwidth=0,
            relief="flat",
        )
        style.map("TScrollbar", background=[("active", select_bg)])

        self.root.configure(background=bg_color)
        self.root.option_add("*TCombobox*Listbox.background", input_bg)
        self.root.option_add("*TCombobox*Listbox.foreground", fg_color)
        self.root.option_add("*TCombobox*Listbox.selectBackground", select_bg)
        self.root.option_add("*TCombobox*Listbox.selectForeground", select_fg)
        self.root.option_add("*TCombobox*Listbox.font", self.font)

        for attribute in ("event_desc_text", "result_text"):
            if hasattr(self, attribute):
                widget = getattr(self, attribute)
                widget.config(
                    bg=input_bg,
                    fg=fg_color,
                    insertbackground=fg_color,
                    selectbackground=select_bg,
                    selectforeground=select_fg,
                    highlightbackground=border_color,
                    highlightcolor=select_bg,
                    highlightthickness=0,
                    borderwidth=0,
                    relief=tk.FLAT,
                )
                widget.vbar.config(
                    background=input_bg,
                    troughcolor=bg_color,
                    activebackground=select_bg,
                    borderwidth=0,
                    highlightthickness=0,
                    relief=tk.FLAT,
                )
                widget.tag_configure(
                    "player_name",
                    foreground=colors["player_name"],
                    font=(self.font_family, 14, "bold"),
                )
        for attribute in ("slot_tree", "settlement_tree"):
            if hasattr(self, attribute):
                getattr(self, attribute).tag_configure(
                    "hover", background=colors["hover"]
                )
        if hasattr(self, "result_text"):
            self.result_text.tag_configure("comment", foreground=colors["comment"])

        self.colors = colors
        return colors

    def check_system_theme(self):
        """运行期间检测 Windows 主题变化。"""
        dark_mode = self.is_system_dark_mode()
        if dark_mode != self.system_dark_mode:
            self.system_dark_mode = dark_mode
            self.apply_theme(dark_mode)
        self.root.after(2000, self.check_system_theme)

    def show_message(self, title, message, kind="info"):
        """显示与主界面主题一致的模态消息窗口。"""
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title(title)
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.configure(background=self.colors["bg"])

        body = ttk.Frame(dialog, padding=(24, 20, 24, 14))
        body.pack(fill=tk.BOTH, expand=True)
        icon = "⚠" if kind == "error" else "ⓘ"
        icon_color = self.colors["error"] if kind == "error" else self.colors["info"]
        tk.Label(
            body,
            text=icon,
            background=self.colors["bg"],
            foreground=icon_color,
            font=self.dialog_icon_font,
        ).grid(row=0, column=0, padx=(0, 16), sticky="n")
        ttk.Label(body, text=message, font=self.font, wraplength=480, justify=tk.LEFT).grid(
            row=0,
            column=1,
            sticky="w",
        )

        button_frame = ttk.Frame(dialog, padding=(24, 0, 24, 18))
        button_frame.pack(fill=tk.X)
        close_button = ttk.Button(button_frame, text="确定", width=12, command=dialog.destroy)
        close_button.pack(side=tk.RIGHT)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Return>", lambda event: dialog.destroy())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_reqwidth()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        dialog.deiconify()
        dialog.grab_set()
        close_button.focus_set()
        self.root.wait_window(dialog)

    def create_ui(self):
        colors = self.colors
        
        # 创建主框架 - 去掉边框
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        
        # 数据来源：内置数据不暴露内部路径，自定义数据显示用户选择的目录
        control_frame = ttk.LabelFrame(main_frame, text="数据来源", padding=8)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        control_frame.grid_columnconfigure(0, weight=1)

        self.data_source_var = tk.StringVar(value="内置数据")
        self.folder_path = tk.StringVar(value="（内置数据）")
        ttk.Entry(
            control_frame, textvariable=self.folder_path, state="readonly"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.load_button = ttk.Button(
            control_frame,
            text="选择游戏目录并重新加载数据",
            width=26,
            command=self.browse_folder,
        )
        self.load_button.grid(row=0, column=1, padx=(0, 6))
        self.reset_button = ttk.Button(
            control_frame,
            text="重置为内置数据",
            width=18,
            command=self.reset_to_bundled_data,
        )
        self.reset_button.grid(row=0, column=2)

        # 玩家名称只影响文本显示，不参与事件筛选
        display_frame = ttk.LabelFrame(main_frame, text="显示设置", padding=8)
        display_frame.pack(fill=tk.X, pady=(0, 10))
        display_frame.grid_columnconfigure(2, weight=1)

        ttk.Label(display_frame, text="玩家名称：").grid(
            row=0, column=0, padx=(0, 6), sticky="w"
        )
        self.player_name = tk.StringVar(value="阿尔图")
        ttk.Entry(display_frame, textvariable=self.player_name, width=24).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(
            display_frame, text="（用于替换事件文本中的[player.name]）"
        ).grid(row=0, column=2, padx=(8, 0), sticky="w")
        self.player_name.trace_add("write", self.on_player_name_change)

        # 仅放置真正影响事件列表的筛选项
        event_select_frame = ttk.LabelFrame(main_frame, text="筛选条件", padding=8)
        event_select_frame.pack(fill=tk.X, pady=(0, 10))
        event_select_frame.grid_columnconfigure(1, weight=1, uniform="search")
        event_select_frame.grid_columnconfigure(3, weight=1, uniform="search")

        ttk.Label(event_select_frame, text="角色：").grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        self.character_combo = ttk.Combobox(event_select_frame, font=self.font)
        self.character_combo.grid(row=0, column=1, sticky="ew")
        self.character_combo.bind("<KeyRelease>", self.filter_characters)
        self.character_combo.bind("<<ComboboxSelected>>", self.on_character_selected)
        self.character_combo.bind("<Return>", self.on_character_selected)
        self.character_combo.bind(
            "<FocusIn>", lambda event: self.clear_placeholder(self.character_combo)
        )
        self.character_combo.bind(
            "<FocusOut>", lambda event: self.restore_placeholder(self.character_combo)
        )

        ttk.Label(event_select_frame, text="事件：").grid(
            row=0, column=2, padx=(15, 5), sticky="w"
        )
        self.event_combo = ttk.Combobox(event_select_frame, font=self.font)
        self.event_combo.grid(row=0, column=3, sticky="ew")
        self.event_combo.bind("<KeyRelease>", self.filter_events)
        self.event_combo.bind("<<ComboboxSelected>>", self.on_event_selected)
        self.event_combo.bind("<Return>", self.on_event_selected)
        self.event_combo.bind(
            "<FocusIn>", lambda event: self.clear_placeholder(self.event_combo)
        )
        self.event_combo.bind(
            "<FocusOut>", lambda event: self.restore_placeholder(self.event_combo)
        )
        
        # 创建事件描述区域 - 去掉边框
        description_frame = ttk.LabelFrame(main_frame, text="事件说明", padding=6)
        description_frame.pack(fill=tk.X, pady=(0, 10))
        
        
        # 事件描述文本
        self.event_desc_text = scrolledtext.ScrolledText(description_frame, wrap=tk.WORD, font=self.font, height=3)
        self.event_desc_text.pack(fill=tk.X, expand=True)
        # 设置文本颜色
        self.event_desc_text.config(
            bg=colors["input_bg"],
            fg=colors["fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"],
            state=tk.DISABLED,
        )
        
        # 创建中间区域 - 分为左右两列
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        middle_frame.grid_columnconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(1, weight=1)
        middle_frame.grid_rowconfigure(0, weight=1)
        
        # 左侧 - Slot条件列表 - 去掉边框
        slot_frame = ttk.LabelFrame(middle_frame, text="触发条件（Slot）", padding=6)
        slot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        
        # Slot条件列表
        self.slot_tree = ttk.Treeview(slot_frame, columns=("id", "description"), show="headings", height=8)
        self.slot_tree.heading("id", text="ID", anchor=tk.W)
        self.slot_tree.heading("description", text="条件描述", anchor=tk.W)
        self.slot_tree.column("id", width=100, minwidth=80, stretch=False)
        self.slot_tree.column("description", width=400, minwidth=180, stretch=True)
        
        # 添加滚动条
        slot_scrollbar = ttk.Scrollbar(slot_frame, orient="vertical", command=self.slot_tree.yview)
        self.slot_tree.configure(yscrollcommand=slot_scrollbar.set)
        
        # 放置树形视图和滚动条
        self.slot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        slot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.slot_tree.bind("<<TreeviewSelect>>", self.on_slot_selected)
        self.slot_tree.bind("<Motion>", self.on_tree_motion)
        self.slot_tree.bind("<Leave>", self.on_tree_leave)
        self.slot_column_separator = ttk.Separator(
            self.slot_tree, orient=tk.VERTICAL, style="ColumnSeparator.TSeparator"
        )
        self.slot_column_separator.place(x=100, y=0, relheight=1)
        
        # 右侧 - Settlement条件列表 - 去掉边框
        settlement_frame = ttk.LabelFrame(middle_frame, text="结算条件（Settlement）", padding=6)
        settlement_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        
        # Settlement条件列表
        self.settlement_tree = ttk.Treeview(settlement_frame, columns=("id", "description"), show="headings", height=8)
        self.settlement_tree.heading("id", text="ID", anchor=tk.W)
        self.settlement_tree.heading("description", text="条件描述", anchor=tk.W)
        self.settlement_tree.column("id", width=110, minwidth=80, stretch=False)
        self.settlement_tree.column("description", width=400, minwidth=180, stretch=True)
        
        # 添加滚动条
        settlement_scrollbar = ttk.Scrollbar(settlement_frame, orient="vertical", command=self.settlement_tree.yview)
        self.settlement_tree.configure(yscrollcommand=settlement_scrollbar.set)
        
        # 放置树形视图和滚动条
        self.settlement_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        settlement_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.settlement_tree.bind("<<TreeviewSelect>>", self.on_settlement_selected)
        self.settlement_tree.bind("<Motion>", self.on_tree_motion)
        self.settlement_tree.bind("<Leave>", self.on_tree_leave)
        self.settlement_column_separator = ttk.Separator(
            self.settlement_tree,
            orient=tk.VERTICAL,
            style="ColumnSeparator.TSeparator",
        )
        self.settlement_column_separator.place(x=110, y=0, relheight=1)
        
        # 创建结果文本区域 - 去掉边框
        result_frame = ttk.LabelFrame(main_frame, text="事件内容 / 原始脚本", padding=6)
        result_frame.pack(fill=tk.BOTH, expand=True)
                
        # 结果标题
        self.result_title_var = tk.StringVar()
        title_label = ttk.Label(result_frame, textvariable=self.result_title_var, font=self.title_font)
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 结果文本
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=self.font)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        # 设置文本颜色
        self.result_text.config(
            bg=colors["input_bg"],
            fg=colors["fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"],
            state=tk.DISABLED,
        )
        # 配置标签样式
        self.result_text.tag_configure("title", font=self.title_font)
        self.result_text.tag_configure("content", font=self.font)
        self.result_text.tag_configure("comment", font=(self.font_family, 11, "italic"), foreground=colors["comment"])

        self.status_var = tk.StringVar(value="正在加载内置数据...")
        ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel", anchor="w").pack(
            side=tk.BOTTOM, fill=tk.X, pady=(8, 0)
        )
        
    def load_default_characters(self):
        """加载随程序提供的人工校正人物元数据。"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_path = os.path.join(
            current_dir, "data", "character", "characters.json"
        )
        try:
            with open(metadata_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except Exception as error:
            print(f"加载人物元数据失败: {metadata_path}, 错误: {error}")
            return []

    def strip_json_comments(self, content):
        """移除字符串外的 // 注释，并清理尾随逗号。"""
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

    def update_characters_from_cards(self, rite_folder):
        """用 rite 同级的 cards.json 更新运行时人物列表，不写入硬盘。"""
        self.characters = copy.deepcopy(self.default_characters)
        cards_path = os.path.join(os.path.dirname(os.path.normpath(rite_folder)), "cards.json")
        if not os.path.isfile(cards_path):
            return

        try:
            with open(cards_path, "r", encoding="utf-8") as file:
                cards_data = json.loads(self.strip_json_comments(file.read()))
        except Exception as error:
            print(f"加载卡牌数据失败: {cards_path}, 错误: {error}")
            return

        valid_cards = {}
        for key, card in cards_data.items():
            if not isinstance(card, dict) or card.get("type") != "char":
                continue
            title = card.get("title", "")
            tags = card.get("tag", {})
            if title in {"未启用", "食客", "路人"} or "食客" in tags:
                continue
            try:
                card_id = int(card.get("id", key))
            except (TypeError, ValueError):
                continue
            valid_cards[card_id] = card

        records = copy.deepcopy(self.default_characters)
        for record in records:
            record["card_ids"] = [card_id for card_id in record.get("card_ids", []) if card_id in valid_cards]

        id_to_record = {}
        name_to_record = {}
        for record in records:
            for card_id in record.get("card_ids", []):
                id_to_record[card_id] = record
            for name in [record.get("name", ""), *record.get("aliases", [])]:
                if name:
                    name_to_record.setdefault(name, record)

        for card_id, card in valid_cards.items():
            name = card.get("name", "").strip()
            if not name:
                continue
            if card_id in id_to_record:
                record = id_to_record[card_id]
                if name != record.get("name") and name not in record.get("aliases", []):
                    record.setdefault("aliases", []).append(name)
                    name_to_record.setdefault(name, record)
                continue
            record = name_to_record.get(name)
            if record is None:
                record = {"name": name, "aliases": [], "card_ids": []}
                records.append(record)
                name_to_record[name] = record
            record["card_ids"].append(card_id)
            id_to_record[card_id] = record

        self.characters = [record for record in records if record.get("card_ids")]
        for record in self.characters:
            record["card_ids"] = sorted(set(record["card_ids"]))
        self.characters.sort(key=lambda record: min(record["card_ids"]))

    def format_character_option(self, character):
        aliases = "/".join(character.get("aliases", []))
        card_ids = ", ".join(str(card_id) for card_id in character.get("card_ids", []))
        name = character.get("name", "")
        name_with_aliases = f"{name} ({aliases})" if aliases else name
        return f"{name_with_aliases} - {card_ids}"

    def refresh_character_options(self):
        self.character_display_map = {
            self.format_character_option(character): character
            for character in self.characters
        }
        options = [self.CHARACTER_DEFAULT_SELECTION, *self.character_display_map.keys()]
        self.character_combo["values"] = options
        self.character_combo.set(self.CHARACTER_PLACEHOLDER)

    def clear_placeholder(self, combo):
        placeholder = self.CHARACTER_PLACEHOLDER if combo is self.character_combo else self.EVENT_DEFAULT_SELECTION
        if combo.get() == placeholder:
            combo.set("")

    def restore_placeholder(self, combo):
        if not combo.get().strip():
            if combo is self.character_combo:
                combo.set(self.CHARACTER_PLACEHOLDER)
                self.on_character_selected()
            elif combo is self.event_combo:
                combo.set(self.EVENT_DEFAULT_SELECTION)
                self.on_event_selected(None)

    def set_text_content(self, widget, content="", tag=None):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        if content:
            widget.insert(tk.END, content, tag) if tag else widget.insert(tk.END, content)
        widget.config(state=tk.DISABLED)

    def clear_event_display(self):
        self.current_event = None
        self.current_settlement = None
        self.current_detail = None
        self.show_empty_state(self.NO_EVENT_TEXT)

    def show_empty_state(self, message):
        """在所有详情区域显示当前没有数据的原因。"""
        self.set_text_content(self.event_desc_text, message)
        self.set_text_content(self.result_text, message)
        self.result_title_var.set("")
        for tree in (self.slot_tree, self.settlement_tree):
            for item in tree.get_children():
                tree.delete(item)
            tree.insert("", "end", values=("", message), tags=("empty",))

    def set_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def on_tree_motion(self, event):
        """鼠标经过条件行时，仅高亮当前行。"""
        tree = event.widget
        item = tree.identify_row(event.y)
        previous = getattr(tree, "_hover_item", "")
        if item == previous:
            return

        if previous and tree.exists(previous):
            tags = tuple(
                tag for tag in tree.item(previous, "tags") if tag != "hover"
            )
            tree.item(previous, tags=tags)

        if item:
            tags = tuple(tree.item(item, "tags"))
            if "hover" not in tags:
                tree.item(item, tags=(*tags, "hover"))
        tree._hover_item = item

    def on_tree_leave(self, event):
        tree = event.widget
        previous = getattr(tree, "_hover_item", "")
        if previous and tree.exists(previous):
            tags = tuple(
                tag for tag in tree.item(previous, "tags") if tag != "hover"
            )
            tree.item(previous, tags=tags)
        tree._hover_item = ""

    def filter_characters(self, event=None):
        if event and event.keysym in ("Down", "Up", "Return", "Tab"):
            return
        search_text = self.character_combo.get().strip().lower()
        if search_text in (
            self.CHARACTER_DEFAULT_SELECTION.lower(),
            self.CHARACTER_PLACEHOLDER.lower(),
        ):
            search_text = ""
        if hasattr(self, "_character_filter_job"):
            self.root.after_cancel(self._character_filter_job)
        self._character_filter_job = self.root.after(500, lambda: self._do_filter_characters(search_text))

    def _do_filter_characters(self, search_text):
        matches = [
            option for option in self.character_display_map
            if not search_text or search_text in option.lower()
        ]
        self.character_combo["values"] = [self.CHARACTER_DEFAULT_SELECTION, *matches]
        if search_text and matches:
            self.character_combo.event_generate("<Down>")

    def on_character_selected(self, event=None):
        selected = self.character_combo.get().strip()
        character = self.character_display_map.get(selected)
        if character is None:
            self.available_event_names = self.all_event_names.copy()
        else:
            card_ids = set(character.get("card_ids", []))
            self.available_event_names = [
                event_name for event_name in self.all_event_names
                if self.event_card_ids.get(self.event_name_to_file[event_name], set()) & card_ids
            ]
        self.event_combo["values"] = [self.EVENT_DEFAULT_SELECTION, *self.available_event_names]
        self.event_combo.set(self.EVENT_DEFAULT_SELECTION)
        self.clear_event_display()

    def resolve_event_folder(self, selected_folder):
        """兼容选择游戏根目录、config 目录或 rite 目录。"""
        candidates = [
            selected_folder,
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
        for candidate in candidates:
            if os.path.isdir(candidate) and glob.glob(os.path.join(candidate, "*.json")):
                return candidate
        return selected_folder

    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择游戏目录或 rite 目录")
        if folder:
            self.selected_game_directory = folder
            self.custom_data_folder = self.resolve_event_folder(folder)
            self.data_source_var.set("自定义目录")
            self.folder_path.set(f"（自定义目录）{folder}")
            self.load_event_files()
    
    def reset_to_bundled_data(self):
        """清除自定义目录并立即重新加载程序内置数据。"""
        self.custom_data_folder = None
        self.selected_game_directory = None
        self.data_source_var.set("内置数据")
        self.folder_path.set("（内置数据）")
        self.load_event_files()

    def filter_events(self, event=None):
        """根据输入过滤当前人物范围内的事件列表。"""
        if event and event.keysym in ("Down", "Up", "Return", "Tab"):
            return
        search_text = self.event_combo.get().strip().lower()
        if search_text == self.EVENT_DEFAULT_SELECTION.lower():
            search_text = ""
        if hasattr(self, "_filter_job"):
            self.root.after_cancel(self._filter_job)
        self._filter_job = self.root.after(500, lambda: self._do_filter(search_text))

    def _do_filter(self, search_text):
        filtered_events = [
            name for name in self.available_event_names
            if not search_text or search_text in name.lower()
        ]
        self.event_combo["values"] = [self.EVENT_DEFAULT_SELECTION, *filtered_events]
        if search_text and filtered_events:
            self.event_combo.event_generate("<Down>")

    def extract_comments(self, content):
        """从JSON内容中提取注释"""
        comments = {}
        
        # 匹配 "key":value //comment 格式的注释
        comment_pattern = r'"([^"]+)":\s*([^,\{\}\[\]]+|\"[^\"]*\"|true|false|null),?\s*//(.+?)(?=\n|$)'
        matches = re.finditer(comment_pattern, content)
        
        for match in matches:
            key = match.group(1)
            value = match.group(2).strip()
            comment = match.group(3).strip()
            
            # 构建键，形如 "key:value"
            comment_key = f"{key}:{value}"
            comments[comment_key] = comment
        
        # 匹配行末尾带有注释的对象和数组值
        object_comment_pattern = r'"([^"]+)":\s*(\{|\[)\s*//(.+?)(?=\n|$)'
        matches = re.finditer(object_comment_pattern, content)
        
        for match in matches:
            key = match.group(1)
            comment = match.group(3).strip()
            comments[key] = comment
        
        # 匹配单独的键值对末尾的注释（不依赖于值的类型）
        key_value_pattern = r'"([^"]+)":\s*([^,\n]*),?\s*//(.+?)(?=\n|$)'
        matches = re.finditer(key_value_pattern, content)
        
        for match in matches:
            key = match.group(1)
            value = match.group(2).strip()
            comment = match.group(3).strip()
            
            if value and value not in ['{', '[']:
                comment_key = f"{key}:{value}"
                if comment_key not in comments:
                    comments[comment_key] = comment
            else:
                if key not in comments:
                    comments[key] = comment
        
        return comments
    
    def player_name_segments(self, text):
        """拆分玩家名占位符，并仅在紧邻文字时补半角空格。"""
        placeholder = "[player.name]"
        player_name = self.player_name.get().strip() or "阿尔图"
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

    def replace_player_name(self, text):
        return "".join(content for content, _ in self.player_name_segments(text))

    def insert_player_text(self, widget, text, default_tag=None):
        for content, is_player_name in self.player_name_segments(text):
            if is_player_name:
                tags = (default_tag, "player_name") if default_tag else "player_name"
            else:
                tags = default_tag
            if tags:
                widget.insert(tk.END, content, tags)
            else:
                widget.insert(tk.END, content)

    def set_player_text_content(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        self.insert_player_text(widget, text)
        widget.config(state=tk.DISABLED)

    def on_player_name_change(self, *args):
        """玩家名称改变后刷新当前可见的事件文本。"""
        if self.current_event:
            event_data = self.event_data[self.current_event]
            description = event_data.get("text") or "当前事件没有事件说明"
            self.set_player_text_content(self.event_desc_text, description)

        if self.current_settlement:
            self.display_result_text(self.current_settlement)
        elif self.current_detail and self.current_detail[0] == "group":
            self.display_group_results(self.current_detail[1])
        elif self.current_detail and self.current_detail[0] == "random":
            self.display_random_text(
                self.current_detail[1], self.current_detail[2]
            )
    
    def format_condition(self, condition, comments=None):
        """格式化条件为可读文本，可选添加注释"""
        if not condition:
            return "无条件"
        
        # 简单展示条件内容
        condition_str = json.dumps(condition, ensure_ascii=False)
        
        # 添加注释（如果有）
        if comments:
            comment_parts = []
            for key, value in condition.items():
                comment_key = f"{key}:{value}"
                if comment_key in comments:
                    comment_parts.append(f"{comments[comment_key]}")
                elif key in comments:
                    comment_parts.append(f"{comments[key]}")
            
            if comment_parts:
                condition_str = " ".join(comment_parts) + condition_str
        
        return condition_str
    
    def load_event_files(self):
        using_bundled_data = self.custom_data_folder is None
        source_name = "内置数据" if using_bundled_data else "自定义目录"
        if using_bundled_data:
            folder = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "data", "rite"
            )
            self.data_source_var.set("内置数据")
            self.folder_path.set("（内置数据）")
        else:
            folder = self.custom_data_folder
            self.data_source_var.set("自定义目录")
            visible_folder = self.selected_game_directory or folder
            self.folder_path.set(f"（自定义目录）{visible_folder}")

        if not os.path.isdir(folder):
            message = "未找到事件数据，请确认游戏目录是否正确"
            self.set_status(f"加载失败：{message}")
            self.show_message("加载失败", message, kind="error")
            return

        self.load_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)
        self.set_status(f"正在加载{source_name}...")
        self.event_files = []
        self.event_data = {}
        self.comments_data = {}
        self.event_card_ids = {}
        self.event_name_to_file = {}
        self.update_characters_from_cards(folder)
        self.clear_event_display()
        
        try:
            load_errors = []
            # 查找所有json文件
            json_files = glob.glob(os.path.join(folder, "*.json"))
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 提取注释信息
                        self.comments_data[file_path] = self.extract_comments(content)
                        
                        # 尝试修复常见的JSON错误
                        # 1. 移除//类型的注释，但先保存它们以便后续显示
                        content_no_comments = re.sub(r'//.*', '', content)
                        
                        # 2. 末尾多余的逗号问题
                        content_no_comments = re.sub(r',\s*([}\]])', r'\1', content_no_comments)
                        
                        # 3. 清理剩余可能导致问题的格式
                        content_no_comments = re.sub(r'(?m)^\s*//.*$', '', content_no_comments)  # 删除整行注释
                        
                        try:
                            # 尝试使用标准JSON解析
                            data = json.loads(content_no_comments)
                            # 检查是否是事件数据
                            if 'id' in data and 'name' in data and 'settlement' in data:
                                self.event_files.append(file_path)
                                self.event_data[file_path] = data
                                self.event_card_ids[file_path] = {
                                    int(card_id)
                                    for card_id in re.findall(r"(?<!\d)2\d{6}(?!\d)", content_no_comments)
                                }
                        except json.JSONDecodeError as error:
                            load_errors.append(f"{os.path.basename(file_path)}：{error}")
                            
                except Exception as error:
                    load_errors.append(f"{os.path.basename(file_path)}：{error}")
            
            # 更新事件下拉列表
            event_names = []
            for file_path in self.event_files:
                event_data = self.event_data[file_path]
                event_names.append(f"{event_data['id']} - {event_data['name']}")
            
            # 按ID排序事件列表
            event_names.sort(key=lambda x: int(x.split(' - ')[0]) if x.split(' - ')[0].isdigit() else float('inf'))
            
            # 保存所有事件名称和对应文件，以便人物联动与筛选
            self.all_event_names = event_names.copy()
            self.available_event_names = event_names.copy()
            self.event_name_to_file = {
                f"{self.event_data[file_path]['id']} - {self.event_data[file_path]['name']}": file_path
                for file_path in self.event_files
            }
            self.refresh_character_options()
            self.event_combo["values"] = [self.EVENT_DEFAULT_SELECTION, *event_names]
            self.event_combo.set(self.EVENT_DEFAULT_SELECTION)
            
            if event_names:
                self.show_empty_state(self.NO_EVENT_TEXT)
                status = (
                    f"已加载{source_name}：{len(self.characters)} 个角色 / "
                    f"{len(event_names)} 个事件"
                )
                if load_errors:
                    status += f"（{len(load_errors)} 个文件读取失败）"
                self.set_status(status)
            else:
                message = "未找到事件数据，请确认游戏目录是否正确"
                self.set_status(f"加载失败：{message}")
                self.show_empty_state("未加载到有效事件")
                self.show_message("加载失败", message, kind="error")

        except Exception as error:
            message = f"读取事件文件时出错：{error}"
            self.set_status(f"加载失败：{message}")
            self.show_empty_state("数据加载失败")
            self.show_message("加载失败", message, kind="error")
        finally:
            self.load_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
    
    def on_event_selected(self, event):
        """当从下拉列表选择事件时调用"""
        selected_event = self.event_combo.get().strip()
        if not selected_event or selected_event == self.EVENT_DEFAULT_SELECTION:
            self.clear_event_display()
            return

        file_path = self.event_name_to_file.get(selected_event)
        if file_path is None:
            return
        event_data = self.event_data[file_path]
        self.current_event = file_path
        self.current_settlement = None
        self.current_detail = None
        description = event_data.get("text") or "当前事件没有事件说明"
        self.set_player_text_content(self.event_desc_text, description)
        self.result_title_var.set("原始脚本")
        self.set_text_content(
            self.result_text,
            json.dumps(event_data, ensure_ascii=False, indent=2),
            "content",
        )
        self.update_condition_lists()
    
    def update_condition_lists(self):
        """更新条件列表"""
        if not self.current_event:
            return
        
        # 清空树形视图
        for item in self.slot_tree.get_children():
            self.slot_tree.delete(item)
        
        for item in self.settlement_tree.get_children():
            self.settlement_tree.delete(item)
        
        event_data = self.event_data[self.current_event]
        comments = self.comments_data.get(self.current_event, {})
        
        # 添加slot条件
        if "cards_slot" in event_data:
            for slot_key, slot_info in event_data["cards_slot"].items():
                if "condition" in slot_info:
                    condition_desc = self.format_condition(slot_info["condition"], comments)
                    slot_text = slot_info.get("text", "")
                    # 显示最多200个字符，避免过长
                    full_text = f"{condition_desc} - {slot_text}"
                    display_text = full_text[:200] + "..." if len(full_text) > 200 else full_text
                    self.slot_tree.insert("", "end", values=(f"s{slot_key}", display_text))
        
        # 整理settlement条件 - 按条件归类
        condition_groups = {}
        
        # 处理settlement
        if "settlement" in event_data:
            for i, settlement in enumerate(event_data["settlement"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("settlement", i, settlement))
        
        # 处理settlement_prior
        if "settlement_prior" in event_data:
            for i, settlement in enumerate(event_data["settlement_prior"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("prior", i, settlement))
        
        # 处理settlement_extre
        if "settlement_extre" in event_data:
            for i, settlement in enumerate(event_data["settlement_extre"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("extre", i, settlement))
        
        # 添加分组后的条件到树中
        group_index = 0
        for condition_key, group in condition_groups.items():
            condition = json.loads(condition_key)
            condition_desc = self.format_condition(condition, comments)
            display_text = condition_desc[:200] + "..." if len(condition_desc) > 200 else condition_desc
            
            # 添加组条目
            group_id = f"group_{group_index}"
            self.settlement_tree.insert("", "end", group_id, values=(f"条件组 {group_index}", display_text))
            
            # 添加组内每个条目
            for item_type, item_index, item in group:
                title = item.get("result_title", "无标题")
                title_display = title[:80] + "..." if len(title) > 80 else title if title else "无标题"
                value_id = f"{item_type}_{item_index}"
                self.settlement_tree.insert(group_id, "end", values=(value_id, title_display))
            
            group_index += 1
                    
        # 修改添加random_text条件的部分
        if "random_text_up" in event_data:
            for key, random_text in event_data["random_text_up"].items():
                if isinstance(random_text, dict) and "text" in random_text:
                    display_text = f"随机文本 {key}: {random_text['text'][:100]}"
                    if len(random_text["text"]) > 100:
                        display_text += "..."
                    self.settlement_tree.insert("", "end", values=(f"random_{key}", display_text))

        if not self.slot_tree.get_children():
            self.slot_tree.insert(
                "", "end", values=("", "当前事件无触发条件"), tags=("empty",)
            )
        if not self.settlement_tree.get_children():
            self.settlement_tree.insert(
                "", "end", values=("", "当前事件无结算条件"), tags=("empty",)
            )

    def display_result_text(self, settlement):
        """显示结果文本，替换玩家名称并添加注释"""
        self.result_text.config(state=tk.NORMAL)
        # 保存当前settlement以便名称变更时更新
        self.current_settlement = settlement
        self.current_detail = None

        # 显示结果标题
        title = settlement.get("result_title", "无标题")
        self.result_title_var.set(title)
        
        # 显示结果文本，替换玩家名称
        result_text = settlement.get("result_text", "无结果文本")
        self.result_text.delete(1.0, tk.END)
        self.insert_player_text(self.result_text, result_text, "content")
        
        # 获取结果文本末尾注释
        comments = self.comments_data.get(self.current_event, {})
        result_text_comment = comments.get("result_text", "")
        if result_text_comment:
            self.result_text.insert(tk.END, f"\n// {result_text_comment}", "content")

        # 附加显示条件详情
        if "condition" in settlement:
            self.result_text.insert(tk.END, "\n\n--- 条件详情 ---\n", "title")
            
            # 获取当前事件的注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 格式化条件并添加注释
            for key, value in settlement["condition"].items():
                # 处理值，将其转换为字符串
                str_value = str(value)
                
                # 构建与注释匹配的键
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"{key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
        
        # 附加显示结果效果
        if "result" in settlement:
            self.result_text.insert(tk.END, "\n\n--- 结果效果 ---\n", "title")
            
            # 获取注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 显示结果并添加注释
            for key, value in settlement["result"].items():
                # 处理值，将其转换为字符串
                str_value = str(value)
                
                # 构建与注释匹配的键
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"{key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
        
        # 附加显示后续行动
        if "action" in settlement:
            self.result_text.insert(tk.END, "\n\n--- 后续行动 ---\n", "title")
            
            # 获取注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 显示行动并添加注释
            for key, value in settlement["action"].items():
                # 处理值，将其转换为字符串
                str_value = str(value)
                
                # 构建与注释匹配的键
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"{key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
        self.result_text.config(state=tk.DISABLED)
    
    def on_slot_selected(self, event):
        """当选择Slot条件时显示相关信息"""
        selected_items = self.slot_tree.selection()
        if not selected_items or not self.current_event:
            return
        
        # 清除settlement树中的选择
        self.settlement_tree.selection_remove(self.settlement_tree.selection())
        
        selected_id = self.slot_tree.item(selected_items[0], "values")[0]
        event_data = self.event_data[self.current_event]
        
        # 获取真正的slot键（去掉's'前缀）
        slot_key = selected_id[1:] if selected_id.startswith("s") else selected_id
        
        if "cards_slot" in event_data and slot_key in event_data["cards_slot"]:
            slot_info = event_data["cards_slot"][slot_key]
            self.result_title_var.set(f"Slot {slot_key}信息")
            self.result_text.config(state=tk.NORMAL)
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "插槽条件用于定义卡牌放置的规则。\n\n")
            
            # 获取注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 显示条件和注释
            self.result_text.insert(tk.END, "--- 条件 ---\n", "title")
            
            if "condition" in slot_info:
                for k, v in slot_info["condition"].items():
                    comment_key = f"{k}:{v}"
                    comment = comments.get(comment_key, comments.get(k, ""))
                    
                    if comment:
                        self.result_text.insert(tk.END, f"{k}: {v}", "content")
                        self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                    else:
                        self.result_text.insert(tk.END, f"{k}: {v}\n", "content")
            
            # 显示其他信息
            self.result_text.insert(tk.END, "\n--- 其他信息 ---\n", "title")
            for k, v in slot_info.items():
                if k != "condition":
                    if k == "pops" and isinstance(v, list):
                        self.result_text.insert(tk.END, f"{k}:\n", "content")
                        self.format_pops_list(v, comments)
                    else:
                        comment_key = f"{k}:{v}"
                        comment = comments.get(comment_key, comments.get(k, ""))
                        
                        if comment:
                            self.result_text.insert(tk.END, f"{k}: {v}", "content")
                            self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                        else:
                            self.result_text.insert(tk.END, f"{k}: {v}\n", "content")
            self.result_text.config(state=tk.DISABLED)
                            
    def format_pops_list(self, pops_list, comments):
        """格式化pops列表，使其更有结构且仅显示关键信息"""
        indent = "    "  # 基本缩进
        
        for i, pop in enumerate(pops_list):
            self.result_text.insert(tk.END, f"{indent}[\n", "content")
            
            # 处理condition部分
            if "condition" in pop:
                self.result_text.insert(tk.END, f"{indent*2}\"condition\": {{\n", "content")
                for k, v in pop["condition"].items():
                    # 保留有意义的条件:
                    # 1. 包含中文字符的键值
                    # 2. 所有类型指示符(type)
                    # 3. 所有ID相关的键值(is, s1.is)
                    # 4. 所有比较运算符(>=, <, >, <=)
                    # 5. 所有否定条件(!xxx)
                    # 6. 所有计数器相关条件(counter.)
                    # 7. 所有状态检查(have.)
                    is_chinese = any('\u4e00' <= char <= '\u9fff' for char in str(k) + str(v))
                    is_key_condition = (k.startswith("!") or 
                                      k.startswith("s1.") or
                                      "counter." in k or
                                      "have." in k or
                                      k in ["type", "is"] or 
                                      k.endswith(">=") or k.endswith("<") or 
                                      k.endswith(">") or k.endswith("<="))
                    
                    if is_chinese or is_key_condition:
                        comment_key = f"{k}:{v}"
                        comment = comments.get(comment_key, comments.get(k, ""))
                        
                        value_str = json.dumps(v, ensure_ascii=False)
                        if comment:
                            self.result_text.insert(tk.END, f"{indent*3}\"{k}\": {value_str}", "content")
                            self.result_text.insert(tk.END, f" // {comment}\n", "comment")
                        else:
                            self.result_text.insert(tk.END, f"{indent*3}\"{k}\": {value_str}\n", "content")
                self.result_text.insert(tk.END, f"{indent*2}}},\n", "content")
            
            # 处理action部分，只保留有解释意义的内容
            if "action" in pop:
                # 检查是否有解释性文本
                has_meaningful_text = False
                text_content = ""
                
                if "choose" in pop["action"] and isinstance(pop["action"]["choose"], dict):
                    for key, value in pop["action"]["choose"].items():
                        if key.startswith("pop.") and isinstance(value, str) and value:
                            has_meaningful_text = True
                            text_content = value
                            break
                
                # 如果没有choose但有直接的pop.xxxx.self值
                elif any(k.startswith("pop.") for k in pop["action"].keys()):
                    for key, value in pop["action"].items():
                        if key.startswith("pop.") and isinstance(value, str) and value:
                            has_meaningful_text = True
                            text_content = value
                            break
                
                # 只展示有意义的解释文本，去掉花括号和引号
                if has_meaningful_text:
                    self.result_text.insert(tk.END, f"{indent*2}\"action\": \"{text_content}\"\n", "content")
            
            self.result_text.insert(tk.END, f"{indent}]\n", "content")
            
            # 添加一个分隔
            if i < len(pops_list) - 1:
                self.result_text.insert(tk.END, "\n", "content")

    def on_settlement_selected(self, event):
        """当选择Settlement条件时显示相关信息"""
        selected_items = self.settlement_tree.selection()
        if not selected_items or not self.current_event:
            return
        
        # 清除slot树中的选择
        self.slot_tree.selection_remove(self.slot_tree.selection())
        
        selected_id = self.settlement_tree.item(selected_items[0], "values")[0]
        event_data = self.event_data[self.current_event]
        
        # 检查是否是组标题
        if selected_id.startswith("条件组 "):
            # 如果选择了组标题，显示此组所有结果的合并
            group_index = int(selected_id.split(" ")[1])
            self.display_group_results(group_index)
            return
        
        if selected_id.startswith("prior_"):
            # 处理settlement_prior条件
            index = int(selected_id.split("_")[1])
            if "settlement_prior" in event_data and 0 <= index < len(event_data["settlement_prior"]):
                settlement = event_data["settlement_prior"][index]
                self.display_result_text(settlement)
        elif selected_id.startswith("extre_"):
            # 处理settlement_extre条件
            index = int(selected_id.split("_")[1])
            if "settlement_extre" in event_data and 0 <= index < len(event_data["settlement_extre"]):
                settlement = event_data["settlement_extre"][index]
                self.display_result_text(settlement)
        elif selected_id.startswith("random_"):
            # 处理random_text条件
            key = selected_id[len("random_"):]
            if "random_text_up" in event_data and key in event_data["random_text_up"]:
                random_text = event_data["random_text_up"][key]
                self.display_random_text(random_text, key)
        elif selected_id.startswith("settlement_"):
            # 处理普通settlement条件
            try:
                index = int(selected_id.split("_")[1])
                if "settlement" in event_data and 0 <= index < len(event_data["settlement"]):
                    settlement = event_data["settlement"][index]
                    self.display_result_text(settlement)
            except (ValueError, IndexError):
                pass
                
    def display_group_results(self, group_index):
        """显示同一条件组下的所有结果文本"""

    
        if not self.current_event:
            return
        
        event_data = self.event_data[self.current_event]
        
        # 重建条件组
        condition_groups = {}
        
        # 处理settlement
        if "settlement" in event_data:
            for i, settlement in enumerate(event_data["settlement"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("settlement", i, settlement))
        
        # 处理settlement_prior
        if "settlement_prior" in event_data:
            for i, settlement in enumerate(event_data["settlement_prior"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("prior", i, settlement))
        
        # 处理settlement_extre
        if "settlement_extre" in event_data:
            for i, settlement in enumerate(event_data["settlement_extre"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("extre", i, settlement))
        
        # 获取指定组索引的组
        if len(condition_groups) <= group_index:
            return
        
        target_group = list(condition_groups.values())[group_index]
        self.current_settlement = None
        self.current_detail = ("group", group_index)

        self.result_title_var.set("结果文本")
        self.result_text.config(state=tk.NORMAL)
        
        # 清空结果区
        self.result_text.delete(1.0, tk.END)
        
        
        
        # 显示所有结果
        for item_type, item_index, item in target_group:
            title = item.get("result_title", "")
            text = item.get("result_text", "")
            
            # 不再显示标记，直接显示标题和文本
            if title:
                self.result_text.insert(tk.END, f"{title}\n", "title")
            
            self.insert_player_text(self.result_text, text, "content")
            self.result_text.insert(tk.END, "\n\n", "content")
            
            # 显示条件详情
            condition = json.loads(list(condition_groups.keys())[group_index])
            self.result_text.insert(tk.END, "--- 条件详情 ---\n", "title")
            comments = self.comments_data.get(self.current_event, {})
            
            for key, value in condition.items():
                str_value = str(value)
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
            
            self.result_text.insert(tk.END, "\n", "content")
            
            # 显示结果效果和后续动作
            if "result" in item and item["result"]:
                self.result_text.insert(tk.END, "--- 结果效果 ---:\n", "title")
                for k, v in item["result"].items():
                    comment = self.comments_data.get(self.current_event, {}).get(f"{k}:{v}", "")
                    if comment:
                        self.result_text.insert(tk.END, f"  {k}: {v} // {comment}\n", "content")
                    else:
                        self.result_text.insert(tk.END, f"  {k}: {v}\n", "content")
                self.result_text.insert(tk.END, "\n")
            
            if "action" in item and item["action"]:
                self.result_text.insert(tk.END, "--- 后续动作 ---:\n", "title")
                for k, v in item["action"].items():
                    comment = self.comments_data.get(self.current_event, {}).get(f"{k}:{v}", "")
                    if comment:
                        self.result_text.insert(tk.END, f"  {k}: {v} // {comment}\n", "content")
                    else:
                        self.result_text.insert(tk.END, f"  {k}: {v}\n", "content")
                self.result_text.insert(tk.END, "\n")
            
            # 添加分隔线
            if target_group.index((item_type, item_index, item)) < len(target_group) - 1:
                self.result_text.insert(tk.END, "—" * 50 + "\n\n", "comment")
        self.result_text.config(state=tk.DISABLED)
            
    def display_random_text(self, random_text, key):
        """显示随机文本信息"""
        self.current_settlement = None
        self.current_detail = ("random", random_text, key)
        self.result_title_var.set(f"随机文本 {key}")
        self.result_text.config(state=tk.NORMAL)
        
        self.result_text.delete(1.0, tk.END)
        
        # 显示随机文本内容
        if isinstance(random_text, dict):
            # 随机文本是字典形式
            if "text" in random_text:
                text = random_text["text"]
                self.insert_player_text(self.result_text, text, "content")
                self.result_text.insert(tk.END, "\n\n", "content")
            
            # 显示其他属性
            for k, v in random_text.items():
                if k != "text":
                    self.result_text.insert(tk.END, f"{k}: {v}\n", "content")
                    # 检查是否有low_target等特殊属性
                    if k == "low_target" or k == "type" or k == "type_tips":
                        self.result_text.insert(tk.END, "\n", "content")
        self.result_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.title("苏丹的游戏 - 事件分支查看器")
            
        app = EventViewer(root)
        root.mainloop()
    except Exception as e:
        import traceback
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"发生错误: {e}\n")
            f.write(traceback.format_exc())
        messagebox.showerror("错误", f"程序发生错误: {e}\n详细错误信息已保存到error_log.txt")

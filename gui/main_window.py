import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, font
import webbrowser
from PIL import Image, ImageTk
from pathlib import Path
from queue import Empty
from logger import logger
from .node_frame import NodeFrame
from .speed_frame import SpeedFrame
from .pz_memory_frame import PZMemoryFrame

def get_resource_path(relative_path):
    """獲取資源文件的路徑，支援打包和非打包環境"""
    import sys
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包環境
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow:
    """主視窗"""
    def __init__(self, root, kcptube_manager, speedtest_manager, pz_manager, config_manager):
        self.root = root
        self.root.title('Minidoracat 伺服器專用優化工具')
        self.root.geometry('800x750')  # 加高視窗以容納更大的間距
        self.root.resizable(True, True)
        
        # 設定全域字體
        self.setup_global_font()
        
        # 設定自定義樣式
        self.setup_custom_styles()
        
        # 儲存管理器實例
        self.kcptube = kcptube_manager
        self.speedtest = speedtest_manager
        self.pz = pz_manager
        self.config_manager = config_manager
        
        # 設定應用程式圖標
        ico_path = get_resource_path('image/app.ico')
        if os.path.exists(ico_path):
            self.root.iconbitmap(ico_path)
        
        # 載入圖片
        self.load_images()
        
        logger.info("啟動器開始運行")
        
        # 註冊視窗關閉事件處理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化 UI
        self.init_ui()
        self.setup_log_monitor()
        
        # 檢查更新
        self.check_updates()
        
        # 自動同步設定檔（延遲執行以確保 UI 已完全載入）
        self.root.after(1000, self.initial_sync)
        
        logger.info("使用者介面初始化完成")
    
    def setup_custom_styles(self):
        """設定自定義樣式"""
        style = ttk.Style()
        
        # 設定重要資訊的樣式（高對比度）
        style.configure('Important.TLabel',
                       foreground='#00FF00',  # 亮綠色
                       font=('Noto Sans TC Medium', 11))
        
        # 設定一般資訊的樣式（柔和色調）
        style.configure('Info.TLabel',
                       foreground='#B0C4DE',  # 淡鋼藍
                       font=('Noto Sans TC Medium', 11))
        
        # 設定提示文字的樣式（淺色）
        style.configure('Tip.TLabel',
                       foreground='#87CEEB',  # 天藍色
                       font=('Noto Sans TC Medium', 11))
        
        # 設定版本資訊的樣式
        style.configure('Version.TLabel',
                       foreground='#FFD700',  # 金黃色
                       font=('Noto Sans TC Medium', 11))
        
        # 設定按鈕樣式
        style.configure('TButton',
                       font=('Noto Sans TC Medium', 11))
        
        # 設定圖標按鈕樣式
        style.configure('Icon.TButton',
                       padding=2)
        
        # 設定標籤框樣式
        style.configure('TLabelframe',
                       background='#2B2B2B')  # 深灰色背景
        
        style.configure('TLabelframe.Label',
                       font=('Noto Sans TC Medium', 11),
                       foreground='#B0C4DE')  # 淡鋼藍色文字
        
        # 設定多行文字的樣式
        style.configure('Multiline.TLabel',
                       wraplength=700,  # 設定文字換行寬度
                       justify='left',  # 文字左對齊
                       padding=(0, 8),  # 增加垂直間距
                       font=('Noto Sans TC Medium', 11),
                       foreground='#87CEEB')  # 使用天藍色
        
        # 設定多行文字的提示樣式
        style.configure('Multiline.Tip.TLabel',
                       wraplength=700,  # 設定文字換行寬度
                       justify='left',  # 文字左對齊
                       padding=(0, 8),  # 增加垂直間距
                       font=('Noto Sans TC Medium', 11),
                       foreground='#87CEEB')  # 使用天藍色
    
    def setup_global_font(self):
        """設定全域字體"""
        try:
            # 載入 Medium 字重的字體
            font_path = get_resource_path(os.path.join('fonts', 'Noto_Sans_TC', 'static', 'NotoSansTC-Medium.ttf'))
            
            if os.path.exists(font_path):
                # 載入字體到系統
                self.root.tk.call('font', 'create', 'NotoSansTC', '-family', 'Noto Sans TC Medium')
                self.root.tk.call('font', 'configure', 'NotoSansTC', '-size', 11)
                
                # 設定全域字體
                style = ttk.Style()
                default_font = ('Noto Sans TC Medium', 11)
                
                # 設定所有 ttk 元件的預設字體
                style.configure('.', font=default_font)
                
                # 設定特定元件的字體
                style.configure('TLabel', font=default_font)
                style.configure('TButton', font=default_font)
                style.configure('TNotebook.Tab', font=default_font)
                style.configure('TLabelframe.Label', font=default_font)
                style.configure('Treeview', font=default_font)
                style.configure('Treeview.Heading', font=(default_font[0], default_font[1], 'bold'))
                
                # 設定下拉選單和其他特殊元件的字體
                self.root.option_add('*TCombobox*Listbox.font', default_font)
                self.root.option_add('*Text.font', default_font)
                self.root.option_add('*Entry.font', default_font)
                self.root.option_add('*Button.font', default_font)
                self.root.option_add('*Label.font', default_font)
                
                # 設定對話框字體
                self.root.option_add('*Dialog.msg.font', default_font)
                self.root.option_add('*Dialog.msg.tk.font', default_font)
                
                # 設定選單字體
                self.root.option_add('*Menu.font', default_font)
                
                # 設定訊息框字體
                self.root.option_add('*MessageBox.message.font', default_font)
                self.root.option_add('*MessageBox.button.font', default_font)
                
                logger.info("成功載入 Noto Sans TC Medium 字體")
            else:
                logger.warning("找不到字體檔案，使用系統預設字體")
        except Exception as e:
            logger.error(f"載入字體時發生錯誤: {str(e)}")
    
    def initial_sync(self):
        """初始同步設定檔"""
        try:
            logger.info("正在執行初始同步...")
            self.config_manager.sync_configs(force=False)  # 只在首次啟動時同步
            self.node_frame.load_nodes()  # 重新載入節點列表
            logger.info("初始同步完成")
        except Exception as e:
            logger.error(f"初始同步失敗: {str(e)}")
            messagebox.showerror('錯誤', '初始同步失敗，請檢查網路連接')
    
    def load_images(self):
        """載入圖片"""
        # GitHub 圖標
        github_path = get_resource_path('image/github.png')
        if os.path.exists(github_path):
            github_img = Image.open(github_path)
            github_img = github_img.resize((24, 24), Image.Resampling.LANCZOS)  # 增加圖標大小
            self.github_icon = ImageTk.PhotoImage(github_img)
        else:
            self.github_icon = None
            logger.warning("找不到 GitHub 圖標")
        
        # Discord 圖標
        discord_path = get_resource_path('image/discord.png')
        if os.path.exists(discord_path):
            discord_img = Image.open(discord_path)
            discord_img = discord_img.resize((24, 24), Image.Resampling.LANCZOS)  # 增加圖標大小
            self.discord_icon = ImageTk.PhotoImage(discord_img)
        else:
            self.discord_icon = None
            logger.warning("找不到 Discord 圖標")

    def init_ui(self):
        """初始化使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 頂部工具列
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=X, pady=(0, 20))
        
        # 版本資訊（左側）
        self.version_label = ttk.Label(
            toolbar,
            text="正在載入版本資訊...",
            style='Version.TLabel'
        )
        self.version_label.pack(side=LEFT)
        
        # 社群連結（右側）
        links_frame = ttk.Frame(toolbar)
        links_frame.pack(side=RIGHT)
        
        # GitHub 連結
        if self.github_icon:
            github_button = ttk.Button(
                links_frame,
                image=self.github_icon,
                text="下載最新版本",
                compound=LEFT,  # 圖標在左側
                command=lambda: webbrowser.open('https://github.com/Minidoracat/minidoracat_server_launch/releases'),
                style='info-outline',
                cursor="hand2",
                padding=(10, 5)  # 增加內部間距
            )
            github_button.pack(side=LEFT, padx=(0, 10))
        
        # Discord 連結
        if self.discord_icon:
            discord_button = ttk.Button(
                links_frame,
                image=self.discord_icon,
                text="加入 Discord 社群",
                compound=LEFT,  # 圖標在左側
                command=lambda: webbrowser.open('https://discord.gg/Gur2V67'),
                style='info-outline',
                cursor="hand2",
                padding=(10, 5)  # 增加內部間距
            )
            discord_button.pack(side=LEFT)
        
        # 中間區域 - 使用 Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=YES, pady=(0, 20))
        
        # 節點設定頁面
        self.node_frame = NodeFrame(notebook, self.kcptube, self.config_manager)
        notebook.add(self.node_frame, text="節點設定")
        
        # 速度設定頁面
        self.speed_frame = SpeedFrame(notebook, self.speedtest, self.config_manager)  # 傳入 config_manager
        notebook.add(self.speed_frame, text="速度設定")
        
        # 綁定速度設定更新事件
        self.speed_frame.bind('<<SpeedSettingsUpdated>>', lambda e: self.node_frame.on_node_selected(None))
        
        # Project Zomboid 記憶體設定頁面
        self.pz_frame = PZMemoryFrame(notebook, self.pz)
        notebook.add(self.pz_frame, text="PZ 記憶體設定")
        
        # 日誌區域
        log_frame = ttk.Labelframe(main_frame, text="系統日誌", padding=10)
        log_frame.pack(fill=BOTH, expand=YES)
        
        # 建立日誌容器框架
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 日誌文字框 - 使用等寬字體
        self.log_text = ttk.Text(
            log_container,
            wrap=NONE,  # 禁用自動換行
            font=('Cascadia Code', 10),
            height=10,
            spacing1=2,  # 設定行前間距
            spacing2=2,  # 設定行間間距
            spacing3=2   # 設定行後間距
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # 垂直捲軸
        v_scrollbar = ttk.Scrollbar(log_container, orient=VERTICAL, command=self.log_text.yview)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 水平捲軸
        h_scrollbar = ttk.Scrollbar(log_frame, orient=HORIZONTAL, command=self.log_text.xview)
        h_scrollbar.pack(fill=X)
        
        # 設定捲軸
        self.log_text.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # 創建工具提示標籤
        self.tooltip = ttk.Label(
            self.root,
            style='Tip.TLabel',
            background='#2B2B2B',
            relief='solid',
            borderwidth=1
        )
    
    def show_tooltip(self, event, text):
        """顯示工具提示"""
        widget = event.widget
        x = widget.winfo_rootx() + widget.winfo_width() // 2
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        
        self.tooltip['text'] = text
        self.tooltip.place(x=x, y=y, anchor='n')
    
    def hide_tooltip(self, event=None):
        """隱藏工具提示"""
        self.tooltip.place_forget()
    
    def setup_log_monitor(self):
        """設置日誌監控"""
        def check_log_queue():
            # 檢查佇列中的新日誌
            try:
                while True:
                    record = logger.get_gui_queue().get_nowait()
                    msg = self.format_log_message(record)
                    self.log_text.insert(END, msg + '\n')
                    self.log_text.see(END)  # 自動滾動到最新的日誌
                    
                    # 根據日誌等級設定顏色
                    tag = f"level_{record.levelname}"
                    last_line = f"{self.log_text.get('end-2c linestart', 'end-1c')}\n"
                    self.log_text.tag_add(tag, f"end-{len(last_line)}c", "end-1c")
            except Empty:
                pass
            finally:
                # 每 100ms 檢查一次佇列
                self.root.after(100, check_log_queue)
        
        # 設定不同日誌等級的顏色（高對比度）
        self.log_text.tag_config('level_ERROR', foreground='#FF4040')    # 亮紅色
        self.log_text.tag_config('level_WARNING', foreground='#FFD700')  # 金黃色
        self.log_text.tag_config('level_INFO', foreground='#98FB98')     # 淺綠色
        self.log_text.tag_config('level_DEBUG', foreground='#87CEEB')    # 天藍色
        
        # 開始監控
        check_log_queue()
    
    def format_log_message(self, record):
        """格式化日誌訊息"""
        return f"{record.asctime} [{record.levelname}] {record.message}"
    
    def update_version_info(self):
        """更新版本資訊顯示"""
        version_info = self.kcptube.version_manager.get_version_info()
        
        # 使用 version_manager 提供的版本文字
        self.version_label['text'] = version_info['version_text']
        
        # 如果有更新，顯示提醒
        if version_info['has_launcher_update'] or version_info['has_kcptube_update']:
            update_items = []
            if version_info['has_launcher_update']:
                update_items.append("啟動器")
            if version_info['has_kcptube_update']:
                update_items.append("KCPTube")
            
            messagebox.showinfo(
                '發現更新',
                f"發現新版本可用：{' 和 '.join(update_items)}，請至 GitHub 下載更新。"
            )
    
    def check_updates(self):
        """檢查更新"""
        self.update_version_info()
    
    def on_closing(self):
        """視窗關閉事件處理"""
        try:
            # 先停止 KCPTube
            if self.kcptube.process:
                logger.info("視窗關閉，正在停止 KCPTube...")
                self.kcptube.stop_kcptube()
            
            # 然後關閉視窗
            logger.info("正在關閉啟動器...")
            self.root.destroy()
        except Exception as e:
            logger.error(f"關閉程式時發生錯誤: {str(e)}")
            self.root.destroy()

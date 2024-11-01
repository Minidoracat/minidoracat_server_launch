import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
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
    def __init__(self, root, kcptube_manager, speedtest_manager, pz_manager):
        self.root = root
        self.root.title('Minidoracat 伺服器專用優化工具')
        self.root.geometry('800x700')  # 加寬視窗
        self.root.resizable(True, True)
        
        # 儲存管理器實例
        self.kcptube = kcptube_manager
        self.speedtest = speedtest_manager
        self.pz = pz_manager
        
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
    
    def initial_sync(self):
        """初始同步設定檔"""
        try:
            logger.info("正在執行初始同步...")
            self.kcptube.sync_configs(force=False)  # 只在首次啟動時同步
            self.node_frame.load_nodes()  # 重新載入節點列表
            logger.info("初始同步完成")
        except Exception as e:
            logger.error(f"初始同步失敗: {str(e)}")
            messagebox.showerror('錯誤', '初始同步失敗，請檢查網路連接')
    
    def sync_configs(self):
        """手動同步設定檔"""
        logger.info("正在同步設定檔...")
        try:
            self.kcptube.sync_configs(force=True)  # 強制同步
            self.node_frame.load_nodes()  # 重新載入節點列表
            logger.info("設定檔同步完成")
        except Exception as e:
            logger.error(f"同步設定檔失敗: {str(e)}")
            messagebox.showerror('錯誤', '同步設定檔失敗，請檢查網路連接')
    
    def load_images(self):
        """載入圖片"""
        # GitHub 圖標
        github_path = get_resource_path('image/github.png')
        if os.path.exists(github_path):
            github_img = Image.open(github_path)
            github_img = github_img.resize((16, 16), Image.Resampling.LANCZOS)
            self.github_icon = ImageTk.PhotoImage(github_img)
        else:
            self.github_icon = None
            logger.warning("找不到 GitHub 圖標")
        
        # Discord 圖標
        discord_path = get_resource_path('image/discord.png')
        if os.path.exists(discord_path):
            discord_img = Image.open(discord_path)
            discord_img = discord_img.resize((16, 16), Image.Resampling.LANCZOS)
            self.discord_icon = ImageTk.PhotoImage(discord_img)
        else:
            self.discord_icon = None
            logger.warning("找不到 Discord 圖標")
    
    def init_ui(self):
        """初始化使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 頂部區域
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 20))
        
        # 版本資訊（左側）
        version_frame = ttk.Frame(top_frame)
        version_frame.pack(side=LEFT, fill=X, expand=YES)
        
        self.version_label = ttk.Label(
            version_frame,
            text="正在載入版本資訊...",
            style='info'
        )
        self.version_label.pack(side=LEFT)
        
        # 更新按鈕（右側）
        self.sync_button = ttk.Button(
            top_frame,
            text='下載節點設定',
            command=self.sync_configs,
            style='info-outline',
            width=15
        )
        self.sync_button.pack(side=RIGHT)
        
        # 連結區域
        links_frame = ttk.Frame(main_frame)
        links_frame.pack(fill=X, pady=(0, 20))
        
        # GitHub 連結
        github_frame = ttk.Frame(links_frame)
        github_frame.pack(side=LEFT, padx=(0, 20))
        
        if self.github_icon:
            github_icon_label = ttk.Label(
                github_frame,
                image=self.github_icon
            )
            github_icon_label.pack(side=LEFT, padx=(0, 5))
        
        github_label = ttk.Label(
            github_frame,
            text="下載最新版本",
            style='info',
            cursor="hand2"
        )
        github_label.pack(side=LEFT)
        github_label.bind('<Button-1>', lambda e: webbrowser.open('https://github.com/Minidoracat/minidoracat_server_launch/releases'))
        
        # Discord 連結
        discord_frame = ttk.Frame(links_frame)
        discord_frame.pack(side=LEFT)
        
        if self.discord_icon:
            discord_icon_label = ttk.Label(
                discord_frame,
                image=self.discord_icon
            )
            discord_icon_label.pack(side=LEFT, padx=(0, 5))
        
        discord_label = ttk.Label(
            discord_frame,
            text="加入 Discord 社群",
            style='info',
            cursor="hand2"
        )
        discord_label.pack(side=LEFT)
        discord_label.bind('<Button-1>', lambda e: webbrowser.open('https://discord.gg/Gur2V67'))
        
        # 中間區域 - 使用 Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=YES, pady=(0, 20))
        
        # 節點設定頁面
        self.node_frame = NodeFrame(notebook, self.kcptube)
        notebook.add(self.node_frame, text="節點設定")
        
        # 速度設定頁面
        self.speed_frame = SpeedFrame(notebook, self.speedtest)
        notebook.add(self.speed_frame, text="速度設定")
        
        # 綁定速度設定更新事件
        self.speed_frame.bind('<<SpeedSettingsUpdated>>', lambda e: self.node_frame.on_node_selected(None))
        
        # Project Zomboid 記憶體設定頁面
        self.pz_frame = PZMemoryFrame(notebook, self.pz)
        notebook.add(self.pz_frame, text="PZ 記憶體設定")
        
        # 日誌區域
        log_frame = ttk.Labelframe(main_frame, text="系統日誌", padding=15)
        log_frame.pack(fill=BOTH, expand=YES)
        
        # 建立日誌容器框架
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=BOTH, expand=YES)
        
        # 日誌文字框
        self.log_text = ttk.Text(
            log_container,
            wrap=NONE,  # 禁用自動換行
            font=('Consolas', 9),
            height=10
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
        
        # 設定不同日誌等級的顏色
        self.log_text.tag_config('level_ERROR', foreground='red')
        self.log_text.tag_config('level_WARNING', foreground='orange')
        self.log_text.tag_config('level_INFO', foreground='white')
        self.log_text.tag_config('level_DEBUG', foreground='gray')
        
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

import sys
import os
import json
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime
from queue import Empty
from pathlib import Path
import re
import webbrowser
from PIL import Image, ImageTk
from logger import logger
from version_manager import VersionManager
from kcptube_manager import KCPTubeManager
from speed_test_manager import SpeedTestManager

def get_resource_path(relative_path):
    """獲取資源文件的路徑，支援打包和非打包環境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包環境
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow:
    """主視窗"""
    def __init__(self, root):
        self.root = root
        self.root.title('Minidoracat 伺服器專用優化工具')
        self.root.geometry('800x700')  # 加寬視窗
        self.root.resizable(True, True)
        
        # 設定應用程式圖標
        ico_path = get_resource_path('image/app.ico')
        if os.path.exists(ico_path):
            self.root.iconbitmap(ico_path)
        
        # 載入圖片
        self.load_images()
        
        logger.info("啟動器開始運行")
        
        # 初始化管理器
        self.kcptube = KCPTubeManager()
        self.speedtest = SpeedTestManager()
        
        # 註冊視窗關閉事件處理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.init_ui()
        self.setup_log_monitor()
        
        # 同步設定檔
        self.sync_configs()
        
        # 載入速度設定
        self.load_speed_settings()
        
        # 檢查更新
        self.check_updates()
        
        logger.info("使用者介面初始化完成")
    
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
        
        # 節點頁面
        node_frame = ttk.Frame(notebook, padding=15)
        notebook.add(node_frame, text="節點設定")
        
        # 節點選擇
        node_select_frame = ttk.Frame(node_frame)
        node_select_frame.pack(fill=X, pady=(0, 10))
        
        self.node_combo = ttk.Combobox(
            node_select_frame,
            state='readonly',
            font=('微軟正黑體', 10),
            width=30
        )
        self.node_combo.pack(side=LEFT, padx=(0, 15))
        self.node_combo.bind('<<ComboboxSelected>>', self.on_node_selected)
        
        # 節點資訊
        node_info_frame = ttk.Frame(node_frame)
        node_info_frame.pack(fill=X, pady=(0, 10))
        
        self.node_speed_label = ttk.Label(
            node_info_frame,
            text="節點速度設定: 未選擇",
            style='info'
        )
        self.node_speed_label.pack(side=LEFT)
        
        self.node_connect_label = ttk.Label(
            node_info_frame,
            text="連線資訊: 未選擇",
            style='info'
        )
        self.node_connect_label.pack(side=RIGHT)

        # 速度設定提示
        speed_tip_frame = ttk.Frame(node_frame)
        speed_tip_frame.pack(fill=X, pady=(0, 10))
        
        speed_tip_label = ttk.Label(
            speed_tip_frame,
            text="提示：您可以在「速度設定」頁面測試或設定網路頻寬。本工具使用頻寬設定來優化連線，降低延遲並提升穩定性，建議依據您的實際網路頻寬進行設定。",
            style='info',
            wraplength=700  # 設定文字換行寬度
        )
        speed_tip_label.pack(fill=X)
        
        # 控制按鈕
        control_frame = ttk.Frame(node_frame)
        control_frame.pack(fill=X, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame,
            text='啟動加速',
            command=self.start_service,
            style='success',
            width=15
        )
        self.start_button.pack(side=LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            control_frame,
            text='停止加速',
            command=self.stop_service,
            state='disabled',
            style='danger-outline',
            width=15
        )
        self.stop_button.pack(side=LEFT)
        
        self.status_label = ttk.Label(
            control_frame,
            text='狀態: 未啟動',
            style='info'
        )
        self.status_label.pack(side=RIGHT)
        
        # 速度設定頁面
        speed_frame = ttk.Frame(notebook, padding=15)
        notebook.add(speed_frame, text="速度設定")
        
        # 速度輸入區域
        speed_input_frame = ttk.Frame(speed_frame)
        speed_input_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            speed_input_frame,
            text="下載速度 (M):",
            style='info'
        ).pack(side=LEFT, padx=(0, 5))
        
        self.download_speed_var = tk.StringVar()
        self.download_speed_entry = ttk.Entry(
            speed_input_frame,
            textvariable=self.download_speed_var,
            width=10,
            font=('微軟正黑體', 10)
        )
        self.download_speed_entry.pack(side=LEFT, padx=(0, 20))
        
        ttk.Label(
            speed_input_frame,
            text="上傳速度 (M):",
            style='info'
        ).pack(side=LEFT, padx=(0, 5))
        
        self.upload_speed_var = tk.StringVar()
        self.upload_speed_entry = ttk.Entry(
            speed_input_frame,
            textvariable=self.upload_speed_var,
            width=10,
            font=('微軟正黑體', 10)
        )
        self.upload_speed_entry.pack(side=LEFT)
        
        # 自動套用選項
        self.auto_apply_var = tk.BooleanVar()
        self.auto_apply_checkbox = ttk.Checkbutton(
            speed_frame,
            text="自動套用速度設定到節點",
            variable=self.auto_apply_var,
            command=self.on_auto_apply_changed,
            style='round-toggle'
        )
        self.auto_apply_checkbox.pack(fill=X, pady=10)
        
        # 速度控制按鈕
        speed_control_frame = ttk.Frame(speed_frame)
        speed_control_frame.pack(fill=X)
        
        self.apply_speed_button = ttk.Button(
            speed_control_frame,
            text="套用設定到節點",
            command=self.apply_speed_settings,
            style='primary-outline',
            width=15
        )
        self.apply_speed_button.pack(side=LEFT, padx=(0, 10))
        
        self.speedtest_button = ttk.Button(
            speed_control_frame,
            text="測試網路速度",
            command=self.start_speedtest,
            style='info-outline',
            width=15
        )
        self.speedtest_button.pack(side=LEFT)
        
        self.speed_info_label = ttk.Label(
            speed_control_frame,
            text="目前未設定速度",
            style='info'
        )
        self.speed_info_label.pack(side=RIGHT)
        
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
        
        # 載入節點列表
        self.load_nodes()
    
    def get_node_speeds(self, config_path):
        """讀取節點的速度設定"""
        try:
            content = Path(config_path).read_text(encoding='utf-8')
            
            # 使用正則表達式找到速度設定
            inbound_match = re.search(r'inbound_bandwidth=(\d+)M', content)
            outbound_match = re.search(r'outbound_bandwidth=(\d+)M', content)
            
            inbound = int(inbound_match.group(1)) if inbound_match else 0
            outbound = int(outbound_match.group(1)) if outbound_match else 0
            
            return inbound, outbound
        except Exception as e:
            logger.error(f"讀取節點速度設定失敗: {str(e)}")
            return 0, 0
    
    def get_node_info(self, config_path):
        """讀取節點的設定資訊"""
        try:
            content = Path(config_path).read_text(encoding='utf-8')
            
            # 使用正則表達式找到設定
            inbound_match = re.search(r'inbound_bandwidth=(\d+)M', content)
            outbound_match = re.search(r'outbound_bandwidth=(\d+)M', content)
            port_match = re.search(r'listen_port=(\d+)', content)
            
            inbound = int(inbound_match.group(1)) if inbound_match else 0
            outbound = int(outbound_match.group(1)) if outbound_match else 0
            port = port_match.group(1) if port_match else "未知"
            
            return {
                'inbound': inbound,
                'outbound': outbound,
                'port': port
            }
        except Exception as e:
            logger.error(f"讀取節點設定失敗: {str(e)}")
            return {
                'inbound': 0,
                'outbound': 0,
                'port': "未知"
            }
    
    def on_node_selected(self, event):
        """當選擇節點時更新顯示"""
        selected = self.node_combo.get()
        if selected:
            config_path = self.node_configs.get(selected)
            info = self.get_node_info(config_path)
            
            # 更新節點速度資訊
            self.node_speed_label['text'] = (
                f"節點速度設定: 下載 {info['inbound']}M | "
                f"上傳 {info['outbound']}M"
            )
            
            # 更新節點連線資訊
            self.node_connect_label['text'] = (
                f"連線資訊 - IP地址: 127.0.0.1 | "
                f"端口: {info['port']}"
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
    
    def load_nodes(self):
        """載入節點列表"""
        conf_dir = Path("conf")
        self.node_configs = {}
        
        if conf_dir.exists():
            for file in conf_dir.glob("*.conf"):
                name = file.stem
                self.node_configs[name] = str(file)
                logger.debug(f"找到節點設定檔: {name} -> {file}")
            
            if self.node_configs:
                self.node_combo['values'] = list(self.node_configs.keys())
                self.node_combo.current(0)
                # 觸發節點選擇事件來更新顯示
                self.on_node_selected(None)
                logger.info(f"載入了 {len(self.node_configs)} 個節點設定")
            else:
                logger.warning("未找到任何節點設定檔")
    
    def on_auto_apply_changed(self):
        """當自動套用勾選框狀態改變時"""
        enabled = self.auto_apply_var.get()
        self.speedtest.set_auto_apply(enabled)
        if enabled:
            self.apply_speed_button['state'] = 'disabled'
            logger.info("已啟用自動套用速度設定到節點")
        else:
            self.apply_speed_button['state'] = 'normal'
            logger.info("已停用自動套用速度設定到節點")
            
    def load_speed_settings(self):
        """載入速度設定"""
        speeds = self.speedtest.get_current_speeds()
        self.download_speed_var.set(str(int(speeds['download_speed'])))
        self.upload_speed_var.set(str(int(speeds['upload_speed'])))
        self.auto_apply_var.set(speeds['auto_apply'])
        
        # 根據自動套用設定更新按鈕狀態
        if speeds['auto_apply']:
            self.apply_speed_button['state'] = 'disabled'
        else:
            self.apply_speed_button['state'] = 'normal'
        
        self.update_speed_info()
    
    def update_speed_info(self):
        """更新速度資訊顯示"""
        speeds = self.speedtest.get_current_speeds()
        mode = "手動設定" if speeds['manual_mode'] else "自動測試"
        last_test = speeds.get('last_test', '從未測試')
        auto_apply = "自動套用已啟用" if speeds['auto_apply'] else "自動套用已停用"
        self.speed_info_label['text'] = (
            f"目前速度設定 ({mode}):\n"
            f"下載: {int(speeds['download_speed'])}M | "
            f"上傳: {int(speeds['upload_speed'])}M\n"
            f"最後更新: {last_test}\n"
            f"{auto_apply}"
        )
    
    def apply_speed_settings(self):
        """套用速度設定"""
        try:
            download = float(self.download_speed_var.get())
            upload = float(self.upload_speed_var.get())
            
            if download <= 0 or upload <= 0:
                raise ValueError("速度必須大於 0")
            
            self.speedtest.set_manual_speeds(download, upload)
            self.update_speed_info()
            
            # 更新設定檔
            if self.speedtest.update_conf_files():
                messagebox.showinfo('成功', '速度設定已更新')
                # 更新節點速度顯示
                self.on_node_selected(None)
            else:
                messagebox.showwarning('警告', '速度設定已儲存，但更新設定檔時發生錯誤')
        except ValueError as e:
            messagebox.showerror('錯誤', '請輸入有效的數字')
    
    def start_speedtest(self):
        """開始速度測試"""
        if self.speedtest.is_running():
            logger.warning("速度測試已在進行中")
            return
        
        def on_test_complete(result):
            """速度測試完成的回調函數"""
            self.download_speed_var.set(str(int(result['download_speed'])))
            self.upload_speed_var.set(str(int(result['upload_speed'])))
            self.update_speed_info()
            
            # 如果啟用了自動套用，則更新設定檔
            if self.auto_apply_var.get():
                if self.speedtest.update_conf_files():
                    messagebox.showinfo('成功', '速度測試完成並已更新設定')
                    # 更新節點速度顯示
                    self.on_node_selected(None)
                else:
                    messagebox.showwarning('警告', '速度測試完成，但更新設定檔時發生錯誤')
            else:
                messagebox.showinfo('成功', '速度測試完成')
            
            self.speedtest_button['text'] = '測試網路速度'
            self.speedtest_button['state'] = 'normal'
        
        self.speedtest_button['text'] = '測試中...'
        self.speedtest_button['state'] = 'disabled'
        self.speed_info_label['text'] = '正在進行速度測試，請稍候...'
        
        self.speedtest.start_test(on_test_complete)
    
    def start_service(self):
        """啟動服務"""
        selected = self.node_combo.get()
        if not selected:
            logger.warning("未選擇節點就嘗試啟動")
            messagebox.showwarning('錯誤', '請選擇節點')
            return
            
        logger.info(f"嘗試啟動節點: {selected}")
        config_path = self.node_configs.get(selected)
        if self.kcptube.start_kcptube(config_path):
            self.status_label['text'] = '狀態: 運行中'
            self.start_button['state'] = 'disabled'
            self.stop_button['state'] = 'normal'
            self.sync_button['state'] = 'disabled'
            logger.info(f"節點 {selected} 啟動成功")
        else:
            logger.error(f"節點 {selected} 啟動失敗")
            messagebox.showwarning('錯誤', '啟動失敗')
    
    def stop_service(self):
        """停止服務"""
        logger.info("嘗試停止服務")
        if self.kcptube.stop_kcptube():
            self.status_label['text'] = '狀態: 已停止'
            self.start_button['state'] = 'normal'
            self.stop_button['state'] = 'disabled'
            self.sync_button['state'] = 'normal'
            logger.info("服務已停止")
    
    def sync_configs(self):
        """同步設定檔"""
        logger.info("正在同步設定檔...")
        try:
            self.kcptube.sync_configs()
            self.load_nodes()  # 重新載入節點列表
            logger.info("設定檔同步完成")
        except Exception as e:
            logger.error(f"同步設定檔失敗: {str(e)}")
            messagebox.showerror('錯誤', '同步設定檔失敗，請檢查網路連接')
    
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

if __name__ == '__main__':
    try:
        root = ttk.Window(themename="superhero")
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程式啟動失敗: {str(e)}")
        sys.exit(1)

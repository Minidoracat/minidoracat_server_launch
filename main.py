import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from queue import Empty
from pathlib import Path
import re
import webbrowser
from logger import logger
from version_manager import VersionManager
from kcptube_manager import KCPTubeManager
from speed_test_manager import SpeedTestManager

class MainWindow:
    """主視窗"""
    def __init__(self, root):
        self.root = root
        self.root.title('KCPTube 遊戲加速器')
        self.root.geometry('800x700')  # 加寬視窗
        self.root.resizable(True, True)
        
        # 設定主題色彩
        self.colors = {
            'bg': '#1E1E1E',           # 深色背景
            'button': '#3C4043',       # 按鈕背景
            'button_hover': '#4E5255', # 按鈕懸停
            'text': '#FFFFFF',         # 文字
            'accent': '#007AFF',       # 強調色
            'error': '#FF3B30',        # 錯誤
            'success': '#34C759',      # 成功
            'warning': '#FF9500',      # 警告
            'link': '#58A6FF'          # 連結顏色
        }
        
        # 設定根視窗背景
        self.root.configure(bg=self.colors['bg'])
        
        logger.info("啟動器開始運行")
        
        # 初始化管理器
        self.kcptube = KCPTubeManager()
        self.speedtest = SpeedTestManager()
        
        self.init_ui()
        self.setup_log_monitor()
        
        # 同步設定檔
        self.sync_configs()
        
        # 載入速度設定
        self.load_speed_settings()
        
        # 檢查更新
        self.check_updates()
        
        logger.info("使用者介面初始化完成")
    
    def init_ui(self):
        """初始化使用者介面"""
        # 設定全局樣式
        style = ttk.Style()
        style.theme_use('default')
        
        # 配置樣式
        style.configure('Main.TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['button'])
        style.configure(
            'Custom.TButton',
            background=self.colors['button'],
            foreground=self.colors['text'],
            font=('微軟正黑體', 10),
            padding=5
        )
        style.configure(
            'Action.TButton',
            background=self.colors['accent'],
            foreground=self.colors['text'],
            font=('微軟正黑體', 10, 'bold'),
            padding=5
        )
        style.configure(
            'Custom.TLabel',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=('微軟正黑體', 10)
        )
        style.configure(
            'Title.TLabel',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=('微軟正黑體', 12, 'bold')
        )
        style.configure(
            'Link.TLabel',
            background=self.colors['bg'],
            foreground=self.colors['link'],
            font=('微軟正黑體', 10, 'underline'),
            cursor='hand2'
        )
        style.configure(
            'Card.TLabelframe',
            background=self.colors['button'],
            foreground=self.colors['text']
        )
        style.configure(
            'Card.TLabelframe.Label',
            background=self.colors['button'],
            foreground=self.colors['text'],
            font=('微軟正黑體', 10, 'bold')
        )
        
        # 主框架
        main_frame = ttk.Frame(self.root, style='Main.TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 頂部區域
        top_frame = ttk.Frame(main_frame, style='Main.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 版本資訊（左側）
        version_frame = ttk.Frame(top_frame, style='Main.TFrame')
        version_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.version_label = ttk.Label(
            version_frame,
            text="正在載入版本資訊...",
            style='Custom.TLabel'
        )
        self.version_label.pack(side=tk.LEFT)
        
        # 更新按鈕（右側）
        self.sync_button = ttk.Button(
            top_frame,
            text='下載節點設定',
            command=self.sync_configs,
            style='Custom.TButton',
            width=15
        )
        self.sync_button.pack(side=tk.RIGHT)
        
        # 連結區域
        links_frame = ttk.Frame(main_frame, style='Main.TFrame')
        links_frame.pack(fill=tk.X, pady=(0, 20))
        
        # GitHub 連結
        github_label = ttk.Label(
            links_frame,
            text="下載最新版本",
            style='Link.TLabel',
            cursor='hand2'
        )
        github_label.pack(side=tk.LEFT, padx=(0, 20))
        github_label.bind('<Button-1>', lambda e: webbrowser.open('https://github.com/Minidoracat/kcptube_launch/releases'))
        
        # Discord 連結
        discord_label = ttk.Label(
            links_frame,
            text="加入 Discord 社群",
            style='Link.TLabel',
            cursor='hand2'
        )
        discord_label.pack(side=tk.LEFT)
        discord_label.bind('<Button-1>', lambda e: webbrowser.open('https://discord.gg/Gur2V67'))
        
        # 中間區域
        middle_frame = ttk.Frame(main_frame, style='Main.TFrame')
        middle_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 節點選擇區域
        node_frame = ttk.LabelFrame(
            middle_frame,
            text="節點選擇",
            style='Card.TLabelframe',
            padding="10"
        )
        node_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 節點選擇上半部
        node_top_frame = ttk.Frame(node_frame, style='Card.TFrame')
        node_top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 節點下拉選單
        self.node_combo = ttk.Combobox(
            node_top_frame,
            state='readonly',
            font=('微軟正黑體', 10),
            width=30
        )
        self.node_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.node_combo.bind('<<ComboboxSelected>>', self.on_node_selected)
        
        # 節點資訊顯示區域
        node_info_frame = ttk.Frame(node_frame, style='Card.TFrame')
        node_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 節點速度資訊
        self.node_speed_label = ttk.Label(
            node_info_frame,
            text="節點速度設定: 未選擇",
            style='Custom.TLabel'
        )
        self.node_speed_label.pack(side=tk.LEFT)
        
        # 節點連線資訊
        self.node_connect_label = ttk.Label(
            node_info_frame,
            text="連線資訊: 未選擇",
            style='Custom.TLabel'
        )
        self.node_connect_label.pack(side=tk.RIGHT)
        
        # 節點選擇下半部
        node_bottom_frame = ttk.Frame(node_frame, style='Card.TFrame')
        node_bottom_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 啟動按鈕
        self.start_button = ttk.Button(
            node_bottom_frame,
            text='啟動加速',
            command=self.start_service,
            style='Action.TButton',
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 停止按鈕
        self.stop_button = ttk.Button(
            node_bottom_frame,
            text='停止加速',
            command=self.stop_service,
            state='disabled',
            style='Custom.TButton',
            width=15
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # 狀態顯示
        self.status_label = ttk.Label(
            node_bottom_frame,
            text='狀態: 未啟動',
            style='Custom.TLabel'
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # 速度設定區域
        speed_frame = ttk.LabelFrame(
            middle_frame,
            text="網路速度設定",
            style='Card.TLabelframe',
            padding="10"
        )
        speed_frame.pack(fill=tk.X)
        
        # 速度設定上半部
        speed_top_frame = ttk.Frame(speed_frame, style='Card.TFrame')
        speed_top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 下載速度設定
        ttk.Label(
            speed_top_frame,
            text="下載速度 (M):",
            style='Custom.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.download_speed_var = tk.StringVar()
        self.download_speed_entry = ttk.Entry(
            speed_top_frame,
            textvariable=self.download_speed_var,
            width=10,
            font=('微軟正黑體', 10)
        )
        self.download_speed_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 上傳速度設定
        ttk.Label(
            speed_top_frame,
            text="上傳速度 (M):",
            style='Custom.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.upload_speed_var = tk.StringVar()
        self.upload_speed_entry = ttk.Entry(
            speed_top_frame,
            textvariable=self.upload_speed_var,
            width=10,
            font=('微軟正黑體', 10)
        )
        self.upload_speed_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 速度設定下半部
        speed_bottom_frame = ttk.Frame(speed_frame, style='Card.TFrame')
        speed_bottom_frame.pack(fill=tk.X)
        
        # 設定按鈕
        self.apply_speed_button = ttk.Button(
            speed_bottom_frame,
            text="套用設定到節點",
            command=self.apply_speed_settings,
            style='Custom.TButton',
            width=15
        )
        self.apply_speed_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 速度測試按鈕
        self.speedtest_button = ttk.Button(
            speed_bottom_frame,
            text="測試網路速度",
            command=self.start_speedtest,
            style='Custom.TButton',
            width=15
        )
        self.speedtest_button.pack(side=tk.LEFT)
        
        # 速度資訊顯示
        self.speed_info_label = ttk.Label(
            speed_bottom_frame,
            text="目前未設定速度",
            style='Custom.TLabel'
        )
        self.speed_info_label.pack(side=tk.RIGHT)
        
        # 日誌顯示區
        log_frame = ttk.LabelFrame(
            main_frame,
            text="系統日誌",
            style='Card.TLabelframe',
            padding="10"
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日誌文字框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            background='#2D2D2D',
            foreground='#FFFFFF',
            insertbackground='#FFFFFF'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
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
                    self.log_text.insert(tk.END, msg + '\n')
                    self.log_text.see(tk.END)  # 自動滾動到最新的日誌
                    
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
        self.log_text.tag_config('level_ERROR', foreground=self.colors['error'])
        self.log_text.tag_config('level_WARNING', foreground=self.colors['warning'])
        self.log_text.tag_config('level_INFO', foreground=self.colors['text'])
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
    
    def load_speed_settings(self):
        """載入速度設定"""
        speeds = self.speedtest.get_current_speeds()
        self.download_speed_var.set(str(int(speeds['download_speed'])))
        self.upload_speed_var.set(str(int(speeds['upload_speed'])))
        self.update_speed_info()
    
    def update_speed_info(self):
        """更新速度資訊顯示"""
        speeds = self.speedtest.get_current_speeds()
        mode = "手動設定" if speeds['manual_mode'] else "自動測試"
        last_test = speeds.get('last_test', '從未測試')
        self.speed_info_label['text'] = (
            f"目前速度設定 ({mode}):\n"
            f"下載: {int(speeds['download_speed'])}M | "
            f"上傳: {int(speeds['upload_speed'])}M\n"
            f"最後更新: {last_test}"
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
            
            # 更新設定檔
            if self.speedtest.update_conf_files():
                messagebox.showinfo('成功', '速度測試完成並已更新設定')
                # 更新節點速度顯示
                self.on_node_selected(None)
            else:
                messagebox.showwarning('警告', '速度測試完成，但更新設定檔時發生錯誤')
            
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
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程式啟動失敗: {str(e)}")
        sys.exit(1)

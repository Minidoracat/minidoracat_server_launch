import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import re
from pathlib import Path
from .base_frame import BaseFrame
from logger import logger

class NodeFrame(BaseFrame):
    """節點設定頁面"""
    def __init__(self, master, kcptube_manager, config_manager, **kwargs):
        self.kcptube = kcptube_manager
        self.config_manager = config_manager
        self.node_configs = {}
        super().__init__(master, padding=20, **kwargs)  # 增加內部邊距
    
    def init_ui(self):
        """初始化節點設定頁面"""
        # 節點選擇區域
        node_select_frame = ttk.Frame(self)
        node_select_frame.pack(fill=X, pady=(0, 15))  # 增加與下方元件的間距
        
        # 左側：節點選擇
        select_container = ttk.Frame(node_select_frame)
        select_container.pack(side=LEFT)
        
        ttk.Label(
            select_container,
            text="選擇節點:",
            style='Info.TLabel'
        ).pack(side=LEFT, padx=(0, 8))  # 增加標籤與下拉選單的間距
        
        self.node_combo = ttk.Combobox(
            select_container,
            state='readonly',
            width=30
        )
        self.node_combo.pack(side=LEFT)
        self.node_combo.bind('<<ComboboxSelected>>', self.on_node_selected)
        
        # 右側：下載節點設定按鈕
        self.sync_button = ttk.Button(
            node_select_frame,
            text='下載節點設定',
            command=self.sync_configs,
            style='info-outline',
            width=15
        )
        self.sync_button.pack(side=RIGHT)
        
        # 節點資訊
        node_info_frame = ttk.Frame(self)
        node_info_frame.pack(fill=X, pady=(0, 20))  # 增加與下方元件的間距
        
        self.node_speed_label = ttk.Label(
            node_info_frame,
            text="節點速度設定: 未選擇",
            style='Important.TLabel'  # 使用重要資訊樣式
        )
        self.node_speed_label.pack(side=LEFT)
        
        self.node_connect_label = ttk.Label(
            node_info_frame,
            text="連線資訊: 未選擇",
            style='Important.TLabel'  # 使用重要資訊樣式
        )
        self.node_connect_label.pack(side=RIGHT)
        
        # 節點控制區域
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=X, pady=(0, 15))  # 增加與下方元件的間距
        
        # 狀態顯示
        self.status_label = ttk.Label(
            control_frame,
            text='狀態: 未啟動',
            style='Important.TLabel'  # 使用重要資訊樣式
        )
        self.status_label.pack(side=LEFT)
        
        # 控制按鈕（右側）
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=RIGHT)
        
        self.start_button = ttk.Button(
            button_frame,
            text='啟動加速',
            command=self.start_service,
            style='success',
            width=15
        )
        self.start_button.pack(side=LEFT, padx=(0, 15))  # 增加按鈕之間的間距
        
        self.stop_button = ttk.Button(
            button_frame,
            text='停止加速',
            command=self.stop_service,
            state='disabled',
            style='danger-outline',
            width=15
        )
        self.stop_button.pack(side=LEFT)
        
        # 速度設定提示
        tip_frame = ttk.Frame(self)
        tip_frame.pack(fill=X, pady=(0, 15))  # 增加與下方元件的間距
        
        tip_label = ttk.Label(
            tip_frame,
            text="提示：您可以在「速度設定」頁面測試或設定網路頻寬。本工具使用頻寬設定來優化連線，降低延遲並提升穩定性，建議依據您的實際網路頻寬進行設定。",
            style='Multiline.Tip.TLabel'  # 使用多行文字提示樣式
        )
        tip_label.pack(fill=X)
        
        # 載入節點列表
        self.load_nodes()
    
    def sync_configs(self):
        """同步節點設定"""
        logger.info("正在同步設定檔...")
        try:
            self.config_manager.sync_configs(force=True)  # 強制同步
            self.load_nodes()  # 重新載入節點列表
            logger.info("設定檔同步完成")
            messagebox.showinfo('成功', '節點設定已更新')
        except Exception as e:
            logger.error(f"同步設定檔失敗: {str(e)}")
            messagebox.showerror('錯誤', '同步設定檔失敗，請檢查網路連接')
    
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
                # 獲取節點列表
                nodes = list(self.node_configs.keys())
                self.node_combo['values'] = nodes
                
                # 嘗試選擇上次使用的節點
                selected_node = self.config_manager.get_selected_node()
                if selected_node and selected_node in nodes:
                    self.node_combo.set(selected_node)
                else:
                    # 如果沒有上次使用的節點或節點不存在，選擇第一個
                    self.node_combo.current(0)
                
                # 觸發節點選擇事件來更新顯示
                self.on_node_selected(None)
                logger.info(f"載入了 {len(self.node_configs)} 個節點設定")
            else:
                logger.warning("未找到任何節點設定檔")
    
    def on_node_selected(self, event):
        """當選擇節點時更新顯示"""
        selected = self.node_combo.get()
        if selected:
            # 儲存選擇的節點
            self.config_manager.set_selected_node(selected)
            
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
            logger.info("服務已停止")

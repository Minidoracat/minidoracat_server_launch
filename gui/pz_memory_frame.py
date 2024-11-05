import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from .base_frame import BaseFrame
from logger import logger

class PZMemoryFrame(BaseFrame):
    """Project Zomboid 記憶體設定頁面"""
    def __init__(self, master, pz_manager, **kwargs):
        self.pz = pz_manager
        super().__init__(master, padding=20, **kwargs)  # 增加內部邊距
        
        # 檢查是否使用預設值
        current_memory = self.pz.get_current_memory_setting()
        if current_memory == 3:  # 如果是預設的 3GB
            self.after(1000, self.show_default_memory_warning)  # 延遲 1 秒顯示警告
    
    def init_ui(self):
        """初始化記憶體設定頁面"""
        # 系統資訊區域
        system_frame = ttk.Frame(self)
        system_frame.pack(fill=X, pady=(0, 20))  # 增加與下方元件的間距
        
        self.system_memory_label = ttk.Label(
            system_frame,
            text=f"系統記憶體: {self.pz.get_system_memory()}GB",
            style='Important.TLabel'  # 使用重要資訊樣式
        )
        self.system_memory_label.pack(side=LEFT)
        
        # 當前設定區域
        current_frame = ttk.Frame(self)
        current_frame.pack(fill=X, pady=(0, 20))  # 增加與下方元件的間距
        
        current_memory = self.pz.get_current_memory_setting()
        current_text = f"當前遊戲記憶體設定: {int(current_memory)}GB" if current_memory else "當前遊戲記憶體設定: 預設值 (3GB)"
        self.current_memory_label = ttk.Label(
            current_frame,
            text=current_text,
            style='Important.TLabel'  # 使用重要資訊樣式
        )
        self.current_memory_label.pack(side=LEFT)
        
        # 建議設定區域
        recommend_frame = ttk.Frame(self)
        recommend_frame.pack(fill=X, pady=(0, 25))  # 增加與下方元件的間距
        
        recommended_memory = self.pz.get_recommended_memory()
        description = self.pz.get_memory_recommendation_description()
        self.recommend_memory_label = ttk.Label(
            recommend_frame,
            text=f"建議遊戲記憶體設定: {recommended_memory}GB\n{description}",
            style='Important.TLabel',  # 使用重要資訊樣式
            justify='left'  # 文字左對齊
        )
        self.recommend_memory_label.pack(side=LEFT)
        
        # 記憶體設定控制區域
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=X, pady=(0, 20))  # 增加與下方元件的間距
        
        # 記憶體大小輸入
        input_frame = ttk.Frame(control_frame)
        input_frame.pack(side=LEFT)
        
        ttk.Label(
            input_frame,
            text="記憶體大小 (GB):",
            style='Info.TLabel'
        ).pack(side=LEFT, padx=(0, 8))  # 增加標籤與輸入框的間距
        
        self.memory_size_var = tk.StringVar(value=str(int(current_memory) if current_memory else 3))
        self.memory_size_entry = ttk.Entry(
            input_frame,
            textvariable=self.memory_size_var,
            width=10
        )
        self.memory_size_entry.pack(side=LEFT, padx=(0, 15))  # 增加與按鈕的間距
        
        # 控制按鈕
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=LEFT)
        
        self.apply_memory_button = ttk.Button(
            button_frame,
            text="套用設定",
            command=self.apply_memory_setting,
            style='primary-outline',
            width=15
        )
        self.apply_memory_button.pack(side=LEFT, padx=(0, 15))  # 增加按鈕之間的間距
        
        self.use_recommended_button = ttk.Button(
            button_frame,
            text="使用建議值",
            command=self.use_recommended_memory,
            style='info-outline',
            width=15
        )
        self.use_recommended_button.pack(side=LEFT)
        
        # 記憶體設定提示
        tip_frame = ttk.Frame(self)
        tip_frame.pack(fill=X, pady=(20, 0))  # 增加與上方元件的間距
        
        tip_label = ttk.Label(
            tip_frame,
            text="提示：記憶體設定會影響遊戲的運行效能，過低的設定可能導致遊戲卡頓，特別是在使用大量模組時。但設定過高也可能影響系統穩定性，建議根據您的實際系統配置選擇合適的值。",
            style='Multiline.Tip.TLabel'  # 使用多行文字提示樣式
        )
        tip_label.pack(fill=X)
    
    def show_default_memory_warning(self):
        """顯示預設記憶體警告"""
        recommended = self.pz.get_recommended_memory()
        description = self.pz.get_memory_recommendation_description()
        messagebox.showwarning(
            '記憶體設定建議',
            '檢測到您正在使用預設的記憶體設定（3GB）。\n\n'
            '為了獲得更好的遊戲體驗，特別是在使用大量模組時，'
            '建議您根據系統配置調整記憶體設定。\n\n'
            f'根據您的系統配置 {description}\n'
            f'建議設定為 {recommended}GB。'
        )
    
    def apply_memory_setting(self):
        """套用記憶體設定"""
        try:
            size = float(self.memory_size_var.get())
            if size <= 0:
                raise ValueError("記憶體大小必須大於 0")
            
            # 檢查是否超過系統記憶體
            system_mem = self.pz.get_system_memory()
            if size > system_mem:
                if not messagebox.askyesno('警告', 
                    f'設定的記憶體大小 ({int(size)}GB) 超過系統總記憶體 ({system_mem}GB)，'
                    '這可能會導致系統不穩定。確定要繼續嗎？'):
                    return
            
            # 檢查是否超過建議的最大值
            max_recommended = self.pz.get_max_recommended_memory()
            if size > max_recommended:
                if not messagebox.askyesno('警告',
                    f'設定的記憶體大小 ({int(size)}GB) 超過建議的最大值 ({max_recommended}GB)，'
                    '這可能會影響系統的穩定性。\n\n'
                    '建議至少保留 20% 的系統記憶體給作業系統使用。\n\n'
                    '確定要繼續嗎？'):
                    return
            
            if self.pz.update_memory_setting(size):
                messagebox.showinfo('成功', f'已將遊戲記憶體設定更新為 {int(size)}GB')
                # 更新顯示
                self.current_memory_label['text'] = f"當前遊戲記憶體設定: {int(size)}GB"
            else:
                messagebox.showerror('錯誤', '更新記憶體設定失敗')
        except ValueError:
            messagebox.showerror('錯誤', '請輸入有效的數字')
    
    def use_recommended_memory(self):
        """使用建議的記憶體設定"""
        recommended = self.pz.get_recommended_memory()
        self.memory_size_var.set(str(recommended))
        self.apply_memory_setting()

import os
import json
import psutil
import winreg
from pathlib import Path
from logger import logger

class ProjectZomboidManager:
    """Project Zomboid 管理器"""
    
    def __init__(self):
        self.steam_path = self._get_steam_path()
        self.pz_path = self._get_pz_path() if self.steam_path else None
        self.config_path = os.path.join(self.pz_path, "ProjectZomboid64.json") if self.pz_path else None
    
    def _get_steam_path(self):
        """從註冊表獲取 Steam 安裝路徑"""
        try:
            # 嘗試從註冊表讀取 Steam 安裝路徑
            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam")
            steam_path = winreg.QueryValueEx(hkey, "InstallPath")[0]
            winreg.CloseKey(hkey)
            
            logger.info(f"從註冊表找到 Steam 路徑: {steam_path}")
            return steam_path
        except Exception as e:
            logger.error(f"從註冊表讀取 Steam 路徑失敗: {str(e)}")
            return None
    
    def _get_pz_path(self):
        """尋找 Project Zomboid 安裝路徑"""
        try:
            # 從 Steam 的 libraryfolders.vdf 讀取所有遊戲庫位置
            vdf_path = os.path.join(self.steam_path, "steamapps", "libraryfolders.vdf")
            library_folders = [self.steam_path]  # 預設 Steam 安裝路徑
            
            if os.path.exists(vdf_path):
                with open(vdf_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 使用簡單的解析來找到路徑
                import re
                paths = re.findall(r'"path"\s*"([^"]+)"', content)
                library_folders.extend([p.replace('\\\\', '\\') for p in paths])
            
            # 在所有遊戲庫中尋找 Project Zomboid
            for library in library_folders:
                pz_path = os.path.join(library, "steamapps", "common", "ProjectZomboid")
                if os.path.exists(pz_path):
                    logger.info(f"找到 Project Zomboid 路徑: {pz_path}")
                    return pz_path
            
            logger.warning("未找到 Project Zomboid 路徑")
            return None
            
        except Exception as e:
            logger.error(f"尋找 Project Zomboid 路徑失敗: {str(e)}")
            return None
    
    def get_system_memory(self):
        """獲取系統記憶體大小（GB）"""
        try:
            return round(psutil.virtual_memory().total / (1024**3))
        except:
            return 0
    
    def get_current_memory_setting(self):
        """獲取當前記憶體設定"""
        try:
            if not self.config_path or not os.path.exists(self.config_path):
                return None
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            for arg in config.get('vmArgs', []):
                if arg.startswith('-Xmx'):
                    # 將 -Xmx3072m 或 -Xmx3g 轉換為 GB
                    value = arg[4:-1]  # 去掉 -Xmx 和最後的單位
                    if arg.endswith('g'):
                        return int(float(value))  # 確保返回整數
                    else:  # 假設是 m
                        return round(float(value) / 1024)  # 轉換為 GB 並四捨五入為整數
            return None
        except Exception as e:
            logger.error(f"讀取記憶體設定失敗: {str(e)}")
            return None
    
    def get_max_recommended_memory(self):
        """獲取最大建議記憶體值（系統記憶體減去20%）"""
        system_mem = self.get_system_memory()
        return int(system_mem * 0.8)  # 保留20%給系統
    
    def get_recommended_memory(self):
        """獲取建議的記憶體設定"""
        system_mem = self.get_system_memory()
        
        # 動態計算建議值：
        # 1. 保留系統記憶體的 20% 給系統和其他程式
        # 2. 如果系統記憶體小於 8GB，則保留 2GB
        # 3. 最小值 3GB，最大值 24GB
        if system_mem <= 8:
            available_mem = system_mem - 2  # 保留 2GB
        else:
            available_mem = system_mem * 0.8  # 保留 20%
        
        # 四捨五入到最接近的整數
        recommended = round(available_mem)
        
        # 確保在合理範圍內
        if recommended < 3:
            return 3
        elif recommended > 24:
            return 24
        
        return recommended
    
    def get_memory_recommendation_description(self):
        """獲取記憶體建議值的說明"""
        system_mem = self.get_system_memory()
        if system_mem <= 8:
            return f"（系統記憶體 {system_mem}GB，保留 2GB 給系統使用）"
        else:
            reserved = int(system_mem * 0.2)
            return f"（系統記憶體 {system_mem}GB，保留 {reserved}GB (20%) 給系統使用）"
    
    def update_memory_setting(self, size_gb):
        """更新記憶體設定
        
        Args:
            size_gb (int/float): 記憶體大小（GB）
        
        Returns:
            bool: 是否更新成功
        """
        try:
            if not self.config_path or not os.path.exists(self.config_path):
                logger.error("找不到設定檔")
                return False
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 確保記憶體大小為整數
            size_gb = int(round(float(size_gb)))
            
            # 更新或添加記憶體設定
            new_args = []
            memory_set = False
            for arg in config.get('vmArgs', []):
                if arg.startswith('-Xmx'):
                    new_args.append(f'-Xmx{size_gb}g')
                    memory_set = True
                else:
                    new_args.append(arg)
            
            if not memory_set:
                new_args.append(f'-Xmx{size_gb}g')
            
            config['vmArgs'] = new_args
            
            # 寫入設定檔
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent='\t')
            
            logger.info(f"已更新記憶體設定為 {size_gb}GB")
            return True
            
        except Exception as e:
            logger.error(f"更新記憶體設定失敗: {str(e)}")
            return False

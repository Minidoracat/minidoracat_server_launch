import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path
from logger import logger

class VersionManager:
    """版本管理類"""
    def __init__(self):
        self.version_file = Path('version.json')
        self.local_versions = self._load_local_versions()
        self.remote_versions = None  # 初始化時不載入遠端版本
        self._update_version_text()  # 先更新本地版本顯示
    
    def _load_local_versions(self):
        """載入本地版本資訊"""
        try:
            # 如果本地檔案不存在，嘗試從打包資源建立
            if not self.version_file.exists() and getattr(sys, 'frozen', False):
                try:
                    # 獲取執行檔所在目錄
                    if hasattr(sys, '_MEIPASS'):
                        base_path = Path(sys._MEIPASS)
                    else:
                        base_path = Path(sys.executable).parent
                    
                    # 從資源中讀取版本資訊
                    version_path = base_path / 'version.json'
                    if version_path.exists():
                        versions = json.loads(version_path.read_text(encoding='utf-8'))
                        logger.info("從執行檔中載入版本資訊")
                        
                        # 將版本資訊寫入本地檔案
                        self.version_file.write_text(
                            json.dumps(versions, indent=4, ensure_ascii=False),
                            encoding='utf-8'
                        )
                        logger.info("已將版本資訊寫入本地檔案")
                        return versions
                except Exception as e:
                    logger.error(f"從執行檔載入版本資訊失敗: {str(e)}")
            
            # 從本地檔案讀取
            if self.version_file.exists():
                versions = json.loads(self.version_file.read_text(encoding='utf-8'))
                logger.info("從本地檔案載入版本資訊")
                return versions
            
            logger.warning("找不到版本資訊檔案")
        except Exception as e:
            logger.error(f"讀取版本資訊失敗: {str(e)}")
        
        # 如果都無法讀取，返回 unknown
        return {
            "launcher_version": "unknown",
            "kcptube_version": "unknown",
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _load_remote_versions(self):
        """從 GitHub 載入遠端版本資訊"""
        try:
            url = "https://raw.githubusercontent.com/Minidoracat/minidoracat_server_launch/main/version.json"
            logger.info(f"正在從 {url} 下載版本資訊...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            versions = response.json()
            logger.info("成功載入遠端版本資訊")
            return versions
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
                logger.error("找不到遠端版本資訊檔案")
            else:
                logger.error(f"載入遠端版本資訊失敗: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"處理遠端版本資訊時發生錯誤: {str(e)}")
            return None
    
    def _check_updates(self):
        """檢查更新"""
        if not self.remote_versions:
            logger.warning("無法檢查更新：無法取得遠端版本資訊")
            return
        
        try:
            local_launcher = self.local_versions.get('launcher_version', '0.0.0')
            remote_launcher = self.remote_versions.get('launcher_version', '0.0.0')
            
            local_kcptube = self.local_versions.get('kcptube_version', '0.0.0')
            remote_kcptube = self.remote_versions.get('kcptube_version', '0.0.0')
            
            self.has_launcher_update = self._compare_versions(local_launcher, remote_launcher)
            self.has_kcptube_update = self._compare_versions(local_kcptube, remote_kcptube)
            
            if self.has_launcher_update:
                logger.info(f"發現啟動器新版本: {remote_launcher} (目前版本: {local_launcher})")
            if self.has_kcptube_update:
                logger.info(f"發現 KCPTube 新版本: {remote_kcptube} (目前版本: {local_kcptube})")
        except Exception as e:
            logger.error(f"檢查更新時發生錯誤: {str(e)}")
    
    def _compare_versions(self, local_ver, remote_ver):
        """比較版本號"""
        try:
            if local_ver == "unknown" or remote_ver == "unknown":
                return False
            
            # 將版本號分割為數字列表
            local_parts = [int(x) for x in local_ver.split('.')]
            remote_parts = [int(x) for x in remote_ver.split('.')]
            
            # 確保兩個列表長度相同
            while len(local_parts) < len(remote_parts):
                local_parts.append(0)
            while len(remote_parts) < len(local_parts):
                remote_parts.append(0)
            
            # 比較每個部分
            for local, remote in zip(local_parts, remote_parts):
                if remote > local:
                    return True
                if local > remote:
                    return False
            return False
        except Exception:
            return False
    
    def _update_version_text(self):
        """更新版本顯示文字"""
        local_launcher = self.local_versions.get('launcher_version', 'unknown')
        local_kcptube = self.local_versions.get('kcptube_version', 'unknown')
        
        if self.remote_versions:
            remote_launcher = self.remote_versions.get('launcher_version', 'unknown')
            remote_kcptube = self.remote_versions.get('kcptube_version', 'unknown')
            self.version_text = (
                f"本機版本 - 啟動器: {local_launcher} | "
                f"KCPTube: {local_kcptube}\n"
                f"最新版本 - 啟動器: {remote_launcher} | "
                f"KCPTube: {remote_kcptube}"
            )
        else:
            self.version_text = (
                f"本機版本 - 啟動器: {local_launcher} | "
                f"KCPTube: {local_kcptube}"
            )
    
    def get_version_info(self):
        """獲取版本資訊"""
        # 檢查遠端版本
        if self.remote_versions is None:
            self.remote_versions = self._load_remote_versions()
            if self.remote_versions:
                self._check_updates()
            self._update_version_text()
        
        return {
            'local_launcher': self.local_versions.get('launcher_version', 'unknown'),
            'local_kcptube': self.local_versions.get('kcptube_version', 'unknown'),
            'remote_launcher': self.remote_versions.get('launcher_version', 'unknown') if self.remote_versions else 'unknown',
            'remote_kcptube': self.remote_versions.get('kcptube_version', 'unknown') if self.remote_versions else 'unknown',
            'has_launcher_update': getattr(self, 'has_launcher_update', False),
            'has_kcptube_update': getattr(self, 'has_kcptube_update', False),
            'version_text': self.version_text
        }
    
    @property
    def launcher_version(self):
        """取得啟動器版本"""
        return self.local_versions.get('launcher_version', 'unknown')
    
    @property
    def kcptube_version(self):
        """取得 KCPTube 版本"""
        return self.local_versions.get('kcptube_version', 'unknown')

import json
import requests
from datetime import datetime
from pathlib import Path
from logger import logger

class VersionManager:
    """版本管理類"""
    def __init__(self):
        self.version_file = Path('version.json')
        self.local_versions = self._load_local_versions()
        self.remote_versions = self._load_remote_versions()
        self._check_updates()
    
    def _load_local_versions(self):
        """載入本地版本資訊"""
        try:
            if self.version_file.exists():
                versions = json.loads(self.version_file.read_text(encoding='utf-8'))
                logger.info("成功載入本地版本資訊")
                return versions
        except Exception as e:
            logger.error(f"讀取本地版本資訊失敗: {str(e)}")
        
        return {
            "launcher_version": "unknown",
            "kcptube_version": "unknown",
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _load_remote_versions(self):
        """從 GitHub 載入遠端版本資訊"""
        try:
            url = "https://raw.githubusercontent.com/Minidoracat/kcptube_launch/main/version.json"
            response = requests.get(url)
            response.raise_for_status()
            
            versions = response.json()
            logger.info("成功載入遠端版本資訊")
            return versions
        except Exception as e:
            logger.error(f"載入遠端版本資訊失敗: {str(e)}")
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
            
            if self.has_launcher_update or self.has_kcptube_update:
                logger.info("發現新版本可用")
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
    
    def get_version_info(self):
        """獲取版本資訊"""
        local_launcher = self.local_versions.get('launcher_version', 'unknown')
        local_kcptube = self.local_versions.get('kcptube_version', 'unknown')
        remote_launcher = self.remote_versions.get('launcher_version', 'unknown') if self.remote_versions else 'unknown'
        remote_kcptube = self.remote_versions.get('kcptube_version', 'unknown') if self.remote_versions else 'unknown'
        
        return {
            'local_launcher': local_launcher,
            'local_kcptube': local_kcptube,
            'remote_launcher': remote_launcher,
            'remote_kcptube': remote_kcptube,
            'has_launcher_update': getattr(self, 'has_launcher_update', False),
            'has_kcptube_update': getattr(self, 'has_kcptube_update', False)
        }
    
    @property
    def launcher_version(self):
        """取得啟動器版本"""
        return self.local_versions.get('launcher_version', 'unknown')
    
    @property
    def kcptube_version(self):
        """取得 KCPTube 版本"""
        return self.local_versions.get('kcptube_version', 'unknown')

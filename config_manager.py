import os
import requests
import logging
from pathlib import Path

class ConfigManager:
    """設定檔管理類"""
    def __init__(self, github_user, github_repo):
        self.github_user = github_user
        self.github_repo = github_repo
        self.base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main"
        self.conf_dir = Path("conf")
        self.ensure_conf_dir()
    
    def ensure_conf_dir(self):
        """確保設定檔目錄存在"""
        self.conf_dir.mkdir(exist_ok=True)
    
    def download_config(self, filename):
        """下載設定檔"""
        url = f"{self.base_url}/conf/{filename}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            config_path = self.conf_dir / filename
            with open(config_path, "wb") as f:
                f.write(response.content)
            
            logging.info(f"成功下載設定檔：{filename}")
            return True
        except Exception as e:
            logging.error(f"下載設定檔失敗 {filename}: {str(e)}")
            return False
    
    def list_remote_configs(self):
        """列出遠端可用的設定檔"""
        try:
            # 使用 GitHub API 獲取檔案列表
            api_url = f"https://api.github.com/repos/{self.github_user}/{self.github_repo}/contents/conf"
            response = requests.get(api_url)
            response.raise_for_status()
            
            configs = []
            for item in response.json():
                if item["name"].endswith(".conf"):
                    configs.append(item["name"])
            
            return configs
        except Exception as e:
            logging.error(f"獲取遠端設定檔列表失敗: {str(e)}")
            return []
    
    def sync_configs(self):
        """同步設定檔"""
        remote_configs = self.list_remote_configs()
        local_configs = [f.name for f in self.conf_dir.glob("*.conf")]
        
        # 下載新的設定檔
        for config in remote_configs:
            if config not in local_configs:
                self.download_config(config)
        
        return [f for f in self.conf_dir.glob("*.conf")]
    
    def get_config_path(self, config_name):
        """獲取設定檔路徑"""
        return str(self.conf_dir / config_name)

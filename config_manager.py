import os
import json
import requests
from pathlib import Path
from urllib.parse import quote
from logger import logger

class ConfigManager:
    """設定檔管理類"""
    def __init__(self, github_user, github_repo):
        self.github_user = github_user
        self.github_repo = github_repo
        self.base_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main"
        self.conf_dir = Path("conf")
        self.config_file = Path("config.json")
        self.ensure_conf_dir()
        self._load_config()
    
    def ensure_conf_dir(self):
        """確保設定檔目錄存在"""
        self.conf_dir.mkdir(exist_ok=True)
        logger.debug("確保設定檔目錄存在: conf/")
    
    def _load_config(self):
        """載入 config.json 設定檔"""
        default_config = {
            "speed_test": {
                "download_speed": 0,
                "upload_speed": 0,
                "last_test": None,
                "manual_mode": False,
                "auto_apply": False
            },
            "node": {
                "selected": ""  # 選擇的節點名稱
            }
        }
        
        try:
            if self.config_file.exists():
                # 讀取現有設定
                current_config = json.loads(self.config_file.read_text(encoding='utf-8'))
                
                # 合併設定，保留現有設定，但確保所有必要的欄位都存在
                self.config = default_config.copy()
                if 'speed_test' in current_config:
                    self.config['speed_test'].update(current_config['speed_test'])
                if 'node' in current_config:
                    self.config['node'].update(current_config['node'])
                
                logger.info("成功載入設定檔")
            else:
                self.config = default_config
                self._save_config()
                logger.info("建立新的設定檔")
        except Exception as e:
            logger.error(f"載入設定檔失敗: {str(e)}")
            self.config = default_config
    
    def _save_config(self):
        """儲存 config.json 設定檔"""
        try:
            # 確保速度值為整數
            if 'speed_test' in self.config:
                self.config['speed_test']['download_speed'] = int(self.config['speed_test']['download_speed'])
                self.config['speed_test']['upload_speed'] = int(self.config['speed_test']['upload_speed'])
            
            self.config_file.write_text(
                json.dumps(self.config, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.info("成功儲存設定檔")
            return True
        except Exception as e:
            logger.error(f"儲存設定檔失敗: {str(e)}")
            return False
    
    # 節點相關方法
    def get_selected_node(self):
        """獲取選擇的節點名稱"""
        return self.config['node'].get('selected', '')
    
    def set_selected_node(self, node_name):
        """設定選擇的節點名稱"""
        self.config['node']['selected'] = node_name
        self._save_config()
    
    # 速度測試相關方法
    def get_speed_settings(self):
        """獲取速度設定"""
        return self.config.get('speed_test', {})
    
    def set_speed_settings(self, settings):
        """設定速度設定"""
        self.config['speed_test'].update(settings)
        self._save_config()
    
    def set_auto_apply(self, enabled):
        """設定是否自動套用到節點設定"""
        self.config['speed_test']['auto_apply'] = enabled
        self._save_config()
    
    def is_auto_apply_enabled(self):
        """檢查是否啟用自動套用"""
        return self.config['speed_test'].get('auto_apply', False)
    
    # 節點設定檔管理方法
    def is_first_launch(self):
        """檢查是否是首次啟動"""
        return not any(self.conf_dir.glob("*.conf"))
    
    def remove_legacy_configs(self):
        """刪除指定的舊設定檔"""
        legacy_configs = [
            "PZ_Server_2.conf",
            "PZ#1服.conf",
            "PZ#3服.conf"
        ]
        
        removed_count = 0
        for config in legacy_configs:
            config_path = self.conf_dir / config
            if config_path.exists():
                try:
                    config_path.unlink()
                    logger.info(f"已刪除舊的設定檔: {config}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"刪除設定檔失敗 {config}: {str(e)}")
        
        if removed_count > 0:
            logger.info(f"共刪除 {removed_count} 個舊設定檔")
        return removed_count
    
    def download_config(self, filename):
        """下載設定檔，總是覆蓋本地檔案"""
        # URL 編碼檔案名稱，但保留斜線
        encoded_filename = quote(filename)
        url = f"{self.base_url}/conf/{encoded_filename}"
        
        try:
            logger.info(f"正在下載設定檔：{filename}")
            logger.debug(f"下載 URL: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            config_path = self.conf_dir / filename
            config_path.write_bytes(response.content)
            
            logger.info(f"成功下載設定檔：{filename}")
            return True
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
                logger.error(f"找不到設定檔 {filename}，URL: {url}")
            else:
                logger.error(f"下載設定檔失敗 {filename}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"處理設定檔時發生錯誤 {filename}: {str(e)}")
            return False
    
    def list_remote_configs(self):
        """列出遠端可用的設定檔"""
        try:
            logger.info("正在獲取遠端設定檔列表...")
            # 使用 GitHub API 獲取檔案列表
            api_url = f"https://api.github.com/repos/{self.github_user}/{self.github_repo}/contents/conf"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            configs = []
            for item in response.json():
                if item["type"] == "file" and item["name"].endswith(".conf"):
                    configs.append(item["name"])
            
            if configs:
                logger.info(f"找到 {len(configs)} 個遠端設定檔: {', '.join(configs)}")
            else:
                logger.warning("未找到任何遠端設定檔")
            
            return configs
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
                logger.error("找不到設定檔目錄，請確認倉庫設定")
            else:
                logger.error(f"獲取遠端設定檔列表失敗: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"處理遠端設定檔列表時發生錯誤: {str(e)}")
            return []
    
    def sync_configs(self, force=False):
        """同步設定檔，總是覆蓋本地檔案
        
        Args:
            force (bool): 是否強制同步，即使不是首次啟動
        """
        try:
            # 如果不是首次啟動且不是強制同步，則跳過
            if not force and not self.is_first_launch():
                logger.info("非首次啟動，跳過自動同步設定檔")
                return []
            
            # 獲取遠端設定檔列表
            remote_configs = self.list_remote_configs()
            if not remote_configs:
                return []
            
            # 下載所有設定檔，無論是否已存在
            success_count = 0
            for config in remote_configs:
                if self.download_config(config):
                    success_count += 1
            
            if success_count > 0:
                logger.info(f"成功下載 {success_count} 個設定檔")
            elif remote_configs:
                logger.info("所有設定檔都是最新的")
            
            # 返回更新後的設定檔列表
            return [f for f in self.conf_dir.glob("*.conf")]
        except Exception as e:
            logger.error(f"同步設定檔時發生錯誤: {str(e)}")
            return []
    
    def get_config_path(self, config_name):
        """獲取設定檔路徑"""
        return str(self.conf_dir / config_name)
    
    def update_node_bandwidth(self, download_speed, upload_speed):
        """更新所有節點設定檔中的頻寬設定"""
        try:
            if not self.conf_dir.exists():
                logger.error("找不到設定檔目錄")
                return False
            
            # 遍歷所有 .conf 檔案
            for conf_file in self.conf_dir.glob('*.conf'):
                try:
                    # 讀取原始內容
                    content = conf_file.read_text(encoding='utf-8').splitlines()
                    
                    # 更新內容
                    new_content = []
                    for line in content:
                        if line.startswith('inbound_bandwidth='):
                            line = f'inbound_bandwidth={int(download_speed)}M'
                        elif line.startswith('outbound_bandwidth='):
                            line = f'outbound_bandwidth={int(upload_speed)}M'
                        new_content.append(line)
                    
                    # 寫回檔案
                    conf_file.write_text('\n'.join(new_content) + '\n', encoding='utf-8')
                    logger.info(f"已更新設定檔: {conf_file.name}")
                except Exception as e:
                    logger.error(f"更新設定檔 {conf_file.name} 失敗: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"更新設定檔時發生錯誤: {str(e)}")
            return False

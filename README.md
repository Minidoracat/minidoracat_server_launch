# Minidoracat 伺服器專用優化工具

這是專門為 Minidoracat 伺服器設計的連線優化工具，提供圖形化界面來管理和優化 KCPTube 連線。

[![Discord](https://img.shields.io/discord/YOUR_SERVER_ID?color=7289DA&logo=discord&logoColor=white)](https://discord.gg/Gur2V67)

## 社群支援

加入我們的 Discord 社群以獲取最新資訊和支援：
- 💬 [Minidoracat Discord 社群](https://discord.gg/Gur2V67)
- 即時技術支援
- 問題回報與建議
- 版本更新通知

## 下載

請前往 [Releases](https://github.com/Minidoracat/minidoracat_server_launch/releases) 頁面下載最新版本。

## 功能特點

- 專為 Minidoracat 伺服器最佳化
- 現代化的深色主題界面設計
- 分頁式的功能佈局，操作更直觀
- 多節點管理與快速切換
- 即時狀態監控與日誌顯示
- 自動版本更新檢查
- 網路速度測試與自動配置
- 支援手動或自動套用速度設定
- 完整的錯誤處理與提示

## 使用方法

1. 從 Releases 頁面下載最新版本
2. 解壓縮到任意目錄
3. 在 `conf` 目錄下可以找到預設的節點設定檔
   - 可以直接使用現有的設定檔
   - 可以根據需要修改設定檔
   - 可以新增其他節點的設定檔
4. 執行 minidoracat_server_launch.exe
5. 從下拉選單選擇要連接的節點
6. 點擊啟動按鈕開始使用

## 界面說明

### 主要功能區
- **節點設定**：選擇和管理連線節點
- **速度設定**：進行速度測試和配置
- **系統日誌**：查看運行狀態和錯誤訊息

### 速度測試功能

#### 自動測速
1. 點擊「測試網路速度」按鈕
2. 系統會自動尋找最佳測試節點
3. 依序測試下載和上傳速度
4. 測試完成後會顯示結果

#### 速度設定
- 可以手動輸入下載和上傳速度
- 可以使用自動測速的結果
- 支援自動套用速度設定到節點
- 所有速度單位均為 Mbps

#### 自動套用
- 可以選擇是否自動套用速度設定到節點
- 啟用自動套用後，測速結果會自動更新到節點設定
- 可以隨時切換自動/手動模式

## 設定檔管理

### 設定檔位置
- 所有設定檔都放在 `conf` 目錄下
- 檔案名稱格式為 `名稱.conf`
- 檔案名稱會顯示在啟動器的下拉選單中

### 設定檔格式
```conf
mode=client
kcp=fast2
inbound_bandwidth=1000M
outbound_bandwidth=600M
listen_port=16361
destination_port=10871
destination_address=your_server_ip
encryption_algorithm=none
ipv4_only=true
blast=1
fec=1:1
log_path=./
```

### 新增節點
1. 在 `conf` 目錄下建立新的 `.conf` 檔案
2. 參考現有設定檔的格式進行設定
3. 重新啟動程式，新節點會自動出現在選單中

## 系統需求

- Windows 10/11 64位元作業系統
- 不需要安裝其他相依套件
- 需要網路連接以進行速度測試

## 開發資訊

### 使用的技術
- Python 3.10+
- ttkbootstrap（現代化界面框架）
- PyInstaller（打包工具）
- speedtest-cli（網速測試）
- Pillow（圖片處理）

### 專案結構
```
minidoracat_server_launch/
├── main.py              # 主程式
├── config_manager.py    # 設定檔管理
├── speed_test_manager.py # 速度測試
├── version_manager.py   # 版本管理
├── logger.py           # 日誌系統
├── build.py            # 打包腳本
├── conf/               # 設定檔目錄
├── image/              # 圖片資源
└── logs/               # 日誌檔案
```

## 版本資訊

版本資訊請參考 [Releases](https://github.com/Minidoracat/minidoracat_server_launch/releases) 頁面。

## 問題回報

如果您遇到任何問題或有建議：
1. 加入我們的 [Discord 社群](https://discord.gg/Gur2V67)
2. 在 GitHub Issues 中提出問題
3. 透過 Discord 私訊管理員

## 授權聲明

本軟體為私有軟體，保留所有權利。專門用於 Minidoracat 伺服器的連線優化。

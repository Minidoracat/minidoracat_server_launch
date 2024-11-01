# Minidoracat 伺服器專用優化工具

這是專門為 Minidoracat 伺服器設計的連線優化工具，提供圖形化界面來管理和優化 KCPTube 連線。本工具基於 [KCPTube](https://github.com/cnbatch/kcptube) 開發，為其提供了現代化的管理界面和自動化功能。KCPTube 是一個高效能的網路加速工具，使用 KCP 協議來優化網路連線，特別適合需要低延遲和高穩定性的應用場景。

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
- Project Zomboid 記憶體優化功能
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
- **PZ 記憶體設定**：Project Zomboid 遊戲記憶體優化
- **系統日誌**：查看運行狀態和錯誤訊息

### 速度設定功能

> **重要提示**：本工具使用頻寬設定來優化連線品質，透過合適的頻寬配置可以有效降低延遲並提升連線穩定性。強烈建議您在「速度設定」頁面測試或設定符合您實際網路環境的頻寬數值，以獲得最佳的連線體驗。

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

### Project Zomboid 記憶體設定功能

> **重要提示**：合適的記憶體設定可以大幅提升遊戲效能，特別是在使用大量模組時。本工具會根據您的系統配置自動計算最佳的記憶體設定值。

#### 主要功能
- 自動檢測系統記憶體大小
- 智能計算建議的記憶體設定值
- 檢測並提醒預設記憶體設定（3GB）
- 一鍵套用建議設定
- 防呆機制，避免設定不合理的值

#### 使用方式
1. 切換到「PZ 記憶體設定」頁面
2. 查看系統記憶體和建議設定值
3. 使用「使用建議值」按鈕一鍵套用
4. 或手動輸入記憶體大小後點擊「套用設定」

#### 注意事項
- 首次啟動時如果檢測到預設設定會自動提醒
- 設定過高或過低時會顯示警告提示
- 建議保留適當的系統記憶體給其他程式使用

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
- [KCPTube](https://github.com/cnbatch/kcptube)（核心網路加速引擎）
- Python 3.10+
- ttkbootstrap（現代化界面框架）
- PyInstaller（打包工具）
- speedtest-cli（網速測試）
- Pillow（圖片處理）
- psutil（系統資訊獲取）

### 專案結構
```
minidoracat_server_launch/
├── main.py              # 主程式
├── config_manager.py    # 設定檔管理
├── speed_test_manager.py # 速度測試
├── version_manager.py   # 版本管理
├── pz_manager.py        # PZ 記憶體管理
├── logger.py           # 日誌系統
├── build.py            # 打包腳本
├── gui/                # GUI 模組
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

本軟體為私有軟體，保留所有權利。專門用於 Minidoracat 伺服器的連線優化。本專案使用的 KCPTube 核心遵循其原始授權條款。

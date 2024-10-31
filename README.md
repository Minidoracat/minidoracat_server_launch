# KCPTube 啟動器

這是一個用於管理和啟動 KCPTube 的圖形化工具。

## 下載

請前往 [Releases](https://github.com/Minidoracat/kcptube_launch/releases) 頁面下載最新版本。

## 功能特點

- 圖形化介面，簡單易用
- 多節點管理與切換
- 即時狀態監控
- 自動版本更新檢查

## 使用方法

1. 從 Releases 頁面下載最新版本
2. 解壓縮到任意目錄
3. 在 `conf` 目錄下可以找到預設的節點設定檔
   - 可以直接使用現有的設定檔
   - 可以根據需要修改設定檔
   - 可以新增其他節點的設定檔
4. 執行 kcptube_launcher.exe
5. 從下拉選單選擇要連接的節點
6. 點擊啟動按鈕開始使用

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

## 版本資訊

當前版本：[version.txt](kcptube/version.txt)

## 授權聲明

本軟體為私有軟體，保留所有權利。

# Kassow KR810 自動夾取系統

收到兩個壓縮檔：

**`kassow_handover.tar.gz`** — 主程式，解壓後得到 `kassow_RobotUse/` 資料夾，裡面有 `20260615進度交接安裝說明.md`，照那份文件裝好環境就能跑。

**`ros2_ws_src.tar.gz`** — Kassow 機器人 ROS2 SDK，在家目錄（`~/`）解壓，會自動建出 `~/ros2_ws/src/`，再照安裝說明 Step 2 跑 `colcon build` 即可。

兩份都解壓、環境裝好後，進 `kassow_RobotUse/` 執行 `./run.sh` 啟動。

---

**`自動化夾取流程相關說明.md`** — 說明整個自動夾取的狀態機流程、各物件職責、重要參數、已修復問題與待處理事項，接手開發前建議先閱讀。

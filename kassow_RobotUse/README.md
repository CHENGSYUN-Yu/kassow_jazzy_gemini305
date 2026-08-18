# Kassow KR810 自動夾取系統

Kassow KR810 右臂 + 雙相機（頭部 Intel RealSense D435I、手腕 Orbbec Gemini 305），
以 YOLO 辨識手術器械並全自動夾取、放置、還原。**第一次接手請從本檔讀起。**

---

## 一、硬體前提（需與原開發機同規格）

- Kassow KR810 手臂（IP `192.168.38.1`，`ROS_DOMAIN_ID=1`）
- 頭部相機：Intel RealSense D435I（USB3，index 0）
- 手腕相機：Orbbec Gemini 305（USB3，index 1，原生 848×530）
- NVIDIA GPU（driver 575+，CUDA 13）
- OS：Ubuntu 24.04 LTS / Python 3.12 / ROS2 Jazzy

## 二、你需要拿到的兩樣東西

1. **本專案資料夾 `kassow_RobotUse/`**（git clone 或解壓皆可）
   — 含主程式、YOLO 模型、校正矩陣、`requirements.txt`、本說明文件。
2. **`ros2_ws_src.tar.gz`**（Kassow ROS2 SDK，**另外提供，不在本資料夾內**）
   — 程式會 `import kr_msgs`，缺這包環境裝好也起不來。

## 三、安裝步驟（照 `202608_new進度交接安裝說明.md` §0→§6 依序做）

該文件是**唯一權威的逐步安裝手冊**，本表僅為路線地圖，每步對應該文件章節：

| 步驟 | 做什麼 | 重點 |
|------|--------|------|
| §0 | 安裝 NVIDIA Driver | `nvidia-smi` 顯示 CUDA 13.x |
| §1 | 安裝 ROS2 Jazzy | `ros-jazzy-desktop` |
| §2 | 解壓 `ros2_ws_src.tar.gz` → build `kr_msgs` | ★需上面第 2 樣東西★ |
| §3 | 頭部相機 udev + 中文字型 + `python3-tk` | 裝完登出再登入 |
| §4 | 設定手臂網路靜態 IP `192.168.38.20` | `ping 192.168.38.1` 通 |
| §5 | 建 venv（Python 3.12）+ torch cu130 + `requirements.txt` | venv 不加 `--system-site-packages` |
| §5.5 | 手腕相機 Orbbec Gemini 305 的 USB 權限（udev） | `lsusb \| grep -i orbbec` 驗證 |
| §6 | 啟動 | `./run_fixed.sh` |

## 四、啟動

```bash
cd kassow_RobotUse
./run_fixed.sh          # 用 run_fixed.sh（不是 run.sh）
```

## 五、想了解夾取流程或接手開發

讀 **`自動化夾取流程相關說明.md`** — 完整狀態機流程、各物件職責、重要參數、
已修復問題與待處理事項。接手開發前務必先看。

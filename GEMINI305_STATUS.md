# Gemini 305 開發進度

## ⚠️ 當前狀態

**Gemini 305 軟體驅動尚未安裝**

此版本基於 jazzy0605 交接版本複製，為 Gemini 305 手部相機開發預備。

## 硬體測試結果

| 相機 | 驅動 | 狀態 |
|------|------|------|
| D435I（頭部） | RealSense | ✅ **功能正常（已測試）** |
| Gemini 305（手腕） | Orbbec | ⚠️ 待配置 |

## 待辦事項

### 高優先
- [ ] 安裝 Orbbec SDK
- [ ] 更新 `src/realsense.py` 適配 Gemini 305
- [ ] 更新 `src/get_depth_handcam.py` 深度讀取邏輯
- [ ] 更新 `src/pixel2handcam.py` 內參校正
- [ ] 重新校正 `T_cam2gripper` 變換矩陣

### 中優先
- [ ] 更新 requirements.txt
- [ ] 完整流程測試（Gemini 305 + 自動夾取）
- [ ] 調試和優化

## 環境清單

- ✅ 完整自動夾取程式（狀態機、各功能模組）
- ✅ YOLO 訓練資料集和模型
- ✅ 開發日誌和訓練記錄
- ✅ 獨立虛擬環境 (.venv)
- ✅ 獨立 git 版本控制

## 開發環境規格

- Python 3.12.3
- ROS2 Jazzy
- CUDA 13.0
- PyTorch 2.12.0
- ultralytics 8.4.60

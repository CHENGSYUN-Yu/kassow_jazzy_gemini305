# Gemini 305 開發進度紀錄

**最後更新**: 2026-06-29

## ✅ 已完成

### 驅動層 (realsense.py)
- [x] Orbbec SDK 導入和可用性檢測
- [x] CameraType 枚舉（支持多種相機類型）
- [x] _Camera 類重構（支持 RealSense 和 Orbbec）
- [x] _connect_orbbec() 方法實現
  - 設備檢測和初始化
  - Pipeline 和 Config 配置
  - enable_stream() - 只用流類型參數
  - AlignFilter() - 用 OBStreamType.COLOR_STREAM
  - 內參讀取（有預設值備用）
  - Depth scale 配置
- [x] _capture_loop_orbbec() 方法實現
  - wait_for_frames() - 位置參數調用
  - YUYV→BGR 色彩轉換（基本邏輯）
  - 深度幀擷取和濾波
  - 紋理轉換
- [x] _scan() 方法擴展
  - RealSense 設備掃描
  - Orbbec 設備掃描
  - 設備排序邏輯（D435I > Gemini 305 > D405）
- [x] RealSense 類改動
  - 傳遞 device_name 參數給 _Camera
  - connect() 和 connect_one() 更新
- [x] _cleanup() 方法擴展（支持 Orbbec）

### 測試驗證
- [x] API 調用驗證 - 所有 Orbbec SDK 函數可用
- [x] 雙相機連線測試 - 兩台相機都能成功連線
- [x] 幀資料擷取 - Orbbec 能成功擷取 848×530 YUYV 幀

### 組態管理
- [x] pyorbbecsdk2==1.14.30 添加到 requirements.txt

## ❌ 尚未解決

### 關鍵問題：Gemini 305 GUI 畫面顯示異常
**症狀**:
- cam2（Gemini 305）顯示為水平條紋雜訊，無法看清內容
- cam3 也顯示相同雜訊（可能是 GUI 索引映射問題）
- 但相機連線成功且有光影變化（說明數據本身有效）

**根本原因未明確**:
- YUYV→BGR 轉換邏輯可能不正確
  - 嘗試過的方式：reshape(-1, 4)、reshape(h, w, 2) 等
  - 之前多次嘗試都未成功解決
- 或 GUI 層相機索引映射有問題
- 或 Orbbec 返回的數據格式與標準 YUYV 不同

**診斷線索**:
- Orbbec color_frame 返回 1D 數組（898880 字節）
- 分辨率：848×530
- 數據大小：848 * 530 * 2 = 898,880 bytes ✓（符合 YUYV 2字節/像素）
- 數據有效（前次診斷發現色彩信息存在）

## 🔄 待診斷

1. **YUYV 轉換的正確格式**
   - Orbbec YUYV 的實際排列順序
   - 是否需要特殊的轉換公式

2. **GUI 層相機索引問題**
   - cam2、cam3 為何顯示相同內容
   - 是否與驅動層無關

3. **色彩轉換方案**
   - 考慮使用 OpenCV 的 cvtColor（如果可用）
   - 或其他經過驗證的 YUYV 轉換庫

## 📋 下一步建議

### 優先順序
1. **深入診斷 Orbbec 數據格式** - 確認 YUYV 的實際排列
2. **診斷 GUI 層** - 檢查相機索引映射邏輯
3. **嘗試簡化轉換** - 先顯示灰階（只用 Y 通道）驗證數據有效性
4. **考慮替代方案** - 如果標準轉換失敗，尋求其他解決方案

## 技術規格參考

**Gemini 305 相機**:
- 類型: Orbbec 手腕掛載立體視覺深度相機
- 色彩幀: 848×530, YUYV 格式, ~2字節/像素
- 深度幀: 848×530, uint8/uint16

**已驗證的 Orbbec API**:
- `config.enable_stream(obs.OBStreamType.COLOR_STREAM)` ✓
- `config.enable_stream(obs.OBStreamType.DEPTH_STREAM)` ✓
- `pipeline.wait_for_frames(timeout_ms)` - 必須用位置參數 ✓
- `AlignFilter(obs.OBStreamType.COLOR_STREAM)` ✓

## 相關文件
- `/home/bf-robotics/jazzy_gemini305_0628/kassow_RobotUse/src/realsense.py` - 主要驅動層
- `/home/bf-robotics/jazzy_gemini305_0628/kassow_RobotUse/requirements.txt` - 依賴管理
- `/home/bf-robotics/jazzy_gemini305_0628/kassow_RobotUse/src/app.py` - GUI 邏輯（待檢查）

---

**狀態**: 驅動層基本完成，待解決 GUI 顯示問題

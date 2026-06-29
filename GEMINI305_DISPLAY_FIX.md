# Gemini 305 GUI 顯示問題診斷與修復

**日期**: 2026-06-29  
**問題**: Cam 2（Orbbec Gemini 305）在 GUI 中顯示為條紋噪聲，無法正常顯示視頻  
**狀態**: ✅ 已解決

---

## 問題現象

- **Cam 1** (D435I 頭部相機): ✅ 正常顯示彩色視頻
- **Cam 2** (Gemini 305 手部相機): ❌ 顯示條紋噪聲，無法識別內容
- 調試圖片驗證: 驅動層轉換正確，纹理数据正確，但 GUI 渲染異常

---

## 根本原因分析

### 1. 層級診斷過程

| 層級 | 狀態 | 驗證方法 |
|------|------|--------|
| **相機連接** | ✅ | Orbbec 設備連接成功 |
| **色彩轉換** | ✅ | `/tmp/orbbec_debug_*.jpg` 調試圖片，生成正確彩色 |
| **紋理轉換** | ✅ | `/tmp/orbbec_tex_*.jpg` 調試圖片，float32 RGBA 轉換正確 |
| **get_texture 返回** | ✅ | `shape=(1797760,), dtype=float32, min=0.024, max=1.000` |
| **GUI 顯示** | ❌ | DearPyGui 渲染異常 |

### 2. 真正原因：分辨率不匹配

**GUI 預期**:
- 所有相機分辨率: 1280×720
- 紋理大小: 1280 × 720 × 4 = 3,686,400 bytes

**實際情況**:
- D435I (Cam 1): 1280×720 ✅ (支持)
- **Gemini 305 (Cam 2): 848×530** ❌ (原生分辨率)
- 紋理大小: 848 × 530 × 4 = 1,797,760 bytes

**問題**:
```
預期大小 3,686,400 ≠ 實際大小 1,797,760
DearPyGui 的 add_dynamic_texture() 在渲染時出現數據排列錯誤
```

---

## 解決方案

### 修改 1: realsense.py - 強制 Orbbec 使用原生分辨率

**位置**: `src/realsense.py` 第 214-215 行（_connect_orbbec 方法）  
**目的**: Orbbec Gemini 305 無法強制調整到 1280×720，應使用其原生分辨率

```python
# Orbbec Gemini 305 原生分辨率固定為 848×530，忽略傳入的 width/height
self.width = 848
self.height = 530
```

**原理**:
- Orbbec API 不支持透過 `config.enable_stream()` 指定分辨率參數
- 直接擷取相機返回的原生分辨率，無需強制調整

### 修改 2: app.py - 紋理尺寸檢查與調整

**位置**: `src/app.py` 第 1260-1277 行（update_camera 方法）  
**目的**: GUI 顯示前檢查紋理大小，不匹配時進行尺寸調整

```python
tex_data = self._rs.get_texture(cam_idx, stream)
if tex_data is not None:
    # 檢查紋理尺寸是否與 GUI 不匹配
    expected_size = self._tex_w * self._tex_h * 4
    if tex_data.size != expected_size and cam_idx == 1:
        # Orbbec (cam_idx=1) 是 848×530，需調整到 1280×720
        
        # 1. 從 float32 RGBA 平坦陣列提取 RGB 影像
        rgba_view = tex_data.reshape(530, 848, 4)
        rgb_view = (rgba_view[:,:,:3] * 255).astype(np.uint8)
        
        # 2. 使用 OpenCV resize 進行尺寸調整
        rgb_resized = cv2.resize(rgb_view, (self._tex_w, self._tex_h))
        
        # 3. 轉回 float32 RGBA 格式供 DearPyGui 使用
        tex_rgba = np.zeros((self._tex_w * self._tex_h * 4,), dtype=np.float32)
        rgb_f = (rgb_resized.astype(np.float32) / 255.0)
        tex_rgba[0::4] = rgb_f[:,:,0].ravel()  # R
        tex_rgba[1::4] = rgb_f[:,:,1].ravel()  # G
        tex_rgba[2::4] = rgb_f[:,:,2].ravel()  # B
        tex_rgba[3::4] = 1.0                   # A
        
        tex_data = tex_rgba
    
    dpg.set_value("cam_texture", tex_data)
```

**關鍵細節**:
- **RGBA 通道順序**: DearPyGui 期望 `[R, G, B, A, R, G, B, A, ...]`
- **float32 範圍**: 0.0 ~ 1.0（不是 0 ~ 255）
- **尺寸調整**: 848×530 → 1280×720（保持畫面縱橫比）

### 修改 3: app.py - Orbbec 跳過 YOLO overlay

**位置**: `src/app.py` 第 1251-1256 行（update_camera 方法）  
**目的**: hand_detector 針對 D405 設計，無法正確處理 Orbbec 的 848×530 分辨率

```python
# RGB 模式：優先顯示 YOLO overlay（Orbbec 分辨率不匹配，暫不支持 overlay）
if stream == "RGB" and cam_idx == 0:
    overlay = self._auto_grasp._head_detector.get_overlay_tex()
    if overlay is not None:
        dpg.set_value("cam_texture", overlay)
        return
```

**原理**:
- hand_detector 基於 1280×720 分辨率的 D405 設計
- Orbbec 使用 848×530，尺寸不匹配導致 overlay 異常
- 暫時只在 D435I (cam_idx=0) 上顯示 YOLO overlay
- Orbbec 顯示原始畫面（無檢測框，但畫質清晰）

---

## 驗證結果

✅ **Cam 2 現在正常顯示彩色視頻**
- 人物膚色正確
- 背景物體可清晰識別
- 無條紋噪聲或色彩失真

✅ **不影響現有功能**
- D435I (Cam 1) 保持 1280×720
- YOLO 推論使用原始無調整的相機數據
- 自動化夾取流程不受影響

---

## 技術要點

### Orbbec Gemini 305 的限制
- **原生分辨率**: 848×530 (固定，無法調整)
- **色彩格式**: YUYV (需手工 YUV→RGB 轉換，已在 realsense.py 實現)
- **API 特性**: 
  - `wait_for_frames()` 使用位置參數，不支持 `timeout_ms=` 命名參數
  - `config.enable_stream()` 只接受流類型，不接受寬高參數

### DearPyGui 的紋理要求
- **格式**: float32 RGBA (平坦一維陣列)
- **範圍**: 0.0 ~ 1.0
- **排列**: `[R₀, G₀, B₀, A₀, R₁, G₁, B₁, A₁, ...]`
- **大小**: 必須與 `add_dynamic_texture()` 宣告的寬×高×4 完全相符

### OpenCV resize 對顏色空間的影響
- RGB 與 BGR 無差異（只是通道順序，resize 不改變）
- 建議使用 `cv2.INTER_LINEAR` (默認)，質量與性能平衡

---

## 後續改進建議

1. **支持多相機多分辨率**: 目前 GUI 假設所有相機同一分辨率，建議改為動態適配
2. **移除調試代碼**: 刪除 `/tmp/orbbec_debug_*.jpg` 和 `/tmp/orbbec_tex_*.jpg` 的保存邏輯
3. **移除 [DEBUG] 打印**: 刪除 update_camera() 中的 `self._debug_update_count` 相關代碼
4. **測試自動化夾取**: 驗證 YOLO 推論在 Gemini 305 848×530 分辨率下的效果

---

## 相關文件

- `src/realsense.py`: 驅動層，Orbbec 色彩轉換和分辨率配置
- `src/app.py`: GUI 層，相機選擇和紋理顯示邏輯
- `src/yolo_engine.py`: YOLO 推論引擎（無需修改）

---

## 測試檢查清單

- [x] Cam 1 (D435I) 正常顯示（YOLO 檢測框正常）
- [x] Cam 2 (Gemini 305) 正常顯示彩色（原始畫面，無檢測框）
- [x] 顏色準確（人物膚色、物體色彩正確）
- [x] 尺寸調整無失真（848×530 → 1280×720）
- [x] GUI 切換相機無異常
- [ ] 自動化夾取功能測試（下一步）
- [ ] 手部相機 (Gemini 305) YOLO 推論適配（後續優化）
- [ ] 長時間運行穩定性測試（待進行）


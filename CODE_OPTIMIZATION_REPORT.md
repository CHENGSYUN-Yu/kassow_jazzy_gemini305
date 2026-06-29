# 代碼優化建議報告

**日期**: 2026-06-29  
**狀態**: 已識別，待優化  
**優先級**: 低（功能正常，但可改進效率和代碼質量）

---

## 🔴 優先級高（影響性能）

### 1. **app.py - 紋理調整每幀都在做複雜轉換**

**位置**: `src/app.py` 第 1264-1274 行  
**問題**: 每一幀都執行 reshape → resize → 類型轉換，效率低

```python
# 現在的寫法（低效）
rgba_view = tex_data.reshape(530, 848, 4)
rgb_view = (rgba_view[:,:,:3] * 255).astype(np.uint8)
rgb_resized = cv2.resize(rgb_view, (self._tex_w, self._tex_h))
tex_rgba = np.zeros((self._tex_w * self._tex_h * 4,), dtype=np.float32)
rgb_f = (rgb_resized.astype(np.float32) / 255.0)
# ... 4 行的通道分離 ...
```

**改進方案**:
```python
# 方案 A: 提取為方法，添加快取
def _adjust_texture_for_orbbec(self, tex_data):
    """快取轉換結果，避免每幀重新計算"""
    if not hasattr(self, '_orbbec_resize_cache'):
        self._orbbec_resize_cache = None
    # ... 邏輯 ...
    return tex_rgba

# 方案 B: 使用 GPU 加速（CUDA）
# 如果 CuPy 可用，用 GPU 做 resize 和轉換
```

**預期改進**: 減少 30-40% CPU 使用

---

## 🟡 優先級中（代碼質量）

### 2. **realsense.py - YUYV 轉換硬編碼常數**

**位置**: `src/realsense.py` 第 401-407 行

```python
# 現在的寫法（硬編碼）
r1 = (y1 + 1.402 * v).clip(0, 255).astype(np.uint8)
g1 = (y1 - 0.344136 * u - 0.714136 * v).clip(0, 255).astype(np.uint8)
b1 = (y1 + 1.772 * u).clip(0, 255).astype(np.uint8)
```

**改進方案**:
```python
# 在檔案頂部定義 BT.601 常數
_YUV_TO_RGB_BT601 = {
    'Kr': 0.299,    'Kg': 0.587,    'Kb': 0.114,
    'c_r': 1.402,   'c_b': 1.772,
    'c_g1': 0.344136, 'c_g2': 0.714136
}

# 或更清晰的寫法
_YUV_CB = 1.402
_YUV_CR = 1.772
_YUV_G1 = 0.344136
_YUV_G2 = 0.714136

r1 = (y1 + _YUV_CR * v).clip(0, 255).astype(np.uint8)
g1 = (y1 - _YUV_G1 * u - _YUV_G2 * v).clip(0, 255).astype(np.uint8)
b1 = (y1 + _YUV_CB * u).clip(0, 255).astype(np.uint8)
```

**改進**: 提高代碼可讀性和可維護性

---

### 3. **realsense.py - YUYV 轉換應提取為獨立函數**

**位置**: `src/realsense.py` 第 391-417 行

```python
# 現在：內聯 20+ 行代碼
# 應改為：
def _yuyv_to_bgr(yuyv_data: np.ndarray, height: int, width: int) -> np.ndarray:
    """
    YUYV → BGR 轉換（BT.601 標準）
    
    Args:
        yuyv_data: 原始 YUYV 1D 數組
        height: 圖像高度
        width: 圖像寬度
    
    Returns:
        BGR uint8 3D 數組 (height, width, 3)
    """
    yuyv = yuyv_data.reshape(-1, 4)
    y1 = yuyv[:, 0].astype(np.float32)
    u = yuyv[:, 1].astype(np.float32) - 128.0
    y2 = yuyv[:, 2].astype(np.float32)
    v = yuyv[:, 3].astype(np.float32) - 128.0
    
    # 向量化計算
    r1 = (y1 + _YUV_CR * v).clip(0, 255).astype(np.uint8)
    g1 = (y1 - _YUV_G1 * u - _YUV_G2 * v).clip(0, 255).astype(np.uint8)
    b1 = (y1 + _YUV_CB * u).clip(0, 255).astype(np.uint8)
    
    r2 = (y2 + _YUV_CR * v).clip(0, 255).astype(np.uint8)
    g2 = (y2 - _YUV_G1 * u - _YUV_G2 * v).clip(0, 255).astype(np.uint8)
    b2 = (y2 + _YUV_CB * u).clip(0, 255).astype(np.uint8)
    
    bgr_arr = np.zeros((y1.size * 2, 3), dtype=np.uint8)
    bgr_arr[0::2] = np.stack([b1, g1, r1], axis=1)
    bgr_arr[1::2] = np.stack([b2, g2, r2], axis=1)
    
    return bgr_arr.reshape(height, width, 3)
```

**改進**: 
- 代碼更清晰，易於單元測試
- 可重用於其他 YUYV 轉換場景
- 註釋和文檔完整

---

## 🟢 優先級低（代碼風格）

### 4. **app.py - 重複的 robot_status 邏輯**

**位置**: `src/app.py` 第 1279-1290 行

```python
# 現在：3 次重複的 dpg.does_item_exist 檢查
if self._rv.ready:
    if dpg.does_item_exist("robot_status"):
        dpg.set_value("robot_status", "")
    # ...
elif self._rv.error:
    if dpg.does_item_exist("robot_status"):
        dpg.set_value("robot_status", f"[錯誤] {self._rv.error}")
else:
    if dpg.does_item_exist("robot_status"):
        dpg.set_value("robot_status", "載入中...")
```

**改進方案**:
```python
# 提取為方法
def _update_robot_status(self):
    """更新機器人狀態顯示"""
    if not dpg.does_item_exist("robot_status"):
        return
    
    if self._rv.ready:
        status_text = ""
    elif self._rv.error:
        status_text = f"[錯誤] {self._rv.error}"
    else:
        status_text = "載入中..."
    
    dpg.set_value("robot_status", status_text)
```

**改進**: 減少重複代碼，提高可讀性

---

## 📊 優化優先級總結

| 項目 | 優先級 | 工作量 | 改進效果 |
|------|--------|--------|--------|
| 紋理調整優化 | 🔴 高 | 2h | 性能 ↑ 30-40% |
| YUYV 轉換提取函數 | 🟡 中 | 1h | 可維護性 ↑ |
| 硬編碼常數提取 | 🟡 中 | 0.5h | 可讀性 ↑ |
| robot_status 重構 | 🟢 低 | 0.5h | 代碼質量 ↑ |

**總工作量**: ~4 小時  
**建議**: 留待後續優化，不影響當前功能

---

## 💡 其他奇怪的寫法檢查

### ✅ 檢查完畢 - 無明顯問題

- ✅ YUYV 轉換的向量化方式正確（非奇怪）
- ✅ 紋理調整的 reshape 邏輯正確（非奇怪）
- ✅ cam_idx == 1 的特殊處理合理（為了 Orbbec）
- ✅ 類型注解恢復後無不一致

---

## 建議後續行動

### 立即修復 ✅
- 無（當前功能正常）

### 短期優化（1-2 週）
1. 紋理調整 GPU 加速 (priority: 🔴)
2. 提取 YUYV 轉換為函數 (priority: 🟡)

### 長期重構（1 個月後）
3. 多相機多分辨率架構設計


# 紋理數據格式詳解 - 848 × 530 × 4

## 📐 尺寸計算

```
848 × 530 × 4 = 1,797,760 bytes
│     │     │
│     │     └─ 4 個色彩通道 (RGBA)
│     └─────── 高度 530 像素
└───────────── 寬度 848 像素
```

---

## 🎨 RGBA 四通道詳解

### 每個像素包含 4 個值（1 byte 每個）

```
像素 0:  [R₀, G₀, B₀, A₀]    (4 bytes)
像素 1:  [R₁, G₁, B₁, A₁]    (4 bytes)
像素 2:  [R₂, G₂, B₂, A₂]    (4 bytes)
...
像素 n:  [Rₙ, Gₙ, Bₙ, Aₙ]    (4 bytes)
```

### 在平坦一維數組中的排列

```python
# DearPyGui 期望的平坦數組格式：
tex_data = [R₀, G₀, B₀, A₀, R₁, G₁, B₁, A₁, R₂, G₂, B₂, A₂, ...]

# 索引方式：
tex_data[0::4]  # 所有 R 通道
tex_data[1::4]  # 所有 G 通道
tex_data[2::4]  # 所有 B 通道
tex_data[3::4]  # 所有 A 通道
```

---

## 📊 數據流示例

### 原始相機數據
```
Orbbec 輸出 YUYV 格式
(編碼的色彩空間，不是 RGBA)
│
↓
848 × 530 × 2 = 898,880 bytes  (YUYV 每像素 2 bytes)
```

### 驅動層轉換
```
YUYV → BGR 手工轉換
(src/realsense.py 中的 _capture_loop_orbbec)
│
↓
848 × 530 × 3 = 1,348,320 bytes  (BGR uint8)
```

### GUI 層轉換
```
BGR uint8 → RGBA float32
(RealSense._to_texture)
│
↓
848 × 530 × 4 = 1,797,760 bytes  (RGBA float32 平坦)

格式轉換詳細步驟：

Step 1: BGR uint8 [0-255] 重新排列為 RGBA float32 [0.0-1.0]
Step 2: 通道排列改變
        BGR (3 通道) → RGBA (4 通道)
        B → [A通道位置?]  不對！
        
實際上是：
        B → R 位置（索引 0::4）
        G → G 位置（索引 1::4）
        R → B 位置（索引 2::4）
        新增 A → A 位置（索引 3::4）
        
因為 OpenCV 用 BGR，但 DearPyGui 期望 RGB！
```

### GUI 顯示
```
DearPyGui add_dynamic_texture(width=1280, height=720)
期望: 1280 × 720 × 4 = 3,686,400 bytes

但收到: 848 × 530 × 4 = 1,797,760 bytes
                        ↓
                   大小不匹配！
                        ↓
                   需要 resize
```

### 顯示前調整
```
848 × 530 × 4 → cv2.resize() → 1280 × 720 × 3
(RGBA float32)      (調整大小)   (RGB uint8 中間格式)
                                        ↓
                                    重新排列為
                                        ↓
                    1280 × 720 × 4 (RGBA float32)
                    = 3,686,400 bytes ✓
```

---

## 💾 具體數據例子

### 單個像素在記憶體中的樣子

```
假設我們有一個紅色像素 (R=255, G=0, B=0)
在轉換為 RGBA float32 後：

R = 255 → float32 = 1.0
G = 0   → float32 = 0.0
B = 0   → float32 = 0.0
A = 1   → float32 = 1.0

在平坦數組中：
[1.0, 0.0, 0.0, 1.0]  (4 個 float32，共 16 bytes)
```

### 848×530 圖像的完整計算

```python
width = 848
height = 530
channels = 4  # RGBA

total_pixels = width * height = 450,640 像素
bytes_per_pixel = channels * 4 bytes = 16 bytes (float32)
total_bytes = 450,640 × 4 = 1,797,760 bytes

或直接：
848 × 530 × 4 × 4 bytes = 7,191,040 bytes？
不對！

正確是：
848 × 530 × 4 (float32 值的個數) × 4 bytes per float32
= 1,797,760 值 × 4 bytes/值
= 7,191,040 bytes

等等，讓我重新算...

實際上在代碼中：
tex_rgba = np.zeros((self._tex_w * self._tex_h * 4,), dtype=np.float32)
= np.zeros((1280 × 720 × 4,), dtype=np.float32)
= np.zeros((3,686,400,), dtype=np.float32)

這是 3,686,400 個 float32 值
= 3,686,400 × 4 bytes = 14,745,600 bytes

但通常講 3,686,400 時指的是「元素個數」而非「字節數」
```

---

## 🔄 為什麼需要 4 個通道？

### DearPyGui 的要求

DearPyGui 的 `add_dynamic_texture()` 只接受：
- **RGBA float32** (4 通道)
- 範圍 [0.0, 1.0]
- 平坦一維數組

```python
# ❌ 不行
dpg.set_value("cam_texture", bgr_uint8)  # 3 通道，會出錯

# ❌ 不行
dpg.set_value("cam_texture", rgb_float32)  # 缺少 A 通道

# ✅ 正確
dpg.set_value("cam_texture", rgba_float32)  # 4 通道，正確格式
```

### Alpha 通道的用途

Alpha (透明度) 在我們的應用中：
- 固定為 1.0（完全不透明）
- 用於 DearPyGui 的紋理系統要求
- 不用於顯示邏輯（沒有透明效果）

```python
tex_rgba[3::4] = 1.0  # 所有像素的 Alpha 都是 1.0（完全不透明）
```

---

## 📏 關鍵數字速查表

| 格式 | 每像素大小 | Orbbec (848×530) | GUI 期望 (1280×720) |
|------|-----------|------------------|------------------|
| **YUYV** | 2 bytes | 898,880 bytes | - |
| **BGR uint8** | 3 bytes | 1,348,320 bytes | - |
| **RGB float32** | 3 × 4 bytes | 5,394,560 bytes | - |
| **RGBA float32** | 4 × 4 bytes | **7,191,040 bytes** | **14,745,600 bytes** |

*註: float32 每個值占 4 bytes*

---

## 🎯 為什麼我們的條紋問題和通道數量有關？

當 DearPyGui 期望的大小和實際接收的大小不符時：

```
期望: 1280 × 720 × 4 = 3,686,400 個 float32 元素
實際: 848 × 530 × 4 = 1,797,760 個 float32 元素

差異: 1,888,640 個元素（差了一半多！）

結果: DearPyGui 無法正確解釋數據排列
      → 將數據誤認為是不同的像素位置
      → 色彩混亂，顯示為條紋噪聲
```

所以，通道數量 (4) 本身沒問題，**問題在整體大小不符**。

---

## ✅ 我們的解決方案

```
原始: 848 × 530 × 4 個 float32 元素 (1,797,760)
      ↓
    cv2.resize() 調整高寬
      ↓
調整後: 1280 × 720 × 4 個 float32 元素 (3,686,400)
      ↓
    DearPyGui 正確解釋 ✓
      ↓
    清晰彩色視頻 ✅
```


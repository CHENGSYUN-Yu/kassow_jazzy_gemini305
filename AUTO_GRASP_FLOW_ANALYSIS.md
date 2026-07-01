# 自動化夾取完整流程分析

**文檔日期**: 2026-06-30  
**涉及組件**: Gemini 305 手腕相機 + D435I 頭部相機  
**重點**: 識別相機更換和T矩陣更換的影響點

---

## 🔄 完整流程圖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 初始化 (idle)                                                             │
│    • 加載 YOLO 模型（頭部、手部）                                            │
│    • 加載 T_matrix（頭部 + 手部）                                            │
│    • RealSense 連接（雙相機）                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 頭部相機偵測 (detecting → confirm_selection)                             │
│    ├─ 讀取 D435I 彩色幀 + 深度幀                                            │
│    ├─ YOLO 推論（cam0）                                                    │
│    ├─ 座標轉換鏈：                                                          │
│    │   pixel → headcam 3D → base frame → Rz/yaw                          │
│    ├─ 涉及內參：D435I 的 fx, fy, cx, cy                                   │
│    ├─ 涉及 T_matrix：T_matrix_20260603_head30.npy（headcam2base）         │
│    ├─ 涉及偏移：yaw_offset_deg = -45.0°                                   │
│    └─ 用戶確認選擇的器械                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 計算接近目標 (_step_compute_target)                                      │
│    ├─ TargetZCompute：計算相機應到達高度（器械上方 300mm）                │
│    ├─ PoseOffset：硬性補償 x+25.0mm                                        │
│    │   （這個補償值是基於 D405 手部相機的設計）                            │
│    ├─ Cam2Flange：通過 T_cam2gripper 轉換                                 │
│    │   （從「相機應到達位置」轉為「法蘭應到達位置」）                     │
│    └─ 輸出：flange_target（法蘭接近目標）                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 移動到接近位置 (confirm_target → moving_approach → confirm_arrived)      │
│    ├─ MoveLinear 服務呼叫：                                                │
│    │   • pos = [x_mm, y_mm, z_mm] 法蘭位置                               │
│    │   • rot = [R, P, 當前yaw]（yaw 不變）                               │
│    │   • speed = GUI 設定的速度                                           │
│    └─ 監測到達                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. 手部相機偵測 (handcam_detecting)  ⚡ 關鍵：相機更換影響區                │
│    ├─ 讀取 Orbbec 彩色幀 + 深度幀                                          │
│    ├─ 內參：Orbbec 的 fx, fy, cx, cy（新相機需更新）                      │
│    ├─ YOLO 推論（cam1, 手部模型）                                         │
│    ├─ 座標轉換鏈：                                                          │
│    │   ① Pixel2HandCam：pixel + depth → 相機座標系 3D                   │
│    │   ② HandCam2Flange：相機座標系 → 法蘭座標系（T矩陣）             │
│    │      ⚠️ 使用 T_cam2gripper_gemini.npy（新T矩陣）                   │
│    │   ③ Angle2RzHandcam：2D 傾角 → 法蘭 Rz                             │
│    │      使用 T_cam2gripper_gemini.npy（用於 Rz 計算）               │
│    │   ④ Flange2Base：法蘭 → base 座標系（手臂即時位姿）              │
│    ├─ HandcamAngle2Yaw：用 offset (-135.0°) 覆蓋 Rz 結果               │
│    │   （此偏移與手部相機的物理安裝角度相關）                          │
│    └─ 等待 5s 讓偵測穩定                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. 計算夾取目標 (_step_compute_grasp)                                       │
│    ├─ TargetConsiderGripper：                                             │
│    │   考慮夾爪長度（100.0mm）的補償                                      │
│    │   基於器械位置（來自手部相機）計算法蘭最終目標                       │
│    ├─ GraspZOverride：強制設定 Z = -394.5mm（桌面高度）                 │
│    └─ 安全檢查：Z 是否超出下限                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 7. 移動到夾取位置 (confirm_grasp_target → moving_grasp → confirm_arrived)   │
│    ├─ MoveLinear 服務呼叫：                                                │
│    │   • pos = [x_mm, y_mm, z_mm] 法蘭位置                               │
│    │   • rot = [R, P, grasp_yaw]（yaw 設定為手部相機結果）              │
│    └─ 監測到達                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 8. 夾爪閉合 (closing_gripper)                                               │
│    └─ GripperControl 服務呼叫                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 9. 放置與回 Home (moving_sequence → opening_gripper → complete)            │
│    ├─ PlaceSequenceTargets：計算放置位置（提升 200mm）                   │
│    ├─ ReturnHomeTargets：計算回 Home 位置（提升 200mm）                  │
│    ├─ MoveLinear 執行放置和回 Home                                        │
│    └─ 夾爪張開                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 詳細組件映射

### Step 1: 初始化階段

| 組件 | 配置文件/變量 | 相機依賴 | T矩陣依賴 |
|------|--------------|--------|---------|
| YoloEngine (頭部) | `HEAD_MODEL_PATH` | D435I | ❌ |
| YoloEngine (手部) | `HAND_MODEL_PATH` | **Orbbec** | ❌ |
| HeadCam2Base | `T_MATRIX_PATH` | D435I | ✅ (`T_matrix_20260603_head30.npy`) |
| HandCam2Flange | `EIH_T_PATH` | **Orbbec** | ✅ (`T_cam2gripper_gemini.npy`) |
| RealSense | 雙相機初始化 | D435I + **Orbbec** | ❌ |

---

### Step 2: 頭部相機偵測鏈

```
D435I 彩色幀 + 深度幀
    ↓
YOLO (頭部模型)
    ↓
DepthReader.get_depth()    [讀取 5×5 patch 中位數]
    ↓
Pixel2HeadCam.project_all()    [需要 D435I 內參: fx, fy, cx, cy]
    ↓
HeadCam2Base.transform_all()   [需要 T_matrix_20260603_head30.npy]
    ↓
Angle2Rz.convert_all()         [2D傾角 → base Rz]
    ↓
Yaw 180° 對稱解 + yaw_offset_deg (-45.0°)  [全局頭部偏移]
    ↓
結果: pos_base_mm, yaw_deg
```

**硬體依賴**:
- ✅ D435I 必須可用
- ✅ D435I 內參必須正確
- ✅ T_matrix_20260603_head30.npy 必須正確

**相機更換影響**: ❌ 不影響（頭部相機不變）

---

### Step 3: 計算接近目標

```
DetectionResult (pos_base_mm)
    ↓
TargetZCompute(z_offset_mm=300.0)
    → 計算器械上方 300mm 位置（相機應該到達的位置）
    ↓
PoseOffset(dx=25.0, dy=0.0, dz=0.0)
    → 在 base frame 中直接加 x +25mm
    ⚠️ 這個 25mm 是基於 D405 手部相機的設計參數
    ↓
Cam2Flange.compute()
    → 使用 T_cam2gripper 轉換
    → 從「相機應到位置」轉為「法蘭應到位置」
    ↓
結果: flange_target (法蘭接近目標)
```

**硬體依賴**:
- ✅ T_cam2gripper_gemini.npy（手部相機T矩陣）
- ⚠️ PoseOffset (dx=25.0) - **基於D405設計**

**相機更換影響**:
- 如果 Orbbec 與 D405 的物理安裝位置不同
- 可能需要調整 PoseOffset 的 dx 值
- 可能需要重新標定 T_matrix

---

### Step 4: 移動到接近位置

```
flange_target (法蘭接近位置)
    ↓
TrajectoryPlan.plan()
    → 規劃軌跡
    ↓
MoveLinear 服務
    → pos = [x_mm, y_mm, z_mm]
    → rot = [R, P, 當前yaw]  ← yaw 不變（保持當前姿態）
    → speed_mm_s (GUI設定)
    ↓
CheckArrive.check()
    → 確認手臂到達（穩定 0.3s）
```

**硬體依賴**: ❌ 無直接硬體依賴

**相機更換影響**: ❌ 不影響

---

### Step 5: 手部相機偵測鏈 ⚡ **核心影響區**

```
Orbbec 彩色幀 + 深度幀
    ↓
YOLO (手部模型)  [cam1, 需要穩定偵測]
    ↓
GetDepthHandcam.get_depth()    [讀取 5×5 patch 中位數]
    ↓
Pixel2HandCam.project_all()    [需要 Orbbec 內參: fx, fy, cx, cy]
    │
    ├─ ❌ **相機更換影響點 1**: 內參不同
    │      D405: fx≠Orbbec_fx 等
    │
    ↓
HandCam2Flange.transform_all()  [需要 T_cam2gripper]
    │
    ├─ ✅ **已更新**: T_cam2gripper_gemini.npy
    │      （Gemini 305 的手眼標定結果）
    │
    ↓
Angle2RzHandcam.convert_all()  [2D傾角 → 法蘭 Rz]
    │
    ├─ ✅ **也使用 T_cam2gripper_gemini.npy**
    │      （用於 Rz 計算，基於機械設計）
    │
    ↓
Flange2Base.transform_all()    [法蘭 → base, 需要手臂即時位姿]
    │
    ├─ ❌ **相機更換影響點 2**: 手臂位姿更新頻率
    │      可能需要更高頻率確保同步
    │
    ↓
HandcamAngle2Yaw.convert_all()  [2D傾角直接 → yaw]
    │
    ├─ ⚠️ **相機更換影響點 3**: offset_deg = -135.0°
    │      此偏移與 Orbbec 的物理安裝角度相關
    │      新相機安裝角度不同，需要重新標定
    │
    ↓
結果: pos_base_mm, yaw_base_deg
```

**硬體依賴**:
- ✅ Orbbec 相機必須可用
- ❌ Orbbec 內參必須正確（新相機）
- ✅ T_cam2gripper_gemini.npy 已更新
- ⚠️ HandcamAngle2Yaw offset 基於物理安裝

**相機更換影響**: ✅ **全面影響**
- 內參 (fx, fy, cx, cy) 完全不同
- T_matrix 已更新
- 安裝角度偏移可能需要調整

---

### Step 6: 計算夾取目標

```
handcam_selected (來自手部相機)  OR  auto_selected (來自頭部相機)
    ↓
TargetConsiderGripper.compute()
    → gripper_length_mm = 100.0  ⚠️ 夾爪長度補償
    → 計算法蘭最終夾取位置
    ↓
GraspZOverride.apply()
    → z_mm = -394.5  ⚠️ **桌面絕對高度**
    → 強制覆蓋 Z 軸（因為手腕深度不穩定）
    ↓
安全檢查: z_mm >= grasp_z_limit
    → grasp_z_limit = -(_TABLE_Z_ABS_MM + gripper_length_mm + _Z_BUFFER_MM)
    → grasp_z_limit = -(395.0 + 100.0 + 2.0) = -497.0mm
    ↓
結果: grasp_target (夾取最終目標)
```

**硬體依賴**:
- ⚠️ `gripper_length_mm = 100.0` - 夾爪長度
- ⚠️ `_TABLE_Z_ABS_MM = 395.0` - 桌面高度
- ⚠️ `_grasp_z_ovr.z_mm = -394.5` - 強制Z值

**相機更換影響**:
- ❌ 不直接影響（來自前面計算）
- ⚠️ 如果手部相機的深度精度不同，可能需要調整 GraspZOverride 的值

---

### Step 7-9: 移動、夾爪、放置

```
grasp_target (法蘭夾取目標)
    ↓
MoveLinear
    → pos = [x_mm, y_mm, z_mm]
    → rot = [R, P, grasp_yaw]  ← **yaw 來自手部相機**
    ↓
GripperControl
    ↓
PlaceSequenceTargets(lift_z_mm=200.0)
    → 計算放置位置
    ↓
ReturnHomeTargets(lift_z_mm=200.0)
    → 計算回 Home 位置
```

**硬體依賴**:
- ⚠️ `lift_z_mm = 200.0` - 提升高度

**相機更換影響**:
- ❌ 不影響（都是基於計算結果）

---

## 📋 相機更換和T矩陣更換的完整影響分析

### 🔴 **必須調整的地方**

| # | 項目 | 當前值 | 需要調整 | 影響度 | 優先級 |
|---|------|--------|--------|--------|--------|
| 1 | Orbbec 內參 | D405參數 | **更新為 Orbbec 值** | 🔴 致命 | P0 |
| 2 | T_cam2gripper 矩陣 | D405標定 | **✅ 已更新為 Gemini.npy** | 🔴 致命 | P0 |
| 3 | PoseOffset dx 值 | +25.0mm | 可能需要微調 | 🟡 中等 | P1 |
| 4 | HandcamAngle2Yaw offset | -135.0° | 可能需要重新標定 | 🟡 中等 | P1 |
| 5 | GraspZOverride z值 | -394.5mm | 可能需要微調 | 🟡 中等 | P1 |

---

### 🟡 **應該驗證的地方**

| # | 項目 | 當前值 | 驗證方法 | 風險 |
|---|------|--------|--------|------|
| 1 | Orbbec 內參精度 | `fx, fy, cx, cy` | 執行自動化夾取，檢查座標偏差 | 準度不足 |
| 2 | T_cam2gripper 精度 | Gemini 305標定 | 執行手部相機偵測，檢查夾取位置 | 夾不準 |
| 3 | PoseOffset 補償值 | +25.0mm | 試運行，調整x/y/z直到最優 | 碰撞或夾不住 |
| 4 | HandcamAngle2Yaw 偏移 | -135.0° | 檢查物體抓取角度是否合理 | 夾爪角度錯誤 |
| 5 | GraspZOverride 桌面高度 | -394.5mm | 多次試運行，確保不碰撞 | 碰撞桌面 |
| 6 | Orbbec 深度精度 | 當前濾波器設定 | 比對D405和Orbbec的深度，看偏差 | 深度偏差大 |

---

### ✅ **已完成不需要改動**

| # | 項目 | 說明 |
|---|------|------|
| 1 | T_matrix_20260603_head30.npy | D435I 頭部標定（不變） |
| 2 | HeadCam2Base 轉換 | D435I 流程不變 |
| 3 | 頭部相機 yaw_offset | -45.0°（保持） |
| 4. | PlaceSequence 和 ReturnHome | 邏輯不變 |

---

## 🧪 **建議的驗證測試順序**

### **第一階段：基礎驗證（必做）**

```
1. ✅ 確認 Orbbec 內參已正確讀取
   → 在 Pixel2HandCam 中添加 debug log 打印內參
   → 對比已知的 Orbbec 內參值

2. ✅ 確認 T_cam2gripper_gemini.npy 已載入
   → 檢查 auto_grasp.py 第 151、186 行的載入日誌
   → 確認矩陣值合理

3. 執行手部相機偵測單獨測試
   → 物體放在已知位置
   → 檢查手部相機計算的位置是否準確
   → 對比頭部相機的位置
```

### **第二階段：整流程驗證（關鍵）**

```
4. 執行一次完整自動化夾取（不夾物體）
   → 觀察手臂是否移動到正確位置
   → 檢查 log 中的所有座標轉換

5. 逐項檢查夾取目標
   → 接近位置：手部相機是否能看清物體？
   → 夾取位置：法蘭末端是否對準物體？
   → yaw 角度：夾爪是否正確對齊？

6. 微調補償參數
   → 如果接近位置有偏差 → 調整 PoseOffset
   → 如果夾取角度有偏差 → 調整 HandcamAngle2Yaw offset
   → 如果高度有偏差 → 調整 GraspZOverride
```

### **第三階段：性能驗證（最後）**

```
7. 執行 10 次以上的完整夾取-放置循環
   → 評估成功率和精度穩定性
   → 識別任何偶發問題

8. 測試邊界情況
   → 器械在工作範圍邊界
   → 器械堆疊（多層）
   → 器械方向變化
```

---

## 💾 **關鍵配置文件清單**

### **必須存在的文件**

```
/home/bf-robotics/jazzy_gemini305_0628/kassow_RobotUse/
├── T_matrix_20260603_head30.npy          ✅ D435I → base
├── T_cam2gripper_gemini.npy              ✅ Orbbec → 法蘭 (已新增)
├── models/
│   ├── best.pt                            ✅ 頭部 YOLO
│   └── best20260603.pt                    ✅ 手部 YOLO
└── src/
    ├── auto_grasp.py                      ✅ 主流程
    ├── realsense.py                       ✅ 相機驅動
    └── ... (其他組件)
```

### **需要驗證的內參**

```
# D435I (頭部) - 固定
fx_D435I  = ~910.0
fy_D435I  = ~910.0
cx_D435I  = ~640.0
cy_D435I  = ~360.0

# Orbbec Gemini 305 (手部) - 需要驗證
fx_Orbbec = ?
fy_Orbbec = ?
cx_Orbbec = ?
cy_Orbbec = ?
```

---

## 🔗 **相機更換的連鎖影響圖**

```
Orbbec 相機更換
    ↓
├─ 內參變化 (fx, fy, cx, cy)
│   ├─ Pixel2HandCam 計算受影響 ⚠️
│   ├─ 座標精度±5-10mm
│   └─ 夾取精度受影響
│
├─ T_matrix 更新 (T_cam2gripper_gemini.npy)
│   ├─ HandCam2Flange 計算受影響
│   ├─ Angle2RzHandcam 計算受影響 ⚠️
│   ├─ 座標精度±3-5mm
│   └─ yaw 角度精度 ±5-10°
│
├─ 物理安裝角度可能變化
│   ├─ HandcamAngle2Yaw offset 可能需要調整 ⚠️
│   └─ 夾爪角度精度 ±10-20°
│
└─ 深度精度可能變化
    ├─ GraspZOverride 可能需要調整
    └─ 高度精度 ±5-10mm
```

---

## 📝 **調整清單（執行時參考）**

```
□ 1. 驗證 Orbbec 內參是否正確載入
     文件位置: auto_grasp.py _process_handcam()
     檢查: self._p2h.set_intrinsics() 的參數

□ 2. 驗證 T_cam2gripper_gemini.npy 是否正確載入
     文件位置: auto_grasp.py 第 151、186 行
     檢查: 載入成功的 log 信息

□ 3. 測試手部相機座標精度
     方法: 物體放在已知位置，比對計算結果
     目標: 誤差 < ±10mm

□ 4. 微調 PoseOffset (dx=25.0)
     影響: 接近位置的 x 軸偏移
     測試: ±10mm 調整，找最優值

□ 5. 微調 HandcamAngle2Yaw offset (-135.0°)
     影響: 夾爪角度
     測試: ±10° 調整，找最優值

□ 6. 驗證 GraspZOverride (z_mm=-394.5)
     影響: 夾取高度
     測試: 確保不碰撞，准確度最優

□ 7. 執行完整自動化流程測試 (至少 10 次)
     評估: 成功率、精度、穩定性

□ 8. 記錄所有調整參數和測試結果
```

---

**結論**: 相機更換主要影響手部相機的整個座標轉換鏈（Step 5），需要重點驗證內參、T矩陣和各種補償參數的正確性。

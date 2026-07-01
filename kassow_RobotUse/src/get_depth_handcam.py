"""
get_depth_handcam.py — 手腕相機（Orbbec Gemini 305）深度讀取物件（獨立工廠）

職責：
    從手腕相機（Orbbec Gemini 305）的深度圖，
    取得指定像素位置的深度值（mm）。

    功能與 DepthReader 相同，但完整獨立實作，不依賴 DepthReader：
    - 可針對 Gemini 305 特性獨立調整（近距離精度更高、有效深度範圍不同）
    - 內部修改不影響頭部相機的深度讀取

Gemini 305 特性：
    有效深度範圍：50mm ～ 1000mm（支援手腕親密距離拍攝）
    深度圖來源：Orbbec SDK depth stream（uint16，mm）

外部使用方式：
    gd = GetDepthHandcam(patch_size=5)
    depth_mm = gd.get_depth((cx, cy), depth_img)
    if depth_mm is not None:
        print(f'{depth_mm:.1f} mm')
"""

import collections
import numpy as np


class GetDepthHandcam:
    """
    手腕相機（Orbbec Gemini 305）深度讀取物件。

    空間濾波：patch 中位數採樣，自動過濾無效像素（深度=0）。
    時間濾波：最近 buffer_size 幀有效深度值的中位數，抑制跨幀隨機跳動。
    完整獨立，不依賴 DepthReader。
    """

    def __init__(self, patch_size: int = 5, buffer_size: int = 7):
        """
        patch_size  : 採樣區塊邊長（奇數），預設 5×5。
        buffer_size : 跨幀中位數緩衝幀數，預設 7 幀。
                      值越大越穩定，但對快速移動的響應越慢。
        """
        self._half        = max(1, patch_size // 2)
        self._buffer_size = max(1, buffer_size)
        self._depth_buf   = collections.deque(maxlen=self._buffer_size)

    # ── 主要功能 ──────────────────────────────────────────────────────────────

    def get_depth(self, pixel, depth_img: np.ndarray):
        """
        取得手腕相機指定像素位置的深度值（mm）。

        先對當前幀做 patch 空間中位數，再將結果放入跨幀緩衝，
        回傳緩衝內所有有效值的中位數（時間濾波）。

        參數：
            pixel     : (cx, cy) 像素座標（float 或 int 皆可）
            depth_img : H×W uint16 numpy array，
                        來自 /cam1/aligned_depth_to_color/image_raw

        回傳：
            float  — 深度值（mm），跨幀中位數
            None   — 越界、或 patch 內無有效深度（全為 0）時
        """
        if depth_img is None:
            return None

        H, W   = depth_img.shape[:2]
        cx, cy = float(pixel[0]), float(pixel[1])
        ui, vi = int(round(cx)), int(round(cy))

        if not (0 <= ui < W and 0 <= vi < H):
            return None

        h  = self._half
        y0 = max(0, vi - h);  y1 = min(H, vi + h + 1)
        x0 = max(0, ui - h);  x1 = min(W, ui + h + 1)

        patch = depth_img[y0:y1, x0:x1]
        valid = patch[patch > 0]

        if len(valid) == 0:
            return None

        # 空間中位數（單幀）
        frame_depth = float(np.median(valid))

        # 加入跨幀緩衝，回傳時間中位數
        self._depth_buf.append(frame_depth)
        return float(np.median(self._depth_buf))

    def reset_buffer(self):
        """清空跨幀深度緩衝，每次開始新一輪偵測前呼叫。"""
        self._depth_buf.clear()

    # ── 設定 ──────────────────────────────────────────────────────────────────

    def set_patch_size(self, patch_size: int):
        """動態調整採樣 patch 大小。"""
        self._half = max(1, patch_size // 2)

    def set_buffer_size(self, buffer_size: int):
        """動態調整跨幀緩衝大小，會清空現有緩衝。"""
        self._buffer_size = max(1, buffer_size)
        self._depth_buf   = collections.deque(maxlen=self._buffer_size)

    @property
    def patch_size(self) -> int:
        return self._half * 2 + 1

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

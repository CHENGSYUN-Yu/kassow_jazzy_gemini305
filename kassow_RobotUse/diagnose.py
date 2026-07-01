import sys
sys.path.insert(0, 'src')
from realsense import RealSense
import time

rs = RealSense(width=1280, height=720, fps=30)

print("\n【相機連線狀態診斷】")
for i in range(3):
    connected = rs.is_connected(i)
    status = "✅ 已連線" if connected else "❌ 未連線"
    print(f"Cam {i}: {status}")

print("\n【嘗試取紋理】")
for i in range(3):
    if rs.is_connected(i):
        time.sleep(0.5)
        tex = rs.get_texture(i, 'RGB')
        if tex is not None:
            print(f"Cam {i}: ✅ 紋理可用 {tex.shape}")
        else:
            print(f"Cam {i}: ❌ 紋理為 None")

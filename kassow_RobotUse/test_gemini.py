import sys
sys.path.insert(0, 'src')
from realsense import RealSense
import time

rs = RealSense(width=1280, height=720, fps=30)
print("\n【連接所有相機】")
count = rs.connect()
print(f"連接結果：{count}/3 台相機")

time.sleep(2)

print("\n【檢查 Cam 1 (Gemini 305)】")
if rs.is_connected(1):
    print("✅ Cam 1 已連線")

    # 等待幾幀讓相機初始化
    for i in range(10):
        tex = rs.get_texture(1, "RGB")
        if tex is not None:
            print(f"  第 {i+1} 幀：✅ 紋理可用 {tex.shape}")
            break
        time.sleep(0.2)
    else:
        print(f"  ❌ 10 幀後仍無紋理")
else:
    print("❌ Cam 1 未連線")

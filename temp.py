import math
import time
import os

def heart_frame(scale):
    lines = []
    for y in range(15, -15, -1):
        line = ""
        for x in range(-30, 30):
            xx = x * 0.05
            yy = y * 0.1 * scale
            if (xx**2 + yy**2 - 1)**3 - xx**2 * yy**3 <= 0:
                line += "*"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    while True:
        # 缩放系数，实现心跳大小变化
        for s in [1, 1.12, 1, 0.88]:
            os.system("cls")
            print(heart_frame(s))
            time.sleep(0.12)
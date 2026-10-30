# -*- coding: utf-8 -*-
"""抠绿幕：从画面边缘泛洪去除背景，再压掉残留绿边。

用法：
    python key_green.py 输入.png [输出.png]

不写输出时，保存为 <输入名>-keyed.png。
"""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def key_green(path_in: Path) -> Image.Image:
    im = Image.open(path_in).convert("RGBA")
    a = np.array(im).astype(np.int16)
    h, w = a.shape[:2]
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]

    # 宽松的"像绿"判定：只要绿色明显高过红蓝
    greenish = (g > r + 12) & (g > b + 12) & (g > 80)

    # 从四边泛洪：只有和边缘连通的绿才是背景
    bg = np.zeros((h, w), bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if greenish[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if greenish[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    while dq:
        cy, cx = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and greenish[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                dq.append((ny, nx))

    # 残留的强绿也算背景（避免头发上留一圈绿边）
    strong = (g > r + 40) & (g > b + 40)
    mask = bg | strong

    # 去绿边：把绿色压回不超过 max(r, b)
    mx = np.maximum(r, b)
    a[:, :, 1] = np.where(a[:, :, 1] > mx + 6, mx + 6, a[:, :, 1])
    a[:, :, 3] = np.where(mask, 0, 255)

    out = Image.fromarray(a.astype(np.uint8))
    bbox = out.getchannel("A").getbbox()
    return out.crop(bbox) if bbox else out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "-keyed.png")
    img = key_green(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    print(f"{dst}  {img.width}x{img.height}")


if __name__ == "__main__":
    main()

"""裁掉录音两头的静音，做无缝循环，输出适合网页的音频。

做法：
  1. 自动找有声区间（能量超过阈值的最长连续段）
  2. 前后各留 30ms 余量，避免把起音削掉
  3. 头尾各加 15ms 淡入淡出 —— 不加的话循环到接缝处会"啪"一声
  4. 峰值归一化到 0.89（留一点余量，防削顶）
  5. 重采样到 22050 Hz 单声道 —— 笑声不需要高保真，体积直接减半
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

SRC = Path(r"E:\00_workspace\dsh\haha-site\laugh-raw.wav")
OUT = Path(r"E:\00_workspace\dsh\haha-site\sounds")
OUT.mkdir(exist_ok=True)

# ---------- 读 ----------
with wave.open(str(SRC), "rb") as w:
    rate = w.getframerate()
    n_ch = w.getnchannels()
    raw = w.readframes(w.getnframes())

data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
if n_ch > 1:
    data = data.reshape(-1, n_ch).mean(axis=1)

print("=" * 62)
print("  裁剪")
print("=" * 62)
print(f"  原文件: {len(data) / rate:.2f} 秒 @ {rate} Hz")

# ---------- 1. 找有声区间 ----------
WIN = int(rate * 0.02)
nw = len(data) // WIN
env = np.array([float(np.sqrt(np.mean(data[i*WIN:(i+1)*WIN]**2))) for i in range(nw)])
floor = float(np.percentile(env, 20))
peak_all = float(np.max(np.abs(data)))
thresh = max(floor * 3.0, peak_all * 0.06, 0.008)

loud = env > thresh
# 最长连续有声段
best = (0, 0)
i = 0
while i < len(loud):
    if loud[i]:
        j = i
        while j < len(loud) and loud[j]:
            j += 1
        if j - i > best[1] - best[0]:
            best = (i, j)
        i = j
    else:
        i += 1

t0 = best[0] * 0.02
t1 = best[1] * 0.02
print(f"  有声区间: {t0:.2f}s ~ {t1:.2f}s  ({t1 - t0:.2f} 秒)")

# ---------- 2. 留余量 ----------
PAD = 0.03
a = max(0, int((t0 - PAD) * rate))
b = min(len(data), int((t1 + PAD) * rate))
seg = data[a:b].copy()
print(f"  加余量后: {a / rate:.2f}s ~ {b / rate:.2f}s  ({len(seg) / rate:.2f} 秒)")

# ---------- 3. 淡入淡出（防接缝爆音）----------
FADE = int(rate * 0.015)
if len(seg) > FADE * 2:
    seg[:FADE] *= np.linspace(0, 1, FADE, dtype=np.float32)
    seg[-FADE:] *= np.linspace(1, 0, FADE, dtype=np.float32)

# ---------- 4. 归一化 ----------
pk = float(np.max(np.abs(seg)))
if pk > 0:
    seg *= (0.89 / pk)
print(f"  归一化  : 峰值 {pk:.3f} → 0.89")

# ---------- 5. 重采样到 22050（两抽一，够用且体积减半）----------
TARGET = 22050
if rate != TARGET:
    idx = np.linspace(0, len(seg) - 1, int(len(seg) * TARGET / rate))
    seg = np.interp(idx, np.arange(len(seg)), seg).astype(np.float32)
    print(f"  重采样  : {rate} → {TARGET} Hz")

pcm = np.clip(seg, -1.0, 1.0)
pcm = (pcm * 32767).astype(np.int16)

# ---------- 输出 ----------
dst = OUT / "laugh.wav"
with wave.open(str(dst), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(TARGET)
    w.writeframes(pcm.tobytes())

print()
print("=" * 62)
print(f"  输出: {dst}")
print(f"  时长: {len(pcm) / TARGET:.2f} 秒")
print(f"  大小: {dst.stat().st_size / 1024:.0f} KB")
print("=" * 62)

# 顺便报告一下最终音频的音量，便于和页面其他声音配平
rms = float(np.sqrt(np.mean(seg ** 2)))
print(f"  最终 RMS: {rms:.4f}   峰值: 0.89")

"""录电脑**正在播放**的声音（WASAPI 环回）。

为什么不用 Windows 录音机：这台机器的 Realtek 驱动没提供「立体声混音」，
录音机只能录麦克风，录不到网页里放出来的声音。

环回（loopback）是 Windows 提供的另一条路：把「扬声器输出」当成一个
录音设备来读。开着网页放视频，这边就能原样录下来，音质是数字直录，
不经过空气，所以比拿麦克风对着音箱录干净得多。

用法：
    python rec.py 20            录 20 秒，存成 rec.wav
    python rec.py 20 laugh.wav  指定输出文件名
"""

from __future__ import annotations

import sys
import time
import wave
from pathlib import Path

import numpy as np
import soundcard as sc

RATE = 48000          # 采样率
CHUNK = 0.1           # 每次读多少秒（用来做实时电平显示）


def main() -> int:
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "rec.wav")
    if not out.is_absolute():
        out = Path(__file__).resolve().parent / out

    spk = sc.default_speaker()
    try:
        mic = sc.get_microphone(id=str(spk.name), include_loopback=True)
    except Exception as exc:  # noqa: BLE001
        print(f"找不到 {spk.name} 的环回设备：{exc}")
        return 1

    print("=" * 56)
    print("  录电脑正在播放的声音（环回）")
    print("=" * 56)
    print(f"  扬声器  : {spk.name}")
    print(f"  录音源  : {mic.name}")
    print(f"  时长    : {secs:.0f} 秒")
    print(f"  输出    : {out}")
    print()

    # 倒计时，留出切到浏览器播放视频的时间
    for i in (3, 2, 1):
        print(f"  {i} ...", flush=True)
        time.sleep(1)
    print("  ● 开始！现在去播放视频", flush=True)

    frames: list[np.ndarray] = []
    done = 0.0
    bar_last = -1
    with mic.recorder(samplerate=RATE, channels=2) as rec:
        while done < secs:
            block = rec.record(numframes=int(RATE * CHUNK))
            frames.append(block)
            done += CHUNK

            # 实时电平：让用户看得出到底录进去没有
            lvl = float(np.max(np.abs(block))) if block.size else 0.0
            bars = min(28, int(lvl * 90))
            mark = "#" * bars + "." * (28 - bars)
            pct = int(done / secs * 100)
            if pct // 5 != bar_last:
                bar_last = pct // 5
                print(f"  [{mark}] {pct:3d}%", flush=True)

    print("  ■ 录完了", flush=True)

    data = np.concatenate(frames, axis=0) if frames else np.zeros((1, 2))
    mono = data.mean(axis=1) if data.ndim > 1 else data

    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(mono ** 2))) if mono.size else 0.0

    print()
    print(f"  峰值  : {peak:.4f}")
    print(f"  均方根: {rms:.4f}")
    if peak < 0.01:
        print("  ⚠ 几乎没录到声音 —— 检查：视频在播吗？音量开了吗？")
        print("     也可能声音走的是另一个输出设备（比如 HDMI 显示器）。")
    else:
        print("  ✓ 录到了")

    pcm = np.clip(mono, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())

    size_kb = out.stat().st_size / 1024
    print()
    print(f"  已保存: {out}")
    print(f"  大小  : {size_kb:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

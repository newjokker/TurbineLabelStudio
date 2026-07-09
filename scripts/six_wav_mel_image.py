#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate one stacked mel jpg from exactly 6 wav files.

This version is intentionally light on dependencies for TurbineLabelStudio:
it only needs numpy, scipy and soundfile. It does not call the original
dcu_interface WavList/DataGroup helpers, and it does not require librosa,
matplotlib, opencv, pillow, or noisereduce.
"""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt, stft

PathLike = Union[str, os.PathLike]

DEFAULT_MEL_CONFIG = {
    "n_fft": 2048,
    "hop_length": 512,
    "n_mels": 128,
    "fmax": 24000,
    "cutoff_freq": 500,
    "filter_order": 5,
    # "reorder": [0, 3, 1, 4, 2, 5],
    "reorder": [0,1,2,3,4,5],
    "output_width": 1200,
    "row_height": 200,
    "vmin_db": -50,
    "vmax_db": 0,
}

VIRIDIS_ANCHORS = np.array(
    [
        [68, 1, 84],
        [72, 35, 116],
        [64, 67, 135],
        [52, 94, 141],
        [41, 120, 142],
        [32, 144, 140],
        [34, 167, 132],
        [68, 190, 112],
        [121, 209, 81],
        [189, 223, 38],
        [253, 231, 37],
    ],
    dtype=np.float32,
)


def _validate_wav_files(wav_files: Sequence[str]) -> List[str]:
    if len(wav_files) != 6:
        raise ValueError("wav_files 必须正好传入 6 个 wav 文件")

    wav_paths = [str(Path(p).expanduser().resolve()) for p in wav_files]
    for wav_path in wav_paths:
        if not Path(wav_path).is_file():
            raise FileNotFoundError(f"wav 文件不存在: {wav_path}")
    return wav_paths


def _to_mono(data: np.ndarray) -> np.ndarray:
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 1:
        return data
    return np.mean(data, axis=1).astype(np.float32)


def _repeat_audio_to_20_seconds(data: np.ndarray, sr: int) -> np.ndarray:
    if data is None or len(data) < sr:
        return data

    seconds = int(len(data) / sr)
    if seconds == 0 or seconds >= 18:
        return data

    energies = [np.sum(data[i * sr:(i + 1) * sr] ** 2) for i in range(seconds)]
    quietest_idx = int(np.argmin(energies))
    quietest = data[quietest_idx * sr:(quietest_idx + 1) * sr]

    seconds_to_fill = 20 - seconds
    fill_front = seconds_to_fill // 2
    fill_back = seconds_to_fill - fill_front
    return np.concatenate([np.tile(quietest, fill_front), data, np.tile(quietest, fill_back)]).astype(np.float32)


def _highpass_filter(data: np.ndarray, sr: int, cutoff: float, order: int) -> np.ndarray:
    nyquist = 0.5 * sr
    if cutoff <= 0 or cutoff >= nyquist:
        return data.astype(np.float32)
    b, a = butter(order, cutoff / nyquist, btype="high", analog=False)
    return filtfilt(b, a, data).astype(np.float32)


def _read_wav_for_mel(wav_path: str) -> Tuple[np.ndarray, int]:
    data, sr = sf.read(wav_path)
    data = _to_mono(data)
    data = _repeat_audio_to_20_seconds(data, int(sr))
    return data, int(sr)


def _hz_to_mel(freq_hz: np.ndarray) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + freq_hz / 700.0)


def _mel_to_hz(mel: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def _mel_filterbank(sr: int, n_fft: int, n_mels: int, fmax: float) -> np.ndarray:
    fmax = min(float(fmax), sr / 2.0)
    mel_points = np.linspace(_hz_to_mel(np.array([0.0]))[0], _hz_to_mel(np.array([fmax]))[0], n_mels + 2)
    hz_points = _mel_to_hz(mel_points)
    fft_freqs = np.linspace(0.0, sr / 2.0, n_fft // 2 + 1)

    filters = np.zeros((n_mels, len(fft_freqs)), dtype=np.float32)
    for i in range(n_mels):
        left, center, right = hz_points[i], hz_points[i + 1], hz_points[i + 2]
        if center <= left or right <= center:
            continue
        rising = (fft_freqs - left) / (center - left)
        falling = (right - fft_freqs) / (right - center)
        filters[i] = np.maximum(0.0, np.minimum(rising, falling))
    return filters


def _make_mel(data: np.ndarray, sr: int, config: dict) -> np.ndarray:
    filtered = _highpass_filter(
        data,
        sr,
        cutoff=config["cutoff_freq"],
        order=config["filter_order"],
    )
    _, _, zxx = stft(
        filtered,
        fs=sr,
        window="hann",
        nperseg=config["n_fft"],
        noverlap=config["n_fft"] - config["hop_length"],
        nfft=config["n_fft"],
        boundary=None,
        padded=False,
    )
    power = np.abs(zxx) ** 2
    mel_filters = _mel_filterbank(sr, config["n_fft"], config["n_mels"], config["fmax"])
    return np.maximum(np.dot(mel_filters, power), 1e-12)


def _power_to_db(mel: np.ndarray, ref_power: float) -> np.ndarray:
    return 10.0 * np.log10(np.maximum(mel, 1e-12) / max(ref_power, 1e-12))


def _resize_2d(values: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
    src_h, src_w = values.shape
    x_old = np.arange(src_w)
    x_new = np.linspace(0, src_w - 1, target_w)
    resized_w = np.empty((src_h, target_w), dtype=np.float32)
    for row in range(src_h):
        resized_w[row] = np.interp(x_new, x_old, values[row])

    y_old = np.arange(src_h)
    y_new = np.linspace(0, src_h - 1, target_h)
    resized = np.empty((target_h, target_w), dtype=np.float32)
    for col in range(target_w):
        resized[:, col] = np.interp(y_new, y_old, resized_w[:, col])
    return resized


def _apply_viridis(normalized: np.ndarray) -> np.ndarray:
    normalized = np.clip(normalized, 0.0, 1.0)
    positions = normalized * (len(VIRIDIS_ANCHORS) - 1)
    left = np.floor(positions).astype(np.int32)
    right = np.clip(left + 1, 0, len(VIRIDIS_ANCHORS) - 1)
    frac = (positions - left)[..., None]
    rgb = VIRIDIS_ANCHORS[left] * (1.0 - frac) + VIRIDIS_ANCHORS[right] * frac
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _mel_to_rgb_row(mel: np.ndarray, ref_power: float, config: dict) -> np.ndarray:
    mel_db = _power_to_db(mel, ref_power)
    mel_db = _resize_2d(mel_db, config["row_height"], config["output_width"])
    mel_db = np.flipud(mel_db)
    normalized = (mel_db - config["vmin_db"]) / (config["vmax_db"] - config["vmin_db"])
    return _apply_viridis(normalized)


def _write_ppm(rgb: np.ndarray, ppm_path: Path) -> None:
    h, w, _ = rgb.shape
    header = f"P6\n{w} {h}\n255\n".encode("ascii")
    ppm_path.write_bytes(header + np.ascontiguousarray(rgb).tobytes())


def _save_rgb_image(rgb: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        ppm_path = Path(tmpdir) / "stacked.ppm"
        _write_ppm(rgb, ppm_path)

        sips = shutil.which("sips")
        if sips:
            subprocess.run(
                [sips, "-s", "format", "jpeg", str(ppm_path), "--out", str(output_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", str(ppm_path), str(output_path)],
                check=True,
            )
            return

        magick = shutil.which("magick") or shutil.which("convert")
        if magick:
            subprocess.run([magick, str(ppm_path), str(output_path)], check=True)
            return

        raise RuntimeError("无法保存 jpg：需要系统存在 sips、ffmpeg、magick/convert 中的任意一个")


def wavs_to_stacked_mel_image(
    wav_files: Sequence[str],
    mel_config: Optional[dict] = None,
) -> np.ndarray:
    """将 6 个 wav 转成纵向拼接的梅尔频谱 RGB 图片数组。"""
    config = dict(DEFAULT_MEL_CONFIG)
    if mel_config:
        config.update(mel_config)

    wav_paths = _validate_wav_files(wav_files)
    wav_datas = [_read_wav_for_mel(wav_path) for wav_path in wav_paths]
    min_length = min(len(data) / sr for data, sr in wav_datas)
    if min_length < 9:
        raise ValueError("wav 时长过短，最短音频不足 9 秒")

    target_mels = []
    max_power = -np.inf
    for data, sr in wav_datas:
        target_len = int(min_length * sr)
        mel = _make_mel(data[:target_len], sr, config)
        target_mels.append(mel)
        max_power = max(max_power, float(np.max(mel)))

    rows = []
    for wav_idx in config["reorder"]:
        rows.append(_mel_to_rgb_row(target_mels[wav_idx], max_power, config))
    return np.vstack(rows)


def save_6_wavs_mel_jpg(
    wav_files: Sequence[str],
    jpg_path: PathLike,
    mel_config: Optional[dict] = None,
) -> str:
    """将 6 个 wav 生成梅尔频谱拼接图，并保存为 jpg。"""
    output_path = Path(jpg_path).expanduser().resolve()
    rgb = wavs_to_stacked_mel_image(wav_files, mel_config=mel_config)
    _save_rgb_image(rgb, output_path)
    return str(output_path)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate one stacked mel jpg from exactly 6 wav files.")
    parser.add_argument("wav_files", nargs="*", help="Exactly 6 wav file paths.")
    parser.add_argument("-o", "--output", default="test_mel.jpg", help="Output jpg path.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.wav_files:
        wav_list = args.wav_files
    else:
        wav_list = [
            "/Volumes/Jokker/Code/TurbineLabelStudio/data/test/BUC_000086/0b6fab18df34d68627ba81468806fd70.wav",
            "/Volumes/Jokker/Code/TurbineLabelStudio/data/test/BUC_000086/174586a5f685b88966ce5c8eb50cff50.wav",
            "/Volumes/Jokker/Code/TurbineLabelStudio/data/test/BUC_000086/aceb8572766c154d7e1078fd11e0df6a.wav",
            "/Volumes/Jokker/Code/TurbineLabelStudio/data/test/BUC_000086/c5e8b0b8e8cefffe340c5c6e27d8d910.wav",
            "/Volumes/Jokker/Code/TurbineLabelStudio/data/test/BUC_000086/dc25c98eb680ba32a76918a6c294450f.wav",
            "/Volumes/Jokker/Code/TurbineLabelStudio/data/test/BUC_000086/e311a986c3368ccca5c0031505f76c3d.wav",
        ]

    saved_path = save_6_wavs_mel_jpg(wav_list, args.output)
    print(f"梅尔拼接图已保存: {saved_path}")


if __name__ == "__main__":
    main()

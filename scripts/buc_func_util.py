
from pathlib import Path
import cv2
import librosa
import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')  
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from scipy import signal


DEFAULT_IMAGE_CONFIG = {
    "n_fft": 2048,
    "hop_length": 512,
    "n_mels": 128,
    "fmax": 24000,
    "cutoff_freq": 500,
    "filter_order": 5,
    "reorder": [0, 1, 2, 3, 4, 5],
}


def get_buc_image_by_func(file_list, func_name, save_path):
    """根据方法和 buc 获取 mel 图"""
    # buc 获取 
    
    if func_name == "wh_jzp_before_20260708":
        return wh_jzp_before_20260708(file_list, save_path)

def wh_jzp_before_20260708(wav_files, jpg_path):
    """将 6 个 wav 生成梅尔频谱拼接图，并保存为 jpg。"""
    
    output_path = Path(jpg_path).expanduser().resolve()
    return generate_wav_image(wav_files, output_path)

def generate_wav_image(wav_path_list, output_path):
    """
    Generate a stacked mel image from ordered wav paths.

    wav_path_list must be ordered by measurement point:
    [1A, 1B, 2A, 2B, 3A, 3B].
    Fill missing measurement points with None to keep their rows blank.
    """
    data_type = _detect_wav_data_type(wav_path_list)
    img_array = wav_paths_to_img_array(wav_path_list, DEFAULT_IMAGE_CONFIG, data_type=data_type)
    return _write_img_array(img_array, output_path)


def wav_paths_to_img(wav_items, data_type, output_path, status=None, collect_time=None, image_config=None):
    """Generate a mel voiceprint image from wav paths and point metadata."""
    wav_paths = _extract_wav_paths(wav_items)
    img_array = wav_paths_to_img_array(wav_paths, image_config or DEFAULT_IMAGE_CONFIG, data_type=data_type)
    return _write_img_array(img_array, output_path)


def wav_paths_to_img_array(wav_paths, image_config=None, data_type="blade"):
    """Convert wav paths to a six-channel mel image array."""
    config = {**DEFAULT_IMAGE_CONFIG, **(image_config or {})}
    audio_list, sample_rate = _load_audio_list(wav_paths)
    audio_list = _prepare_audio_list(audio_list, sample_rate, data_type)
    mel_list = [_audio_to_mel(audio, sample_rate, config) if audio is not None else None for audio in audio_list]
    return _draw_mel_image(mel_list, sample_rate, config)


def _extract_wav_paths(wav_items):
    """Extract wav paths from point metadata."""
    if not wav_items:
        raise ValueError("wav_items cannot be empty")
    return [item["wav_path"] for item in wav_items]


def _detect_wav_data_type(wav_path_list):
    """Detect data type from ordered wav path sizes."""
    valid_paths = [Path(wav_path) for wav_path in wav_path_list if wav_path is not None]
    if not valid_paths:
        raise ValueError("wav_path_list must contain at least one real wav path")
    if any(path.stat().st_size < 1024 * 1024 for path in valid_paths):
        return "blade_ddn"
    return "blade"


def get_wav_image_duration_seconds(wav_path_list):
    """返回当前 mel 图片1200px横轴对应的实际秒数。

    这里只读取 WAV 头信息，但时长处理规则与 ``wav_paths_to_img_array``
    保持一致：普通6通道取重采样后的最短长度，blade_ddn 使用补齐后的长度。
    """
    data_type = _detect_wav_data_type(wav_path_list)
    valid_paths = [Path(wav_path) for wav_path in wav_path_list if wav_path is not None]
    infos = [sf.info(str(wav_path)) for wav_path in valid_paths]
    sample_rate = infos[0].samplerate

    lengths = [
        info.frames
        if info.samplerate == sample_rate
        else int(np.ceil(info.frames * sample_rate / info.samplerate))
        for info in infos
    ]

    if data_type == "blade_ddn":
        source_length = lengths[0]
        if source_length < sample_rate:
            raise ValueError("audio must be at least one second")
        whole_seconds = int(source_length / sample_rate)
        if whole_seconds >= 18:
            image_length = min(source_length, 20 * sample_rate)
        else:
            image_length = source_length + (20 - whole_seconds) * sample_rate
        return image_length / float(sample_rate)

    return min(lengths) / float(sample_rate)


def _load_audio_list(wav_paths):
    """Read wav files and normalize them to mono arrays."""
    audio_list = []
    sample_rate = None
    for wav_path in wav_paths:
        if wav_path is None:
            audio_list.append(None)
            continue
        audio, current_sample_rate = sf.read(str(wav_path))
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        if sample_rate is None:
            sample_rate = current_sample_rate
        elif current_sample_rate != sample_rate:
            audio = librosa.resample(audio.astype(np.float32), orig_sr=current_sample_rate, target_sr=sample_rate)
        audio_list.append(audio.astype(np.float32))
    if sample_rate is None:
        raise ValueError("wav_paths must contain at least one real wav path")
    return audio_list, sample_rate


def _fill_audio_list(audio_list, target_count=6):
    """Pad audio channels to the target count with empty placeholders."""
    if len(audio_list) > target_count:
        return audio_list[:target_count]
    return audio_list + [None] * (target_count - len(audio_list))


def _prepare_audio_list(audio_list, sample_rate, data_type):
    """Prepare audio channels according to the data type."""
    if data_type == "blade_ddn":
        return _prepare_blade_ddn_audio_list(audio_list, sample_rate)
    audio_list = _fill_audio_list(audio_list)
    return _trim_to_min_length(audio_list, sample_rate)


def _prepare_blade_ddn_audio_list(audio_list, sample_rate):
    """Repeat one blade_ddn wav to 20 seconds and copy it to rows one, three, and five."""
    source_audio = next((audio for audio in audio_list if audio is not None), None)
    if source_audio is None:
        raise ValueError("blade_ddn requires at least one wav file")
    audio = _repeat_audio_to_20_seconds(source_audio, sample_rate)
    return [audio.copy(), None, audio.copy(), None, audio.copy(), None]


def _repeat_audio_to_20_seconds(audio, sample_rate):
    """Pad audio to 20 seconds with the quietest one-second segment."""
    if audio is None or len(audio) < sample_rate:
        raise ValueError("audio must be at least one second")
    seconds = int(len(audio) / sample_rate)
    if seconds >= 18:
        return audio[:20 * sample_rate]
    quietest_index = int(np.argmin([
        np.sum(audio[index * sample_rate:(index + 1) * sample_rate] ** 2)
        for index in range(seconds)
    ]))
    quietest = audio[quietest_index * sample_rate:(quietest_index + 1) * sample_rate]
    seconds_to_fill = 20 - seconds
    fill_front = seconds_to_fill // 2
    fill_back = seconds_to_fill - fill_front
    return np.concatenate([
        np.tile(quietest, fill_front),
        audio,
        np.tile(quietest, fill_back),
    ])


def _trim_to_min_length(audio_list, sample_rate):
    """Trim all existing channels to the same shortest duration."""
    valid_audio = [audio for audio in audio_list if audio is not None and len(audio) > 0]
    if not valid_audio:
        raise ValueError("no readable wav audio")
    min_length = min(len(audio) for audio in valid_audio)
    min_length = max(min_length, min(sample_rate, min_length))
    return [audio[:min_length] if audio is not None else None for audio in audio_list]


def _audio_to_mel(audio, sample_rate, config):
    """Convert one audio channel to a denoised mel spectrogram."""
    filtered = _highpass_filter(audio, sample_rate, config["cutoff_freq"], config["filter_order"])
    return librosa.feature.melspectrogram(
        y=filtered,
        sr=sample_rate,
        n_fft=config["n_fft"],
        hop_length=config["hop_length"],
        win_length=config["n_fft"],
        n_mels=config["n_mels"],
        fmax=config["fmax"],
    )


def _highpass_filter(audio, sample_rate, cutoff_freq, filter_order):
    """Apply a high-pass filter before mel conversion."""
    sos = signal.butter(filter_order, cutoff_freq, btype="highpass", fs=sample_rate, output="sos")
    return signal.sosfiltfilt(sos, audio)


def _draw_mel_image(mel_list, sample_rate, config):
    """Draw mel spectrograms into one stacked image."""
    max_power = max(float(np.max(mel)) for mel in mel_list if mel is not None)
    fig, axes = plt.subplots(nrows=6, ncols=1, figsize=(12, 12), sharex="all", sharey="all")
    for row_index, wav_index in enumerate(config["reorder"]):
        ax = axes[row_index]
        mel = mel_list[wav_index]
        if mel is not None:
            librosa.display.specshow(
                librosa.power_to_db(mel, ref=max_power),
                sr=sample_rate,
                x_axis="time",
                y_axis="mel",
                fmax=config["fmax"],
                ax=ax,
                cmap="viridis",
                vmin=-50,
                vmax=0,
            )
            ax.set_ylim(0, config["fmax"])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.tick_params(left=False, bottom=False)
        ax.set_frame_on(False)
        ax.set_ylabel("")
        ax.set_xlabel("")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
    
    canvas = FigureCanvas(fig)
    canvas.draw()
    
    # 修改这部分：使用 tostring_argb() 替代 tostring_rgb()
    width, height = canvas.get_width_height()
    
    # 兼容不同版本的 Matplotlib
    if hasattr(canvas, 'tostring_argb'):
        # 使用 ARGB 格式，移除 Alpha 通道
        img_array = np.frombuffer(canvas.tostring_argb(), dtype="uint8").reshape(
            (height, width, 4)
        )[:, :, 1:4]  # 取 RGB 通道
    elif hasattr(canvas, 'tostring_rgb'):
        # 旧版本使用 RGB 格式
        img_array = np.frombuffer(canvas.tostring_rgb(), dtype="uint8").reshape(
            (height, width, 3)
        )
    else:
        # 备用方案：使用 buffer_rgba
        buffer = canvas.buffer_rgba()
        img_array = np.frombuffer(buffer, dtype="uint8").reshape(
            (height, width, 4)
        )[:, :, :3]
    
    plt.close(fig)
    return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

def _write_img_array(img_array, output_path):
    """Write an OpenCV image array to the output path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix or ".jpg"
    success, encoded = cv2.imencode(suffix, img_array)
    if not success:
        raise RuntimeError(f"image encode failed: {path}")
    encoded.tofile(str(path))
    return path


if __name__ == "__main__":
    
    wav_path = "/Volumes/Jokker/Code/TurbineLabelStudio/2026_05_22_05_40_12_风机F007_叶片1测点B.wav"
    
    wh_jzp_before_20260708([wav_path], "res.jpg")

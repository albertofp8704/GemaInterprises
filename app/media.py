"""Image + slideshow video generation for the faceless-script tool.

Images: Kandinsky 3 (open-source) via Replicate.
Storage: Cloudinary.
Video: ffmpeg Ken Burns slideshow, assembled server-side.
"""
import os
import shutil
import subprocess
import tempfile

import httpx
import replicate
import cloudinary
import cloudinary.uploader

KANDINSKY_MODEL = "ai-forever/kandinsky-3"
WORDS_PER_SECOND = 2.5
MIN_SCENE_SECONDS = 2.5
FPS = 25


def images_configured() -> bool:
    return bool(os.getenv("REPLICATE_API_TOKEN")) and bool(os.getenv("CLOUDINARY_URL"))


def generate_scene_image(prompt: str, script_id: int, scene_order: int) -> str:
    output = replicate.run(KANDINSKY_MODEL, input={"prompt": prompt})
    image_url = str(output[0] if isinstance(output, list) else output)

    uploaded = cloudinary.uploader.upload(
        image_url,
        folder=f"gema/scripts/{script_id}",
        public_id=f"scene_{scene_order}",
        overwrite=True,
        resource_type="image",
    )
    return uploaded["secure_url"]


def _scene_duration(word_count: int) -> float:
    return max(MIN_SCENE_SECONDS, word_count / WORDS_PER_SECOND)


def _srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_subtitles(scenes) -> str:
    lines = []
    t = 0.0
    for i, scene in enumerate(scenes, start=1):
        duration = _scene_duration(len(scene.text.split()))
        lines.append(str(i))
        lines.append(f"{_srt_timestamp(t)} --> {_srt_timestamp(t + duration)}")
        lines.append(scene.text.strip())
        lines.append("")
        t += duration
    return "\n".join(lines)


def assemble_slideshow_video(scenes, script_id: int) -> tuple[str, str]:
    """Builds a Ken Burns slideshow from scene images + an .srt of the narration.

    Returns (video_secure_url, subtitles_secure_url).
    """
    workdir = tempfile.mkdtemp(prefix=f"gema_video_{script_id}_")
    try:
        clip_paths = []
        with httpx.Client(timeout=30) as hc:
            for i, scene in enumerate(scenes):
                img_path = os.path.join(workdir, f"scene_{i}.jpg")
                resp = hc.get(scene.image_url)
                resp.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(resp.content)

                duration = _scene_duration(len(scene.text.split()))
                frames = max(1, int(duration * FPS))
                clip_path = os.path.join(workdir, f"clip_{i}.mp4")
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
                        "-vf",
                        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
                        f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:s=1280x720:fps={FPS}",
                        "-t", str(duration), "-pix_fmt", "yuv420p", clip_path,
                    ],
                    check=True, capture_output=True,
                )
                clip_paths.append(clip_path)

        list_path = os.path.join(workdir, "list.txt")
        with open(list_path, "w") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")

        output_path = os.path.join(workdir, "final.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output_path],
            check=True, capture_output=True,
        )

        video_uploaded = cloudinary.uploader.upload(
            output_path,
            folder=f"gema/scripts/{script_id}",
            public_id="video",
            overwrite=True,
            resource_type="video",
        )

        srt_path = os.path.join(workdir, "subtitles.srt")
        with open(srt_path, "w") as f:
            f.write(build_subtitles(scenes))
        srt_uploaded = cloudinary.uploader.upload(
            srt_path,
            folder=f"gema/scripts/{script_id}",
            public_id="subtitles",
            overwrite=True,
            resource_type="raw",
        )

        return video_uploaded["secure_url"], srt_uploaded["secure_url"]
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

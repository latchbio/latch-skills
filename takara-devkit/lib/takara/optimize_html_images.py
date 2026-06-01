import re
import base64
import io
from PIL import Image
from latch.ldata.path import LPath


def optimize(src: LPath, ldata_dst_dir: str) -> None:
    max_width = 2000

    html_path = src.download(cache=True)
    html = html_path.read_text()

    def replace_image(match: re.Match[str]) -> str:
        raw = base64.b64decode(match.group(1))
        img = Image.open(io.BytesIO(raw))

        if img.mode in ("P", "PA"):
            img = img.convert("RGBA")
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        if w > max_width:
            img = img.resize(
                (max_width, int(h * max_width / w)), Image.Resampling.LANCZOS
            )

        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/webp;base64,{b64}"

    pattern = r"data:image/[a-z]+;base64,([A-Za-z0-9+/=\s]+)"
    result = re.sub(pattern, replace_image, html)

    out_path = html_path.with_suffix(".optimized.html")
    out_path.write_text(result)
    LPath(f"{ldata_dst_dir}/{out_path.name}").upload_from(out_path)

"""
from lplots.widgets.ldata import w_ldata_picker

path = w_ldata_picker(label="select html file").value

if path is not None:
    optimize(src=path, ldata_dst_dir=...)
"""

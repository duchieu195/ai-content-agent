import base64
import os
from pathlib import Path

import anthropic

STYLE_FILE = Path(__file__).parent / "style_data" / "my_posts.txt"


def _load_style_samples() -> str:
    if not STYLE_FILE.exists():
        return ""
    return STYLE_FILE.read_text(encoding="utf-8").strip()


SYSTEM_PROMPT = """\
Bạn là một AI ghostwriter chuyên nghiệp. Nhiệm vụ của bạn là viết bài đăng Facebook \
ngắn dựa trên ý tưởng thô mà người dùng cung cấp.

## Quy tắc bắt buộc

1. **Phong cách viết**: Bạn PHẢI bắt chước chính xác phong cách viết từ các bài mẫu bên dưới. \
Hãy phân tích kỹ:
   - Giọng văn (formal hay casual, hài hước hay nghiêm túc)
   - Cách ngắt dòng, xuống hàng
   - Cách sử dụng emoji (loại emoji, tần suất, vị trí đặt)
   - Cấu trúc bài viết (mở bài, thân bài, kết bài)
   - Độ dài trung bình của bài viết
   - Các pattern lặp lại (câu hỏi tu từ, call-to-action, hashtag...)

2. **Nội dung**: Chỉ trả về bài đăng Facebook hoàn chỉnh, sẵn sàng copy-paste. \
Không giải thích, không thêm ghi chú, không bọc trong markdown code block.

3. **Ngôn ngữ**: Viết bằng đúng ngôn ngữ mà các bài mẫu sử dụng.

4. **Khi có ảnh sản phẩm**: Quan sát kỹ ảnh để nhận diện tên sản phẩm, thương hiệu, \
dung tích, mùi hương, thành phần nổi bật in trên bao bì. Dùng các thông tin đó làm \
nguyên liệu cho bài viết. Nếu thông tin nào không đọc rõ từ ảnh, đừng bịa ra.

## Các bài viết mẫu để học phong cách

{style_samples}
"""


def _build_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    )


def _extract_text(message) -> str:
    for block in message.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


def _system_prompt() -> str:
    style_samples = _load_style_samples()
    if not style_samples:
        style_samples = "(Chưa có bài mẫu — viết theo phong cách tự nhiên, gần gũi trên Facebook.)"
    return SYSTEM_PROMPT.format(style_samples=style_samples)


def generate_post(raw_content: str) -> str:
    client = _build_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": f"Ý tưởng thô: {raw_content}\n\nHãy viết thành bài đăng Facebook.",
            }
        ],
    )
    return _extract_text(message)


def generate_post_from_image(image_bytes: bytes, caption: str = "", media_type: str = "image/jpeg") -> str:
    client = _build_client()

    user_text = (
        "Đây là ảnh sản phẩm mình muốn đăng. Hãy đọc thông tin trên bao bì "
        "(tên, thương hiệu, dung tích, công dụng, thành phần nổi bật...) rồi viết "
        "thành bài đăng Facebook theo phong cách đã học."
    )
    if caption.strip():
        user_text += f"\n\nGhi chú thêm từ mình: {caption.strip()}"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    return _extract_text(message)

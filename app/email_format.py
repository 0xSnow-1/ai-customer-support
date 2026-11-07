import re

SIGN_OFF = "Harbor & Pine support"


def format_email(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    text = text.replace("\\t", " ").replace('\\"', '"')
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?<!\n)(?<!\A)(?=\d{1,2}\.\s*[A-Z])", "\n", text)
    text = re.sub(
        r"^([A-Z][^,\n]{0,40},)\s*(.)",
        lambda match: f"{match.group(1)}\n\n{match.group(2).upper()}",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(rf"\s*({re.escape(SIGN_OFF)})\s*\.?\s*$", r"\n\n\1", text, count=1)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()

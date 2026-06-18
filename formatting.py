import html
import re


def _superscripts(text: str) -> str:
    mapping = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻", "+": "⁺", "n": "ⁿ"}
    return re.sub(
        r"\^\{([^}]+)\}|\^(\d)",
        lambda m: "".join(mapping.get(c, c) for c in (m.group(1) or m.group(2))),
        text,
    )


def _subscripts(text: str) -> str:
    mapping = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"}
    return re.sub(
        r"_\{([^}]+)\}|_(\d)",
        lambda m: "".join(mapping.get(c, c) for c in (m.group(1) or m.group(2))),
        text,
    )


def _latex_to_plain(text: str) -> str:
    replacements = {
        r"\Delta": "Δ",
        r"\pm": "±",
        r"\mp": "∓",
        r"\times": "×",
        r"\div": "÷",
        r"\cdot": "·",
        r"\leq": "≤",
        r"\geq": "≥",
        r"\neq": "≠",
        r"\approx": "≈",
        r"\infty": "∞",
        r"\pi": "π",
        r"\alpha": "α",
        r"\beta": "β",
        r"\gamma": "γ",
        r"\theta": "θ",
        r"\rightarrow": "→",
        r"\leftarrow": "←",
        r"\Rightarrow": "⇒",
        r"\,": " ",
        r"\;": " ",
        r"\!": "",
        r"\text{": "",
        r"\mathrm{": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    while True:
        match = re.search(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", text)
        if not match:
            break
        text = text[: match.start()] + f"({match.group(1)})/({match.group(2)})" + text[match.end() :]

    while True:
        match = re.search(r"\\sqrt\{([^{}]+)\}", text)
        if not match:
            break
        text = text[: match.start()] + f"√({match.group(1)})" + text[match.end() :]

    text = re.sub(r"\\\[|\\\]|\\\(|\\\)|\$", "", text)
    text = _superscripts(text)
    text = _subscripts(text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = text.replace("{", "").replace("}", "")
    return text


def _markdown_to_html(text: str) -> str:
    lines_out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            lines_out.append(f"<b>{html.escape(stripped[4:])}</b>")
        elif stripped.startswith("## "):
            lines_out.append(f"<b>{html.escape(stripped[3:])}</b>")
        elif stripped == "---":
            lines_out.append("────────────")
        else:
            escaped = html.escape(line)
            escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
            escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
            lines_out.append(escaped)
    return "\n".join(lines_out)


def format_for_telegram(text: str) -> str:
    """Convert AI output to readable Telegram HTML (no LaTeX rendering in Telegram)."""
    text = _latex_to_plain(text)
    text = _markdown_to_html(text)
    return text.strip()

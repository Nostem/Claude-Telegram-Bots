"""Text shown for cards. Telegram HTML formatting; all card text is escaped."""
from html import escape


def side(reversed_):
    return "reversed" if reversed_ else "upright"


def title(card, reversed_):
    return f"{card.name} (reversed)" if reversed_ else card.name


def caption(card, reversed_, heading=None):
    """Short text under the card image: name, keywords, one-line meaning."""
    d, s = card.data, side(reversed_)
    lines = []
    if heading:
        lines.append(escape(heading))
    lines += [
        f"<b>{escape(title(card, reversed_))}</b>",
        f"<i>{escape(', '.join(d['keywords'][s]))}</i>",
        "",
        escape(d["short"][s]),
    ]
    return "\n".join(lines)


def full_text(card, reversed_):
    """The More view: full meaning, love/work/advice, symbolism, reflection questions."""
    d, s = card.data, side(reversed_)
    lines = [f"<b>{escape(title(card, reversed_))}</b>", "", escape(d["meaning"][s].strip())]
    if not reversed_:
        ctx = d["in_context"]
        lines += ["", f"❤️ <b>Love:</b> {escape(ctx['love'])}",
                  f"💼 <b>Work:</b> {escape(ctx['work'])}",
                  f"🧭 <b>Advice:</b> {escape(ctx['advice'])}"]
    lines += ["", "<b>Symbolism</b>"] + [f"• {escape(x)}" for x in d["symbolism"]]
    lines += ["", "<b>To reflect on</b>"] + [f"• {escape(q)}" for q in d["reflection"]]
    lines += ["", f"<i>{escape(correspondences(card))}</i>"]
    return "\n".join(lines)


def correspondences(card):
    c = card.data["correspondences"]
    parts = [f"Element: {c['element']}"]
    if c.get("astrology"):
        parts.append(f"Astrology: {c['astrology']}")
    if c.get("hebrew_letter"):
        parts.append(f"Hebrew letter: {c['hebrew_letter']}")
    return " · ".join(parts)


def waite_text(card):
    w = card.data["waite_1910"]
    return (f"<b>{escape(card.name)}: Waite's meanings (1910)</b>\n\n"
            f"<b>Upright:</b> {escape(w['upright'].strip())}\n\n"
            f"<b>Reversed:</b> {escape(w['reversed'].strip())}\n\n"
            "<i>From A. E. Waite's Pictorial Key to the Tarot, kept here as history. "
            "Some of it reads oddly today.</i>")


def card_line(card, reversed_):
    """One line in a journal entry or draw summary."""
    return f"{escape(card.name)}{' (reversed)' if reversed_ else ''}"

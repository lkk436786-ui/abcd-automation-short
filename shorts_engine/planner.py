from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import random
from typing import Iterable

from .catalog import Asset
from .history import known_signatures


THEME_POOLS = {
    "vehicles": {"bus", "car", "firetruck", "helicopter", "jeep", "motorcycle", "rocket", "scooter", "ship", "train", "van", "yellowbus"},
    "fruits": {"apple", "banana", "grapes", "lemon", "mango", "orange", "pineapple", "strawberry", "tomato", "watermelon"},
    "animals": {"cat", "dog", "dolphin", "elephant", "frog", "giraffe", "goat", "horse", "kangaroo", "koala", "lion", "monkey", "rabbit", "tiger", "turtle", "whale", "zebra"},
}

# Hindi letter-word mapping for SEO — matches reference channel style
_HINDI = {
    'a': 'अ से अनार', 'b': 'ब से बस', 'c': 'क से केला',
    'd': 'ड से डमरू', 'e': 'ए से एक', 'f': 'फ से फूल',
    'g': 'ग से गाय', 'h': 'ह से हाथी', 'i': 'इ से इमली',
    'j': 'ज से जहाज', 'k': 'क से कमल', 'l': 'ल से लड्डू',
    'm': 'म से मछली', 'n': 'न से नाव', 'o': 'ओ से ओखली',
    'p': 'प से पंखा', 'q': 'क्यू से क्यूब', 'r': 'र से राजा',
    's': 'स से सेब', 't': 'त से तोता', 'u': 'उ से उल्लू',
    'v': 'व से वायुयान', 'w': 'व से वर्षा', 'x': 'एक्स से एक्स-रे',
    'y': 'य से यात्री', 'z': 'ज़ से ज़ेबरा',
}

_DESC_TAGS = "#abcd #phonicssong #shorts #short #kidslearning #alphabetsong #abcsong #preschool #toddlers #kidseducation #phonic #alphabet #abcdforkids"


@dataclass
class ShortPlan:
    signature: str
    theme: str
    title: str
    description: str
    assets: list[Asset]
    style_index: int

    def manifest(self) -> dict:
        data = asdict(self)
        data["assets"] = [asset.name for asset in self.assets]
        return data


def _pool(assets: list[Asset], names: set[str] | None = None) -> list[Asset]:
    if not names:
        return list(assets)
    selected = [asset for asset in assets if asset.key in names]
    return selected or list(assets)


def _signature(theme: str, assets: Iterable[Asset], style: int) -> str:
    return f"{theme}|{','.join(asset.key for asset in assets)}|style-{style}"


def plan_batch(assets: list[Asset], history_path, count: int = 5, on_date: date | None = None, seed: int | None = None) -> list[ShortPlan]:
    if not assets:
        raise RuntimeError("No usable PNG assets were found in assets/real_png")
    known = known_signatures(history_path)
    day = on_date or date.today()
    seed_value = seed if seed is not None else int(hashlib.sha256(day.isoformat().encode()).hexdigest()[:12], 16)
    rng = random.Random(seed_value)
    result: list[ShortPlan] = []
    themes = ["quiz", "abc", "count", "vehicles", "animals", "colors"]
    for index in range(count):
        made = None
        for attempt in range(200):
            theme = themes[(index + attempt) % len(themes)]
            style = (seed_value + index + attempt) % 4
            if theme == "abc":
                start = (index * 4 + attempt + seed_value) % 23
                chosen = []
                for offset in range(4):
                    letter = chr(ord("a") + start + offset)
                    candidates = [asset for asset in assets if asset.letter == letter]
                    chosen.append(rng.choice(candidates or assets))
            elif theme == "count":
                chosen = rng.sample(_pool(assets, THEME_POOLS["fruits"]), min(4, len(_pool(assets, THEME_POOLS["fruits"]))))
            elif theme == "vehicles":
                chosen = rng.sample(_pool(assets, THEME_POOLS["vehicles"]), min(4, len(_pool(assets, THEME_POOLS["vehicles"]))))
            elif theme == "animals":
                chosen = rng.sample(_pool(assets, THEME_POOLS["animals"]), min(4, len(_pool(assets, THEME_POOLS["animals"]))))
            else:
                chosen = rng.sample(assets, min(4, len(assets)))
            # Fixed title and description — same for every video, matching reference channel exactly
            title = "A for apple | अ से अनार | abcd | phonics song | a for apple b for ball c for cat #shorts #short"
            desc = (
                "A for apple | B for ball | C for cat | D for dog\n\n"
                f"{_DESC_TAGS}"
            )
            signature = _signature(theme, chosen, style)
            if signature in known or any(plan.signature == signature for plan in result):
                continue
            made = ShortPlan(signature, theme, title[:100], desc, chosen, style)
            break
        if made is None:
            raise RuntimeError("Could not find a non-repeating Shorts plan after 200 attempts")
        result.append(made)
    return result

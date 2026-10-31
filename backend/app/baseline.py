"""LLM-only baseline: same profile, no Qloo data. Output is shown raw and labelled Unverified."""

import json
import logging

from . import config
from .explain import error_reason, extract_json, make_client
from .models import BaselineResult, BaselineSuggestion, Profile

log = logging.getLogger("tastebridge.baseline")

PROMPT = """A student is moving to {city}. Suggest 6 things to do in their first week.
Profile (user-provided): from {origin}; wants to keep: {preserve}; loves: {loved};
budget about {budget} CAD per activity; {hours} hours per week; max travel {travel} minutes;
diet: {diet}; social comfort: {comfort}.
Return JSON only: a list of objects {{"name": str, "description": str}}."""


async def run_baseline(profile: Profile, client=None) -> BaselineResult:
    if config.llm_mode() != "on":
        return BaselineResult(
            available=False,
            message="Baseline unavailable: no LLM is configured (LLM_MODE=off or no LLM_API_KEY). Nothing is faked here.",
        )
    prompt = PROMPT.format(
        city=config.CITY["name"],
        origin=profile.origin,
        preserve=", ".join(profile.preserve) or "nothing specified",
        loved=", ".join(i.text for i in profile.loved_items) or "nothing specified",
        budget=profile.budget_per_activity_cad,
        hours=profile.hours_per_week,
        travel=profile.max_travel_minutes,
        diet=", ".join(profile.diet),
        comfort=profile.comfort.replace("_", " "),
    )
    try:
        client = client or make_client()
        resp = await client.chat.completions.create(
            model=config.llm_settings()["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,  # reasoning models (e.g. gpt-oss) spend tokens before the answer
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        reason = config.redact(error_reason(e))
        log.warning("baseline LLM call failed: %s", reason)
        return BaselineResult(available=False, message=f"Baseline unavailable: the LLM call failed ({reason}).")
    if not text:
        return BaselineResult(available=False, message="Baseline unavailable: the LLM returned an empty answer.")

    suggestions = []
    try:
        data = json.loads(extract_json(text, "["))
        for d in data if isinstance(data, list) else []:
            if isinstance(d, dict) and isinstance(d.get("name"), str):
                suggestions.append(BaselineSuggestion(name=d["name"][:200], description=str(d.get("description", ""))[:500]))
    except ValueError:  # includes JSONDecodeError; raw text is shown instead
        pass
    return BaselineResult(available=True, suggestions=suggestions, raw_text=None if suggestions else text[:3000])

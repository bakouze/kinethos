#!/usr/bin/env python3 
import argparse, json, os
from datetime import datetime, timedelta
from dateutil import tz
from jsonschema import validate, Draft202012Validator
from pydantic import BaseModel, Field

MOCK_MODE = True  # Set False in Slice 1 when you wire Bedrock


class Recovery(BaseModel):
    hrv: int
    rhr: int
    sleep_score: int
    trend: str


class TodayPlan(BaseModel):
    sport: str
    intent: str
    duration_min: int
    target: dict


class Briefing(BaseModel):
    date: str
    recovery: Recovery
    assessment: str
    today_plan: TodayPlan
    alternatives: list
    cta: list


def load_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)


def load_schema(path: str):
    with open(path, 'r') as f:
        return json.load(f)


def simple_assessment(hrv: int, rhr: int, sleep: int):
    if hrv < 50 and rhr > 55 and sleep < 70:
        return "Signs of fatigue—prefer the easy option."
    if hrv < 60 and rhr > 53:
        return "Slight strain—train but avoid maximal efforts."
    if sleep < 65:
        return "Sleep debt—reduce intensity if legs feel heavy."
    return "Good to train as planned; minor residual fatigue."


def mock_bedrock_briefing(context: dict) -> dict:
    met = context['metrics']
    plan = context['plan']
    assessment = simple_assessment(met['hrv'], met['rhr'], met['sleep_score'])

    briefing = {
        "date": context['date'],
        "recovery": {
            "hrv": met['hrv'],
            "rhr": met['rhr'],
            "sleep_score": met['sleep_score'],
            "trend": met.get('trend', 'stable')
        },
        "assessment": assessment,
        "today_plan": {
            "sport": plan['sport'],
            "intent": plan['intent'],
            "duration_min": plan['duration_min'],
            "target": plan.get('target', {})
        },
        "alternatives": [
            {"label": "Easier Z2 35min + mobility 15min", "code": "ALT_EASY"},
            {"label": "Bike Z2 60min if legs sore", "code": "ALT_BIKE"}
        ],
        "cta": ["\ud83d\udcac Questions", "\ud83d\udd01 Swap", "\ud83e\uddd8\u200d\u2642\ufe0f Recovery"]
    }
    return briefing


def generate_briefing(context: dict) -> dict:
    if MOCK_MODE:
        return mock_bedrock_briefing(context)
    else:
        return context  # TODO (Slice 1): Replace with Bedrock invoke # - Load prompts/briefing_system.txt # - Construct messages with context # - Call Claude 3.5 Sonnet via boto3 bedrock-runtime # - Parse JSON, return dict raise NotImplementedError("Bedrock call not wired yet")


def whatsapp_text(brief: dict, first_name: str) -> str:
    r = brief['recovery']
    p = brief['today_plan']
    return (
        f"Morning, {first_name}! \ud83c\udf24\ufe0f\n" f"Recovery: HRV {r['hrv']}, RHR {r['rhr']}, Sleep {r['sleep_score']}/100 → {brief['assessment']}\n" f"Today: {p['sport']} {p['duration_min']}min • {p['intent']} • target {p['target'].get('pace') or p['target'].get('hr_zone') or 'easy'}\n" f"Reply: \ud83d\udd01 Swap • \ud83d\udcac Ask • \ud83e\uddd8\u200d\u2642\ufe0f Recovery")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)  # ISO date for briefing
    ap.add_argument('--metrics', required=True)
    ap.add_argument('--activities', required=True)
    ap.add_argument('--profile', required=True)
    ap.add_argument('--out', required=False)
    args = ap.parse_args()

    # Load inputs
    metrics = load_json(args.metrics)
    activities = load_json(args.activities)
    profile = load_json(args.profile)

    # Minimal plan inference (from profile availability + a stub). In Slice 2 we replace with real plan.
    # Here we just create a "planned session" for the given date based on a simple weekday rule.
    weekday = datetime.fromisoformat(args.date).strftime('%a')
    default_plan = {
        "sport": "run",
        "intent": "tempo" if weekday in ["Tue", "Thu"] else ("long" if weekday == "Sun" else "Z2 base"),
        "duration_min": 50 if weekday in ["Tue", "Thu"] else (80 if weekday == "Sun" else 45),
        "target": {"pace": "4:45-4:55/km" if weekday in ["Tue", "Thu"] else "easy"}
    }

    context = {
        "date": args.date,
        "metrics": metrics,
        "activities": activities,
        "profile": profile,
        "plan": default_plan
    }

    briefing = generate_briefing(context)

    # Validate against schema
    schema = load_schema('schemas/briefing.schema.json')
    Draft202012Validator.check_schema(schema)
    validate(instance=briefing, schema=schema)

    text = whatsapp_text(briefing, first_name=profile.get('first_name', 'athlete'))

    # Output
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, 'w') as f:
            json.dump({"briefing": briefing, "whatsapp": text}, f, indent=2)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps({"briefing": briefing, "whatsapp": text}, indent=2))


if __name__ == '__main__':
    main()

## Description
First simple version of the MVP for Kinethos.

**What the vision for Kinethos?** – the first AI-powered training coach that learns from your data, understands your goals, and proactively guides you every day. Kinethos connects to your favorite fitness platforms, reads your health and activity metrics, and delivers expert coaching directly to you via WhatsApp messages or calls.

Your Kinethos coach will:
- Design a personalized training plan adapted to your lifestyle.
- Adjust daily targets based on recovery data like HRV, sleep quality, and resting heart rate.
- Answer any question in real time, backed by the latest sports science.
- Motivate you every day with actionable insights and clear next steps.

From telling you _“Today’s a good day for speed work”_ to advising _“Take it easy today, your body needs recovery”_, Kinethos brings elite-level coaching to everyone—for a fraction of the cost.

## What does this script do?
This script is the first naive version of the MVP, it uses sample garmin data calls mocked Bedrock to produce a training plan and daily briefing.
- Loads sample daily metrics + recent activity summaries.
- Loads a simplified athlete profile (your goals + availability).
- Calls a mocked Bedrock function to produce a training plan and daily briefing JSON + a WhatsApp-ready text.
- Validates the output against schemas/briefing.schema.json.

## how to execute it?
```zsh
python simulate_daily_briefing.py \
  --date 2025-08-10 \
  --metrics samples/garmin/daily_metrics_2025-08-09.json \
  --activities samples/garmin/activities_2025-08-09.json \
  --profile samples/user_profile.json \
  --out samples_outputs/briefing_2025-08-10.json
```
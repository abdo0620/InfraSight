# Meta models you can use with the $150 credit

Prices are from Meta's own pages ([models](https://dev.meta.ai/docs/models),
[pricing and rate limits](https://dev.meta.ai/docs/pricing-rate-limits)), read on 1 November 2026. Check them again
before relying on them. All models below are reached with the same `META_API_KEY` at `https://api.meta.ai/v1`.

## The models on the Meta Model API

| Model ID | What it does | Price | Used in InfraSight |
|---|---|---|---|
| `muse-spark-1.3` | Latest Muse Spark. Reads text, images, video, audio and PDF; writes text. 1M-token context. Tuned for agents and tool use. | $1.25 in · $0.15 cached · $4.25 out, per 1M tokens | Not yet. Same price as 1.1, so worth switching (see below) |
| `muse-spark-1.2` | Same as 1.3, slightly older. Better than 1.3 for **audio** input. | Same as 1.3 | No |
| `muse-spark-1.1` | First Muse Spark. Text, images, video, audio, PDF → text. | Same as 1.3 | **Yes**: all 9 text functions (triage, reports, stages, size, repair check, traffic order, forecast, brief, citizen messages) |
| `muse-spark-1.3-contributor` / `muse-spark-1.2-contributor` | The same models, **12× cheaper**, but **Meta may use what you send to train its models**. Lower rate limit (150 requests/min). | $0.10 in · $0.002 cached · $0.20 out, per 1M tokens | No. Don't use it with real citizens' photos and reports. Fine for tests with fake data. |
| `muse-wonder-1.0` | Meta's strongest model (preview). Long, complex tasks: software engineering, multi-step agents. Same inputs as Muse Spark. | $4.00 in · $0.20 cached · $20.00 out, per 1M tokens | No. About 4× the cost of Spark, not needed here |
| `muse-image-1.0` | Creates and **edits** images from text and images. | **$0.01 per image** (billed only when an image is returned) | **Yes**: the "after repair" preview |
| `sam-3.1` | Segment Anything. You give a short noun ("pothole") and an image or video; it returns the **exact outline** (box + mask) of every match. | **$2.50 per 1,000 images** ($0.0025 each). Video: $0.20 per 1,000 frames | **Yes**: the red damage zone (through the API, no GPU needed) |
| `muse-voice-transcribe-1.0` | Speech to text: 25 languages, live or from a file, tells speakers apart. Does not speak. | $0.18 per hour of audio | No |

Extra: **web search** (a tool Muse Spark and Muse Wonder can use) costs $2.50 per 1,000 searches, on top of tokens.

**Not on the Model API, so the $150 credit doesn't cover them:**
- **Muse Spark Open** (open-weight Muse Spark, 816B parameters) and **Muse Glimmer** (small open-weight model,
  text and images): you run them yourself or through a partner (Baseten, Modal and Fireworks offer separate credits).
  There is a $10,000 bonus prize for the best project built on them.
- **Muse Wonder Full**: only in Muse Code, with a subscription.

## What $150 buys

| If you spend it all on… | You get about |
|---|---|
| Muse Image | 15,000 images |
| SAM 3.1 | 60,000 images |
| Muse Spark, one typical call (≈5,000 tokens in, 1,000 out) | 14,000 calls |
| Muse Wonder, same call | 3,700 calls |
| Muse Voice Transcribe | 830 hours of audio |

**InfraSight, per citizen report with a photo** (rough estimate, because Meta doesn't publish how many tokens a photo
counts for):

| Step | Model | Cost |
|---|---|---|
| Triage | Muse Spark | ~$0.007 |
| Damage outline | SAM 3.1 | $0.0025 |
| Repair preview | Muse Image | $0.01 |
| Message to the citizen | Muse Spark | ~$0.001 |
| **Total** | | **≈ $0.02**, so roughly **7,000 reports** for $150 |

Staff actions add a little per click: a full AI report is about $0.02, a stage draft about $0.01, a new preview
$0.01. **For the hackathon demo, $150 is far more than enough.**

## Tips

- **Switch to Muse Spark 1.3.** It's the latest and costs the same. In `backend/.env`:
  `MODEL_QUICK=muse-spark-1.3` and `MODEL_DEFAULT=muse-spark-1.3`.
- **Set a spending limit** on the Billing page at dev.meta.ai, so you never go over the $150.
- **Rate limits** are per team: 3,000 requests/min for Muse Spark, Muse Wonder and SAM 3.1; 150/min for Muse Image
  and the contributor models.
- **Availability depends on the country.** Muse Wonder isn't available in South Korea; see Meta's Geographic Use
  Policy.

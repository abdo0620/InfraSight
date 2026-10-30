# InfraSight

## The Problem
Every day, citizens encounter broken infrastructure: potholes, shattered benches, cracked sidewalks. Current reporting systems rely on raw, unstructured photos that force city engineers to manually assess severity, estimate costs, and prioritize tasks. This creates massive bottlenecks and leaves citizens feeling unheard.

## The Solution
InfraSight is an agentic, multimodal platform that acts as both a civil engineer and an urban planner in your pocket. Built for the "Build for Your World" track, it lets anyone snap a photo of urban damage and instantly generate a comprehensive, actionable repair blueprint.

## How we use Meta AI tooling
- **Precision isolation (SAM 3.1):** extracts the exact boundaries of the damage so the LLM never sees a noisy image.
- **Structural diagnostics (Muse Spark):** a strict civil-engineering system prompt returns structured JSON: tripping hazard, exposed materials, accessibility impact, severity score.
- **Generative reconstruction (Muse Image):** targeted inpainting inside the SAM mask gives a photorealistic "After" preview without altering the surroundings.

## Impact
InfraSight bridges the gap between citizen frustration and municipal action: triage-ready data for cities, and an inspiring vision of the repaired neighborhood for citizens.

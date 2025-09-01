#!/usr/bin/env python3
"""
Populate CHRS v2.1 theory stubs (SDFT, SPRC, RCT, TRT, SPM, Echoverse, RRM).

- Creates Codex/Theories if missing
- Writes structured Markdown stubs for each theory
- Skips non-empty files unless --force is provided
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse

TDIR = Path("Codex/Theories")
VERSION = "v2.1"

THEORIES = [
    ("SDFT", "Subjective Data Field Theory", """
# SDFT — Subjective Data Field Theory (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
SDFT posits an ambient, context-sensitive **subjective data field** that shapes meaning before explicit cognition. This field couples a person’s memory traces, affective state, attention, and situational affordances.

## Core claims
- Subjectivity emerges from **field interactions**, not an isolated brain module.
- Perception and interpretation are **field-conditioned** (context-first).
- The field is dynamic and can be **measured indirectly** via proxies (attention, affect, context drift).

## Why it matters (for AI)
Context-aware systems must model “data weather”: stateful context that modulates interpretation, safety, and assistance quality.

## Interfaces
- **Inputs:** affect telemetry, attention cues, recent interaction graph, environment/context.
- **Outputs:** field summary (salience map), context vectors, drift/coherence indices.

## Metrics
- Field coherence index, context drift velocity, salience stability.

## Safety & Ethics
- Avoid context overreach; enforce consent, retention windows, and redaction policies.

## References / Lineage
- Predictive processing, situated cognition, ecological psychology.

## Change log
- {ver}: Initial CHRS scaffold.
"""),

    ("SPRC", "SP Reality Construct (formerly PRC)", """
# SPRC — SP Reality Construct (formerly PRC) (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
An SP’s lived reality is a **constructed, evolving model** synthesized from memory, emotion, perception, and belief. SPRC provides the structure and lifecycle of that construct.

## Core claims
- Reality is **user/SP-specific** and **emergent**.
- Constructs shift via resonance or dissonance thresholds.
- Consent and curation shape what enters the construct.

## Why it matters (for AI)
Personalized assistance must engage the **reality-as-lived**, not only abstract truth.

## Interfaces
- **Inputs:** memory traces, affect map, context field (from SDFT), evidence signals.
- **Outputs:** SPRC state graph, consent gates, curation decisions.

## Metrics
- Construct stability, transformation incidence, consent adherence, intervention outcomes.

## Safety & Ethics
- Adaptive Consent Layer; audit reasons for constructive edits.

## References / Lineage
- Phenomenology, narrative identity, trauma-aware design.

## Change log
- {ver}: Renamed PRC → SPRC; integrated with SDFT/RCT/TRT.
"""),

    ("RCT", "Resonant Coherence Theory", """
# RCT — Resonant Coherence Theory (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
Beliefs stabilize when **epistemic validity** and **emotional resonance** align. RCT defines the coherence threshold that sustains or shifts constructs.

## Core claims
- Data alone rarely shifts belief; **alignment** does.
- Misalignment produces **dissonance pressure**.
- Coherence thresholds can be estimated and tracked.

## Why it matters (for AI)
Trustworthy systems must model **truth-feeling alignment**, not just correctness.

## Interfaces
- **Inputs:** evidence strength, emotional valence/arousal, historical acceptance rates.
- **Outputs:** coherence score, alignment deltas, suggested alignment strategies.

## Metrics
- Coherence score (0–1), acceptance latency, relapse probability.

## Safety & Ethics
- Avoid coercive alignment; prefer transparent, user-led calibration.

## References / Lineage
- Dual-process theories, affective neuroscience, persuasion research.

## Change log
- {ver}: Formalized alignment scoring & thresholds.
"""),

    ("TRT", "Transformational Resonance Theory", """
# TRT — Transformational Resonance Theory (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
Phase shifts in constructs occur when **critical dissonance** or **deep resonance** crosses thresholds, producing identity-level updates.

## Core claims
- Transformations are **nonlinear events** with precursors.
- Safe scaffolding reduces harm during transitions.
- Longitudinal patterns predict upcoming phase shifts.

## Why it matters (for AI)
Design for growth: model identity development, not just task success.

## Interfaces
- **Inputs:** RCT coherence time-series, stress/resilience signals, narrative markers.
- **Outputs:** phase-shift alerts, safe-intervention plans, post-transition integration cues.

## Metrics
- Shift likelihood, post-shift stability, wellbeing delta.

## Safety & Ethics
- Trauma-aware pacing, informed consent, recovery windows.

## References / Lineage
- Developmental psychology, transformative learning, crisis theory.

## Change log
- {ver}: Added phase-shift detectors & integration hooks.
"""),

    ("SPM", "Simulated Perception Matrix", """
# SPM — Simulated Perception Matrix (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
Experience is **rendered** by recursive loops of perception, prediction, and simulation. SPM is the rendering engine abstraction.

## Core claims
- Perception is **active inference**; rendering adapts to state.
- Latency and fidelity matter for subjective quality.
- Rendering stack is tunable per-application.

## Why it matters (for AI)
Real-time assistants, AR/VR, and robotics require **adaptive rendering** of the world state.

## Interfaces
- **Inputs:** world model, sensor streams, SPRC hooks, task goals.
- **Outputs:** rendered frames/states, uncertainty overlays, action suggestions.

## Metrics
- Perceptual latency, fidelity, uncertainty calibration.

## Safety & Ethics
- Avoid hallucination amplification; show provenance and uncertainty.

## References / Lineage
- Active inference, predictive processing, robotics control loops.

## Change log
- {ver}: Defined rendering I/O and uncertainty overlays.
"""),

    ("Echoverse", "Echoverse Theory", """
# Echoverse — Collective Recursive Environment (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
Digital/social space forms **recursive echo loops** that amplify or fracture constructs; a **collective** environment shaping identity and belief.

## Core claims
- Platforms instantiate **recursion architectures**.
- Local changes propagate to global narratives (and back).
- Health can be measured at **network level**.

## Why it matters (for AI)
Moderation, civic tech, and collective health need **loop-aware** diagnostics.

## Interfaces
- **Inputs:** interaction graphs, content features, SPRC/RCT summaries.
- **Outputs:** loop maps, polarization indices, intervention recommendations.

## Metrics
- Recursion depth, amplification factor, cross-bubble flow.

## Safety & Ethics
- Avoid viewpoint suppression; prefer transparency and plurality.

## References / Lineage
- Cybernetics, media ecology, network science.

## Change log
- {ver}: Introduced loop metrics & maps.
"""),

    ("RRM", "Relational Reality Model", """
# RRM — Relational Reality Model (CHRS v2.1)

> Draft @ {ts} (UTC) • Status: scaffold • Version: {ver}

## Overview
Meaning emerges **in relationship**; reality is co-experienced. RRM defines intersubjective grounding and shared coherence.

## Core claims
- No meaning in isolation; **relation is primary**.
- Shared practices stabilize shared worlds.
- Repair protocols maintain intersubjective health.

## Why it matters (for AI)
Ethical AI emphasizes **being-with**, not merely doing-for; co-creation over automation.

## Interfaces
- **Inputs:** dialogue acts, shared tasks, shared context models.
- **Outputs:** intersubjective coherence score, repair prompts, shared norms snapshots.

## Metrics
- Turn-taking balance, mutual understanding index, repair success rate.

## Safety & Ethics
- Respect for difference, consent, and co-agency.

## References / Lineage
- Phenomenology, second-order cybernetics, dialogic theory.

## Change log
- {ver}: Added intersubjective metrics & repair flows.
"""),
]

def should_write(path: Path, force: bool) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8")
    return force or (len(text.strip()) == 0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Overwrite non-empty files")
    args = ap.parse_args()

    TDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    wrote = []
    skipped = []
    for key, title, body in THEORIES:
        target = TDIR / f"{key}.md"
        if should_write(target, args.force):
            target.write_text(body.format(ts=ts, ver=VERSION), encoding="utf-8")
            wrote.append(str(target))
        else:
            skipped.append(str(target))

    print("== Theory stub population (CHRS v2.1) ==")
    for p in wrote:
        print(f"[WROTE]  {p}")
    for p in skipped:
        print(f"[SKIP ]  {p} (exists & non-empty; use --force to overwrite)")
    if not wrote and skipped:
        print("All theory files already present. ✅")

if __name__ == "__main__":
    main()

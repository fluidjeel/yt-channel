# Human Outcome Engine

> **Status:** **REFERENCE / ARCHITECTURE**  
> **Not shipped:** no loader, analyzer, generator, dashboard, or knowledge graph is implemented from this document.  
> **Evidence base:** `reports/EMOTIONAL_JOB_TO_BE_DONE.md`, `reports/EMOTIONAL_PRODUCT.md`, `reports/NICHE_TAXONOMY_V1.md`, `reports/BENCHMARK_VALIDATION.md`  
> **Current validation:** 3 analyzed channels only (`whisprs_yt`, `soulful_lines`, `the_faceless_storyteller`). Competitor comments are missing.

This document extracts a niche-independent framework from the current Whisprs / recovery benchmark research. Its purpose is to prevent future channels from being designed around surface formulas only.

The central idea:

```text
People do not hire content formats.
They hire emotional outcomes.
```

---

## Layer Model

The current platform architecture says:

```text
Core + Niche + Brand = Content
```

The Human Outcome Engine expands the interpretation layer. `HUMAN_MECHANISM_TAXONOMY.md` adds the causal middle layers (`Recognition` and `Mechanism`):

```text
Layer 0: Human Psychology
Layer 1: Human State / Job To Be Done Engine
Layer 2: Recognition
Layer 3: Mechanism
Layer 4: Emotional Outcome Engine
Layer 5: Niche Wrapper
Layer 6: Brand Personality
Layer 7: Content Generator
```

| Layer | Role | Example from current evidence | Status |
| --- | --- | --- | --- |
| Layer 0 — Human Psychology | Universal drivers: fear, belonging, agency, competence, relief, meaning | emotional regulation, identity transition | REFERENCE |
| Layer 1 — Job To Be Done Engine | What transformation the viewer hires content to perform | "help me regulate pain" | REFERENCE |
| Layer 2 — Recognition | Why the viewer stops: "this is about me" | "needed this", "this hit" | PARTIAL evidence |
| Layer 3 — Mechanism | How content moves the viewer | validation + meaning making | PARTIAL evidence |
| Layer 4 — Emotional Outcome Engine | Desired post-consumption state | acceptance, resilience, peaceful sadness | REFERENCE |
| Layer 5 — Niche Wrapper | Category skin and audience context | anime recovery / self-worth Shorts | PARTIAL evidence |
| Layer 6 — Brand Personality | Differentiation inside the niche | Whisprs = dreamer + looking up + acceptance | PARTIAL evidence |
| Layer 7 — Content Generator | Scripts, image, music, motion | PLANNED; do not build before validation gate clears | PLANNED |

---

## Core Schema

Every future channel should be describable with this schema before any generation work:

```yaml
channel_outcome_profile:
  channel_id: ""
  status: reference | partial | shipped

  job_to_be_done:
    primary_job: ""
    secondary_jobs: []
    frequency: daily | episodic | life_event | unknown
    evidence: []
    confidence: 0.0

  recognition:
    trigger: ""
    viewer_self_identification: ""
    example_language: []
    evidence: []
    confidence: 0.0

  mechanism:
    primary_mechanism: ""
    secondary_mechanisms: []
    evidence: []
    confidence: 0.0

  arrival_state:
    emotional_state: ""
    trigger_contexts: []
    viewer_language: []
    evidence: []
    confidence: 0.0

  desired_state:
    emotional_state: ""
    functional_state: ""
    evidence: []
    confidence: 0.0

  emotional_outcome:
    primary_outcome: ""
    secondary_outcomes: []
    not_the_outcome: []
    evidence: []
    confidence: 0.0

  transformation_arc:
    stages: []
    evidence: []
    confidence: 0.0

  viewer_motivation:
    why_watch: []
    why_save: []
    why_comment: []
    why_share: []
    evidence: []
    confidence: 0.0

  visual_container:
    composition: []
    character_archetype: []
    gaze: []
    palette_or_style: []
    evidence: []
    confidence: 0.0

  brand_flavor:
    emotional_positioning: ""
    voice: ""
    visual_signature: []
    narrative_signature: []
    evidence: []
    confidence: 0.0
```

Required rule: **every field must carry evidence and confidence**. Empty evidence means the field remains a hypothesis.

---

## Current Channel Outcome Profiles

### Whisprs

| Field | Value |
| --- | --- |
| Job To Be Done | Regulate relational/self-worth pain; help viewer accept pain without losing self |
| Arrival State | heartbreak, unrequited love, loneliness, self-doubt, healing journey |
| Desired State | accepted, less alone, self-worthy, emotionally stable |
| Emotional Outcome | acceptance + self-love |
| Transformation Arc | pain -> recognition -> meaning -> acceptance -> restored self-worth |
| Viewer Motivation | "needed this", "thank you", personal affirmation; save > share behavior in comments |
| Visual Container | anime-adjacent solitude, ~80% negative space, tiny-human/large-world |
| Brand Flavor | dreamer, looking-up gaze, acceptance, hopeful solitude |
| Evidence | `audience_psychology.md`, `advanced_visual_analysis.md`, `content_dna.md`, `master_emotional_bible.md` |
| Confidence | 0.86 for Whisprs-specific profile |

Important distinction:

```text
Recovery = probable niche product
Acceptance = Whisprs positioning
```

### Soulful Lines

| Field | Value |
| --- | --- |
| Job To Be Done | Help viewer endure solitude through quiet resilience |
| Arrival State | inferred: loneliness / reflective pain |
| Desired State | resilient, less alone, emotionally steadier |
| Emotional Outcome | resilience + peaceful sadness |
| Transformation Arc | pain -> reflection -> resilience / acceptance (synthesis-level evidence) |
| Viewer Motivation | unknown; comments not collected |
| Visual Container | observer archetype, no-face tendency, high negative space, alone framing |
| Brand Flavor | observer + resilience |
| Evidence | `reports/soulful_lines/advanced_visual_analysis.md`, `content_dna.md`, `master_emotional_bible.md` |
| Confidence | 0.75 visual/emotional; lower for audience motivation |

### The Faceless Storyteller

| Field | Value |
| --- | --- |
| Job To Be Done | Convert loneliness/fearful reflection into survivable story |
| Arrival State | inferred: loneliness, suspense, emotional unease |
| Desired State | catharsis or peaceful sadness; exact audience outcome unknown |
| Emotional Outcome | peaceful sadness + hopeful melancholy (synthesis-level), possible catharsis (unvalidated) |
| Transformation Arc | story tension -> reflection -> insight -> resolution |
| Viewer Motivation | unknown; comments not collected |
| Visual Container | observer, no-face, tiny-human/large-world, alone framing, dark muted style |
| Brand Flavor | faceless observer + horror / creepypasta surface |
| Evidence | `reports/the_faceless_storyteller/advanced_visual_analysis.md`, `narrative_patterns.md`, `content_dna.md`, `master_emotional_bible.md` |
| Confidence | 0.80 visual/brand; 0.40 audience job until comments exist |

---

## Universal Job Families

These are reusable categories for future niches. Only the recovery row is partially validated by current data; the rest are schema examples.

| Job Family | Viewer Hires Content To... | Common Arrival State | Desired State | Candidate Niches | Validation Status |
| --- | --- | --- | --- | --- | --- |
| Emotional Regulation | get through a feeling without denying it | lonely, anxious, hurt, self-doubting | steady, understood, less alone | recovery, humor, music, comfort stories | PARTIAL |
| Identity Transition | become someone who can live after a destabilizing event | breakup, grief, betrayal, failure | accepted, stronger, reoriented | recovery, self-improvement, spirituality | PARTIAL |
| Safe Fear | experience danger without real risk | boredom, curiosity, anxiety | catharsis, alertness, release | horror, mystery, folklore | HYPOTHESIS |
| Uncertainty Reduction | make ambiguity feel navigable | confusion, overwhelm, indecision | clarity, possibility | business, tech, finance, education | HYPOTHESIS |
| Competence Building | feel capable of understanding or doing something | confusion, incompetence, fear of being left behind | competence, control | tech, tutorials, productivity | HYPOTHESIS |
| Agency Restoration | recover a sense of power to act | stuck, passive, defeated | agency, momentum | motivation, fitness, business | HYPOTHESIS |
| Social Relief | escape pressure through laughter or recognition | stress, irritation, social fatigue | relief, belonging | humor, commentary, satire | HYPOTHESIS |
| Meaning Making | convert pain or randomness into significance | loss, emptiness, existential doubt | meaning, purpose, acceptance | spirituality, philosophy, grief | HYPOTHESIS |

---

## Emotional Outcome Taxonomy

| Emotional Outcome | Viewer Feels After Consuming | Difference From Similar Outcomes | Example Wrapper |
| --- | --- | --- | --- |
| Acceptance | "This happened, and I can live with it." | calmer than motivation; less ecstatic than hope | anime recovery |
| Resilience | "I can continue." | action-adjacent but still emotionally grounded | recovery, motivation |
| Peaceful Sadness | "I can hold this sadness safely." | does not resolve pain; regulates it | recovery, grief, reflective stories |
| Catharsis | "I released tension." | more intense than calm; often uses fear, crying, awe, humor | horror, tragedy, humor |
| Relief | "The pressure dropped." | lighter than acceptance; often short-lived | humor, comfort content |
| Possibility | "There may be a path." | future-oriented; less emotional than hope | business ideas, opportunity channels |
| Competence | "I understand this now." | cognitive-emotional outcome; reduces confusion | tech, education |
| Agency | "I can do something." | action-oriented; stronger than possibility | motivation, fitness, business |
| Belonging | "People like me exist." | social regulation; may overlap with relief | fandom, humor, identity content |
| Meaning | "This experience fits into a larger frame." | deeper than acceptance; often spiritual/philosophical | spirituality, grief, philosophy |

---

## Niche Wrapper Examples

These examples are **not validated channels**. They show how the schema can generalize.

### Anime Recovery

| Layer | Value |
| --- | --- |
| Job | regulate pain / support identity transition |
| Outcome | acceptance, self-worth, resilience |
| Wrapper | anime recovery, quote/story Shorts |
| Brand Example | Whisprs = dreamer, looking-up, acceptance |
| Evidence Status | PARTIAL, current project evidence |

### Horror

| Layer | Value |
| --- | --- |
| Job | safe fear experience |
| Outcome | catharsis, alertness, release |
| Wrapper | horror stories, folklore, mystery |
| Brand Example | dark folklore, faceless narrator |
| Evidence Status | HYPOTHESIS; Faceless Storyteller is adjacent but not validated by comments |

### Business Ideas

| Layer | Value |
| --- | --- |
| Job | reduce uncertainty about opportunity |
| Outcome | possibility |
| Wrapper | business opportunities, side hustles, market gaps |
| Brand Example | opportunity scout |
| Evidence Status | HYPOTHESIS |

### Tech

| Layer | Value |
| --- | --- |
| Job | reduce confusion |
| Outcome | competence |
| Wrapper | tech explanations, AI tools, practical tutorials |
| Brand Example | practical futurist |
| Evidence Status | HYPOTHESIS |

### Humor

| Layer | Value |
| --- | --- |
| Job | escape stress / socially process frustration |
| Outcome | relief, belonging |
| Wrapper | comedy, satire, relatable commentary |
| Brand Example | sarcastic observer |
| Evidence Status | HYPOTHESIS |

---

## Platform Mapping

The Human Outcome Engine should sit above niche profiles and brand profiles.

```text
Human Psychology
  -> Human State / Job To Be Done
  -> Recognition
  -> Mechanism
  -> Desired Emotional Outcome
  -> Niche Wrapper
  -> Brand Personality
  -> Content System
```

Current architecture mapping:

| Current Layer | Future Interpretation |
| --- | --- |
| `content_intelligence_core/` | extracts niche-neutral evidence: comments, visuals, audio, narrative, performance |
| `taxonomy/` | stores evidence-backed cross-channel patterns |
| `niches/{id}/` | maps jobs/outcomes into category-specific wrapper |
| `brands/{id}/brand.yaml` | maps wrapper into differentiated style |
| generation layer | should only run after validation gates clear |

Important rule:

```text
Never put brand flavor into niche DNA.
Never put niche wrapper into universal psychology.
Never treat one channel's audience comments as the whole market.
```

---

## Evidence Rules

Every Human Outcome claim must carry:

| Field | Requirement |
| --- | --- |
| Supporting channels | Which channels show the signal |
| Contradicting channels | Which channels do not show it |
| Evidence path | Exact artifact(s), e.g. `audience_psychology.md`, `advanced_visual_analysis.md` |
| Confidence | Numeric score |
| Evidence type | comment, visual, audio, narrative, synthesis, human interpretation |
| Status | SHIPPED / PARTIAL / REFERENCE / HYPOTHESIS |

Confidence defaults:

| Evidence | Max Confidence |
| --- | ---: |
| 5+ channels with comment + visual + narrative agreement | 0.95 |
| 3 channels with direct analyzer agreement | 0.85 |
| 3 channels with synthesis-only agreement | 0.70 |
| 1 channel with comments | 0.50 niche-wide / 0.95 channel-specific |
| Human hypothesis without direct data | 0.30 |

---

## Current Validated / Partial Outcomes

| Outcome | Status | Evidence | Confidence |
| --- | --- | --- | ---: |
| Emotional regulation in anime recovery | PARTIAL | Whisprs comments + 3-channel visual calm/solitude | 0.76 |
| Identity transition in anime recovery | PARTIAL | 3-channel bibles + Whisprs identity/self-worth comments | 0.70 |
| Acceptance as Whisprs positioning | PARTIAL / strong brand-level | Whisprs acceptance 90% high performers; competitors differ | 0.90 |
| Recovery / self-worth as niche wrapper | PARTIAL | 3-channel bibles, visual solitude | 0.72 |
| Observer/no-face competitor pattern | PARTIAL | Soulful + Faceless visual reports | 0.82 |
| Comment-level niche DNA | NOT VALIDATED | competitor comments missing | 0.15 |

---

## What Not To Build Yet

Do not build:

- new analyzers
- generation systems
- knowledge graph claims
- fake dashboards
- multi-niche engine code

Before implementation, finish:

```text
5 validated channels
+ comment collection fixed
+ cross-channel synthesis
```

Only then consider building the Style Evidence Engine or profile loader work.

---

## Next Validation Targets

| Target | Why |
| --- | --- |
| Fix competitor comment collection | required to distinguish audience DNA from visual/narrative DNA |
| Complete 5 live benchmark channels | current evidence overfits Whisprs + 2 competitors |
| Re-run cross-channel synthesis | needed to promote PARTIAL claims to stronger niche claims |
| Test outcome taxonomy on one non-recovery niche | only after recovery validation clears |

---

## Summary

The most reusable discovery so far is not a content formula. It is an architecture:

```text
Human state -> recognition -> mechanism -> emotional outcome -> niche wrapper -> brand flavor -> content format
```

For Whisprs:

```text
Human state: heartbroken / lonely / self-doubting
Recognition: "this is exactly me"
Job: regulate pain / support transition
Mechanism: validation + meaning making
Outcome: acceptance + self-worth
Wrapper: anime recovery
Brand: dreamer, looking-up, hopeful solitude
```

For the platform:

```text
Do not start with niche.
Start with the human state, recognition trigger, mechanism, and outcome the viewer is hiring content to produce.
```


# MVP Confidence Scoring

> **Status:** **PLANNED** — applies at assembly time; no new ML models  
> **Purpose:** Show how field confidence is derived from **existing evidence categories only**

---

## Evidence Categories

These are the only evidence types the MVP recognizes. They map directly to pipeline outputs.

| Category | `evidence_type` | Source artifacts |
| --- | --- | --- |
| **Comment** | `comment` | `audience_psychology.md`, `comments.csv`, `comment_clusters.csv` |
| **Visual** | `visual` | `advanced_visual_analysis.md`, `advanced_visual_videos.csv`, `visual_analysis.md` |
| **Narrative** | `narrative` | `narrative_patterns.md` |
| **Performance** | `performance` | `top_videos.csv`, performance sections in `advanced_visual_analysis.md` |
| **Bible synthesis** | `bible` | `content_dna.md`, `audience_persona.md`, `master_emotional_bible.md` |
| **Cross-channel** | `cross_channel` | `cross_channel_synthesis_v2.md`, `validation_phase2.md` |

**Not valid evidence for MVP Phase 1:**

- `docs/HUMAN_OUTCOME_ENGINE.md` layer labels (REFERENCE unless copied from reports with citations)
- `docs/HUMAN_MECHANISM_TAXONOMY.md` mechanism names without comment phrase proof
- Taxonomy YAML files under `taxonomy/`
- LLM synthesis Interpretations without matching Facts in the same bible section

---

## Confidence Levels

### HIGH

A field is **HIGH** when **all** of the following apply:

1. The claim is supported by **comments** (≥300 cleaned comments AND theme/metric cited in `audience_psychology.md` or `comments.csv`), **and**
2. Supported by **narrative** (`narrative_patterns.md`) **or** **visual** (`advanced_visual_analysis.md`) with explicit counts, **and**
3. Not contradicted by another source report in the same channel folder

**Alternative HIGH path (no comments):**  
Visual + narrative + performance correlation all cite the same pattern on top performers (e.g. "81% negative space on high performers" from advanced visual + top_videos rank alignment). Use sparingly — label `audience_need` fields as MEDIUM max without comments.

**Example (Whisprs):**

- "Self-love is primary audience connection" → HIGH (comments 21% + persona Facts + psychology Key Insights)
- "Acceptance dominates visual expression" → HIGH (90% advanced visual + emotional bible Facts)

---

### MEDIUM

A field is **MEDIUM** when:

- Supported by **exactly two** evidence categories from the table above, **or**
- Supported by **bible synthesis Facts** that reference a single underlying step report with metrics, **or**
- Supported by **cross-channel** pattern (≥3/5 cohort) **plus** one channel-specific bible Fact

**Examples:**

- Emotional journey arc from `master_emotional_bible.md` + `narrative_patterns.md` only → MEDIUM
- Brand personality from `content_dna.md` + `advanced_visual_analysis.md` → MEDIUM
- Cohort-shared "tiny human / large world" from synthesis v2 + channel visual report → MEDIUM for niche; HIGH for niche block only when all 5 channels have advanced visual

---

### LOW

A field is **LOW** when:

- Supported by **one** evidence category only (typically bible Interpretations without Facts), **or**
- Bible **Unknowns / Gaps** section explicitly flags missing data, **or**
- Comment dataset &lt;300 cleaned rows and claim is audience-specific, **or**
- Cross-channel pattern frequency &lt;50% and applied to a single channel without local corroboration

**Examples:**

- Mechanism label ("validation") inferred from bible prose only → LOW
- Recommendation from `content_dna.md` Generation Guidelines without metric → LOW unless tied to a Fact line
- `dark_poetry_hub` audience claims from 3 comments → LOW

---

## Per-Section Roll-Up

### Outcome Profile

| Subfield | HIGH requires | MEDIUM requires | LOW default |
| --- | --- | --- | --- |
| `dominant_emotional_outcome` | comments + (visual OR narrative) | bible Facts + one step report | bible Interpretations only |
| `emotional_journey` | narrative + bible + (comments OR visual) | bible + narrative | bible only |
| `audience_emotional_need` | comments ≥300 + psychology report | comments &lt;300 OR persona without psychology | no comments |

### Brand Profile

| Subfield | HIGH requires | MEDIUM requires | LOW default |
| --- | --- | --- | --- |
| `visual_identity` | advanced_visual_analysis complete | visual_analysis.md only | missing visual reports |
| `narrative_identity` | narrative_patterns + audio pacing | narrative_patterns only | inferred from bible |
| `brand_personality` | content_dna Facts + visual + narrative | any two | bible Interpretations only |
| `cohort_comparison` | pattern in synthesis v2 at ≥80% + local match | synthesis v2 + one local report | synthesis only |

### Content Recommendations

| Subfield | HIGH requires | MEDIUM requires | LOW default |
| --- | --- | --- | --- |
| `patterns_working_today` | performance correlation in advanced visual + top_videos | one performance source | bible Generation Guidelines |
| `opportunities_observed` | comparative metrics (high vs low performers) | single-source trend | gap list only |
| `missing_content_areas` | — | — | always LOW (explicit uncertainty) |

---

## Overall Confidence

```text
overall = min(outcome_confidence, brand_confidence, recommendations_confidence)
```

Where section confidence = **lowest** field confidence in that section unless ≥80% of fields are HIGH (then section = MEDIUM minimum).

**Display rule for UI:** Show overall badge + per-field badges. Never hide LOW fields — label them "hypothesis / needs more data."

---

## Comment Dataset Thresholds

From validation Phase 2 (`reports/validation_phase2.md`):

| Cleaned comments | Audience claims | Mechanism / recognition claims |
| --- | --- | --- |
| ≥300 | HIGH eligible (with corroboration) | MEDIUM eligible |
| 1–299 | MEDIUM max | LOW |
| 0 | Omit or LOW; cite "no comment data" | Not emitted |

Validated HIGH comment channels: `whisprs_yt` (3840), `soulxsigh` (1597).

---

## Contradiction Handling

If two source reports conflict (e.g. bible Fact vs CSV count):

1. Prefer **CSV / step report** over bible synthesis  
2. Downgrade confidence one level (HIGH → MEDIUM → LOW)  
3. Include both values in `evidence_citations` with note "contradiction unresolved"

Do not average or invent reconciliations.

---

## What This Scoring Does Not Do

- No weighted numeric models (no 0.0–1.0 invented scores beyond existing cluster confidence in comments)  
- No LLM-as-judge for confidence  
- No universal baseline across niches — cohort context is recovery-quote Shorts only  
- No automatic upgrade from MEDIUM to HIGH without new evidence collection

---

## Assembler Pseudocode (Phase 1.5)

```python
def score_field(claims: list[EvidenceClaim]) -> Confidence:
    categories = {c.evidence_type for c in claims}
    has_comments = "comment" in categories and cleaned_comment_count >= 300
    if has_comments and len(categories) >= 3 and not contradicted(claims):
        return HIGH
    if len(categories) >= 2:
        return MEDIUM
    return LOW
```

Implementation must live in a thin assembler module — **not** in new analyzers.

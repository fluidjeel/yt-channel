# MVP Data Contract

> **Status:** **PLANNED** — contract between existing analyzers and future MVP UI/assembler  
> **Version:** 1.0  
> **No new analyzers.** All fields map to reports already produced by `main.py` + benchmark extensions.

---

## Overview

```yaml
input:
  channel_url: string

output:
  channel_slug: string
  channel_name: string
  analyzed_at: ISO-8601 datetime
  pipeline_status: full | partial | failed
  outcome_profile: OutcomeProfile
  brand_profile: BrandProfile
  content_recommendations: ContentRecommendations
  metadata:
    source_reports: list[string]   # paths populated
    benchmark_cohort: cross_channel_synthesis_v2
```

**Note on report names:** The pipeline produces `narrative_patterns.md` (step 7), not `narrative_analysis.md`. The contract uses `narrative_patterns.md` as the canonical narrative source.

---

## Input

### `channel_url`

| Property | Value |
| --- | --- |
| **Type** | `string` |
| **Required** | yes |
| **Description** | YouTube channel URL or `@handle` passed to `main.py` or `benchmark_program` |
| **Source reports** | — (triggers pipeline) |
| **Confidence** | N/A |

---

## Output: `OutcomeProfile`

Describes the emotional product the channel delivers to viewers.

### `dominant_emotional_outcome`

| Property | Value |
| --- | --- |
| **Type** | `string` |
| **Description** | Primary emotional state the content moves viewers toward (e.g. "acceptance", "self-love", "peaceful sadness") |
| **Source reports** | `master_emotional_bible.md` (Facts, Interpretations), `content_dna.md` (Emotional Product) |
| **Confidence** | HIGH if comments + emotional bible agree; MEDIUM if bible only; LOW if inferred from quotes only |

### `secondary_outcomes`

| Property | Value |
| --- | --- |
| **Type** | `list[string]` |
| **Description** | Additional outcomes observed in top content or comments |
| **Source reports** | `master_emotional_bible.md`, `emotion_clusters.md`, `audience_psychology.md` (Emotional Triggers) |
| **Confidence** | Per-item via MVP_SCORING |

### `emotional_journey`

| Property | Value |
| --- | --- |
| **Type** | `object` |
| **Description** | Structured arc from arrival to desired state |
| **Fields** | `arrival_state`, `transformation_stages[]`, `desired_state` |
| **Source reports** | `master_emotional_bible.md`, `narrative_patterns.md`, `content_dna.md` |
| **Confidence** | HIGH if narrative + bible + comments align; MEDIUM if two sources; LOW if bible only |

#### `emotional_journey.arrival_state`

| Property | Value |
| --- | --- |
| **Type** | `string` |
| **Description** | Dominant viewer state before/during consumption (e.g. heartbreak, loneliness) |
| **Source reports** | `audience_persona.md`, `audience_psychology.md`, `comments.csv` (theme, emotional_state columns) |
| **Confidence** | HIGH with ≥300 cleaned comments; MEDIUM with bible; LOW without comments |

#### `emotional_journey.transformation_stages`

| Property | Value |
| --- | --- |
| **Type** | `list[string]` |
| **Description** | Ordered stages (e.g. "pain", "recognition", "acceptance", "growth") — use labels from existing bibles, not new taxonomy |
| **Source reports** | `master_emotional_bible.md`, `narrative_patterns.md` |
| **Confidence** | MEDIUM default; HIGH if narrative regex stats + bible match |

#### `emotional_journey.desired_state`

| Property | Value |
| --- | --- |
| **Type** | `string` |
| **Description** | State viewers seek (e.g. "accepted", "self-worthy", "emotionally stable") |
| **Source reports** | `audience_persona.md`, `master_emotional_bible.md` |
| **Confidence** | Same rules as `dominant_emotional_outcome` |

### `audience_emotional_need`

| Property | Value |
| --- | --- |
| **Type** | `object` |
| **Description** | Why viewers hire this channel |
| **Fields** | `primary_need`, `comment_themes`, `save_signals`, `share_signals` |
| **Source reports** | `audience_psychology.md`, `audience_persona.md`, `comments.csv`, `comment_clusters.csv` |
| **Confidence** | HIGH with comment dataset; LOW without |

#### `audience_emotional_need.primary_need`

| Property | Value |
| --- | --- |
| **Type** | `string` |
| **Description** | One-sentence need (e.g. "validation and self-worth after heartbreak") |
| **Source reports** | `audience_persona.md` (Executive Summary), `audience_psychology.md` (Key Insights) |
| **Confidence** | HIGH with comments; MEDIUM bible-only |

#### `audience_emotional_need.comment_themes`

| Property | Value |
| --- | --- |
| **Type** | `list[object]` — `{ theme: string, count: int, pct: float }` |
| **Description** | Top comment theme distribution |
| **Source reports** | `audience_psychology.md`, `comments.csv`, `cross_channel_synthesis_v2.md` (Comment Theme Comparison) |
| **Confidence** | HIGH if raw count ≥300 cleaned; partial if &lt;300; absent if no comments |

#### `audience_emotional_need.save_signals`

| Property | Value |
| --- | --- |
| **Type** | `list[string]` |
| **Description** | Example phrases showing save/bookmark intent ("needed this", "saving this") |
| **Source reports** | `audience_psychology.md` (Why Viewers Save) |
| **Confidence** | HIGH with comment collection; N/A without comments |

### `evidence_confidence`

| Property | Value |
| --- | --- |
| **Type** | `object` |
| **Description** | Roll-up and per-field confidence |
| **Fields** | `overall`, `outcome`, `journey`, `audience_need` — each `HIGH` \| `MEDIUM` \| `LOW` |
| **Source reports** | Computed via `docs/MVP_SCORING.md` from source availability |
| **Confidence** | N/A (meta) |

### `evidence_citations`

| Property | Value |
| --- | --- |
| **Type** | `list[object]` — `{ field, report_path, excerpt, metric? }` |
| **Description** | Traceability for UI and external review |
| **Source reports** | All Outcome Profile sources |
| **Confidence** | Required for every HIGH claim |

---

## Output: `BrandProfile`

Describes how the channel differentiates within the validated recovery-quote Shorts niche.

### `brand_personality`

| Property | Value |
| --- | --- |
| **Type** | `string` |
| **Description** | Emotional positioning and voice (e.g. "intimate, acceptance-forward, non-hype") |
| **Source reports** | `content_dna.md`, `master_emotional_bible.md`, `channel_playbook.md` |
| **Confidence** | MEDIUM (synthesis-heavy); HIGH if visual + narrative corroborate |

### `brand_personality_not`

| Property | Value |
| --- | --- |
| **Type** | `list[string]` |
| **Description** | Explicit exclusions (e.g. "revenge framing", "hype motivation") |
| **Source reports** | `content_dna.md` (Generation Guidelines), `master_emotional_bible.md` |
| **Confidence** | MEDIUM |

### `recurring_themes`

| Property | Value |
| --- | --- |
| **Type** | `list[object]` — `{ theme, frequency, source }` |
| **Description** | Dominant quote/emotion themes in top videos |
| **Source reports** | `quote_patterns.md`, `emotion_clusters.md`, `quote_database.csv` |
| **Confidence** | HIGH if backed by CSV counts; MEDIUM from markdown only |

### `visual_identity`

| Property | Value |
| --- | --- |
| **Type** | `object` |
| **Fields** | `dominant_archetype`, `dominant_gaze`, `dominant_expression`, `dominant_composition`, `avg_negative_space_pct`, `anime_style_score`, `palette_summary` |
| **Description** | Visual DNA from advanced visual layer |
| **Source reports** | `advanced_visual_analysis.md`, `advanced_visual_videos.csv`, `visual_analysis.md` |
| **Confidence** | HIGH when advanced visual complete; MEDIUM with basic visual only |

### `narrative_identity`

| Property | Value |
| --- | --- |
| **Type** | `object` |
| **Fields** | `structure_pattern`, `hook_style`, `avg_words_per_minute`, `resolution_tone` |
| **Description** | How stories are told in Shorts |
| **Source reports** | `narrative_patterns.md`, `audio_analysis.md` (pacing) |
| **Confidence** | MEDIUM (regex/heuristic step 7) |

### `cohort_comparison`

| Property | Value |
| --- | --- |
| **Type** | `object` |
| **Fields** | `shared_niche_patterns[]`, `channel_unique_signals[]` |
| **Description** | Benchmark context — what is niche-wide vs channel-specific |
| **Source reports** | `cross_channel_synthesis_v2.md`, `validation_phase2.md` |
| **Confidence** | HIGH for patterns at 100% cohort frequency; MEDIUM for emerging (40–60%) |

---

## Output: `ContentRecommendations`

Evidence-backed guidance — not invented growth hacks.

### `patterns_working_today`

| Property | Value |
| --- | --- |
| **Type** | `list[RecommendationItem]` |
| **Description** | Patterns correlated with top performers |
| **Source reports** | `advanced_visual_analysis.md` (Performance Correlations), `top_videos.csv`, `content_dna.md` (Facts) |
| **Confidence** | Per-item via MVP_SCORING |

### `opportunities_observed`

| Property | Value |
| --- | --- |
| **Type** | `list[RecommendationItem]` |
| **Description** | Under-indexed themes or visual choices in lower performers vs high performers |
| **Source reports** | `advanced_visual_analysis.md`, `emotion_clusters.md`, `quote_database.csv` |
| **Confidence** | MEDIUM minimum (comparative inference) |

### `missing_content_areas`

| Property | Value |
| --- | --- |
| **Type** | `list[RecommendationItem]` |
| **Description** | Gaps explicitly listed in bible Unknowns/Gaps sections |
| **Source reports** | `content_dna.md`, `audience_persona.md`, `master_emotional_bible.md` (Unknowns / Gaps) |
| **Confidence** | LOW–MEDIUM (explicit gap = honest uncertainty) |

### `recommendations`

| Property | Value |
| --- | --- |
| **Type** | `list[RecommendationItem]` |
| **Description** | Consolidated actionable list for creator |
| **Source reports** | Union of above + `content_dna.md` (Generation Guidelines) where labeled as evidence-based |
| **Confidence** | Per-item |

---

## Shared Type: `RecommendationItem`

```yaml
RecommendationItem:
  id: string
  title: string
  rationale: string
  source_report: string          # e.g. reports/whisprs_yt/advanced_visual_analysis.md
  evidence: string               # quote or metric from source
  evidence_type: comment | visual | narrative | performance | bible | cross_channel
  confidence: HIGH | MEDIUM | LOW
```

---

## Pipeline Artifact Checklist

Minimum artifacts to populate full contract:

| Artifact | Outcome | Brand | Recommendations |
| --- | --- | --- | --- |
| `content_dna.md` | ✓ | ✓ | ✓ |
| `audience_persona.md` | ✓ | ✓ | ✓ |
| `master_emotional_bible.md` | ✓ | ✓ | ✓ |
| `advanced_visual_analysis.md` | | ✓ | ✓ |
| `narrative_patterns.md` | ✓ | ✓ | ✓ |
| `audience_psychology.md` | ✓ | | ✓ |
| `comments.csv` | ✓ | | ✓ |
| `cross_channel_synthesis_v2.md` | | ✓ | ✓ |
| `top_videos.csv` | | | ✓ |

**Partial MVP:** Bibles + visual + narrative without comments → Outcome Profile at MEDIUM confidence; audience fields omitted or marked LOW.

---

## Example JSON Skeleton (illustrative)

```json
{
  "channel_slug": "whisprs_yt",
  "channel_name": "Whisprs",
  "pipeline_status": "full",
  "outcome_profile": {
    "dominant_emotional_outcome": "acceptance",
    "secondary_outcomes": ["self-love", "peaceful sadness"],
    "emotional_journey": {
      "arrival_state": "heartbreak, loneliness",
      "transformation_stages": ["pain", "recognition", "acceptance", "growth"],
      "desired_state": "self-worthy, emotionally stable"
    },
    "audience_emotional_need": {
      "primary_need": "validation and self-worth after relational pain",
      "comment_themes": [
        { "theme": "self_love", "count": 804, "pct": 0.21 }
      ],
      "save_signals": ["needed this", "thank you"]
    },
    "evidence_confidence": {
      "overall": "HIGH",
      "outcome": "HIGH",
      "journey": "MEDIUM",
      "audience_need": "HIGH"
    }
  },
  "brand_profile": { "..." : "..." },
  "content_recommendations": { "..." : "..." }
}
```

Values must be **extracted** from reports — this skeleton is not a hardcoded template.

# MVP Spec — Phase 1 Productization

> **Status:** **PLANNED** (spec only — no MVP UI or assembler shipped yet)  
> **Evidence gate:** Cleared (`reports/validation_phase2.md`)  
> **Research:** Frozen (`research_freeze.yaml`)  
> **Scope:** Channel intelligence only — **no content generation**

---

## Purpose

Convert existing channel analysis artifacts into a **usable MVP** that explains **why a channel works** for emotional recovery / quote Shorts channels validated in the benchmark cohort.

The MVP does **not**:

- Generate scripts, images, video, or voice
- Claim universal psychological truth across all niches
- Introduce new frameworks, taxonomies, mechanisms, or analyzers
- Run discovery or multi-niche orchestration

The MVP **does**:

- Accept a YouTube channel URL
- Run the **existing** pipeline (or read cached artifacts)
- Emit three structured products: **Outcome Profile**, **Brand Profile**, **Content Recommendations**

---

## User Flow

```text
Channel URL
    │
    ▼
Analysis (existing pipeline)
    │  main.py "URL"  OR  benchmark_program --full {slug}
    │  Steps 1–11 + advanced visual + comments + bible synthesis
    │
    ▼
Reports (source of truth on disk)
    │  reports/{slug}/content_dna.md
    │  reports/{slug}/audience_persona.md
    │  reports/{slug}/master_emotional_bible.md
    │  reports/{slug}/advanced_visual_analysis.md
    │  reports/{slug}/narrative_patterns.md
    │  reports/{slug}/audience_psychology.md  (when comments exist)
    │  reports/cross_channel_synthesis_v2.md   (benchmark context)
    │
    ▼
MVP Output (assembled — Phase 1.5 assembler **PLANNED**)
    │  Outcome Profile
    │  Brand Profile
    │  Content Recommendations
    │
    ▼
User / UI reads structured JSON or rendered markdown
```

**Today:** Steps 1–11 and extensions **SHIPPED** via CLI. The final assembly step into three MVP products is **not shipped** — users read bible markdown directly.

**Phase 1 deliverable:** This spec + data contract + scoring + readiness review.  
**Phase 1.5 (next):** Thin `outcome_profile_assembler` that maps existing reports → JSON contract (no new analysis).

---

## Input

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `channel_url` | string | yes | YouTube `@handle` or channel URL |
| `slug` | string | auto | Derived from channel; used for `reports/{slug}/` paths |

Optional (future UI only):

| Field | Type | Notes |
| --- | --- | --- |
| `benchmark_context` | boolean | Include cross-channel comparison from `cross_channel_synthesis_v2.md` |
| `force_rerun` | boolean | Re-run pipeline vs read cache |

---

## Output Sections

### 1. Outcome Profile

**Question answered:** *What emotional job does this channel perform for viewers, and with what confidence?*

Describes the channel's **observed emotional product** — not a universal human psychology model.

| Subsection | Content | Primary sources |
| --- | --- | --- |
| **Dominant emotional outcome** | Primary post-viewing state (e.g. acceptance, self-love, peaceful sadness) | `master_emotional_bible.md`, `content_dna.md` |
| **Emotional journey** | Arrival → transformation → desired state (e.g. pain → acceptance → growth) | `master_emotional_bible.md`, `narrative_patterns.md` |
| **Audience emotional need** | What viewers arrive with; comment-validated where available | `audience_persona.md`, `audience_psychology.md`, `comments.csv` |
| **Evidence confidence** | HIGH / MEDIUM / LOW per field (see `docs/MVP_SCORING.md`) | Scoring rules applied to source tags |

**Evidence rules:**

- Comment-backed claims require `comments.csv` with ≥300 cleaned rows (validated on `whisprs_yt`, `soulxsigh`).
- Bible-only claims are **MEDIUM** at best unless corroborated by visual or narrative reports.
- Do not emit Recognition or Mechanism labels unless supported by `audience_psychology.md` phrase evidence.

**Example (Whisprs — from existing bibles, not new theory):**

- Dominant outcome: acceptance + self-worth restoration  
- Journey: pain → recognition → acceptance → growth  
- Audience need: heartbreak, loneliness, validation ("needed this", "thank you")  
- Confidence: HIGH where comments + visual + narrative align; MEDIUM for brand-specific gaze/archetype claims

---

### 2. Brand Profile

**Question answered:** *How does this channel differentiate within the niche?*

| Subsection | Content | Primary sources |
| --- | --- | --- |
| **Brand personality** | Emotional positioning, voice tone, what the channel is *not* | `content_dna.md`, `master_emotional_bible.md` |
| **Recurring themes** | Quote/emotion themes in top content | `quote_patterns.md`, `emotion_clusters.md`, `content_dna.md` |
| **Visual identity** | Archetype, gaze, composition, palette, negative space | `advanced_visual_analysis.md`, `visual_analysis.md` |
| **Narrative identity** | Hook structure, arc pattern, pacing | `narrative_patterns.md` |

**Cross-channel context (optional block):**

- Patterns shared with benchmark cohort vs channel-unique signals  
- Source: `cross_channel_synthesis_v2.md`, `validation_phase2.md`  
- Label niche-wide patterns as **cohort evidence (5 channels)**; label divergences (e.g. Whisprs dreamer + looking-up) as **channel-specific**

---

### 3. Content Recommendations

**Question answered:** *What is working, what is missing, and what should the creator consider next — based on evidence only?*

| Subsection | Content | Primary sources |
| --- | --- | --- |
| **Patterns working today** | Visual/narrative/emotional patterns correlated with top performers | `advanced_visual_analysis.md` (performance correlations), `top_videos.csv`, `content_dna.md` Facts |
| **Opportunities observed** | Under-used themes or formats in top vs non-top videos | `quote_database.csv`, `emotion_clusters.md`, performance splits in visual report |
| **Missing content areas** | Gaps noted in bible Unknowns/Gaps sections | `content_dna.md`, `audience_persona.md`, `master_emotional_bible.md` |
| **Evidence-backed recommendations** | Actionable suggestions tied to observed data | Must cite source report + metric; no invented strategies |

**Recommendation constraints:**

- Every recommendation must include: `source_report`, `evidence_snippet`, `confidence`
- Benchmark comparisons must reference `cross_channel_synthesis_v2.md` (e.g. "averted gaze appears in 60% of cohort vs dreamer+looking-up on Whisprs only")
- Do **not** recommend tactics absent from reports (e.g. "post 3x daily", "use TikTok") unless `channel_playbook.md` or performance data supports it

**Example evidence-backed recommendations (Whisprs-style):**

- Maintain ≥70% negative space — 81% avg on high performers (`advanced_visual_analysis.md`) [HIGH]
- Lean into self-love + validation comment clusters — 23% + 412 validation comments (`audience_psychology.md`) [HIGH]
- Avoid revenge / hype motivation framing — consistent across bibles and cohort synthesis [MEDIUM]

---

## Source of Truth Hierarchy

When reports conflict, resolve in this order:

1. Raw CSV metrics (`top_videos.csv`, `comments.csv`, `advanced_visual_videos.csv`)
2. Step reports with explicit counts (`advanced_visual_analysis.md`, `audience_psychology.md`)
3. Bible synthesis (`content_dna.md`, `audience_persona.md`, `master_emotional_bible.md`) — verify Facts against step reports
4. Cross-channel synthesis (cohort context only — not channel-specific law)
5. Architecture reference docs (`HUMAN_OUTCOME_ENGINE.md`) — **REFERENCE only**, not auto-populated

---

## Non-Goals (Phase 1)

- Web UI, API server, auth, billing
- Content generation, prompt chains, image/video tools
- Multi-niche profiles (`--niche` / `--brand` loaders)
- Competitor discovery or automatic benchmark selection
- Knowledge graph, vector DB, RAG, agents

See `docs/NON_GOALS.md`.

---

## Success Criteria (MVP Phase 1)

A channel with full pipeline + comments can produce:

1. **Outcome Profile** — readable in &lt;2 min; every claim traceable to a report path  
2. **Brand Profile** — distinguishes channel from cohort where evidence exists  
3. **Content Recommendations** — ≥3 recommendations with cited evidence; zero invented tactics  

**Validated test channels:** `whisprs_yt`, `soulxsigh` (comments + full bibles).  
**Partial test channels:** `soulful_lines`, `dark_poetry_hub`, `the_faceless_storyteller` (bibles + visual; sparse/no comments).

---

## Related Documents

| Doc | Role |
| --- | --- |
| `docs/MVP_DATA_CONTRACT.md` | Field-level schema and report mapping |
| `docs/MVP_SCORING.md` | Confidence calculation rules |
| `reports/mvp_readiness_review.md` | Go/no-go and gap analysis |
| `docs/CURRENT_STATE.md` | What pipeline steps are SHIPPED today |

# Creator Feedback Template — MVP Validation

> **Purpose:** Capture structured validation after a creator reads `reports/{slug}/channel_intelligence_report.md`.  
> **Storage:** Append via `scripts/record_creator_feedback.py` → `data/feedback/creator_feedback.jsonl`

---

## Instructions

1. Run the MVP flow: `python main.py "CHANNEL_URL" --mvp-profile` (or assemble + render for an existing slug).
2. Open `reports/{slug}/channel_intelligence_report.md` and skim all six sections.
3. Fill the fields below (or use the JSON template at `templates/creator_feedback.json`).
4. Record with:

```bash
python scripts/record_creator_feedback.py --interactive
# or
python scripts/record_creator_feedback.py --file my_feedback.json
```

---

## Feedback form

| Field | Your response |
| --- | --- |
| **Channel slug** | |
| **Channel URL** | |
| **Date reviewed** | |
| **Your role** | creator / operator / investor / other |

### Accuracy (1–5)

_How well does the report describe your channel?_

| 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- |
| Mostly wrong | Often off | Mixed | Mostly right | Matches my channel |

**Score:**

### Usefulness (1–5)

_How actionable is this for your next content decisions?_

| 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- |
| Not useful | Vague | Some ideas | Useful | Would change decisions |

**Score:**

### Surprises

What was unexpected, wrong, or missing?

```




```

### Willingness to pay

- [ ] No
- [ ] Maybe (need more proof)
- [ ] Yes, under $50/mo
- [ ] Yes, $50–200/mo
- [ ] Yes, over $200/mo

### Decision it would help with

_Name one concrete decision (topic, format, visual, posting cadence, positioning):_

```




```

### Section ranking (optional)

| Section | Most valuable? | Least valuable? |
| --- | --- | --- |
| 1. Audience Outcome Profile | | |
| 2. Brand Identity Profile | | |
| 3. Content Opportunities | | |
| 4. Evidence Confidence | | |
| 5. Top Performing Patterns | | |
| 6. Recommended Experiments | | |

### Freeform notes

```




```

---

## JSON example

```json
{
  "channel_slug": "whisprs_yt",
  "channel_url": "https://www.youtube.com/@WhisprsYT",
  "report_path": "reports/whisprs_yt/channel_intelligence_report.md",
  "submitted_at": "2026-06-27T12:00:00+00:00",
  "reviewer_role": "creator",
  "accuracy": 4,
  "usefulness": 4,
  "surprises": "Save signals felt too quote-heavy; wanted more on posting frequency.",
  "willingness_to_pay": "maybe",
  "decision_it_would_help_with": "Which emotional themes to double down on in next 10 Shorts",
  "most_valuable_section": "top_performing_patterns",
  "least_valuable_section": "evidence_confidence",
  "freeform_notes": ""
}
```

Schema: `templates/creator_feedback.json`

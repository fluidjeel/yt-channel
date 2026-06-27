# Human Mechanism Taxonomy

> **Status:** **REFERENCE / HYPOTHESIS**  
> **Not shipped:** no analyzer, generator, knowledge graph, vector DB, RAG, dashboard, or agent system is implemented from this document.  
> **Evidence base:** current recovery research only: `reports/EMOTIONAL_JOB_TO_BE_DONE.md`, `reports/EMOTIONAL_PRODUCT.md`, `reports/NICHE_TAXONOMY_V1.md`, `docs/HUMAN_OUTCOME_ENGINE.md`  
> **Current limitation:** 3 analyzed channels, 0 competitor comment datasets.

This document adds the causal layer between:

```text
Job To Be Done
↓
Emotional Outcome
```

That layer is usually not one step. Current architecture now treats it as:

```text
Recognition
↓
Mechanism
```

Recognition explains **why the viewer stops**: "this is about me."

Mechanism explains **how the content moves them** from arrival state to desired state.

---

## Updated Layer Model

```text
Layer 0: Human Psychology
↓
Layer 1: Human State / Job To Be Done
↓
Layer 2: Recognition
↓
Layer 3: Mechanism
↓
Layer 4: Emotional Outcome
↓
Layer 5: Niche Wrapper
↓
Layer 6: Brand Personality
↓
Layer 7: Content
```

Why this matters:

```text
Same outcome can be reached through different mechanisms.
```

Example:

| Outcome | Channel type | Mechanism |
| --- | --- | --- |
| Acceptance | Anime recovery | Validation |
| Acceptance | Philosophy | Meaning Making |
| Acceptance | Psychology | Reframing |

Do not confuse mechanism with niche or brand. A mechanism is reusable across many niches.

---

## Core Schema

Every mechanism should be stored in this structure:

```yaml
mechanism:
  id: validation
  status: reference | partial | hypothesis
  job_to_be_done: ""
  arrival_state: ""
  recognition_trigger:
    viewer_self_identification: ""
    example_language: []
  mechanism: ""
  desired_outcome: ""
  evidence:
    current_project: []
    future_required: []
  example_niches: []
  risks: []
  confidence: 0.0
```

Evidence rule:

```text
No mechanism becomes SHIPPED truth until validated across multiple channels and comments.
```

---

## Mechanism Matrix

| Mechanism | Job To Be Done | Arrival State | Outcome | Evidence Status |
| --- | --- | --- | --- | --- |
| Recognition | make viewer stop and self-identify | "this is about me" moment | attention / relevance | PARTIAL |
| Validation | regulate pain | hurt, unseen, self-doubting | acceptance / relief | PARTIAL |
| Reframing | regulate pain or confusion | stuck interpretation | clarity / acceptance | HYPOTHESIS |
| Meaning Making | process pain or uncertainty | meaningless pain | acceptance / purpose | PARTIAL |
| Catharsis | release tension | fear, grief, suppressed emotion | release | HYPOTHESIS |
| Relief | escape stress | pressure, irritation, fatigue | lightness | HYPOTHESIS |
| Education | reduce ignorance | not knowing | understanding | HYPOTHESIS |
| Opportunity Framing | reduce uncertainty | ambiguity, scarcity, indecision | possibility | HYPOTHESIS |
| Future Projection | imagine a better future state | stuck, uncertain, low hope | hope | HYPOTHESIS |
| Social Proof | reduce risk | doubt, hesitation | confidence | HYPOTHESIS |
| Identity Signaling | express self | unclear belonging/status | self-recognition | HYPOTHESIS |
| Belonging | reduce isolation | loneliness, outsider feeling | connection | PARTIAL |
| Agency Restoration | recover power | stuck, defeated | agency | HYPOTHESIS |
| Competence Building | reduce confusion | incompetence, overwhelm | competence | HYPOTHESIS |
| Status Elevation | resolve status anxiety | low status, comparison, invisibility | significance / prestige | HYPOTHESIS |

---

## Mechanisms

### 0. Recognition

```text
"This is exactly me."
```

| Field | Value |
| --- | --- |
| **Arrival state** | private feeling, unresolved pain, curiosity, anxiety, aspiration |
| **Mechanism** | mirror the viewer's exact internal state, situation, desire, fear, or self-image |
| **Outcome** | attention, relevance, openness to the next mechanism |
| **Current evidence** | Whisprs comments include "needed this", "this hit", and repeated gratitude; hooks in Whisprs/Faceless are designed as direct self-identification prompts |
| **Example niches** | recovery, humor, horror, business, tech, parenting, identity content |
| **Confidence** | 0.68 in current recovery evidence; HYPOTHESIS as universal entry layer |

Recognition is not the final emotional outcome. It is the entry gate.

Without recognition:

```text
No emotional transaction occurs.
```

For Whisprs, a recognition prompt might be:

```text
"You miss them, but you would never tell them."
```

The viewer first thinks:

```text
"This is about me."
```

Only then can validation, meaning making, acceptance, or self-worth restoration occur.

---

### 1. Validation

```text
"What I feel is real."
```

| Field | Value |
| --- | --- |
| **Arrival state** | hurt, unseen, lonely, self-doubting |
| **Mechanism** | name the viewer's feeling and confirm it without mocking or minimizing it |
| **Outcome** | acceptance, relief, emotional regulation |
| **Current evidence** | Whisprs comments: "needed this", "thank you"; heartbreak 23%, self-love 21%; all 3 channels use solitary visual framing |
| **Example niches** | recovery, therapy-adjacent education, grief, identity content |
| **Confidence** | 0.76 in anime recovery; HYPOTHESIS elsewhere |

Validation is likely Whisprs' primary mechanism. The viewer is not being told to become happy. They are being told their pain makes sense.

---

### 2. Reframing

```text
"There is another way to understand this."
```

| Field | Value |
| --- | --- |
| **Arrival state** | stuck interpretation, rumination, shame, confusion |
| **Mechanism** | turn the same event into a different meaning |
| **Outcome** | clarity, acceptance, renewed agency |
| **Current evidence** | Hook -> Reflection -> Insight -> Resolution appears in Whisprs and Faceless; Whisprs comments show viewers using content as interpretation aid |
| **Example niches** | recovery, psychology, philosophy, business, tech explainers |
| **Confidence** | 0.55 current recovery evidence; HYPOTHESIS as universal layer |

Reframing differs from validation. Validation says "your feeling is real." Reframing says "the meaning can change."

---

### 3. Meaning Making

```text
"This pain fits into a larger story."
```

| Field | Value |
| --- | --- |
| **Arrival state** | pain feels random, unfair, pointless, spiritually empty |
| **Mechanism** | connect experience to growth, purpose, fate, wisdom, lesson, or transformation |
| **Outcome** | acceptance, purpose, identity transition |
| **Current evidence** | all 3 bibles repeat Pain -> Understanding -> Acceptance -> Growth; Whisprs comments include spiritual search 10% |
| **Example niches** | spirituality, philosophy, grief, recovery, documentary storytelling |
| **Confidence** | 0.62 current recovery evidence |

Meaning Making may be the bridge between emotional regulation and identity transition.

---

### 4. Catharsis

```text
"Let me feel it intensely, then release it."
```

| Field | Value |
| --- | --- |
| **Arrival state** | fear, grief, rage, tension, suppressed emotion |
| **Mechanism** | intensify emotion in a safe container until release occurs |
| **Outcome** | catharsis, emotional discharge |
| **Current evidence** | not validated; Faceless Storyteller may be adjacent through horror hooks, but comments are missing |
| **Example niches** | horror, tragedy, confession stories, grief content, intense music edits |
| **Confidence** | 0.20 current project |

Do not claim Faceless Storyteller provides catharsis until comment data proves it.

---

### 5. Relief

```text
"Take the pressure off for a moment."
```

| Field | Value |
| --- | --- |
| **Arrival state** | stress, irritation, boredom, social fatigue |
| **Mechanism** | break tension through humor, absurdity, recognition, or lightness |
| **Outcome** | relief, lightness, social reset |
| **Current evidence** | not measured in current recovery project |
| **Example niches** | humor, satire, memes, comfort entertainment |
| **Confidence** | 0.10 current project |

Relief is probably the core mechanism for humor channels, but that is not validated here.

---

### 6. Education

```text
"Explain the thing I do not understand."
```

| Field | Value |
| --- | --- |
| **Arrival state** | ignorance, curiosity, uncertainty |
| **Mechanism** | structured explanation |
| **Outcome** | understanding |
| **Current evidence** | not measured in current recovery project |
| **Example niches** | tech, science, finance, tutorials, history |
| **Confidence** | 0.10 current project |

Education can be purely informational, but for media brands it often works because it creates emotional outcomes: competence, control, confidence.

---

### 7. Opportunity Framing

```text
"There may be a path I did not see."
```

| Field | Value |
| --- | --- |
| **Arrival state** | uncertainty, scarcity, indecision, stuckness |
| **Mechanism** | reveal hidden options, trends, opportunities, or paths |
| **Outcome** | possibility |
| **Current evidence** | not measured in current recovery project |
| **Example niches** | business ideas, side hustles, market intelligence, career content |
| **Confidence** | 0.10 current project |

Opportunity Framing is likely central for future business/opportunity channels.

---

### 8. Social Proof

```text
"Other people believe this, use this, or survived this."
```

| Field | Value |
| --- | --- |
| **Arrival state** | doubt, risk, fear of choosing wrong |
| **Mechanism** | show examples, proof, testimonials, popularity, adoption, precedent |
| **Outcome** | confidence, reduced risk |
| **Current evidence** | weak; Whisprs repeated comments show social resonance but not explicit proof-seeking |
| **Example niches** | business, tech reviews, product reviews, self-improvement, finance |
| **Confidence** | 0.15 current project |

Social Proof is distinct from belonging. It is about reducing decision risk, not necessarily feeling emotionally connected.

---

### 9. Future Projection

```text
"A better future is imaginable."
```

| Field | Value |
| --- | --- |
| **Arrival state** | uncertainty, discouragement, stagnation, low hope |
| **Mechanism** | project a believable future state the viewer can imagine inhabiting |
| **Outcome** | hope, possibility, aspiration |
| **Current evidence** | weak in current recovery project; Whisprs looking-up/hopeful visual flavor may partially perform this, but this is brand-specific evidence |
| **Example niches** | business ideas, startup content, AI opportunity, career, motivation, education |
| **Confidence** | 0.20 current project; important HYPOTHESIS for opportunity channels |

Future Projection differs from Opportunity Framing.

```text
Opportunity Framing = "There is a path."
Future Projection   = "I can imagine myself in that better state."
```

This is likely critical for business, startup, AI, and career channels where the viewer is buying possibility and hope.

---

### 10. Identity Signaling

```text
"This says something about who I am."
```

| Field | Value |
| --- | --- |
| **Arrival state** | unclear self-image, status need, belonging need |
| **Mechanism** | provide language, symbols, taste, or worldview that viewers can adopt |
| **Outcome** | self-recognition, status, belonging |
| **Current evidence** | partial; Whisprs comments include identity 9%, self-esteem 6%; visual/brand style is strongly identity-coded |
| **Example niches** | fashion, fandom, philosophy, aesthetics, political commentary, business identity |
| **Confidence** | 0.35 current recovery evidence |

Identity Signaling may become important if viewers save/share content as self-description. Current share evidence is weak.

---

### 11. Belonging

```text
"People like me exist."
```

| Field | Value |
| --- | --- |
| **Arrival state** | loneliness, outsider feeling, private pain |
| **Mechanism** | reflect a shared feeling, group identity, or unspoken experience |
| **Outcome** | connection, less aloneness |
| **Current evidence** | all 3 channels use solitude visuals; Whisprs loneliness life situation 17%, repeated gratitude |
| **Example niches** | recovery, fandom, humor, identity content, spiritual content |
| **Confidence** | 0.68 current recovery evidence |

Belonging is close to validation but social rather than internal. Validation says "your feeling is real"; belonging says "you are not the only one."

---

### 12. Agency Restoration

```text
"I can do something now."
```

| Field | Value |
| --- | --- |
| **Arrival state** | stuck, defeated, passive, overwhelmed |
| **Mechanism** | show action path, give permission, simplify next step, restore control |
| **Outcome** | agency, momentum |
| **Current evidence** | weak in current recovery project; growth language appears in bibles, but not action-oriented |
| **Example niches** | motivation, fitness, business, productivity, career |
| **Confidence** | 0.20 current project |

Agency Restoration is not the same as motivation. Motivation produces energy; agency produces the belief that action is possible.

---

### 13. Competence Building

```text
"I understand this well enough to act."
```

| Field | Value |
| --- | --- |
| **Arrival state** | confusion, incompetence, fear of being left behind |
| **Mechanism** | simplify, sequence, demonstrate, compare, teach |
| **Outcome** | competence, control |
| **Current evidence** | not measured in current recovery project |
| **Example niches** | tech, education, tutorials, AI tools, finance |
| **Confidence** | 0.10 current project |

Competence Building is likely the core mechanism for tech and educational media brands.

---

### 14. Status Elevation

```text
"This makes me more significant."
```

| Field | Value |
| --- | --- |
| **Arrival state** | status anxiety, comparison, invisibility, fear of falling behind |
| **Mechanism** | associate the viewer with higher-status knowledge, taste, identity, access, skill, wealth, or group membership |
| **Outcome** | significance, prestige, identity reinforcement |
| **Current evidence** | not measured in current recovery project |
| **Example niches** | luxury, finance, entrepreneurship, AI founder content, productivity, self-improvement, fashion |
| **Confidence** | 0.10 current project; important HYPOTHESIS for future non-recovery niches |

Status Elevation is not the same as competence.

```text
Competence = "I can do this."
Status     = "Being able to do/know/own this says something about me."
```

This mechanism should be handled carefully because it can drift into shallow aspiration or fake authority if not evidence-backed.

---

## Mechanism vs Outcome

Do not use these interchangeably.

| Mechanism | Outcome it can produce |
| --- | --- |
| Validation | acceptance, relief, belonging |
| Reframing | clarity, acceptance, agency |
| Meaning Making | purpose, acceptance, identity transition |
| Catharsis | release, relief |
| Relief | lightness, reduced stress |
| Education | understanding, competence |
| Opportunity Framing | possibility, agency |
| Future Projection | hope, aspiration, possibility |
| Social Proof | confidence, reduced risk |
| Identity Signaling | self-recognition, belonging, status |
| Belonging | connection, emotional safety |
| Agency Restoration | momentum, control |
| Competence Building | competence, control |
| Status Elevation | significance, prestige, identity reinforcement |

The same mechanism can produce different outcomes depending on niche and brand.

---

## Examples By Future Channel Type

These are **architecture examples**, not validated project findings.

### Whisprs

| Layer | Value |
| --- | --- |
| Job | regulate pain / support identity transition |
| Recognition | "This is exactly my private pain" |
| Mechanism | validation + meaning making |
| Outcome | acceptance + self-worth |
| Niche Wrapper | anime recovery |
| Brand Personality | dreamer, looking up, hopeful solitude |
| Evidence Status | PARTIAL |

### Horror Channel

| Layer | Value |
| --- | --- |
| Job | safe fear experience |
| Recognition | "This fear / curiosity hooks me" |
| Mechanism | controlled suspense + catharsis |
| Outcome | release |
| Niche Wrapper | horror stories |
| Brand Personality | dark folklore |
| Evidence Status | HYPOTHESIS |

### Business Ideas Channel

| Layer | Value |
| --- | --- |
| Job | reduce uncertainty |
| Recognition | "I might be missing an opportunity" |
| Mechanism | opportunity framing + future projection |
| Outcome | possibility + hope |
| Niche Wrapper | business opportunities |
| Brand Personality | opportunity scout |
| Evidence Status | HYPOTHESIS |

### Tech Channel

| Layer | Value |
| --- | --- |
| Job | reduce confusion |
| Recognition | "I need to understand this before I fall behind" |
| Mechanism | simplification + competence building |
| Outcome | competence |
| Niche Wrapper | tech explanations |
| Brand Personality | practical futurist |
| Evidence Status | HYPOTHESIS |

### Humor Channel

| Layer | Value |
| --- | --- |
| Job | escape stress |
| Recognition | "That is exactly the annoying thing I experience" |
| Mechanism | humor + social recognition |
| Outcome | relief |
| Niche Wrapper | comedy |
| Brand Personality | sarcastic observer |
| Evidence Status | HYPOTHESIS |

---

## Evidence Limits

Current architecture is stronger than current evidence.

Known limits:

- Only 3 full benchmark channels.
- Only Whisprs has usable comment evidence.
- Competitor channels may not represent the niche.
- Faceless Storyteller may be a horror/catharsis channel rather than recovery.
- Soulful Lines transcript quality may distort narrative findings.
- Most non-recovery mechanism examples are strategic hypotheses, not measured outputs.
- Recognition, Future Projection, and Status Elevation are architecturally important but not yet benchmark-validated across niches.

Therefore:

```text
Do not build universal code from this yet.
Use it as a research schema.
```

---

## Validation Requirements

Before promoting this taxonomy beyond REFERENCE:

1. Complete 5 live benchmark channels.
2. Fix competitor comment collection.
3. Re-run cross-channel synthesis.
4. Test mechanism labels against actual comment language.
5. Specifically test recognition phrases: "this is me", "needed this", "felt called out", "so true", "this hit".
6. Validate at least one non-recovery niche before claiming universality.

---

## Summary

The missing layer is:

```text
Mechanism
```

The full reusable stack becomes:

```text
Human Psychology
-> Job To Be Done
-> Recognition
-> Mechanism
-> Emotional Outcome
-> Niche Wrapper
-> Brand Personality
-> Content
```

This prevents a common failure:

```text
copying content style while missing the psychological mechanism.
```

For Whisprs, the current best read is:

```text
Human State: heartbroken / lonely / self-doubting
Recognition: "This is exactly me."
Job: regulate pain
Mechanism: validation + meaning making
Outcome: acceptance
Wrapper: anime recovery
Brand: dreamer / looking-up / hopeful solitude
```


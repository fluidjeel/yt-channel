# Knowledge — Layer 1

**Purpose:** Taxonomy registry, knowledge graph, research database.

**Planned:**
- Register niche profiles from `niches/`
- Graph relationships: emotion ↔ visual ↔ performance
- Persist cross-channel research

**Current implementation:** `market_intelligence/models.py`, `storage.py` (scaffold)  
**Planned paths:** `knowledge_graph/`, `data/research/` (see config)

Core stores **references** to niche IDs, not niche-specific taxonomies inline.

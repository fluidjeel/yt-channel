"""Unit tests for advanced visual analysis heuristics."""

from __future__ import annotations

import numpy as np

from channel_analyzer.advanced_visual.composition import (
    analyze_composition,
    detect_faces,
    infer_relationship_heuristic,
    negative_space_percent,
)
from channel_analyzer.advanced_visual.models import (
    CHARACTER_ARCHETYPES,
    COMPOSITION_TYPES,
    EMOTIONAL_EXPRESSIONS,
    GAZE_TYPES,
    RELATIONSHIP_TYPES,
    SYMBOLISM_TAGS,
    FrameAnalysis,
    VideoVisualProfile,
)
from channel_analyzer.advanced_visual_analyzer import (
    _aggregate_video,
    _build_key_insights,
    _performance_correlations,
)


def test_label_enums_complete():
    assert "solitary_female" in CHARACTER_ARCHETYPES
    assert "looking_away" in GAZE_TYPES
    assert "peaceful_sadness" in EMOTIONAL_EXPRESSIONS
    assert "tiny_human_large_world" in COMPOSITION_TYPES
    assert "sunset" in SYMBOLISM_TAGS
    assert "separated_couple" in RELATIONSHIP_TYPES


def test_negative_space_on_uniform_frame():
    frame = np.full((200, 200, 3), 30, dtype=np.uint8)
    pct = negative_space_percent(frame)
    assert pct > 80


def test_tiny_human_large_world_heuristic():
    frame = np.zeros((400, 400, 3), dtype=np.uint8)
    # Small bright blob = subject
    frame[350:380, 10:40] = 200
    comp, conf, neg_pct, scale = analyze_composition(frame, faces=[])
    assert comp in COMPOSITION_TYPES
    assert 0 <= conf <= 1
    assert neg_pct >= 0


def test_relationship_heuristic_face_count():
    rel, conf = infer_relationship_heuristic([], (480, 640, 3))
    assert rel == "alone"
    assert conf > 0.5

    faces = [(100, 100, 50, 50), (160, 100, 50, 50)]
    rel2, _ = infer_relationship_heuristic(faces, (480, 640, 3))
    assert rel2 in RELATIONSHIP_TYPES


def test_frame_analysis_to_row():
    fa = FrameAnalysis(
        video_id="abc",
        frame_path="/tmp/f.jpg",
        timestamp_sec=1.0,
        character_archetype="solitary_female",
        character_confidence=0.8,
        gaze="looking_away",
        gaze_confidence=0.7,
        expression="hopeful",
        expression_confidence=0.6,
        composition="tiny_human_large_world",
        composition_confidence=0.75,
        negative_space_pct=55.0,
        subject_scale_pct=4.0,
        symbolism=["sunset", "ocean"],
        relationship="alone",
        relationship_confidence=0.9,
        anime_style_score=0.72,
        face_count=0,
    )
    row = fa.to_row()
    assert row["symbolism"] == "sunset|ocean"
    assert row["character_archetype"] == "solitary_female"


def test_aggregate_video_dominant_labels():
    frames = [
        FrameAnalysis(
            video_id="v1",
            frame_path="a.jpg",
            timestamp_sec=0,
            character_archetype="solitary_female",
            character_confidence=0.9,
            gaze="looking_away",
            gaze_confidence=0.8,
            expression="hopeful",
            expression_confidence=0.7,
            composition="tiny_human_large_world",
            composition_confidence=0.8,
            negative_space_pct=60,
            subject_scale_pct=5,
            symbolism=["sunset"],
            relationship="alone",
            relationship_confidence=0.9,
            anime_style_score=0.8,
            face_count=0,
        ),
        FrameAnalysis(
            video_id="v1",
            frame_path="b.jpg",
            timestamp_sec=1,
            character_archetype="solitary_female",
            character_confidence=0.85,
            gaze="side_profile",
            gaze_confidence=0.75,
            expression="longing",
            expression_confidence=0.65,
            composition="tiny_human_large_world",
            composition_confidence=0.7,
            negative_space_pct=58,
            subject_scale_pct=6,
            symbolism=["sunset", "clouds"],
            relationship="alone",
            relationship_confidence=0.85,
            anime_style_score=0.75,
            face_count=0,
        ),
    ]
    profile = _aggregate_video(frames, {"video_id": "v1", "views_per_day": 1000, "rank": 1})
    assert profile.dominant_archetype == "solitary_female"
    assert profile.dominant_composition == "tiny_human_large_world"
    assert profile.symbolism_frequency["sunset"] == 2


def test_key_insights_with_synthetic_profiles():
    import pandas as pd

    profiles = [
        VideoVisualProfile(
            video_id=f"v{i}",
            views_per_day=1000 if i < 5 else 100,
            rank=i,
            dominant_archetype="solitary_female",
            dominant_gaze="looking_away",
            dominant_expression="hopeful",
            dominant_composition="tiny_human_large_world",
            avg_negative_space_pct=55,
            avg_anime_style_score=0.7,
            symbolism_frequency={"sunset": 3},
        )
        for i in range(8)
    ]
    frame_df = pd.DataFrame(
        {
            "video_id": ["v0", "v1", "v2"],
            "symbolism": ["sunset", "sunset|ocean", "clouds"],
            "character_archetype": ["solitary_female"] * 3,
            "gaze": ["looking_away"] * 3,
            "expression": ["hopeful"] * 3,
            "composition": ["tiny_human_large_world"] * 3,
            "negative_space_pct": [55, 60, 50],
            "anime_style_score": [0.7, 0.8, 0.65],
        }
    )
    text = _build_key_insights(profiles, frame_df)
    assert "high-performing" in text.lower() or "%" in text


def test_performance_correlations_minimum_videos():
    profiles = [
        VideoVisualProfile(video_id="a", views_per_day=100),
        VideoVisualProfile(video_id="b", views_per_day=200),
    ]
    assert _performance_correlations(profiles) == {}

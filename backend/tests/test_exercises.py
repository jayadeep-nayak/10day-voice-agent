import pytest
from exercises import (
    fetch_next_exercise_data,
    score_spoken_answer_data,
    EXERCISES,
    VALID_LEVELS,
    _normalize_level,
    _get_exercises_for_level,
)


# ─── Dataset Structure Tests ─────────────────────────────────────────────────

def test_dataset_is_a_flat_list():
    """EXERCISES must be a flat list of dicts, matching the JSON structure."""
    assert isinstance(EXERCISES, list)
    assert len(EXERCISES) >= 30  # At least 30 exercises total


def test_all_valid_levels_have_exercises():
    """Every level in VALID_LEVELS must have at least 3 exercises."""
    for level in VALID_LEVELS:
        exs = _get_exercises_for_level(level)
        assert len(exs) >= 3, f"Level '{level}' only has {len(exs)} exercise(s)"


def test_each_exercise_has_required_fields():
    """Every exercise must have: id, level, type, question, answer, acceptable."""
    for ex in EXERCISES:
        for field in ["id", "level", "type", "question", "answer", "acceptable"]:
            assert field in ex, f"Exercise id={ex.get('id')} missing '{field}'"


def test_each_exercise_has_valid_level():
    """Every exercise.level must be in VALID_LEVELS."""
    for ex in EXERCISES:
        assert ex["level"] in VALID_LEVELS, f"Exercise id={ex['id']} has invalid level '{ex['level']}'"


def test_each_exercise_has_valid_type():
    """Exercise type must be 'english' or 'math'."""
    for ex in EXERCISES:
        assert ex["type"] in ("english", "math"), f"Exercise id={ex['id']} has invalid type '{ex['type']}'"


def test_exercise_ids_are_unique():
    """All exercise IDs must be unique."""
    ids = [ex["id"] for ex in EXERCISES]
    assert len(ids) == len(set(ids)), "Duplicate exercise IDs found"


# ─── Level Normalization Tests ───────────────────────────────────────────────

def test_normalize_valid_levels():
    assert _normalize_level("beginner") == "beginner"
    assert _normalize_level("grade_1") == "grade_1"
    assert _normalize_level("intermediate") == "intermediate"


def test_normalize_aliases():
    assert _normalize_level("1") == "grade_1"
    assert _normalize_level("g2") == "grade_2"
    assert _normalize_level("Grade 3") == "grade_3"
    assert _normalize_level("g4") == "grade_4"
    assert _normalize_level("advanced") == "intermediate"


def test_normalize_invalid_defaults_to_beginner():
    """Requirement 5: invalid levels default to 'beginner'."""
    assert _normalize_level("xyz") == "beginner"
    assert _normalize_level("level_99") == "beginner"
    assert _normalize_level("") == "beginner"


# ─── fetch_next_exercise_data Tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_returns_exercise():
    """Requirement 4: returns exercise information."""
    res = await fetch_next_exercise_data(level="beginner")
    assert res["status"] in ["success", "success_offline_fallback"]
    assert res["exercise_id"] is not None
    assert res["question"] is not None
    assert len(res["question"]) > 5
    assert res["answer"] is not None


@pytest.mark.asyncio
async def test_fetch_beginner_english():
    res = await fetch_next_exercise_data(level="beginner", topic="english")
    assert res["level"] == "beginner"
    assert res["type"] == "english"


@pytest.mark.asyncio
async def test_fetch_grade_1_math():
    res = await fetch_next_exercise_data(level="grade_1", topic="math")
    assert res["level"] == "grade_1"
    assert res["type"] == "math"


@pytest.mark.asyncio
async def test_fetch_grade_2():
    res = await fetch_next_exercise_data(level="grade_2")
    assert res["level"] == "grade_2"


@pytest.mark.asyncio
async def test_fetch_grade_3():
    res = await fetch_next_exercise_data(level="grade_3")
    assert res["level"] == "grade_3"


@pytest.mark.asyncio
async def test_fetch_grade_4():
    res = await fetch_next_exercise_data(level="grade_4")
    assert res["level"] == "grade_4"


@pytest.mark.asyncio
async def test_fetch_intermediate():
    res = await fetch_next_exercise_data(level="intermediate")
    assert res["level"] == "intermediate"


@pytest.mark.asyncio
async def test_fetch_invalid_level_defaults_gracefully():
    """Requirement 5: invalid level → defaults to beginner, no crash."""
    res = await fetch_next_exercise_data(level="xyz_invalid")
    assert res["status"] in ["success", "success_offline_fallback"]
    assert res["level"] == "beginner"
    assert "notice" in res


@pytest.mark.asyncio
async def test_fetch_sequential_rotation():
    """Requirement 3: repeated calls rotate through exercises, not same one."""
    res1 = await fetch_next_exercise_data(level="beginner", topic="english")
    res2 = await fetch_next_exercise_data(level="beginner", topic="english")
    assert res1["exercise_id"] != res2["exercise_id"]


@pytest.mark.asyncio
async def test_fetch_has_timestamp():
    """Step 5: data_timestamp is present and contains 'UTC'."""
    res = await fetch_next_exercise_data(level="beginner")
    assert "data_timestamp" in res
    assert "UTC" in res["data_timestamp"]


@pytest.mark.asyncio
async def test_fetch_has_data_source():
    """Step 2: data_source field declares the source."""
    res = await fetch_next_exercise_data(level="beginner")
    assert "data_source" in res
    assert len(res["data_source"]) > 5


# ─── score_spoken_answer_data Tests ──────────────────────────────────────────

def test_score_exact_match():
    """Answer 'cold' for exercise 1 (opposite of hot) → 100%."""
    res = score_spoken_answer_data(exercise_id=1, spoken_answer="cold")
    assert res["score_percentage"] == 100
    assert res["passed"] is True


def test_score_acceptable_answer():
    """Answer 'cool' is in acceptable list for exercise 1 → 100%."""
    res = score_spoken_answer_data(exercise_id=1, spoken_answer="cool")
    assert res["score_percentage"] == 100
    assert res["passed"] is True


def test_score_number_word_equivalence():
    """Answer 'five' matches expected '5' for exercise 14."""
    res = score_spoken_answer_data(exercise_id=14, spoken_answer="five")
    assert res["score_percentage"] == 100
    assert res["passed"] is True


def test_score_unit_suffix_stripped():
    """Answer '315 kilometres' matches '315' for exercise 37."""
    res = score_spoken_answer_data(exercise_id=37, spoken_answer="315 kilometres")
    assert res["passed"] is True


def test_score_partial_match_reading():
    """Minor word drop in reading → still passes with high score."""
    res = score_spoken_answer_data(
        exercise_id=5,
        spoken_answer="the sun shines bright in sky",
        expected_answer="the sun shines bright in the sky",
    )
    assert res["score_percentage"] >= 70
    assert res["passed"] is True


def test_score_wrong_answer():
    """Completely wrong answer → low score, not passed."""
    res = score_spoken_answer_data(exercise_id=1, spoken_answer="elephant")
    assert res["score_percentage"] < 40
    assert res["passed"] is False


def test_score_has_timestamp():
    """Step 5: scored_at_timestamp is present."""
    res = score_spoken_answer_data(exercise_id=1, spoken_answer="cold")
    assert "scored_at_timestamp" in res
    assert "UTC" in res["scored_at_timestamp"]


def test_score_feedback_is_meaningful():
    """Feedback must be a non-empty string with useful text."""
    res = score_spoken_answer_data(exercise_id=1, spoken_answer="cold")
    assert isinstance(res["feedback"], str)
    assert len(res["feedback"]) > 5

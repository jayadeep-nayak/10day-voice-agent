"""
exercises.py — Learning & Literacy Domain Data Module

Data Source: Hand-built local dataset (declared in README).
             Live vocabulary enrichment via Datamuse Public API.

This module provides two core function-call backends:
  1. fetch_next_exercise_data(level)  — returns a graded exercise
  2. score_spoken_answer_data(...)    — scores a spoken answer
"""

import asyncio
import json
import logging
import random
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger("exercises")

# ─────────────────────────────────────────────────────────────────────────────
# HAND-BUILT LOCAL DATASET
# English-learning and simple math exercises categorized by level.
# Levels: beginner, grade_1, grade_2, grade_3, grade_4, intermediate
# Data source: hand-built by author — declared in README.
# ─────────────────────────────────────────────────────────────────────────────

EXERCISES: List[Dict[str, Any]] = [

    # ── BEGINNER (ages 4-6, pre-school / nursery) ────────────────────────────

    {"id": 1,  "level": "beginner", "type": "english",
     "question": "What is the opposite of 'hot'?",
     "answer": "cold",
     "acceptable": ["cold", "cool"]},

    {"id": 2,  "level": "beginner", "type": "english",
     "question": "What is the plural of 'book'?",
     "answer": "books",
     "acceptable": ["books"]},

    {"id": 3,  "level": "beginner", "type": "english",
     "question": "What rhymes with 'cat'? Say a word that sounds like cat.",
     "answer": "hat",
     "acceptable": ["hat", "bat", "mat", "sat", "rat", "fat", "pat"]},

    {"id": 4,  "level": "beginner", "type": "english",
     "question": "What is the first letter of the word 'apple'?",
     "answer": "a",
     "acceptable": ["a", "the letter a"]},

    {"id": 5,  "level": "beginner", "type": "english",
     "question": "Read this aloud: 'The sun shines bright in the sky.'",
     "answer": "the sun shines bright in the sky",
     "acceptable": ["the sun shines bright in the sky", "sun shines bright in the sky"]},

    {"id": 6,  "level": "beginner", "type": "english",
     "question": "What animal says 'moo' and gives us milk?",
     "answer": "cow",
     "acceptable": ["cow", "a cow", "cows"]},

    {"id": 7,  "level": "beginner", "type": "math",
     "question": "What is 2 plus 1?",
     "answer": "3",
     "acceptable": ["3", "three"]},

    {"id": 8,  "level": "beginner", "type": "math",
     "question": "How many fingers do you have on one hand?",
     "answer": "5",
     "acceptable": ["5", "five"]},

    {"id": 9,  "level": "beginner", "type": "math",
     "question": "How many days are there in one week?",
     "answer": "7",
     "acceptable": ["7", "seven", "seven days"]},

    # ── GRADE 1 (ages 6-7) ───────────────────────────────────────────────────

    {"id": 10, "level": "grade_1", "type": "english",
     "question": "What is the opposite of 'big'?",
     "answer": "small",
     "acceptable": ["small", "little", "tiny"]},

    {"id": 11, "level": "grade_1", "type": "english",
     "question": "Complete the sentence: She ___ to school every day.",
     "answer": "goes",
     "acceptable": ["goes", "walks", "runs"]},

    {"id": 12, "level": "grade_1", "type": "english",
     "question": "Read this sentence: 'Watering plants early keeps them healthy.'",
     "answer": "watering plants early keeps them healthy",
     "acceptable": ["watering plants early keeps them healthy"]},

    {"id": 13, "level": "grade_1", "type": "english",
     "question": "What is the past tense of 'run'?",
     "answer": "ran",
     "acceptable": ["ran"]},

    {"id": 14, "level": "grade_1", "type": "math",
     "question": "Ramesh has 3 apples and gets 2 more. How many apples does he have?",
     "answer": "5",
     "acceptable": ["5", "five", "five apples", "5 apples"]},

    {"id": 15, "level": "grade_1", "type": "math",
     "question": "Priya had 8 pencils. She gave 3 to her friend. How many are left?",
     "answer": "5",
     "acceptable": ["5", "five", "five pencils"]},

    {"id": 16, "level": "grade_1", "type": "math",
     "question": "What is 4 plus 6?",
     "answer": "10",
     "acceptable": ["10", "ten"]},

    # ── GRADE 2 (ages 7-8) ───────────────────────────────────────────────────

    {"id": 17, "level": "grade_2", "type": "english",
     "question": "What is the opposite of 'heavy'?",
     "answer": "light",
     "acceptable": ["light", "lightweight"]},

    {"id": 18, "level": "grade_2", "type": "english",
     "question": "What does the word 'harvest' mean?",
     "answer": "to collect crops",
     "acceptable": ["to collect crops", "collecting crops", "gathering crops", "picking crops"]},

    {"id": 19, "level": "grade_2", "type": "english",
     "question": "Read this aloud: 'The farmer works hard every day to grow food for everyone.'",
     "answer": "the farmer works hard every day to grow food for everyone",
     "acceptable": ["the farmer works hard every day to grow food for everyone"]},

    {"id": 20, "level": "grade_2", "type": "english",
     "question": "Fill in the blank: 'The children ___ playing in the park.' (is / are / am)",
     "answer": "are",
     "acceptable": ["are"]},

    {"id": 21, "level": "grade_2", "type": "math",
     "question": "A farmer planted 12 seeds. Only 7 grew. How many did not grow?",
     "answer": "5",
     "acceptable": ["5", "five", "5 seeds"]},

    {"id": 22, "level": "grade_2", "type": "math",
     "question": "What is 4 times 5?",
     "answer": "20",
     "acceptable": ["20", "twenty"]},

    {"id": 23, "level": "grade_2", "type": "math",
     "question": "There are 3 baskets with 6 mangoes in each. How many mangoes in total?",
     "answer": "18",
     "acceptable": ["18", "eighteen", "eighteen mangoes"]},

    # ── GRADE 3 (ages 8-9) ───────────────────────────────────────────────────

    {"id": 24, "level": "grade_3", "type": "english",
     "question": "What does the word 'irrigation' mean?",
     "answer": "supplying water to crops",
     "acceptable": ["supplying water to crops", "watering the fields", "bringing water to farms", "water supply to fields"]},

    {"id": 25, "level": "grade_3", "type": "english",
     "question": "What is a synonym for the word 'begin'?",
     "answer": "start",
     "acceptable": ["start", "commence", "initiate"]},

    {"id": 26, "level": "grade_3", "type": "english",
     "question": "Read this passage: 'Literacy and numeracy are the foundation of all learning.'",
     "answer": "literacy and numeracy are the foundation of all learning",
     "acceptable": ["literacy and numeracy are the foundation of all learning"]},

    {"id": 27, "level": "grade_3", "type": "english",
     "question": "Choose the correct word: 'She has ___ (ate / eaten) her lunch already.'",
     "answer": "eaten",
     "acceptable": ["eaten"]},

    {"id": 28, "level": "grade_3", "type": "math",
     "question": "Kavya reads 15 pages a day. How many pages in one week?",
     "answer": "105",
     "acceptable": ["105", "one hundred and five", "one hundred five"]},

    {"id": 29, "level": "grade_3", "type": "math",
     "question": "What is 25 multiplied by 4?",
     "answer": "100",
     "acceptable": ["100", "one hundred", "hundred"]},

    {"id": 30, "level": "grade_3", "type": "math",
     "question": "A school has 6 classrooms with 35 students each. How many students in total?",
     "answer": "210",
     "acceptable": ["210", "two hundred and ten", "two hundred ten"]},

    # ── GRADE 4 (ages 9-10) ──────────────────────────────────────────────────

    {"id": 31, "level": "grade_4", "type": "english",
     "question": "What is the meaning of the word 'pesticide'?",
     "answer": "a chemical used to kill insects or pests",
     "acceptable": ["a chemical used to kill insects or pests", "chemical used to destroy insects", "chemical to kill insects", "substance that kills pests"]},

    {"id": 32, "level": "grade_4", "type": "english",
     "question": "Use the word 'although' in a sentence.",
     "answer": "although it was raining he went outside",
     "acceptable": ["although it was raining he went outside", "although she was tired she studied"]},

    {"id": 33, "level": "grade_4", "type": "english",
     "question": "Read this: 'The government provides free textbooks to all primary school students every year.'",
     "answer": "the government provides free textbooks to all primary school students every year",
     "acceptable": ["the government provides free textbooks to all primary school students every year"]},

    {"id": 34, "level": "grade_4", "type": "english",
     "question": "What is the meaning of the word 'numeracy'?",
     "answer": "ability to understand and work with numbers",
     "acceptable": ["ability to understand and work with numbers", "ability to work with numbers", "understanding numbers", "skill with numbers"]},

    {"id": 35, "level": "grade_4", "type": "math",
     "question": "A bag of rice costs 450 rupees. A farmer buys 3 bags and pays 1500. How much change?",
     "answer": "150",
     "acceptable": ["150", "150 rupees", "one hundred and fifty", "one hundred fifty"]},

    {"id": 36, "level": "grade_4", "type": "math",
     "question": "What is 144 divided by 12?",
     "answer": "12",
     "acceptable": ["12", "twelve"]},

    {"id": 37, "level": "grade_4", "type": "math",
     "question": "A train travels 90 km per hour. How far in 3 and a half hours?",
     "answer": "315",
     "acceptable": ["315", "315 km", "315 kilometres", "three hundred and fifteen"]},

    # ── INTERMEDIATE (ages 10+, revision / adult literacy) ───────────────────

    {"id": 38, "level": "intermediate", "type": "english",
     "question": "Complete the sentence: 'If I ___ (was / were) you, I would study harder.'",
     "answer": "were",
     "acceptable": ["were"]},

    {"id": 39, "level": "intermediate", "type": "english",
     "question": "Read this: 'Agricultural productivity in India depends on timely rainfall, modern irrigation, and quality seeds.'",
     "answer": "agricultural productivity in india depends on timely rainfall modern irrigation and quality seeds",
     "acceptable": [
         "agricultural productivity in india depends on timely rainfall modern irrigation and quality seeds",
         "agricultural productivity in india depends on timely rainfall, modern irrigation, and quality seeds",
     ]},

    {"id": 40, "level": "intermediate", "type": "english",
     "question": "What is the difference between 'affect' and 'effect'?",
     "answer": "affect is a verb and effect is a noun",
     "acceptable": ["affect is a verb and effect is a noun", "affect is the verb effect is the noun", "affect verb effect noun"]},

    {"id": 41, "level": "intermediate", "type": "math",
     "question": "What is 15 percent of 200?",
     "answer": "30",
     "acceptable": ["30", "thirty"]},

    {"id": 42, "level": "intermediate", "type": "math",
     "question": "A shopkeeper buys an item for 800 rupees and sells it for 1000. What is the profit percentage?",
     "answer": "25",
     "acceptable": ["25", "25 percent", "twenty five", "twenty five percent"]},
]

# All valid levels in the dataset
VALID_LEVELS = ["beginner", "grade_1", "grade_2", "grade_3", "grade_4", "intermediate"]

# Sequential counter per level so repeated calls rotate through exercises
_EXERCISE_COUNTERS: Dict[str, int] = {}

# Number-word lookup for scoring (e.g. spoken "five" matches answer "5")
_NUM_WORDS: Dict[str, str] = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20", "twenty five": "25",
    "thirty": "30", "hundred": "100", "one hundred": "100",
    "one hundred and five": "105", "two hundred and ten": "210",
    "three hundred and fifteen": "315",
}


def _get_utc_timestamp() -> str:
    """Returns a human-readable UTC timestamp for database/audit storage."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _normalize_level(level: str) -> str:
    """
    Normalize user-spoken level strings to dataset keys.
    Handles: 'Grade 1', 'g2', '3', 'inter', etc.
    Returns a valid level key or 'beginner' as default.
    """
    raw = level.lower().strip().replace(" ", "_")
    aliases: Dict[str, str] = {
        "g1": "grade_1", "grade1": "grade_1", "1": "grade_1",
        "g2": "grade_2", "grade2": "grade_2", "2": "grade_2",
        "g3": "grade_3", "grade3": "grade_3", "3": "grade_3",
        "g4": "grade_4", "grade4": "grade_4", "4": "grade_4",
        "inter": "intermediate", "advanced": "intermediate",
    }
    resolved = aliases.get(raw, raw)
    if resolved in VALID_LEVELS:
        return resolved
    return "beginner"  # Graceful fallback for invalid levels


def _get_exercises_for_level(level: str) -> List[Dict[str, Any]]:
    """Filter the flat EXERCISES list by normalized level."""
    return [ex for ex in EXERCISES if ex["level"] == level]


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def _fetch_live_api_word(topic: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a dynamic vocabulary word from the Datamuse Public API.
    URL: https://api.datamuse.com/words?ml={topic}&max=5&md=d
    Strict 3-second timeout for fast failure handling.
    Returns None if the network is unavailable or API is empty.
    """
    url = f"https://api.datamuse.com/words?ml={topic}&max=5&md=d"
    req = urllib.request.Request(url, headers={"User-Agent": "LiteracyVoiceAgent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data and isinstance(data, list):
                    for item in data:
                        word = item.get("word", "").strip()
                        defs = item.get("defs", [])
                        if word and defs:
                            definition = defs[0]
                            if "\t" in definition:
                                definition = definition.split("\t", 1)[1]
                            return {"word": word, "definition": definition}
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 1:  fetch_next_exercise_data
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_next_exercise_data(level: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch the next exercise for a given learner level.

    Requirements met:
      1. Accepts the learner's level.
      2. Searches the local dataset.
      3. Selects an appropriate exercise (sequential rotation).
      4. Returns the exercise information to the agent.
      5. Handles invalid levels gracefully (defaults to 'beginner').
      6. Handles empty dataset gracefully (returns an error message).

    Also attempts a live Datamuse API call for vocabulary enrichment
    with a 3.5s timeout.  On failure, falls back to the local dataset
    and instructs the agent to announce the failure out loud (Step 4).
    """
    norm_level = _normalize_level(level)
    timestamp = _get_utc_timestamp()
    api_failed = False
    live_word_data = None

    # ── Requirement 5: Handle invalid levels gracefully ──
    level_was_invalid = (norm_level != level.lower().strip().replace(" ", "_")
                         and level.lower().strip().replace(" ", "_") not in VALID_LEVELS)

    # ── Step 2 / Live API: Try Datamuse for vocabulary topics ──
    req_topic = topic.lower().strip() if topic else None
    if req_topic == "vocabulary":
        try:
            logger.info(f"Live API fetch: level={norm_level}, topic=vocabulary")
            live_word_data = await asyncio.wait_for(
                asyncio.to_thread(_fetch_live_api_word, "vocabulary"),
                timeout=3.5,
            )
        except asyncio.TimeoutError:
            logger.warning("Datamuse API timed out (3.5s). Falling back to local dataset.")
            api_failed = True
        except Exception as exc:
            logger.warning(f"Datamuse API failed: {exc}. Falling back to local dataset.")
            api_failed = True

    # If live API returned data, build a live exercise
    if live_word_data and not api_failed:
        word = live_word_data["word"]
        definition = live_word_data["definition"]
        return {
            "status": "success",
            "exercise_id": f"LIVE_{word.upper().replace(' ', '_')}",
            "level": norm_level,
            "type": "english",
            "question": f"Vocabulary challenge: What word means '{definition}'?",
            "answer": word,
            "acceptable": [word],
            "data_source": "Datamuse Public Educational API (live)",
            "data_timestamp": timestamp,
            "notice": f"Live data retrieved from Datamuse API. Timestamp stored: {timestamp}.",
        }

    # ── Requirement 2 & 3: Search local dataset, select exercise ──
    pool = _get_exercises_for_level(norm_level)

    # Filter by topic if requested
    if req_topic:
        topic_map = {"vocabulary": "english", "phonics": "english", "reading": "english",
                     "math": "math", "math_literacy": "math", "english": "english"}
        mapped = topic_map.get(req_topic, req_topic)
        filtered = [ex for ex in pool if ex["type"] == mapped]
        if filtered:
            pool = filtered

    # ── Requirement 6: Handle empty dataset gracefully ──
    if not pool:
        logger.warning(f"No exercises found for level='{level}' (resolved: '{norm_level}').")
        return {
            "status": "error_no_exercises",
            "exercise_id": None,
            "level": norm_level,
            "type": None,
            "question": None,
            "answer": None,
            "data_source": "Local Dataset v2026.08 (hand-built)",
            "data_timestamp": timestamp,
            "notice": (
                "NOTICE TO ASSISTANT: No exercises were found for this level and topic. "
                "You MUST say out loud: 'I don't have any exercises for that level right now. "
                "Would you like to try a different level like beginner or grade 1?'"
            ),
        }

    # ── Requirement 3: Select next exercise (sequential rotation) ──
    counter_key = f"{norm_level}_{req_topic or 'all'}"
    idx = _EXERCISE_COUNTERS.get(counter_key, 0) % len(pool)
    _EXERCISE_COUNTERS[counter_key] = idx + 1
    selected = pool[idx]

    # ── Step 4: Out-loud failure notice if API was tried and failed ──
    if api_failed:
        notice = (
            "NOTICE TO ASSISTANT: The live online vocabulary API timed out or was unreachable. "
            "You MUST say out loud: 'I couldn't reach the live exercise server right now "
            "due to a network delay, so I've loaded a backup question from our offline curriculum.'"
        )
    elif level_was_invalid:
        notice = (
            f"NOTICE TO ASSISTANT: The user asked for level '{level}' which is not in the dataset. "
            f"Defaulted to '{norm_level}'. You MUST say out loud: "
            f"'I don't have exercises for level {level}, so I've picked a {norm_level} exercise for you.'"
        )
    else:
        notice = f"Exercise loaded from Local Literacy Dataset v2026.08. Timestamp stored: {timestamp}."

    # ── Requirement 4: Return exercise information ──
    return {
        "status": "success_offline_fallback" if api_failed else "success",
        "exercise_id": selected["id"],
        "level": selected["level"],
        "type": selected["type"],
        "question": selected["question"],
        "answer": selected["answer"],
        "acceptable": selected["acceptable"],
        "data_source": "Local Literacy Dataset v2026.08 (hand-built)",
        "data_timestamp": timestamp,
        "notice": notice,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 2:  score_spoken_answer_data
# ─────────────────────────────────────────────────────────────────────────────

def score_spoken_answer_data(
    exercise_id: Any,
    spoken_answer: str,
    expected_answer: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Scores a spoken answer against the expected answer for an exercise.

    Scoring method:
      - Exact or acceptable-list match → 100%
      - Otherwise: Levenshtein similarity (60%) + word overlap (40%)

    Also handles number-word equivalence (e.g. 'five' == '5')
    and unit suffixes (e.g. '315 kilometres' matches '315').

    Returns: score %, pass/fail, feedback, and UTC timestamp for DB storage.
    """
    timestamp = _get_utc_timestamp()
    clean_spoken = spoken_answer.lower().strip()

    # Resolve target and acceptable list from dataset + provided expected_answer
    target = (expected_answer or "").lower().strip()
    acceptable_list: list[str] = [target] if target else []

    # Look up exercise in dataset by id
    for ex in EXERCISES:
        if str(ex["id"]) == str(exercise_id):
            target = target or ex["answer"].lower().strip()
            acceptable_list = [a.lower().strip() for a in ex["acceptable"]]
            if ex["answer"].lower().strip() not in acceptable_list:
                acceptable_list.append(ex["answer"].lower().strip())
            if target and target not in acceptable_list:
                acceptable_list.append(target)
            break

    if not target:
        target = clean_spoken  # No reference — give full credit

    # Number-word equivalence (e.g. spoken "five" → matches "5")
    spoken_numeric = _NUM_WORDS.get(clean_spoken)
    if spoken_numeric and spoken_numeric in acceptable_list:
        clean_spoken = spoken_numeric

    # Strip unit suffixes for numeric answers (e.g. '315 kilometres' → '315')
    first_word = clean_spoken.split()[0] if clean_spoken.split() else clean_spoken
    if first_word in acceptable_list:
        clean_spoken = first_word

    # ── Score ──
    if clean_spoken in acceptable_list or clean_spoken == target:
        score = 100
        feedback = "Outstanding! Perfect answer!"
        passed = True
    else:
        # Edit-distance similarity
        dist = _levenshtein_distance(clean_spoken, target)
        max_len = max(len(clean_spoken), len(target), 1)
        similarity = max(0.0, 1.0 - dist / max_len)

        # Word-overlap ratio
        spoken_words = set(clean_spoken.split())
        target_words = set(target.split())
        overlap = len(spoken_words & target_words) / max(len(target_words), 1)

        combined = (similarity * 0.6) + (overlap * 0.4)
        score = int(round(combined * 100))

        if score >= 85:
            feedback = f"Excellent! Very close. The expected answer was '{target}'."
            passed = True
        elif score >= 65:
            feedback = f"Good effort! Your answer was close. The expected answer is '{target}'."
            passed = True
        elif score >= 40:
            feedback = f"Nice try! The expected answer is '{target}'. Let's practise more."
            passed = False
        else:
            feedback = f"Keep going! The correct answer is '{target}'. You'll get it next time!"
            passed = False

    return {
        "status": "success",
        "exercise_id": exercise_id,
        "spoken_answer": spoken_answer,
        "expected_answer": target,
        "score_percentage": score,
        "passed": passed,
        "feedback": feedback,
        "scored_at_timestamp": timestamp,
    }

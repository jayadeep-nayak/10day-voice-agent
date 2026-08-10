import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    UserInputTranscribedEvent,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")

import database  # noqa: E402
import exercises  # noqa: E402
from prompt import SYSTEM_PROMPT  # noqa: E402

logger = logging.getLogger("agent")

# Initialize SQLite database
database.initialize_db()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.current_caller_id = None

    @function_tool
    async def fetch_next_exercise(
        self,
        context: RunContext,
        level: Optional[str] = "beginner",
        topic: Optional[str] = None,
    ) -> str:
        """Fetch the next learning or literacy exercise based on the user's requested level.
        Use this tool whenever the user asks for a practice question, exercise, reading test, math exercise, or word practice.
        Do NOT guess or invent exercises yourself; always call this tool to fetch real exercise data.

        Args:
            level: The learner's level. Options: 'beginner', 'grade_1', 'grade_2', 'grade_3', 'grade_4', 'intermediate'. Defaults to 'beginner'.
            topic: Optional subject filter. Options: 'english', 'math', 'vocabulary', 'reading'. Defaults to None (any topic).
        """
        logger.info(f"Tool fetch_next_exercise called with level={level}, topic={topic}")
        try:
            res = await exercises.fetch_next_exercise_data(
                level=level or "beginner", topic=topic
            )
            logger.info(f"fetch_next_exercise_data result: {res}")

            if res.get("status") == "error_no_exercises":
                return f"System Notice: {res.get('notice', 'No exercises found.')}\n"

            output = (
                f"Exercise ID: {res['exercise_id']}\n"
                f"Level: {res['level']}\n"
                f"Type: {res['type']}\n"
                f"Question: {res['question']}\n"
                f"Answer: {res['answer']}\n"
                f"Data Source: {res['data_source']}\n"
                f"Data Timestamp: {res['data_timestamp']}\n"
            )
            if "notice" in res:
                output += f"System Notice: {res['notice']}\n"
            return output
        except Exception as e:
            logger.error(f"Error fetching next exercise: {e}")
            return (
                "FAILURE_NOTICE: Connection to exercise repository failed. "
                "You MUST announce out loud: 'I could not fetch an exercise right now due to a connection error. "
                "Let's try a quick one from memory: What is the opposite of hot?'"
            )

    @function_tool
    async def score_spoken_answer(
        self,
        context: RunContext,
        spoken_answer: str,
        exercise_id: Optional[str] = None,
        expected_answer: Optional[str] = None,
    ) -> str:
        """Evaluate and score a spoken answer provided by the user for a literacy exercise.
        Use this tool whenever the user attempts an exercise answer, reads a sentence aloud, or asks how well they did on an exercise.

        Args:
            spoken_answer: The user's exact spoken words or transcribed answer.
            exercise_id: The unique ID of the exercise being attempted (e.g., 'EX_BEG_101', 'EX_G1_201').
            expected_answer: The expected or correct phrase/answer, if available.
        """
        logger.info(
            f"Tool score_spoken_answer called with exercise_id={exercise_id}, "
            f"spoken_answer='{spoken_answer}', expected_answer='{expected_answer}'"
        )
        try:
            res = exercises.score_spoken_answer_data(
                exercise_id=exercise_id or "",
                spoken_answer=spoken_answer,
                expected_answer=expected_answer,
            )
            logger.info(f"score_spoken_answer_data result: {res}")
            return (
                f"Evaluation Result for Exercise {res['exercise_id']}:\n"
                f"Spoken Answer: '{res['spoken_answer']}'\n"
                f"Expected Answer: '{res['expected_answer']}'\n"
                f"Score: {res['score_percentage']}%\n"
                f"Passed: {res['passed']}\n"
                f"Feedback: {res['feedback']}\n"
                f"Evaluation Timestamp: {res['scored_at_timestamp']}\n"
            )
        except Exception as e:
            logger.error(f"Error scoring spoken answer: {e}")
            return (
                "FAILURE_NOTICE: Could not access scoring service. "
                "You MUST announce out loud: 'I had trouble evaluating your answer automatically due to a temporary error. "
                "However, you pronounced your answer very clearly! Great job practice speaking.'"
            )

    @function_tool
    async def lookup_caller(
        self,
        context: RunContext,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        """Use this tool to look up a caller's details from the database.
        You can look them up by their unique user ID or their name.

        Args:
            user_id: The unique ID of the caller (e.g. 'usr_1234abcd')
            name: The name of the caller (e.g. 'Ramesh')
        """
        logger.info(f"Tool lookup_caller called with user_id={user_id}, name={name}")

        uid = user_id or self.current_caller_id
        logger.info(
            f"Tool lookup_caller called with user_id={user_id}, name={name}, using uid={uid}"
        )

        caller = None
        if uid:
            caller = database.lookup_caller(uid)
        if not caller and name:
            caller = database.lookup_caller_by_name(name)

        if not caller:
            return f"No record found for caller with user_id='{user_id}' and name='{name}'."

        return (
            f"Found caller record: "
            f"user_id: {caller['user_id']}, "
            f"name: {caller['name']}, "
            f"language_preference: {caller['language_preference']}, "
            f"facts: {caller['facts']}, "
            f"last_interaction: {caller['last_interaction']}"
        )

    @function_tool
    async def save_caller_facts(
        self,
        context: RunContext,
        name: str,
        language_preference: Optional[str] = "English",
        user_id: Optional[str] = None,
        current_level: Optional[str] = None,
        topics_covered: Optional[str] = None,
        mistakes_made: Optional[str] = None,
        action_taken: Optional[str] = None,
    ) -> str:
        """Save the caller's name and what was discussed. Only call AFTER the caller verbally agrees.

        Args:
            name: The caller's name exactly as they said it (e.g. 'Ramesh', 'Jay')
            language_preference: Language they prefer (e.g. 'English', 'Hindi')
            user_id: Leave empty — filled automatically
            current_level: Their learning level (e.g. 'Grade 2', 'Beginner')
            topics_covered: The EXACT topic discussed (e.g. 'cotton farming', 'addition'). Use their exact words.
            mistakes_made: Mistakes they keep making
            action_taken: Action or solution discussed (e.g. 'spraying pesticide', 'daily reading')
        """
        uid = user_id or self.current_caller_id
        if not uid and context and hasattr(context, "session") and context.session.room_io:
            try:
                room = context.session.room_io.room
                if room and room.remote_participants:
                    p = next(iter(room.remote_participants.values()))
                    uid = p.identity
                    self.current_caller_id = uid
            except Exception as ex:
                logger.warning(f"Could not retrieve participant from room: {ex}")

        save_name = name or "User"
        save_lang = language_preference or "English"

        if not uid:
            logger.error("save_caller_facts: uid is still None — cannot save")
            return "Error: could not identify caller. Please try again."

        # Build facts dict — only save values actually provided by the caller
        facts: dict = {}
        if current_level:
            facts["current_level"] = current_level
        if topics_covered:
            facts["topics_covered"] = topics_covered
        if mistakes_made:
            facts["mistakes_made"] = mistakes_made
        if action_taken:
            facts["action_taken"] = action_taken

        logger.info(f"Saving caller: name={save_name}, uid={uid}, facts={facts}")

        try:
            database.save_caller(
                user_id=uid,
                name=save_name,
                language_preference=save_lang,
                facts=facts,
            )
            return f"Successfully saved profile for {save_name} (ID: {uid}). Facts: {facts}"
        except Exception as e:
            logger.error(f"Error saving caller facts: {e}")
            return f"Error saving caller facts: {e!s}"


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="Abhinav",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for Devanagari script characters (native Hindi)
        has_devanagari = any(0x0900 <= ord(c) <= 0x097F for c in transcript)

        # Check for common Hinglish/Hindi romanized keywords
        hindi_keywords = {
            "kya",
            "hai",
            "aur",
            "main",
            "haan",
            "nahin",
            "aap",
            "namaste",
            "shukriya",
            "mein",
            "ke",
            "ki",
            "se",
            "ko",
            "ka",
            "jo",
            "toh",
            "bhi",
            "ho",
            "kar",
            "raha",
            "rahi",
            "rha",
            "rhi",
            "mujhe",
            "mera",
            "meri",
            "hum",
            "tum",
            "apna",
            "apni",
            "karke",
            "karo",
            "karna",
            "tha",
            "thi",
            "the",
            "ab",
            "kab",
            "tab",
            "sab",
            "hindi",
        }
        words = set(transcript.split())
        has_hindi_words = not words.isdisjoint(hindi_keywords)

        if has_devanagari or has_hindi_words:
            logger.info(
                f"Detected Hindi/Hinglish speech: '{ev.transcript}'. Switching TTS locale to hi-IN."
            )
            session.tts.update_options(locale="hi-IN")
        else:
            logger.info(
                f"Detected English speech: '{ev.transcript}'. Switching TTS locale to en-IN."
            )
            session.tts.update_options(locale="en-IN")

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    assistant = Assistant()
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Look up caller information and greet them by name
    logger.info("Looking up caller details to prepare welcoming greeting...")
    participant = None
    for _ in range(300):
        if ctx.room.remote_participants:
            participant = next(iter(ctx.room.remote_participants.values()))
            break
        await asyncio.sleep(0.1)

    caller_name = "user"
    caller_id = None
    caller_record = None

    if participant:
        caller_id = participant.identity
        caller_name = participant.name or "user"
        logger.info(f"Caller identified - user_id: {caller_id}, name: {caller_name}")
        assistant.current_caller_id = caller_id

        # Search the database by participant identity (persistent userId from browser)
        caller_record = database.lookup_caller(caller_id)
        if not caller_record and caller_name and caller_name != "user":
            caller_record = database.lookup_caller_by_name(caller_name)
    else:
        logger.warning("No remote participant detected in the room.")

    greeting_message = ""
    custom_instructions = SYSTEM_PROMPT

    if caller_record:
        # Returning caller
        db_name = caller_record["name"]
        facts = caller_record["facts"]
        topics = facts.get("topics_covered") or facts.get("topic") or facts.get("topics") or "your topic"
        raw_action = facts.get("action_taken") or facts.get("action") or facts.get("mistakes_made") or "spraying"
        level = facts.get("current_level", "Unknown")
        pref_lang = caller_record.get("language_preference", "English")
        mistakes = facts.get("mistakes_made", "None")

        logger.info(f"Loaded returning caller facts for {db_name}: {facts}")

        # Formulate exact returning greeting requested: "Namaste Ramesh, last time we spoke about your cotton. Did the spraying help?"
        if raw_action and raw_action != "None" and raw_action != "spraying":
            action_phrase = (
                raw_action
                if raw_action.lower().startswith(("the ", "your ", "that ", "a ", "an "))
                else f"the {raw_action}"
            )
        else:
            action_phrase = "the spraying"

        greeting_message = f"Namaste {db_name}, last time we spoke about {topics}. Did {action_phrase} help?"

        custom_instructions += f"""

CURRENT CALLER CONTEXT (RETURNING):
- User ID: {caller_id}
- Name: {db_name}
- Preferred Language: {pref_lang}
- Current Level: {level}
- Topics Covered: {topics}
- Mistakes they keep making: {mistakes}

GREETING: You have already greeted the caller with: "{greeting_message}"
Welcome them back and resume the lesson.
"""
    else:
        # New caller
        if caller_name and caller_name != "user":
            greeting_message = f"Hi {caller_name}! Welcome! How can I help you learn today? Feel free to speak in English or Hindi."
            custom_instructions += f"""

CURRENT CALLER CONTEXT (NEW WITH NAME):
- User ID: {caller_id or "Unknown"}
- Name: {caller_name}
- Current Level: New Learner
- Goal: Assess their level and start their first lesson.
GREETING: You have already greeted the caller with: "{greeting_message}"
"""
        else:
            greeting_message = "Hi! How can I help you today? Feel free to speak with me in English or Hindi! May I know your name?"
            custom_instructions += f"""

CURRENT CALLER CONTEXT (NEW UNKNOWN):
- User ID: {caller_id or "Unknown"}
- Name: Unknown
- Current Level: New Learner
- Goal: Ask for their name first and start their first lesson.
GREETING: You have already greeted the caller with: "{greeting_message}"
"""

    # Set caller context instructions
    assistant.update_instructions(custom_instructions)

    # Deliver greeting speech
    session.say(greeting_message, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)

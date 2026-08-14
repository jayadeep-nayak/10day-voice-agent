import asyncio
import logging
import uuid
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
from prompt import MATH_SPECIALIST_PROMPT, OUTBOUND_SYSTEM_PROMPT, SYSTEM_PROMPT  # noqa: E402

logger = logging.getLogger("agent")

# Initialize SQLite database
database.initialize_db()


# ── Outbound call greeting (exact wording required for trust & compliance) ─────
OUTBOUND_GREETING = (
    "Hi, this is your Daily Literacy Coach calling for your scheduled reading practice. "
    "If you want to stop these calls at any time, just say 'cancel my calls'."
)


class Assistant(Agent):
    def __init__(self, is_outbound_call: bool = False) -> None:
        prompt = OUTBOUND_SYSTEM_PROMPT if is_outbound_call else SYSTEM_PROMPT
        super().__init__(instructions=prompt)
        self.current_caller_id = None
        self.is_outbound_call = is_outbound_call
        self.call_id = None
        self.exercises_attempted = 0
        self.exercises_passed = 0

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
        logger.info(
            f"Tool fetch_next_exercise called with level={level}, topic={topic}"
        )
        self.exercises_attempted += 1
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
            if res.get("passed"):
                self.exercises_passed += 1
                logger.info(f"Exercise passed! Total passed: {self.exercises_passed}")
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
    async def cancel_daily_calls(
        self,
        context: RunContext,
    ) -> str:
        """Cancel the user's daily literacy practice call subscription.
        Use this tool ONLY when the user explicitly asks to stop receiving calls,
        e.g. they say 'cancel my calls', 'stop calling me', 'unsubscribe', etc.
        After calling this tool, end the conversation gracefully.
        """
        caller_id = self.current_caller_id or "unknown"
        logger.info(f"cancel_daily_calls requested by caller {caller_id}")

        # Log the cancellation (in production, this would update a scheduling DB)
        logger.info(
            f"CANCELLATION RECORDED: caller_id={caller_id} has opted out of daily calls."
        )

        # Disconnect the SIP call after a short delay to let the goodbye play
        if context and hasattr(context, "session"):
            session = context.session
            if hasattr(session, "room_io") and session.room_io:
                room = session.room_io.room
                if room and room.remote_participants:

                    async def _disconnect_after_goodbye():
                        await asyncio.sleep(6)
                        for p in list(room.remote_participants.values()):
                            if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                                try:
                                    await room.local_participant.publish_data(
                                        "BYE", topic="lk-sip-hangup"
                                    )
                                except Exception as ex:
                                    logger.warning(f"Could not send SIP hangup: {ex}")

                    asyncio.create_task(_disconnect_after_goodbye())

        return (
            f"Cancellation confirmed for caller {caller_id}. "
            "The user has been unsubscribed from daily practice calls. "
            "Please say goodbye warmly and end the conversation."
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
        if (
            not uid
            and context
            and hasattr(context, "session")
            and context.session.room_io
        ):
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

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        who_needs_help: str,
        what_happened: str,
        agent_checks: str,
        urgency: Optional[str] = "medium",
        language_preference: Optional[str] = "English",
        preferred_followup: Optional[str] = "call-back",
    ) -> str:
        """Create an escalation request to connect the learner with a human teacher.
        Only call this tool AFTER the caller gives verbal permission to store their information in the database.
        Do NOT call this tool if the caller says no or declines.
        NEVER include passwords, OTPs, PINs, account numbers, or other private information.

        Args:
            who_needs_help: The caller's name (e.g. 'Ramesh', 'Jay').
            what_happened: A short summary of what happened — why help is needed (e.g. 'Learner is frustrated with grade 2 reading exercises and feeling overwhelmed').
            agent_checks: What the agent already tried before escalating (e.g. 'Offered encouragement, simplified the exercise, asked if they wanted to try a different topic').
            urgency: How urgent the request is. Options: 'high' (learner is very upset/crying) or 'medium' (learner asked for teacher). Defaults to 'medium'.
            language_preference: The caller's preferred language (e.g. 'English', 'Hindi'). Defaults to 'English'.
            preferred_followup: How the caller wants to be contacted. Options: 'call-back', 'text', 'email'. Defaults to 'call-back'.
        """
        caller_id = self.current_caller_id or "unknown"
        logger.info(
            f"Tool create_escalation called: who={who_needs_help}, "
            f"urgency={urgency}, caller_id={caller_id}"
        )

        try:
            reference_id = database.create_escalation(
                who_needs_help=who_needs_help,
                caller_id=caller_id,
                what_happened=what_happened,
                agent_checks=agent_checks or "None",
                urgency=urgency or "medium",
                language_preference=language_preference or "English",
                preferred_followup=preferred_followup or "call-back",
            )
            logger.info(f"Escalation created successfully: {reference_id}")
            return (
                f"Escalation request created successfully.\n"
                f"Reference ID: {reference_id}\n"
                f"Who needs help: {who_needs_help}\n"
                f"Urgency: {urgency}\n"
                f"Status: Open — a teacher will review this request.\n"
                f"IMPORTANT: Tell the caller their reference number is {reference_id} "
                f"and that a teacher will reach out within 24 hours."
            )
        except Exception as e:
            logger.error(f"Error creating escalation: {e}")
            return (
                "FAILURE_NOTICE: Could not create the escalation request due to a system error. "
                "You MUST announce out loud: 'I'm sorry, I had trouble saving your request due to a "
                "temporary error. Please try calling back and asking for a teacher again, "
                "and we will make sure someone helps you.'"
            )

    @function_tool
    async def handoff_to_math_specialist(
        self,
        context: RunContext,
        user_request: str,
    ) -> Agent:
        """Hand off the conversation to Zenith, the Maths Practice Specialist.
        Use this tool AUTOMATICALLY when the user's request is clearly focused on in-depth
        mathematics practice such as:
        - multiplication tables, times tables, division drills
        - fractions, decimals, percentages
        - multi-step word problems or algebra
        - geometry or number patterns
        - any session dedicated to maths exercises
        Do NOT use for simple one-off math questions (e.g. 'what is 2+1?') — handle those yourself.
        Do NOT use for general literacy, reading, vocabulary, or English exercises.
        ALWAYS say: 'Let me connect you to Zenith, our Maths Practice Specialist — they'll take great care of you!'
        BEFORE calling this tool.

        Args:
            user_request: The EXACT math problem or calculation asked by the user (e.g., 'What is 22 times 96?', '125 plus 340'). You MUST include the exact numbers and operations. Do NOT summarize as 'math question' or 'math practice'!
        """
        logger.info(
            f"Handing off to MathSpecialist (Zenith). user_request={user_request!r}, "
            f"caller_id={self.current_caller_id}"
        )
        specialist = MathSpecialist(
            caller_id=self.current_caller_id,
            user_request=user_request,
        )
        return specialist


import re

def try_calculate_math_answer(text: str) -> Optional[str]:
    """Helper to parse and evaluate basic arithmetic expressions from spoken text."""
    if not text:
        return None
    t = text.lower()
    t = re.sub(r'\btimes\b|\bmultiplied by\b|\bx\b', '*', t)
    t = re.sub(r'\bplus\b|\badded to\b', '+', t)
    t = re.sub(r'\bminus\b|\bsubtracted by\b|\btake away\b', '-', t)
    t = re.sub(r'\bdivided by\b|\bover\b', '/', t)
    match = re.search(r'(\d+(?:\.\d+)?\s*[\+\-\*/]\s*\d+(?:\.\d+)?)', t)
    if match:
        try:
            res = eval(match.group(1))
            if isinstance(res, float) and res.is_integer():
                res = int(res)
            return str(res)
        except Exception:
            pass
    return None


class MathSpecialist(Agent):
    """Zenith — a focused Maths Practice Specialist agent.

    This agent only handles mathematics topics. It is activated via a handoff
    from the main Assistant (Nova) when the user asks for dedicated maths practice.
    """

    def __init__(self, caller_id: Optional[str] = None, user_request: str = "") -> None:
        self.user_request = user_request
        self.current_caller_id = caller_id
        self.exercises_attempted = 0
        self.exercises_passed = 0
        self.calculated_answer = try_calculate_math_answer(user_request)

        context_suffix = ""
        if user_request:
            answer_info = f" The calculated numerical answer is {self.calculated_answer}." if self.calculated_answer else ""
            context_suffix = (
                f"\n\nUSER CONTEXT (from Nova handoff):\n"
                f"The user asked Nova this exact math question: '{user_request}'.{answer_info}\n"
                f"You MUST immediately state the numerical answer clearly out loud and explain the calculation step by step. "
                f"Do NOT ask the user any quiz or practice questions afterwards."
            )
        super().__init__(instructions=MATH_SPECIALIST_PROMPT + context_suffix)

    async def on_enter(self) -> None:
        """Automatically called when Zenith takes over after handoff."""
        logger.info(
            f"[Zenith] Entered session after handoff. user_request={self.user_request!r}, "
            f"calculated_answer={self.calculated_answer!r}"
        )
        try:
            if hasattr(self.session, "room_io") and self.session.room_io:
                await self.session.room_io.room.local_participant.set_attributes({
                    "active_agent": "Zenith",
                    "agent_name": "Zenith",
                })
        except Exception as e:
            logger.warning(f"[Zenith] Could not set attributes: {e}")

        # Trigger Zenith's immediate greeting and explicit answer to the handoff question
        if self.user_request:
            if self.calculated_answer:
                intro_prompt = (
                    f"Say out loud: 'Hi! I'm Zenith, your Maths Specialist! {self.user_request} equals {self.calculated_answer}.' "
                    f"Then explain how to solve it in one simple sentence. Do not ask any quiz questions afterwards."
                )
            else:
                intro_prompt = (
                    f"Introduce yourself warmly as Zenith, the Maths Specialist, and immediately solve, calculate, and state the step-by-step explanation and exact final answer for: '{self.user_request}'."
                )
        else:
            intro_prompt = "Introduce yourself as Zenith, the Maths Specialist, and ask what maths question you can solve for them today."

        try:
            self.session.generate_reply(user_input=intro_prompt)
        except Exception as e:
            logger.error(f"[Zenith] Could not generate reply on enter: {e}")

    @function_tool
    async def fetch_next_exercise(
        self,
        context: RunContext,
        level: Optional[str] = "beginner",
        topic: Optional[str] = "math",
    ) -> str:
        """Fetch the next mathematics exercise.
        Always call this with topic='math'. Call at session start and after every scored answer.

        Args:
            level: The learner's level: 'beginner', 'grade_1', 'grade_2', 'grade_3', 'grade_4', 'intermediate'.
            topic: Always 'math' for this specialist.
        """
        logger.info(
            f"[Zenith] fetch_next_exercise called: level={level}, topic={topic}"
        )
        self.exercises_attempted += 1
        try:
            res = await exercises.fetch_next_exercise_data(
                level=level or "beginner", topic="math"
            )
            logger.info(f"[Zenith] fetch_next_exercise_data result: {res}")
            if res.get("status") == "error_no_exercises":
                return (
                    f"System Notice: {res.get('notice', 'No math exercises found.')}\n"
                )
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
            logger.error(f"[Zenith] Error fetching exercise: {e}")
            return (
                "FAILURE_NOTICE: Could not fetch a maths exercise right now. "
                "Please say out loud: 'I couldn't load a question right now — let me give you a quick one from memory: What is 7 times 8?'"
            )

    @function_tool
    async def score_spoken_answer(
        self,
        context: RunContext,
        spoken_answer: str,
        exercise_id: Optional[str] = None,
        expected_answer: Optional[str] = None,
    ) -> str:
        """Score the user's spoken answer for a maths exercise.

        Args:
            spoken_answer: The user's exact spoken words or transcribed answer.
            exercise_id: The unique ID of the exercise (e.g. 'EX_BEG_107').
            expected_answer: The expected correct answer, if available.
        """
        logger.info(
            f"[Zenith] score_spoken_answer called: exercise_id={exercise_id}, "
            f"spoken_answer='{spoken_answer}'"
        )
        try:
            res = exercises.score_spoken_answer_data(
                exercise_id=exercise_id or "",
                spoken_answer=spoken_answer,
                expected_answer=expected_answer,
            )
            if res.get("passed"):
                self.exercises_passed += 1
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
            logger.error(f"[Zenith] Error scoring answer: {e}")
            return (
                "FAILURE_NOTICE: Could not evaluate the answer automatically. "
                "Say: 'I had a small technical hiccup evaluating that — but keep going, you're doing great!'"
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
        """Save the caller's maths session facts. Only call AFTER verbal consent.

        Args:
            name: The caller's name.
            language_preference: Language preference (e.g. 'English', 'Hindi').
            user_id: Leave empty — filled automatically.
            current_level: Their maths level (e.g. 'Grade 2', 'Intermediate').
            topics_covered: Maths topics practiced (e.g. 'multiplication tables, fractions').
            mistakes_made: Common errors noted during session.
            action_taken: What was worked on (e.g. 'times tables drilling').
        """
        uid = user_id or self.current_caller_id
        save_name = name or "User"
        save_lang = language_preference or "English"
        if not uid:
            return "Error: could not identify caller. Please try again."
        facts: dict = {}
        if current_level:
            facts["current_level"] = current_level
        if topics_covered:
            facts["topics_covered"] = topics_covered
        if mistakes_made:
            facts["mistakes_made"] = mistakes_made
        if action_taken:
            facts["action_taken"] = action_taken
        logger.info(
            f"[Zenith] Saving caller: name={save_name}, uid={uid}, facts={facts}"
        )
        try:
            database.save_caller(
                user_id=uid,
                name=save_name,
                language_preference=save_lang,
                facts=facts,
            )
            return f"Successfully saved maths session for {save_name} (ID: {uid}). Facts: {facts}"
        except Exception as e:
            logger.error(f"[Zenith] Error saving caller facts: {e}")
            return f"Error saving session facts: {e!s}"


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

    @session.on("user_started_speaking")
    def on_user_started_speaking():
        logger.info("🎙️ User started speaking detected!")

    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        logger.info("🔇 User stopped speaking detected!")

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

    # ── Detect SIP (phone) participants for outbound call handling ─────────
    # Connect first so we can inspect incoming participants
    await ctx.connect()

    # Wait for a remote participant to join
    logger.info("Waiting for remote participant to join the room...")
    participant = None
    for _ in range(300):
        if ctx.room.remote_participants:
            participant = next(iter(ctx.room.remote_participants.values()))
            break
        await asyncio.sleep(0.1)

    # Determine if this is a SIP (outbound phone) call
    is_sip_call = (
        participant is not None
        and participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
    )
    logger.info(f"Participant detected — SIP call: {is_sip_call}")

    # Start the session with the appropriate prompt
    assistant = Assistant(is_outbound_call=is_sip_call)

    # Generate a unique call ID for tracking
    call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
    assistant.call_id = call_id

    # Record call outcome when session ends
    @ctx.room.on("disconnected")
    def on_room_disconnected():
        outcome = "successful" if assistant.exercises_passed >= 1 else "failed"
        logger.info(
            f"Call {call_id} ended — outcome={outcome}, "
            f"attempted={assistant.exercises_attempted}, passed={assistant.exercises_passed}"
        )
        database.record_call_end(
            call_id=call_id,
            outcome=outcome,
            exercises_attempted=assistant.exercises_attempted,
            exercises_passed=assistant.exercises_passed,
        )

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    None
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    try:
        await ctx.room.local_participant.set_attributes({
            "active_agent": "Nova",
            "agent_name": "Nova",
        })
    except Exception as e:
        logger.warning(f"Could not set initial participant attributes: {e}")
    caller_name = "user"
    caller_id = None
    caller_record = None

    if participant:
        caller_id = participant.identity
        caller_name = participant.name or "user"
        logger.info(f"Caller identified - user_id: {caller_id}, name: {caller_name}")
        assistant.current_caller_id = caller_id

        # Search the database by participant identity
        caller_record = database.lookup_caller(caller_id)
        if not caller_record and caller_name and caller_name != "user":
            caller_record = database.lookup_caller_by_name(caller_name)

        # Outbound SIP fallback for testing/demo
        if not caller_record and is_sip_call:
            logger.info(
                "Outbound SIP call: No direct record match. Falling back to most recent caller."
            )
            caller_record = database.lookup_most_recent_caller()
    else:
        logger.warning("No remote participant detected in the room.")

    # Record call start now that caller_id and caller_name are known
    call_type = "sip" if is_sip_call else "web"
    display_name = "unknown"
    if caller_record:
        display_name = caller_record["name"]
    elif caller_name and caller_name != "user":
        display_name = caller_name
    elif caller_id:
        display_name = caller_id

    database.record_call_start(
        call_id=call_id,
        caller_id=caller_id or "unknown",
        caller_name=display_name,
        call_type=call_type,
    )

    # ── Branch: Outbound SIP call vs. Web/inbound call ────────────────────
    if is_sip_call:
        # ━━━━━━━━━━━ OUTBOUND CALL PATH ━━━━━━━━━━━
        logger.info("Outbound SIP call detected — using Daily Literacy Coach greeting.")

        custom_instructions = OUTBOUND_SYSTEM_PROMPT
        greeting_speech = OUTBOUND_GREETING

        if caller_record:
            db_name = caller_record["name"]
            facts = caller_record["facts"]
            level = facts.get("current_level", "Unknown")
            topics = (
                facts.get("topics_covered")
                or facts.get("topic")
                or facts.get("topics")
                or "general practice"
            )
            raw_action = (
                facts.get("action_taken")
                or facts.get("action")
                or facts.get("mistakes_made")
                or "practice"
            )
            pref_lang = caller_record.get("language_preference", "English")

            if raw_action and raw_action != "None" and raw_action != "spraying":
                action_phrase = (
                    raw_action
                    if raw_action.lower().startswith(
                        ("the ", "your ", "that ", "a ", "an ")
                    )
                    else f"the {raw_action}"
                )
            else:
                action_phrase = "the practice"

            # Personalization suffix for the greeting
            personalization = f" Namaste {db_name}, last time we spoke about {topics}. Did {action_phrase} help?"
            greeting_speech = OUTBOUND_GREETING + personalization

            custom_instructions += f"""

RETURNING CALLER CONTEXT:
- User ID: {caller_id}
- Name: {db_name}
- Preferred Language: {pref_lang}
- Current Level: {level}
- Topics Previously Covered: {topics}

GREETING: The system has already spoken the outbound greeting: "{greeting_speech}"
Wait for the user's response to this greeting before starting the next exercise.
"""
        else:
            custom_instructions += f"""

NEW CALLER CONTEXT:
- User ID: {caller_id or "Unknown"}
- Name: Unknown (phone caller)
- Current Level: New Learner

GREETING: The system has already spoken the outbound greeting: "{greeting_speech}"
After the user responds, ask for their name and start a beginner-level exercise.
"""

        assistant.update_instructions(custom_instructions)

        # Deliver the greeting (exact required 2 sentences first, optionally followed by returning user prompt)
        session.say(greeting_speech, allow_interruptions=True)

    else:
        # ━━━━━━━━━━━ WEB / INBOUND CALL PATH (original logic) ━━━━━━━━━━━
        greeting_message = ""
        custom_instructions = SYSTEM_PROMPT

        if caller_record:
            # Returning caller
            db_name = caller_record["name"]
            facts = caller_record["facts"]
            topics = (
                facts.get("topics_covered")
                or facts.get("topic")
                or facts.get("topics")
                or "your topic"
            )
            raw_action = (
                facts.get("action_taken")
                or facts.get("action")
                or facts.get("mistakes_made")
                or "spraying"
            )
            level = facts.get("current_level", "Unknown")
            pref_lang = caller_record.get("language_preference", "English")
            mistakes = facts.get("mistakes_made", "None")

            logger.info(f"Loaded returning caller facts for {db_name}: {facts}")

            if raw_action and raw_action != "None" and raw_action != "spraying":
                action_phrase = (
                    raw_action
                    if raw_action.lower().startswith(
                        ("the ", "your ", "that ", "a ", "an ")
                    )
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

"""
make_outbound_call.py — Trigger an outbound SIP call to Linphone via LiveKit SIP.

Usage:
    uv run python src/make_outbound_call.py
    uv run python src/make_outbound_call.py --sip-uri "sip:username@sip.linphone.org"
    uv run python src/make_outbound_call.py --sip-uri "sip:username@sip.linphone.org" --room "daily-practice-room"

The script:
  1. Loads LiveKit credentials from .env.local
  2. Creates a LiveKit room
  3. Dispatches the agent into the room
  4. Calls CreateSIPParticipant to dial the Linphone SIP URI
  5. When you answer in Linphone, you're connected to the agent

Prerequisites:
  - A free Linphone account (https://subscribe.linphone.org/)
  - Linphone app installed and signed in (desktop or mobile)
  - A configured SIP Outbound Trunk in LiveKit Cloud pointing to sip.linphone.org
  - LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env.local
  - SIP_OUTBOUND_TRUNK_ID in .env.local (from LiveKit Cloud dashboard)
  - LINPHONE_SIP_URI in .env.local (e.g. sip:username@sip.linphone.org)
"""

import argparse
import asyncio
import logging
import os
import sys
import uuid

from dotenv import load_dotenv

# Load environment from the backend .env.local
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

from livekit import api  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("outbound-call")


async def make_call(sip_uri: str, room_name: str) -> None:
    """Initiate an outbound SIP call to Linphone and connect it to a LiveKit room."""

    # ── Validate environment ──────────────────────────────────────────────
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

    missing = []
    if not livekit_url:
        missing.append("LIVEKIT_URL")
    if not api_key:
        missing.append("LIVEKIT_API_KEY")
    if not api_secret:
        missing.append("LIVEKIT_API_SECRET")
    if not trunk_id:
        missing.append("SIP_OUTBOUND_TRUNK_ID")

    if missing:
        logger.error(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Add them to backend/.env.local"
        )
        sys.exit(1)

    # ── Initialize LiveKit API client ─────────────────────────────────────
    lk = api.LiveKitAPI(
        url=livekit_url,
        api_key=api_key,
        api_secret=api_secret,
    )

    try:
        # ── Step 1: Create the room ───────────────────────────────────────
        logger.info(f"Creating room: {room_name}")
        await lk.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=300,  # 5 min timeout if no one joins
            )
        )
        logger.info(f"Room '{room_name}' is ready.")

        # ── Step 2: Dispatch the agent into the room ──────────────────────
        logger.info("Dispatching agent 'my-agent' into the room...")
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="my-agent",
                room=room_name,
            )
        )
        logger.info("Agent dispatched successfully.")

        # ── Step 3: Dial the Linphone SIP URI ─────────────────────────────
        # Extract the user part from the SIP URI if it is a full URI
        sip_user = sip_uri
        if sip_user.startswith("sip:"):
            sip_user = sip_user[4:]
        if "@" in sip_user:
            sip_user = sip_user.split("@")[0]

        logger.info(f"Dialing SIP URI: {sip_uri} (extracted user: {sip_user})")
        sip_participant = await lk.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=sip_user,
                room_name=room_name,
                participant_identity=f"sip-caller-{uuid.uuid4().hex[:6]}",
                participant_name="Linphone Caller",
            )
        )
        logger.info(
            f"Call initiated! SIP Participant ID: {sip_participant.participant_id}\n"
            f"  SIP Call ID: {sip_participant.sip_call_id}\n"
            f"  Room: {room_name}\n"
            f"  Destination: {sip_uri}\n"
            f"  Status: Ringing — answer the call in your Linphone app..."
        )

    except Exception as e:
        logger.error(f"Failed to initiate outbound call: {e}")
        sys.exit(1)
    finally:
        await lk.aclose()


def main():
    parser = argparse.ArgumentParser(
        description="Trigger an outbound Daily Literacy Practice call to Linphone via LiveKit SIP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python src/make_outbound_call.py
  uv run python src/make_outbound_call.py --sip-uri "sip:username@sip.linphone.org"
  uv run python src/make_outbound_call.py --sip-uri "sip:username@sip.linphone.org" --room "practice-42"
        """,
    )
    parser.add_argument(
        "--sip-uri",
        default=None,
        help='Destination SIP URI (e.g. "sip:username@sip.linphone.org"). '
             "Falls back to LINPHONE_SIP_URI env var if not provided.",
    )
    parser.add_argument(
        "--room",
        default=None,
        help="LiveKit room name (auto-generated if not provided)",
    )

    args = parser.parse_args()

    # Resolve SIP URI from arg or env
    sip_uri = args.sip_uri or os.getenv("LINPHONE_SIP_URI")
    if not sip_uri:
        logger.error(
            "No SIP URI provided. Use --sip-uri or set LINPHONE_SIP_URI in .env.local\n"
            '  Example: --sip-uri "sip:username@sip.linphone.org"'
        )
        sys.exit(1)

    # Auto-generate a unique room name if none provided
    room_name = args.room or f"daily-practice-{uuid.uuid4().hex[:8]}"

    logger.info("=" * 60)
    logger.info("  Daily Literacy Practice — Outbound Call (Linphone)")
    logger.info("=" * 60)
    logger.info(f"  SIP URI      : {sip_uri}")
    logger.info(f"  Room Name    : {room_name}")
    logger.info("=" * 60)

    asyncio.run(make_call(sip_uri, room_name))


if __name__ == "__main__":
    main()

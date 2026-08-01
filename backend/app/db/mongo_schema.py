"""
Module 4.2 - MongoDB schema for polymorphic conversational/multimodal data
(Chat Agent conversation logs, future Vision Agent image metadata).

HONEST STATUS: NOT tested against a live MongoDB instance in this build
environment (no internet here to install/run MongoDB). This is a
documented, carefully-designed schema using pymongo's API correctly, but
you will be the first to run it against a real database. See
docs/SETUP.md for local MongoDB setup steps.

WHY MONGODB HERE (vs adding these fields to Postgres): conversations have
variable structure (a Chat Agent exchange might have 3 turns or 30; a
future Vision Agent entry has image metadata a text conversation doesn't).
Forcing that into fixed relational columns would mean either a lot of
NULL columns or constant schema migrations -- a document store fits this
data's actual shape better. This matches the proposal's stated reasoning
(Chapter 4.5: "MongoDB for polymorphic conversational and multimodal data").

Example document shape (not enforced by MongoDB itself -- validation
happens in application code before insert, shown in validate_conversation_doc below):

{
    "_id": ObjectId(...),
    "encounter_id": 123,           // links back to Postgres encounters.encounter_id
    "conversation_type": "chat",   // "chat" | "vision_analysis" (future)
    "turns": [
        {"role": "user", "text": "My child has a stiff neck", "timestamp": "..."},
        {"role": "assistant", "text": "...", "timestamp": "..."}
    ],
    "created_at": "2026-07-26T12:00:00Z"
}
"""
from datetime import datetime, timezone


REQUIRED_FIELDS = {"encounter_id", "conversation_type", "turns", "created_at"}
VALID_CONVERSATION_TYPES = {"chat", "vision_analysis"}


def build_conversation_doc(encounter_id: int, conversation_type: str, turns: list[dict]) -> dict:
    """
    Builds a conversation document ready for insertion into MongoDB's
    'conversations' collection. Validates shape before returning, since
    MongoDB itself won't enforce this for us (that's the tradeoff of a
    document store vs relational -- validation moves to application code).
    """
    if conversation_type not in VALID_CONVERSATION_TYPES:
        raise ValueError(f"conversation_type must be one of {VALID_CONVERSATION_TYPES}")

    for turn in turns:
        if "role" not in turn or "text" not in turn:
            raise ValueError(f"Each turn needs 'role' and 'text': got {turn}")

    return {
        "encounter_id": encounter_id,
        "conversation_type": conversation_type,
        "turns": turns,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def validate_conversation_doc(doc: dict) -> bool:
    return REQUIRED_FIELDS.issubset(doc.keys())


# --- Real usage once pymongo + a running MongoDB instance are available ---
# from pymongo import MongoClient
# client = MongoClient("mongodb://localhost:27017/")
# db = client["hans_triage"]
# db.conversations.insert_one(build_conversation_doc(123, "chat", turns))


if __name__ == "__main__":
    doc = build_conversation_doc(
        encounter_id=123,
        conversation_type="chat",
        turns=[
            {"role": "user", "text": "My child has a stiff neck and fever",
             "timestamp": datetime.now(timezone.utc).isoformat()},
            {"role": "assistant", "text": "How long has the fever been present?",
             "timestamp": datetime.now(timezone.utc).isoformat()},
        ],
    )
    print("Built conversation document:")
    print(doc)
    print(f"\nValidates: {validate_conversation_doc(doc)}")

    try:
        build_conversation_doc(123, "invalid_type", [])
    except ValueError as e:
        print(f"\nCorrectly rejected invalid type: {e}")

"""
Chat Agent (STUB) - Chapter 4.5/1.4 of proposal: conversational intake
agent, designed to use the Claude API.

HONEST STATUS: this build environment has no internet access and no API
key, so this cannot be exercised here. What's implemented is the real
interface/contract this agent will use -- you'll supply your own Anthropic
API key when running locally (see docs/SETUP.md for exactly where).

Once you have a key, replace the body of `chat_agent()` with an actual
call to the Anthropic API (example shown in the commented-out block below).
"""
import os


def chat_agent(message: str | None) -> dict:
    """
    Takes a free-text patient/caregiver message, returns a conversational
    response. Currently a stub -- see module docstring.
    """
    if message is None:
        return {"status": "STUB -- no message provided", "response": None}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "status": "STUB -- ANTHROPIC_API_KEY not set, cannot call real API",
            "response": (
                "[This would be a conversational reply from the Claude API "
                "once you set ANTHROPIC_API_KEY locally -- see docs/SETUP.md]"
            ),
        }

    # --- Real implementation, once a key is available locally ---
    # import anthropic
    # client = anthropic.Anthropic(api_key=api_key)
    # response = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=500,
    #     messages=[{"role": "user", "content": message}],
    # )
    # return {"status": "ok", "response": response.content[0].text}

    return {"status": "STUB -- real API call not yet wired up", "response": None}

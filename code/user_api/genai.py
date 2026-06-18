import json
import os

from ollama import Client

OLLAMA_HOST = "https://ollama.com"
OLLAMA_MODEL = "gpt-oss:20b"

QUALITY_VALUES = {"low", "normal", "high"}
PRIORITY_VALUES = {"low", "medium", "high", "urgent"}
DEFAULT_ASSESSMENT = {"quality": "normal", "priority": "medium"}

SYSTEM_PROMPT = (
    "You assess citizen city-problem reports. Respond with a JSON object containing "
    "exactly two keys, 'quality' and 'priority'.\n"
    "'quality' measures how complete, descriptive and accurate/helpful the report "
    "information is. It must be one of: low, normal, high.\n"
    "'priority' estimates whether efforts to resolve the issue should be expedited "
    "(based on safety risk and urgency). It must be one of: low, medium, high, urgent.\n"
    "Return only the JSON object, with no extra text."
)


def assess_report(title, description, category_name) -> dict:
    """Ask the LLM to rate a report's quality and priority.

    Args:
        title, description, category_name: Report content sent to the model.

    Returns:
        Dict with ``quality`` and ``priority`` labels, falling back to the
        defaults if the call fails or returns an unexpected value.
    """
    try:
        client = Client(
            host=OLLAMA_HOST,
            headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"},
        )
        user_prompt = (
            f"Category: {category_name}\n"
            f"Title: {title}\n"
            f"Description: {description or '(none provided)'}"
        )
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            format="json",
        )
        parsed = json.loads(response["message"]["content"])
    except Exception:
        return dict(DEFAULT_ASSESSMENT)

    quality = parsed.get("quality")
    priority = parsed.get("priority")
    return {
        "quality": (
            quality if quality in QUALITY_VALUES else DEFAULT_ASSESSMENT["quality"]
        ),
        "priority": (
            priority if priority in PRIORITY_VALUES else DEFAULT_ASSESSMENT["priority"]
        ),
    }

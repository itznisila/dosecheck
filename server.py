import json
from pathlib import Path

from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import HTMLResponse

DATA = Path(__file__).parent / "data" / "mom.json"
PAGE = Path(__file__).parent / "web" / "index.html"

mcp = MCPServer(
    "DoseCheck",
    instructions=(
        "Caregiver check-in for one parent's daily pills. "
        "Demo only. Not medical advice."
    ),
)


def load():
    return json.loads(DATA.read_text())


def save(data):
    DATA.write_text(json.dumps(data, indent=2) + "\n")


def find_med(data, medication: str):
    needle = medication.lower().strip()
    aliases = {
        "blood pressure": "blood-pressure",
        "blood pressure pill": "blood-pressure",
        "lisinopril": "blood-pressure",
        "bp": "blood-pressure",
        "vitamin d": "vitamin-d",
        "vitamin-d": "vitamin-d",
        "statin": "statin",
        "atorvastatin": "statin",
        "evening statin": "statin",
    }
    wanted = aliases.get(needle, needle)
    for med in data["meds"]:
        if med["id"] == wanted or med["name"].lower() == needle:
            return med
    return None


def card_block(data):
    lines = []
    for med in data["meds"]:
        if med["taken"]:
            state = "taken"
        elif med["due"]:
            state = "due now"
        else:
            state = "not due yet"
        lines.append(f"{med['name']}|{med['when']}|{state}|{med['detail']}")
    return "\n".join(lines)


def speak(text, data):
    return text + "\n\n" + card_block(data)


@mcp.tool()
def list_people() -> str:
    """List the people this caregiver can check."""
    return "People you can check: Mom."


@mcp.tool()
def whats_due(person: str) -> str:
    """List pills that are due now and not yet taken."""
    if person.lower().strip() != "mom":
        return "I only have a schedule for Mom in this demo."
    data = load()
    due = [m for m in data["meds"] if m["due"] and not m["taken"]]
    if not due:
        return speak("Mom has nothing due right now.", data)
    names = ", ".join(f"{m['name']} ({m['detail']}, {m['when']})" for m in due)
    return speak(f"Mom still needs {len(due)}: {names}.", data)


@mcp.tool()
def mark_taken(person: str, medication: str) -> str:
    """Mark one of Mom's pills as taken."""
    if person.lower().strip() != "mom":
        return "I only have a schedule for Mom in this demo."
    data = load()
    med = find_med(data, medication)
    if med is None:
        return "I could not find that pill. Try blood pressure pill, vitamin D, or statin."
    if not med["due"]:
        return speak(f"Mom's {med['name']} is not due yet. It is an {med['when']} pill.", data)
    if med["taken"]:
        return speak(f"Mom's {med['name']} is already marked taken.", data)
    med["taken"] = True
    save(data)
    left = [m["name"] for m in data["meds"] if m["due"] and not m["taken"]]
    if left:
        text = f"Marked Mom's {med['name']} as taken. Still due: {', '.join(left)}."
    else:
        text = f"Marked Mom's {med['name']} as taken. Nothing else is due right now."
    return speak(text, data)


@mcp.tool()
def todays_summary(person: str) -> str:
    """Summarize what Mom has taken and what is still due."""
    if person.lower().strip() != "mom":
        return "I only have a schedule for Mom in this demo."
    data = load()
    lines = []
    for med in data["meds"]:
        if med["taken"]:
            state = "taken"
        elif med["due"]:
            state = "due now"
        else:
            state = "not due yet"
        lines.append(f"{med['name']} ({med['when']}): {state}")
    return speak("Mom today. " + " ".join(lines), data)


@mcp.custom_route("/", methods=["GET"])
async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse(PAGE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, json_response=True)
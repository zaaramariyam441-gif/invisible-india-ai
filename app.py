"""Flask backend for the Invisible India discovery prototype."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILES = {
    "resources": DATA_DIR / "resources.json",
    "skills": DATA_DIR / "skills.json",
    "needs": DATA_DIR / "needs.json",
    "feedback": DATA_DIR / "feedback.json",
}
DATA_LOCK = threading.RLock()
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 1_000_000

SEED_DATA: dict[str, list[dict[str, Any]]] = {
    "resources": [
        {"id":"res-computers","name":"Refurbished learning laptops","category":"Computers & digital equipment","description":"Six tested laptops available for supervised digital literacy sessions at a community learning space.","location":"Pune, Maharashtra","availability":"Available","owner":"Demo Learning Collective","tags":["computers","laptops","digital learning","education"],"status":"Available","demo":True},
        {"id":"res-desks","name":"Surplus classroom desks","category":"Educational spaces","description":"A small set of sturdy classroom desks. Some need minor carpentry repairs before reuse.","location":"Jaipur, Rajasthan","availability":"Limited","owner":"Example School Resource Hub","tags":["desks","school","furniture","repair"],"status":"Available","demo":True},
        {"id":"res-tools","name":"Shared repair tool kit","category":"Tools & equipment","description":"Hand tools and a drill for community furniture repair projects, bookable in advance.","location":"Jaipur, Rajasthan","availability":"Available","owner":"Demo Neighbourhood Workshop","tags":["tools","repair","carpentry","workshop"],"status":"Available","demo":True},
        {"id":"res-books","name":"Children’s reading collection","category":"Books & learning materials","description":"Illustrated storybooks and early-reader books for a small community reading corner.","location":"Kochi, Kerala","availability":"Available","owner":"Example Reading Room","tags":["books","children","reading","learning"],"status":"Available","demo":True},
        {"id":"res-hall","name":"Community meeting room","category":"Community facilities","description":"Accessible multipurpose room with seating for workshops, tutoring and neighbourhood meetings.","location":"Pune, Maharashtra","availability":"Limited","owner":"Demo Community Space","tags":["community","room","workshops","tutoring"],"status":"Available","demo":True},
        {"id":"res-sewing","name":"Shared sewing machines","category":"Tools & equipment","description":"Three working sewing machines for supervised textile skills sessions and clothing repair.","location":"Bhopal, Madhya Pradesh","availability":"Available","owner":"Example Maker Circle","tags":["sewing","textiles","machines","repair"],"status":"Available","demo":True},
        {"id":"res-water","name":"Rainwater storage tanks","category":"Agricultural resources","description":"Two clean storage tanks that may support a community garden or small demonstration farm.","location":"Nashik, Maharashtra","availability":"Unknown","owner":"Demo Garden Network","tags":["water","agriculture","garden","storage"],"status":"Available","demo":True},
        {"id":"res-projector","name":"Portable projector","category":"Computers & digital equipment","description":"A portable projector for presentations, film screenings and community learning events.","location":"Lucknow, Uttar Pradesh","availability":"Available","owner":"Example Open Learning Group","tags":["projector","digital","education","events"],"status":"Available","demo":True},
        {"id":"res-bus","name":"Occasional volunteer transport","category":"Transport & logistics","description":"A small van may be available for pre-arranged transport of donated learning materials.","location":"Jaipur, Rajasthan","availability":"Limited","owner":"Demo Logistics Circle","tags":["transport","delivery","books","logistics"],"status":"Available","demo":True},
        {"id":"res-kitchen","name":"Shared community kitchen","category":"Community facilities","description":"A hygienic teaching kitchen for community cooking and food skills workshops.","location":"Kochi, Kerala","availability":"Limited","owner":"Example Neighbourhood Kitchen","tags":["kitchen","food","community","training"],"status":"Available","demo":True},
    ],
    "skills": [
        {"id":"skill-tutor","name":"Volunteer maths tutor","category":"Teaching & tutoring","description":"Can support small-group school-age maths and homework sessions, including foundational numeracy.","location":"Pune, Maharashtra","experience":"Intermediate","availability":"Weekends","tags":["tutoring","maths","education","students"],"status":"Available","demo":True},
        {"id":"skill-carpenter","name":"Furniture repair carpenter","category":"Repair & carpentry","description":"Offers basic wooden desk, shelf and chair repairs using hand tools; small jobs preferred.","location":"Jaipur, Rajasthan","experience":"Experienced","availability":"Limited","tags":["carpentry","furniture","shelves","repair","wood"],"status":"Available","demo":True},
        {"id":"skill-web","name":"Community web developer","category":"Digital & technology","description":"Can build a simple accessible website for a local initiative and help with basic upkeep.","location":"Kochi, Kerala","experience":"Intermediate","availability":"Weekends","tags":["web development","website","digital","technology"],"status":"Available","demo":True},
        {"id":"skill-literacy","name":"Digital literacy facilitator","category":"Teaching & tutoring","description":"Can guide beginners through computer basics, safe browsing and common online services.","location":"Pune, Maharashtra","experience":"Intermediate","availability":"Weekday evenings","tags":["digital literacy","computers","teaching","training"],"status":"Available","demo":True},
        {"id":"skill-electric","name":"Basic electrical repair","category":"Repair & maintenance","description":"Experienced with simple household electrical checks and minor equipment repairs.","location":"Bhopal, Madhya Pradesh","experience":"Experienced","availability":"Limited","tags":["electrical","repair","maintenance","equipment"],"status":"Available","demo":True},
        {"id":"skill-translate","name":"Hindi-English translator","category":"Language & translation","description":"Can translate short community notices, learning materials and event information.","location":"Jaipur, Rajasthan","experience":"Intermediate","availability":"Weekends","tags":["translation","Hindi","English","community"],"status":"Available","demo":True},
        {"id":"skill-design","name":"Volunteer graphic designer","category":"Creative & design","description":"Creates clear posters and simple visual materials for workshops and local programmes.","location":"Lucknow, Uttar Pradesh","experience":"Intermediate","availability":"Weekends","tags":["graphic design","posters","creative","events"],"status":"Available","demo":True},
        {"id":"skill-garden","name":"Urban gardening mentor","category":"Agriculture & gardening","description":"Can help a group plan a small garden and learn basic composting and plant care.","location":"Nashik, Maharashtra","experience":"Experienced","availability":"Limited","tags":["agriculture","gardening","compost","plants"],"status":"Available","demo":True},
        {"id":"skill-sewing","name":"Clothing and textile repair","category":"Craft & textile skills","description":"Can teach basic sewing and mend everyday clothing or reusable fabric items.","location":"Bhopal, Madhya Pradesh","experience":"Experienced","availability":"Weekends","tags":["sewing","textiles","repair","teaching"],"status":"Available","demo":True},
        {"id":"skill-volunteer","name":"Community event volunteer","category":"Community volunteering","description":"Can assist with event setup, attendee coordination and distributing learning materials.","location":"Kochi, Kerala","experience":"Beginner","availability":"Weekends","tags":["volunteering","events","community","logistics"],"status":"Available","demo":True},
    ],
    "needs": [
        {"id":"need-computers","title":"Computers for a learning centre","category":"Digital access","description":"A community learning centre is seeking working computers for beginner digital literacy sessions.","location":"Pune, Maharashtra","urgency":"Medium","required_kind":"resource","requirements":["computers","laptops","digital learning","education"],"beneficiaries":18,"status":"Open","demo":True},
        {"id":"need-desks","title":"Repair desks for a school","category":"Education","description":"A local school needs help repairing wooden desks so they can be returned to classroom use.","location":"Jaipur, Rajasthan","urgency":"Medium","required_kind":"skill","requirements":["carpentry","furniture repair","desks","wood"],"beneficiaries":24,"status":"Open","demo":True},
        {"id":"need-tutors","title":"Volunteer tutors for after-school learning","category":"Education","description":"A neighbourhood study group needs volunteer tutors for foundational maths and homework support.","location":"Pune, Maharashtra","urgency":"High","required_kind":"skill","requirements":["tutoring","maths","education","students"],"beneficiaries":15,"status":"Open","demo":True},
        {"id":"need-website","title":"A simple website for a community initiative","category":"Digital access","description":"A small community initiative needs a basic accessible website to share its programmes and contact details.","location":"Kochi, Kerala","urgency":"Low","required_kind":"skill","requirements":["web development","website","digital"],"beneficiaries":0,"status":"Open","demo":True},
        {"id":"need-books","title":"Books for a children's reading corner","category":"Learning materials","description":"A volunteer-run reading corner is looking for age-appropriate storybooks and early readers.","location":"Kochi, Kerala","urgency":"Medium","required_kind":"resource","requirements":["books","reading","children","learning"],"beneficiaries":20,"status":"Open","demo":True},
        {"id":"need-garden","title":"Guidance for a community garden","category":"Agriculture & environment","description":"A local group would benefit from garden planning, basic plant care and composting guidance.","location":"Nashik, Maharashtra","urgency":"Low","required_kind":"skill","requirements":["gardening","agriculture","compost","plants"],"beneficiaries":12,"status":"Open","demo":True},
        {"id":"need-sewing","title":"Sewing sessions and clothing repair","category":"Skills & livelihoods","description":"A community group wants to run beginner sewing sessions and repair reusable fabric items.","location":"Bhopal, Madhya Pradesh","urgency":"Low","required_kind":"skill","requirements":["sewing","textiles","repair","teaching"],"beneficiaries":10,"status":"Open","demo":True},
        {"id":"need-tools","title":"Tools for a neighbourhood repair day","category":"Community facilities","description":"A volunteer group needs shared hand tools and a drill for a furniture repair event.","location":"Jaipur, Rajasthan","urgency":"Medium","required_kind":"resource","requirements":["tools","repair","carpentry","workshop"],"beneficiaries":12,"status":"Open","demo":True},
        {"id":"need-posters","title":"Design help for learning event posters","category":"Community programmes","description":"A learning group needs clear event posters and simple information materials for families.","location":"Lucknow, Uttar Pradesh","urgency":"Low","required_kind":"skill","requirements":["graphic design","posters","events","creative"],"beneficiaries":35,"status":"Open","demo":True},
        {"id":"need-meals","title":"Community cooking workshop","category":"Food & community","description":"A neighbourhood group is planning a practical cooking workshop and needs access to a teaching kitchen.","location":"Kochi, Kerala","urgency":"Low","required_kind":"resource","requirements":["kitchen","food","community","training"],"beneficiaries":16,"status":"Open","demo":True},
    ],
    "feedback": [],
}


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_records(kind: str) -> list[dict[str, Any]]:
    path = DATA_FILES[kind]
    with DATA_LOCK:
        if not path.exists():
            _atomic_write(path, SEED_DATA[kind])
            return list(SEED_DATA[kind])
        try:
            with path.open(encoding="utf-8") as source:
                records = json.load(source)
            if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
                app.logger.error("Invalid JSON record structure in %s", path)
                return []
            return records
        except (OSError, json.JSONDecodeError) as exc:
            app.logger.error("Could not read %s: %s", path, exc)
            return []


def write_records(kind: str, records: list[dict[str, Any]]) -> None:
    with DATA_LOCK:
        _atomic_write(DATA_FILES[kind], records)


def tokens(value: Any) -> set[str]:
    words = re.findall(r"[a-z0-9]+", str(value or "").lower())
    ignored = {"a", "an", "and", "are", "for", "from", "in", "is", "of", "or", "the", "to", "with", "may", "needs", "need", "help", "available"}
    return {word for word in words if len(word) > 1 and word not in ignored}


def location_score(need_location: str, candidate_location: str) -> tuple[int, str]:
    if not need_location or not candidate_location:
        return 7, "Location is missing on one or both records; proximity is uncertain."
    need_parts = [part.strip().casefold() for part in need_location.split(",")]
    candidate_parts = [part.strip().casefold() for part in candidate_location.split(",")]
    if need_parts[0] == candidate_parts[0]:
        return 20, f"Same city: {candidate_location}."
    if len(need_parts) > 1 and len(candidate_parts) > 1 and need_parts[-1] == candidate_parts[-1]:
        return 12, f"Same state: {candidate_parts[-1]}; city differs."
    return 2, "Locations differ; travel or delivery feasibility is unknown."


def score_match(need: dict[str, Any], candidate: dict[str, Any], kind: str) -> dict[str, Any]:
    requirements = set()
    for item in need.get("requirements", []):
        requirements |= tokens(item)
    candidate_text = " ".join([
        candidate.get("name", ""), candidate.get("category", ""), candidate.get("description", ""),
        " ".join(candidate.get("tags", [])),
    ])
    candidate_words = tokens(candidate_text)
    overlap = requirements & candidate_words
    keyword_score = round(25 * len(overlap) / max(1, len(requirements)))
    need_description_words = tokens(need.get("description", ""))
    candidate_description_words = tokens(candidate.get("description", ""))
    description_overlap = need_description_words & candidate_description_words
    description_score = round(15 * len(description_overlap) / max(1, len(need_description_words)))
    category_tokens = tokens(need.get("category", ""))
    candidate_categories = tokens(candidate.get("category", ""))
    category_match = bool(category_tokens & candidate_categories)
    requirement_match = bool(requirements & candidate_categories)
    category_score = 30 if category_match or requirement_match else (12 if overlap else 0)
    location_points, location_reason = location_score(need.get("location", ""), candidate.get("location", ""))
    availability = str(candidate.get("availability", "Unknown")).casefold()
    availability_points = 10 if availability in {"available", "weekends", "weekday evenings"} else 6 if availability in {"limited", "by arrangement"} else 3
    factors = [
        {"name": "Category compatibility", "points": category_score, "outOf": 30, "detail": "Category or requested terms align." if category_score else "No direct category alignment found."},
        {"name": "Requirement keyword overlap", "points": keyword_score, "outOf": 25, "detail": f"{len(overlap)} of {len(requirements)} meaningful requirement terms overlap" + (f": {', '.join(sorted(overlap)[:5])}." if overlap else "; no matching terms." )},
        {"name": "Description similarity", "points": description_score, "outOf": 15, "detail": f"{len(description_overlap)} of {len(need_description_words)} meaningful need-description terms appear in the candidate description."},
        {"name": "Location", "points": location_points, "outOf": 20, "detail": location_reason},
        {"name": "Availability", "points": availability_points, "outOf": 10, "detail": f"Availability listed as {candidate.get('availability') or 'unknown'}; confirm directly."},
    ]
    warnings = []
    if not need.get("location") or not candidate.get("location"):
        warnings.append("Location information is incomplete.")
    if availability not in {"available", "weekends", "weekday evenings"}:
        warnings.append("Availability needs confirmation.")
    if not candidate.get("contact"):
        warnings.append("No contact method is listed; this prototype does not contact anyone.")
    return {
        "id": f"match-{need['id']}-{candidate['id']}", "need": need,
        "candidate": candidate, "kind": kind, "score": sum(f["points"] for f in factors),
        "factors": factors, "warnings": warnings,
    }


def get_matches() -> list[dict[str, Any]]:
    resources, skills, needs = (read_records(k) for k in ("resources", "skills", "needs"))
    results = []
    for need in needs:
        if need.get("status", "Open").casefold() != "open":
            continue
        kinds = [need.get("required_kind")] if need.get("required_kind") in {"resource", "skill"} else ["resource", "skill"]
        pools = {"resource": resources, "skill": skills}
        for kind in kinds:
            for candidate in pools[kind]:
                if candidate.get("status", "Available").casefold() not in {"available", "open"}:
                    continue
                results.append(score_match(need, candidate, kind))
    return sorted(results, key=lambda item: (-item["score"], item["need"]["title"], item["candidate"]["name"]))


def validate_payload(kind: str, payload: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "Submit a JSON object."
    fields = {
        "resources": ("name", "category", "description", "location", "availability", "owner"),
        "skills": ("name", "category", "description", "location", "experience", "availability"),
        "needs": ("title", "category", "description", "location", "urgency", "required_kind"),
    }[kind]
    cleaned = {}
    for field in fields:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"{field.replace('_', ' ').capitalize()} is required."
        if len(value.strip()) > (1000 if field == "description" else 120):
            return None, f"{field.replace('_', ' ').capitalize()} is too long."
        cleaned[field] = value.strip()
    if kind == "needs" and cleaned["required_kind"] not in {"resource", "skill", "both"}:
        return None, "Required kind must be resource, skill, or both."
    if kind == "needs":
        cleaned["requirements"] = payload.get("requirements", [])
        if isinstance(cleaned["requirements"], str):
            cleaned["requirements"] = [part.strip() for part in cleaned["requirements"].split(",") if part.strip()]
        if not isinstance(cleaned["requirements"], list) or not all(isinstance(item, str) for item in cleaned["requirements"]):
            return None, "Requirements must be a list of words or phrases."
        try:
            cleaned["beneficiaries"] = max(0, min(100000, int(payload.get("beneficiaries") or 0)))
        except (TypeError, ValueError):
            return None, "Beneficiaries must be a whole number."
    else:
        cleaned["tags"] = payload.get("tags", [])
        if isinstance(cleaned["tags"], str):
            cleaned["tags"] = [part.strip() for part in cleaned["tags"].split(",") if part.strip()]
        if not isinstance(cleaned["tags"], list) or not all(isinstance(item, str) for item in cleaned["tags"]):
            return None, "Tags must be a list of words."
        contact = payload.get("contact", "")
        if contact:
            if not isinstance(contact, str) or len(contact.strip()) > 240:
                return None, "Contact method must be text under 240 characters."
            cleaned["contact"] = contact.strip()
    cleaned["id"] = f"{kind[:-1] if kind != 'needs' else 'need'}-{uuid.uuid4().hex[:12]}"
    cleaned["status"] = "Open" if kind == "needs" else "Available"
    cleaned["demo"] = False
    return cleaned, None


@app.get("/")
def home():
    return send_from_directory(BASE_DIR / "static", "index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "application": "Invisible India"})


@app.get("/api/<kind>")
def list_records(kind: str):
    if kind not in {"resources", "skills", "needs"}:
        return jsonify({"error": "Unknown directory."}), 404
    records = read_records(kind)
    query = request.args.get("q", "").strip().casefold()
    category = request.args.get("category", "").strip().casefold()
    location = request.args.get("location", "").strip().casefold()
    if query:
        records = [row for row in records if query in " ".join(str(v) for v in row.values()).casefold()]
    if category:
        records = [row for row in records if category in str(row.get("category", "")).casefold()]
    if location:
        records = [row for row in records if location in str(row.get("location", "")).casefold()]
    return jsonify({"items": records, "total": len(records)})


@app.post("/api/<kind>")
def create_record(kind: str):
    if kind not in {"resources", "skills", "needs"}:
        return jsonify({"error": "Unknown directory."}), 404
    record, error = validate_payload(kind, request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400
    with DATA_LOCK:
        records = read_records(kind)
        records.append(record)
        write_records(kind, records)
    return jsonify({"item": record}), 201


@app.get("/api/dashboard")
def dashboard():
    resources, skills, needs = (read_records(k) for k in ("resources", "skills", "needs"))
    matches = get_matches()
    return jsonify({"resources": len(resources), "skills": len(skills), "needs": len(needs), "matches": sum(1 for item in matches if item["score"] >= 25), "demo": all(row.get("demo", False) for group in (resources, skills, needs) for row in group)})


@app.get("/api/search")
def search():
    query = request.args.get("q", "").strip().casefold()
    result = {}
    for kind in ("resources", "skills", "needs"):
        rows = read_records(kind)
        result[kind] = [row for row in rows if not query or query in " ".join(str(v) for v in row.values()).casefold()]
    return jsonify(result)


@app.get("/api/matches")
def matches():
    result = get_matches()
    match_type = request.args.get("type", "all")
    location = request.args.get("location", "").casefold()
    category = request.args.get("category", "").casefold()
    if match_type in {"resource", "skill"}:
        result = [item for item in result if item["kind"] == match_type]
    if location:
        result = [item for item in result if location in item["need"].get("location", "").casefold() or location in item["candidate"].get("location", "").casefold()]
    if category:
        result = [item for item in result if category in item["need"].get("category", "").casefold() or category in item["candidate"].get("category", "").casefold()]
    result = [item for item in result if item["score"] >= 25]
    return jsonify({"items": result, "total": len(result), "method": "Transparent weighted keyword and attribute scoring (showing candidates with 25+ relevance points); suggestions require human verification."})


@app.get("/api/matches/<match_id>")
def match_detail(match_id: str):
    item = next((match for match in get_matches() if match["id"] == match_id), None)
    if not item:
        return jsonify({"error": "Match suggestion not found."}), 404
    return jsonify({"item": item})


@app.post("/api/feedback")
def submit_feedback():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("match_id"), str) or payload.get("rating") not in {"useful", "irrelevant"}:
        return jsonify({"error": "Provide a match_id and a useful or irrelevant rating."}), 400
    if not any(item["id"] == payload["match_id"] for item in get_matches()):
        return jsonify({"error": "Match suggestion not found."}), 404
    entry = {"id": f"feedback-{uuid.uuid4().hex[:12]}", "match_id": payload["match_id"], "rating": payload["rating"], "created_at": datetime.now(timezone.utc).isoformat()}
    with DATA_LOCK:
        entries = read_records("feedback")
        entries.append(entry)
        write_records("feedback", entries)
    return jsonify({"item": entry}), 201


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return error


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Request is too large."}), 413


def initialize_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for kind, path in DATA_FILES.items():
        if not path.exists():
            _atomic_write(path, SEED_DATA[kind])


initialize_data()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
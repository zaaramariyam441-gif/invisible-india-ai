# Invisible India

**Discover what exists. Connect what matters.**

An early-stage, local prototype for discovering fictional demonstration resources, practical skills, community needs, and explainable potential connections. It uses Flask, Python, HTML, CSS, JavaScript, and JSON files. No paid APIs or external services are required to run the application.

## Run on Windows

Required: Python 3.10 or newer and a terminal such as PowerShell.

1. Open this project folder in VS Code.
2. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

3. Activate it in PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use `py -m pip` in the remaining commands instead of activating the environment.

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start the Flask server:

   ```powershell
   python app.py
   ```

6. Open <http://127.0.0.1:5000> in a browser. Stop the server with `Ctrl+C`.

The presentation files in the project are separate deliverables. The Flask application is served from `static/index.html`.

## Included

- A responsive dashboard with counts calculated from the JSON records.
- Search across resources, skills, and needs; per-directory category and location filters.
- Validated forms that append user submissions to local JSON data.
- Fictional sample data: 10 resources, 10 skills, and 10 community needs. Records are labelled as illustrative in the interface.
- Ranked resource and skill suggestions for open needs, with a score breakdown and missing-information cautions.
- Useful / irrelevant feedback stored in `data/feedback.json`.
- Flask JSON routes under `/api/`, including `/api/health`.

## Matching method

This prototype does **not** use a trained machine-learning model or claim to make AI predictions. It calculates a transparent baseline ranking from four factors:

| Factor | Maximum | Method |
| --- | ---: | --- |
| Category compatibility | 30 | Exact meaningful token overlap between need and candidate categories, or a partial category credit when requirement terms overlap. |
| Requirement keyword overlap | 25 | Share of meaningful need requirement terms found in the candidate's name, category, description, or tags. |
| Description similarity | 15 | Share of meaningful need-description terms appearing in the candidate description. This is a simple token-overlap measure, not semantic NLP. |
| Location | 20 | Same city: 20; same state: 12; different known locations: 2; incomplete location: 7. |
| Listed availability | 10 | Listed available: 10; limited/by arrangement: 6; unknown or unrecognised: 3. Confirm it directly. |

Candidates score from 0 to 100. The match view displays candidates with at least 25 relevance points, sorted by score. Points are heuristic ranking signals, not probabilities, verified compatibility, or confirmed partnerships. Human review is required. The backend implementation is in `app.py` (`score_match`).

## Data and privacy

JSON files are created in `data/` if they do not already exist. Existing files are not reseeded or silently replaced. Writes use a temporary file and an atomic replace. Seed listings are fictional examples; user submissions are stored locally on this machine. Contact information is not required, and the prototype does not contact listing owners.

To reset the sample data, stop the server and manually remove or move the relevant JSON file(s) in `data/`; restarting recreates only missing files from the fictional sample set. Back up user-submitted records first.

## Routes

- `GET /api/dashboard`
- `GET|POST /api/resources`, `/api/skills`, `/api/needs`
- `GET /api/search?q=...`
- `GET /api/matches?type=all|resource|skill&location=...&category=...`
- `GET /api/matches/<match_id>`
- `POST /api/feedback`
- `GET /api/health`

## Tests

Run the API and storage tests with:

```powershell
python -m unittest discover -s tests -v
```

The tests use temporary JSON files and do not alter the working sample data.

## Implemented and planned

**Implemented:** local directories, forms and validation, JSON storage, search and filters, deterministic explainable matching, feedback capture, and responsive views.

**Planned / not implemented:** NLP or semantic embeddings, language support beyond the current English interface and sample text, identity and consent workflows, verified listings, external messaging, production security, national coverage, and real-world impact evaluation. Do not treat demonstration data or matches as verified findings.
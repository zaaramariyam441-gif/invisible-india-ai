import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as prototype


class InvisibleIndiaApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)
        self.files = {kind: self.data_dir / f"{kind}.json" for kind in prototype.DATA_FILES}
        for kind, path in self.files.items():
            path.write_text(json.dumps(prototype.SEED_DATA[kind]), encoding="utf-8")
        self.file_patch = patch.dict(prototype.DATA_FILES, self.files)
        self.file_patch.start()
        self.client = prototype.app.test_client()

    def tearDown(self):
        self.file_patch.stop()
        self.temp.cleanup()

    def test_dashboard_counts_json_records_and_qualified_matches(self):
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["resources"], 10)
        self.assertEqual(response.json["skills"], 10)
        self.assertEqual(response.json["needs"], 10)
        self.assertEqual(response.json["matches"], self.client.get("/api/matches").json["total"])

    def test_matching_explanations_reflect_the_score(self):
        results = self.client.get("/api/matches").json["items"]
        website = next(item for item in results if item["need"]["id"] == "need-website")
        self.assertEqual(website["candidate"]["id"], "skill-web")
        self.assertEqual(website["score"], sum(factor["points"] for factor in website["factors"]))
        self.assertTrue(any("Same city" in factor["detail"] for factor in website["factors"]))

    def test_search_and_filters_use_saved_records(self):
        result = self.client.get("/api/resources?q=laptop&location=Pune").json
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "res-computers")
        self.assertEqual(self.client.get("/api/search?q=carpenter").json["skills"][0]["id"], "skill-carpenter")

    def test_valid_resource_submission_persists_and_is_not_demo_data(self):
        response = self.client.post("/api/resources", json={"name":"Shared tablets","category":"Computers & digital equipment","description":"Two tablets for learning sessions.","location":"Pune, Maharashtra","availability":"Available","owner":"Test contributor","tags":"tablets, learning"})
        self.assertEqual(response.status_code, 201)
        created = response.json["item"]
        self.assertFalse(created["demo"])
        persisted = json.loads(self.files["resources"].read_text(encoding="utf-8"))
        self.assertEqual(persisted[-1]["id"], created["id"])
        self.assertEqual(self.client.get("/api/resources").json["total"], 11)

    def test_valid_skill_and_need_submissions_persist(self):
        skill = self.client.post("/api/skills", json={"name":"Volunteer translator","category":"Language & translation","description":"Can translate short notices.","location":"Pune, Maharashtra","experience":"Intermediate","availability":"Weekends","tags":["translation"]})
        need = self.client.post("/api/needs", json={"title":"Need translation","category":"Community programmes","description":"Translate event details.","location":"Pune, Maharashtra","urgency":"Low","required_kind":"skill","requirements":"translation, Hindi","beneficiaries":"12"})
        self.assertEqual(skill.status_code, 201)
        self.assertEqual(need.status_code, 201)
        self.assertEqual(len(json.loads(self.files["skills"].read_text(encoding="utf-8"))), 11)
        self.assertEqual(json.loads(self.files["needs"].read_text(encoding="utf-8"))[-1]["beneficiaries"], 12)

    def test_invalid_submission_is_rejected(self):
        missing = self.client.post("/api/resources", json={})
        invalid_number = self.client.post("/api/needs", json={"title":"Need","category":"Other","description":"Help","location":"Pune","urgency":"Low","required_kind":"skill","beneficiaries":"many"})
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(invalid_number.status_code, 400)
        self.assertEqual(len(json.loads(self.files["resources"].read_text(encoding="utf-8"))), 10)

    def test_feedback_is_saved_in_json(self):
        match_id = self.client.get("/api/matches").json["items"][0]["id"]
        response = self.client.post("/api/feedback", json={"match_id":match_id,"rating":"useful"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(self.files["feedback"].read_text(encoding="utf-8"))[0]["rating"], "useful")


if __name__ == "__main__":
    unittest.main()
import json
from india_ai_index.providers import Mock, REGISTRY
from india_ai_index.runner import load_tasks, run, validate
from india_ai_index.scoring import chrf, exact, field_accuracy

def test_tasks_load():
    items = load_tasks("tasks"); assert len(items) >= 25
    assert {i["suite"] for i in items} == {"indic_qa", "translation", "doc_extraction"}
    assert {"hi", "ta", "bn", "mr"} <= {i["lang"] for i in items}

def test_synthetic_markers():
    for i in load_tasks("tasks"):
        if i["suite"] == "doc_extraction": assert "SYNTHETIC" in i["prompt"]

def test_scorers():
    assert exact("नई दिल्ली।", "नई दिल्ली") == 1.0 and exact("Mumbai", "Delhi") == 0.0
    assert chrf("कृपया शुक्रवार तक चालान भेजें", "कृपया शुक्रवार तक चालान भेजें।") > 0.99
    assert 0 < chrf("कृपया चालान भेजें", "कृपया शुक्रवार तक चालान भेजें।") < 1
    assert field_accuracy('x {"a": "1", "b": 2}', {"a": 1, "b": 3}) == 0.5

def test_oracle_mock_scores_perfect():
    items = load_tasks("tasks")
    oracle = {i["prompt"]: (json.dumps(i["reference"], ensure_ascii=False) if isinstance(i["reference"], dict) else i["reference"]) for i in items}
    res = run(Mock(oracle=oracle, price_in_usd_per_m=1.0, price_out_usd_per_m=2.0), items, usd_inr=1.0)
    assert res["overall_score"] > 0.99 and not validate(res) and res["cost_inr_total"] > 0

def test_dumb_mock_scores_low():
    res = run(Mock(), load_tasks("tasks"), usd_inr=1.0); assert res["overall_score"] < 0.1

def test_registry_providers_need_keys(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert not REGISTRY["xai"]("grok").available()
    assert set(REGISTRY) >= {"openai", "google", "anthropic", "xai", "sarvam", "hf", "mock"}

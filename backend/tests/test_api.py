import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.ratelimit import SlidingLimiter

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_config_defaults_to_demo_without_keys():
    j = client.get("/api/config").json()
    assert j["providers"] == {"stt": "browser", "translate": "demo", "tts": "browser"}
    assert j["demo_translation"] is True
    assert {l["code"] for l in j["languages"]} >= {"hi", "en"}
    assert "openai" not in str(j).lower().replace("openai_", "")  # no key material in config


def test_demo_translate_marks_simulated():
    j = client.post("/api/translate", json={"text": "नमस्ते!", "source": "hi", "target": "en"}).json()
    assert j["text"] == "Hello" and j["simulated"] is True and j["matched"] is True


def test_demo_translate_no_match_is_flagged():
    j = client.post("/api/translate", json={"text": "random sentence", "source": "en", "target": "hi"}).json()
    assert j["matched"] is False and j["simulated"] is True


def test_translate_validation():
    assert client.post("/api/translate", json={"text": "", "source": "hi", "target": "en"}).status_code == 422
    r = client.post("/api/translate", json={"text": "hi", "source": "xx", "target": "en"})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "unsupported_language"


def test_stt_and_tts_need_server_providers():
    r = client.post("/api/stt", files={"audio": ("a.webm", b"1234", "audio/webm")}, data={"language": "hi"})
    assert r.status_code == 400
    assert client.post("/api/tts", json={"text": "hi", "language": "en"}).status_code == 400


def test_create_room():
    code = client.post("/api/rooms").json()["room"]
    assert len(code) == 6 and code.isalnum()


def test_ws_two_peers_and_third_rejected():
    with client.websocket_connect("/ws/TEST42") as a:
        assert a.receive_json()["peers"] == 0
        with client.websocket_connect("/ws/test42") as b:
            assert b.receive_json()["peers"] == 1
            assert a.receive_json()["type"] == "peer_joined"
            a.send_json({"type": "offer", "sdp": {"type": "offer", "sdp": "x"}})
            got = b.receive_json()
            assert got["type"] == "offer" and "from" in got
            a.send_json({"type": "evil", "x": 1})  # dropped
            a.send_json({"type": "utterance", "original": "a", "translated": "b"})
            assert b.receive_json()["type"] == "utterance"
            with client.websocket_connect("/ws/TEST42") as c:
                assert c.receive_json()["type"] == "room_full"
        assert a.receive_json()["type"] == "peer_left"


def test_ws_invalid_room():
    with client.websocket_connect("/ws/!!") as c:
        assert c.receive_json()["type"] == "error"


def test_provider_selection_and_warnings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    s = get_settings()
    assert (s.stt_provider, s.translate_provider, s.tts_provider) == ("openai", "openai", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("TRANSLATE_PROVIDER", "openai")
    assert any("OPENAI_API_KEY" in w for w in get_settings().warnings())


def test_rate_limiter():
    l = SlidingLimiter()
    assert all(l.allow("ip", 3) for _ in range(3)) and not l.allow("ip", 3)

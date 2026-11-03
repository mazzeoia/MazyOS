from __future__ import annotations

from app.campaigns.schemas import DraftCreate, DraftOut, SyncRequest, SyncResponse


def test_sync_request_schema():
    req = SyncRequest(act_id="act_123")
    assert req.date_preset == "last_7d"


def test_sync_response_schema():
    resp = SyncResponse(campaigns_synced=5, metrics_upserted=35, errors=[{"campaign": "X", "error": "gone"}])
    assert resp.campaigns_synced == 5
    assert len(resp.errors) == 1


def test_draft_create_schema():
    draft = DraftCreate(act_id="act_123", payload={"name": "Test", "objective": "OUTCOME_LEADS"})
    assert draft.payload["objective"] == "OUTCOME_LEADS"


def test_draft_out_schema():
    out = DraftOut(id="d1", status="rascunho", payload={"name": "X"}, meta_campaign_id=None, erro_detalhes=None)
    assert out.status == "rascunho"

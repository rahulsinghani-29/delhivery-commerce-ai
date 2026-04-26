"""Outbound communication orchestrator — coordinates WA -> wait -> voice flow."""
from __future__ import annotations
import sqlite3, uuid
from datetime import datetime, timedelta


class OutboundOrchestrator:
    """Orchestrates outbound customer communication for risky COD orders."""

    def __init__(self, db, whatsapp_client, voice_ai_client, issue_router, escalation_window_hours=2.0):
        self.db = db
        self.whatsapp_client = whatsapp_client
        self.voice_ai_client = voice_ai_client
        self.issue_router = issue_router
        self.escalation_window_hours = escalation_window_hours

    def trigger_outbound(self, order, issue_type):
        oid, mid, cid = order["order_id"], order["merchant_id"], order["customer_ucid"]
        if not self.check_communication_limits(oid, issue_type):
            return self._log(oid, mid, cid, issue_type, ch="whatsapp", st="failed", err="Communication limit reached")
        if not self._check_permission(mid, issue_type):
            return self._log(oid, mid, cid, issue_type, ch="whatsapp", st="failed", err="Merchant permission not granted")
        tf = self.issue_router.get_template_fields(order, issue_type)
        wa = self.whatsapp_client.send_template_message(cid, issue_type, tf)
        if wa["status"] != "sent":
            return self._log(oid, mid, cid, issue_type, ch="whatsapp", st="failed", mid2=wa.get("message_id"), err=wa.get("error_message"))
        esc = (datetime.utcnow() + timedelta(hours=self.escalation_window_hours)).isoformat()
        entry = self._log(oid, mid, cid, issue_type, ch="whatsapp", st="sent", mid2=wa["message_id"], esc=esc)
        self._persist(entry)
        return entry

    def check_and_escalate(self, comm_id):
        entry = self._get(comm_id)
        if entry is None:
            return {"error": "Communication log not found", "status": "failed"}
        mid2 = entry.get("message_id")
        if mid2:
            resp = self.whatsapp_client.check_response(mid2)
            if resp.get("responded"):
                res = self._derive_resolution(entry["issue_type"], resp.get("response_content", ""))
                self._update(comm_id, "responded", res=res, cr=resp.get("response_content"), ra=resp.get("responded_at"))
                self.update_order_resolution(entry["order_id"], res)
                entry["status"] = "responded"
                entry["resolution"] = res
                return entry
        if not self._voice_ok(entry["order_id"], entry["issue_type"]):
            self._update(comm_id, "no_response")
            entry["status"] = "no_response"
            return entry
        ctx = {"order_summary": {"order_id": entry["order_id"], "customer_ucid": entry["customer_ucid"], "merchant_name": ""}}
        cr = self.voice_ai_client.initiate_call(entry["customer_ucid"], entry["issue_type"], ctx)
        vlog = self._log(entry["order_id"], entry["merchant_id"], entry["customer_ucid"], entry["issue_type"], ch="voice", st=self._map_status(cr["status"]), mid2=cr.get("call_id"), res=cr.get("resolution"))
        self._persist(vlog)
        if cr.get("resolution"):
            self.update_order_resolution(entry["order_id"], cr["resolution"])
        return vlog

    def update_order_resolution(self, order_id, resolution):
        try:
            self.db.execute("UPDATE orders SET delivery_outcome=? WHERE order_id=?", ("pending", order_id))
            self.db.commit()
        except Exception:
            pass

    def get_communication_status(self, order_id):
        try:
            rows = self.db.execute("SELECT * FROM communication_logs WHERE order_id=? ORDER BY sent_at DESC", (order_id,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def check_communication_limits(self, order_id, issue_type):
        try:
            r = self.db.execute("SELECT COUNT(*) FROM communication_logs WHERE order_id=? AND issue_type=? AND channel='whatsapp'", (order_id, issue_type)).fetchone()
            return (r[0] if r else 0) < 1
        except Exception:
            return True

    def fallback_to_next_intervention(self, order_id):
        try:
            self.db.execute("UPDATE communication_logs SET status='no_response' WHERE order_id=? AND resolution IS NULL", (order_id,))
            self.db.commit()
        except Exception:
            pass

    def _check_permission(self, merchant_id, issue_type):
        it = "address_enrichment_outreach" if issue_type == "address_enrichment" else "cod_to_prepaid_outreach"
        try:
            r = self.db.execute("SELECT is_enabled FROM merchant_permissions WHERE merchant_id=? AND intervention_type=?", (merchant_id, it)).fetchone()
            return bool(r[0]) if r else False
        except Exception:
            return False

    def _voice_ok(self, order_id, issue_type):
        try:
            r = self.db.execute("SELECT COUNT(*) FROM communication_logs WHERE order_id=? AND issue_type=? AND channel='voice'", (order_id, issue_type)).fetchone()
            return (r[0] if r else 0) < 1
        except Exception:
            return True

    def _log(self, oid, mid, cid, it, *, ch, st, mid2=None, res=None, err=None, esc=None):
        return {
            "communication_id": "comm_" + uuid.uuid4().hex[:12],
            "order_id": oid, "merchant_id": mid, "customer_ucid": cid,
            "issue_type": it, "channel": ch,
            "template_id": it if ch == "whatsapp" else None,
            "message_id": mid2, "status": st, "customer_response": None,
            "resolution": res, "sent_at": datetime.utcnow().isoformat(),
            "responded_at": None, "escalation_scheduled_at": esc,
            "error_message": err,
        }

    def _persist(self, e):
        try:
            self.db.execute(
                "INSERT INTO communication_logs (communication_id,order_id,merchant_id,customer_ucid,issue_type,channel,template_id,message_id,status,customer_response,resolution,sent_at,responded_at,escalation_scheduled_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (e["communication_id"], e["order_id"], e["merchant_id"], e["customer_ucid"], e["issue_type"], e["channel"], e.get("template_id"), e.get("message_id"), e["status"], e.get("customer_response"), e.get("resolution"), e["sent_at"], e.get("responded_at"), e.get("escalation_scheduled_at")))
            self.db.commit()
        except Exception:
            pass

    def _get(self, comm_id):
        try:
            r = self.db.execute("SELECT * FROM communication_logs WHERE communication_id=?", (comm_id,)).fetchone()
            return dict(r) if r else None
        except Exception:
            return None

    def _update(self, comm_id, status, *, res=None, cr=None, ra=None):
        try:
            self.db.execute("UPDATE communication_logs SET status=?,resolution=?,customer_response=?,responded_at=? WHERE communication_id=?", (status, res, cr, ra, comm_id))
            self.db.commit()
        except Exception:
            pass

    @staticmethod
    def _map_status(s):
        return {"completed": "call_completed", "failed": "call_failed", "no_answer": "call_no_answer"}.get(s, "call_initiated")

    @staticmethod
    def _derive_resolution(issue_type, content):
        if issue_type == "address_enrichment":
            return "address_updated"
        if issue_type == "cod_to_prepaid":
            lo = (content or "").lower()
            if any(k in lo for k in ["yes", "pay", "prepaid", "switch"]):
                return "payment_converted"
        return "no_resolution"

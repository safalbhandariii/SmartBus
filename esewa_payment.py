"""
esewa_payment.py
-----------------
Real eSewa ePay v2 (UAT/sandbox) integration for SmartBus.

How it works (per eSewa's official flow):
  1. We build a signed payment request (HMAC-SHA256) and open it in the
     user's default browser, auto-submitting a POST form to eSewa's
     sandbox endpoint.
  2. eSewa shows its own login page (test credentials below) where the
     user completes the payment.
  3. eSewa redirects the browser back to a "success_url" we control,
     with the result encoded in the URL. Since eSewa needs a real
     reachable URL to redirect to, we run a tiny local HTTP server
     (127.0.0.1) to catch that redirect.
  4. We decode + verify the returned signature, confirm the amount
     matches what we requested, and report success/failure back to
     the Tkinter app.

TEST CREDENTIALS (sandbox only — safe to use, publicly documented by eSewa):
  eSewa ID : 9806800001  (or ...002/003/004/005)
  Password : Nepal@123
  MPIN     : 1122
  OTP      : 123456

These are NOT secrets in the security sense — this is eSewa's public
UAT sandbox. Do not use this file's constants for a real production
integration; swap PRODUCT_CODE / SECRET_KEY / BASE_URL for your real
merchant credentials from eSewa when going live (see README section
this module's docstring links to).
"""

import hmac
import hashlib
import base64
import json
import threading
import webbrowser
import http.server
import socketserver
import urllib.parse
import time
import uuid as uuid_lib

# ---------------- Sandbox configuration (official eSewa UAT values) ----------------

PRODUCT_CODE = "EPAYTEST"
SECRET_KEY = "8gBm/:&EnhH.1/q"
ESEWA_FORM_URL = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
ESEWA_STATUS_CHECK_URL = "https://rc.esewa.com.np/api/epay/transaction/status/"

LOCAL_CALLBACK_HOST = "127.0.0.1"
LOCAL_CALLBACK_PORT = 8901
SUCCESS_URL = f"http://{LOCAL_CALLBACK_HOST}:{LOCAL_CALLBACK_PORT}/success"
FAILURE_URL = f"http://{LOCAL_CALLBACK_HOST}:{LOCAL_CALLBACK_PORT}/failure"


def _generate_signature(total_amount, transaction_uuid, product_code=PRODUCT_CODE):
    """HMAC-SHA256, base64-encoded, over the exact field order eSewa requires."""
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    digest = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _make_transaction_uuid():
    """Unique per-transaction ID, alphanumeric + hyphen only (eSewa requirement)."""
    return f"smartbus-{int(time.time())}-{uuid_lib.uuid4().hex[:8]}"


class _CallbackResult:
    """Shared box the HTTP handler writes into, and the caller polls."""
    def __init__(self):
        self.received = False
        self.success = False
        self.data = None
        self.error = None


def _build_callback_server(result_box, expected_uuid, expected_amount):
    """
    Spins up a one-shot local HTTP server that:
      - serves /success and /failure (eSewa redirects the browser here)
      - shows the user a plain confirmation page
      - decodes + verifies the returned payload, stores it in result_box
      - shuts itself down after handling exactly one request
    """

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # keep the terminal quiet

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)

            if parsed.path == "/success":
                qs = urllib.parse.parse_qs(parsed.query)
                encoded_data = qs.get("data", [None])[0]

                if not encoded_data:
                    result_box.success = False
                    result_box.error = "No data received from eSewa."
                else:
                    try:
                        decoded = base64.b64decode(encoded_data).decode()
                        payload = json.loads(decoded)

                        # Verify signature ourselves before trusting anything
                        signed_fields = payload.get("signed_field_names", "").split(",")
                        message = ",".join(f"{field}={payload.get(field)}" for field in signed_fields)
                        expected_sig = base64.b64encode(
                            hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
                        ).decode()

                        sig_ok = hmac.compare_digest(expected_sig, payload.get("signature", ""))
                        uuid_ok = payload.get("transaction_uuid") == expected_uuid
                        amount_ok = float(payload.get("total_amount", -1)) == float(expected_amount)
                        status_ok = payload.get("status") == "COMPLETE"

                        if sig_ok and uuid_ok and amount_ok and status_ok:
                            result_box.success = True
                            result_box.data = payload
                        else:
                            result_box.success = False
                            result_box.error = (
                                f"Verification failed (sig_ok={sig_ok}, uuid_ok={uuid_ok}, "
                                f"amount_ok={amount_ok}, status_ok={status_ok})"
                            )
                    except Exception as e:
                        result_box.success = False
                        result_box.error = f"Could not parse eSewa response: {e}"

                result_box.received = True
                self._send_page("Payment Successful" if result_box.success else "Payment Verification Failed")

            elif parsed.path == "/failure":
                result_box.received = True
                result_box.success = False
                result_box.error = "Payment was cancelled or failed at eSewa."
                self._send_page("Payment Failed / Cancelled")

            else:
                self.send_response(404)
                self.end_headers()

        def _send_page(self, title):
            body = f"""
            <html><body style="font-family:sans-serif;text-align:center;padding-top:80px;">
            <h2>{title}</h2>
            <p>You can close this tab and return to SmartBus.</p>
            </body></html>
            """.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return socketserver.TCPServer((LOCAL_CALLBACK_HOST, LOCAL_CALLBACK_PORT), Handler)


def start_esewa_payment(amount, on_complete):
    """
    Kicks off a real eSewa sandbox payment for `amount` (NPR, numeric).
    Opens the browser to eSewa's payment page. `on_complete` is called
    from a background thread once the result is known, with args:
        on_complete(success: bool, info: dict | None, error: str | None)

    Caller (Tkinter code) should marshal back to the main thread itself
    (e.g. via `root.after(0, ...)`) since this callback fires off-thread.
    """
    amount = round(float(amount), 2)
    transaction_uuid = _make_transaction_uuid()
    signature = _generate_signature(amount, transaction_uuid)

    # Build an auto-submitting HTML form and open it in the default browser.
    # (eSewa's endpoint only accepts POST, so we can't just open a GET URL.)
    form_html = f"""
    <html><body onload="document.forms[0].submit()">
    <form action="{ESEWA_FORM_URL}" method="POST">
        <input type="hidden" name="amount" value="{amount}">
        <input type="hidden" name="tax_amount" value="0">
        <input type="hidden" name="total_amount" value="{amount}">
        <input type="hidden" name="transaction_uuid" value="{transaction_uuid}">
        <input type="hidden" name="product_code" value="{PRODUCT_CODE}">
        <input type="hidden" name="product_service_charge" value="0">
        <input type="hidden" name="product_delivery_charge" value="0">
        <input type="hidden" name="success_url" value="{SUCCESS_URL}">
        <input type="hidden" name="failure_url" value="{FAILURE_URL}">
        <input type="hidden" name="signed_field_names" value="total_amount,transaction_uuid,product_code">
        <input type="hidden" name="signature" value="{signature}">
    </form>
    <p style="font-family:sans-serif;text-align:center;">Redirecting to eSewa…</p>
    </body></html>
    """

    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w") as f:
        f.write(form_html)

    result_box = _CallbackResult()

    def run_server_and_wait():
        try:
            server = _build_callback_server(result_box, transaction_uuid, amount)
        except OSError as e:
            on_complete(False, None, f"Could not start local callback server: {e}")
            return

        server.timeout = 300  # 5 minutes, matching eSewa's own session timeout
        webbrowser.open(f"file://{path}")

        # Handle exactly one request (the success or failure redirect), then stop.
        server.handle_request()
        server.server_close()

        if not result_box.received:
            on_complete(False, None, "Timed out waiting for eSewa response.")
        else:
            on_complete(result_box.success, result_box.data, result_box.error)

    thread = threading.Thread(target=run_server_and_wait, daemon=True)
    thread.start()
    return transaction_uuid


def check_transaction_status(transaction_uuid, total_amount):
    """
    Optional: query eSewa directly for a transaction's status, useful if
    the redirect callback was missed (e.g. browser closed early).
    Returns the parsed JSON response, or None on network failure.
    """
    import urllib.request

    params = urllib.parse.urlencode({
        "product_code": PRODUCT_CODE,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
    })
    url = f"{ESEWA_STATUS_CHECK_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None

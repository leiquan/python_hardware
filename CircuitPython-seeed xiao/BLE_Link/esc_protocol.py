"""Transport-independent ESC protocol. CPython/CircuitPython; no hardware imports."""
import json


class SimulatedESC:
    """Only execution layer shipped. stop() must be idempotent in future drivers."""
    mode = "simulation"

    def __init__(self):
        self.throttle = 0

    def set_throttle(self, value):
        self.throttle = value

    def stop(self):
        self.throttle = 0


class Controller:
    TIMEOUT = 1.5
    MAX_ID = 2147483647

    def __init__(self, driver, clock, session):
        self.driver = driver
        self.clock = clock
        self.session = session
        self.state = "DISARMED"
        self.reason = "startup"
        self.last_control = clock()
        self.last_id = -1
        self.last_request = None
        self.driver.stop()

    def stop(self, reason, emergency=False):
        self.driver.stop()
        if emergency or self.state != "ESTOP":
            self.state = "ESTOP" if emergency else "DISARMED"
        self.reason = reason

    def tick(self):
        if self.state == "ARMED" and self.clock() - self.last_control >= self.TIMEOUT:
            self.stop("command_timeout")

    def disconnect(self):
        self.stop("disconnect")

    def snapshot(self):
        return {"state": self.state, "throttle": self.driver.throttle,
                "mode": self.driver.mode, "reason": self.reason,
                "session": self.session, "timeout_ms": 1500}

    def handle(self, request):
        self.tick()
        rid = request.get("id") if isinstance(request, dict) else None
        def reply(ok, error=None, duplicate=False):
            result = {"id": rid, "ok": ok, "control": self.snapshot()}
            if error:
                result["error"] = error
            if duplicate:
                result["duplicate"] = True
            return result
        if not isinstance(request, dict) or type(rid) is not int or not 0 <= rid <= self.MAX_ID:
            return reply(False, "INVALID_ID")
        cmd = request.get("cmd")
        # Stops are always applied, including stale/session-mismatched requests.
        if cmd in ("ESTOP", "DISARM"):
            self.stop("emergency_stop" if cmd == "ESTOP" else "requested_stop", cmd == "ESTOP")
            self.last_id = max(self.last_id, rid)
            self.last_request = None
            return reply(True)
        if request.get("v") != 1 or type(request.get("v")) is not int:
            return reply(False, "INVALID_VERSION")
        if cmd == "STATUS":
            return reply(True)
        if request.get("session") != self.session:
            return reply(False, "INVALID_SESSION")
        if rid <= self.last_id:
            if rid == self.last_id and request == self.last_request:
                return reply(True, duplicate=True)  # Current state; never refresh lease.
            return reply(False, "STALE_OR_CONFLICTING_ID")
        if cmd not in ("ARM", "SET_THROTTLE", "RESET_ESTOP"):
            return reply(False, "UNKNOWN_COMMAND")
        allowed = {"id", "v", "cmd", "session"}
        if cmd in ("ARM", "SET_THROTTLE"):
            allowed.add("throttle")
            value = request.get("throttle")
            if type(value) is not int or not 0 <= value <= 1000:
                return reply(False, "INVALID_THROTTLE")
            if cmd == "ARM" and value != 0:
                return reply(False, "ARM_REQUIRES_ZERO")
        if set(request) != allowed:
            return reply(False, "INVALID_FIELDS")
        if cmd == "RESET_ESTOP":
            if self.state != "ESTOP":
                return reply(False, "NOT_ESTOP")
            self.state = "DISARMED"
            self.driver.stop()
            self.reason = "estop_reset"
        elif cmd == "ARM":
            if self.state != "DISARMED":
                return reply(False, "NOT_DISARMED")
            self.driver.stop()
            self.state = "ARMED"
            self.reason = "armed"
            self.last_control = self.clock()
        else:
            if self.state != "ARMED":
                return reply(False, "NOT_ARMED")
            self.driver.set_throttle(value)
            self.last_control = self.clock()
            self.reason = "throttle"
        self.last_id = rid
        self.last_request = dict(request)
        return reply(True)

    def frame(self, frame):
        try:
            request = json.loads(frame.decode("utf-8"))
        except (ValueError, UnicodeError, TypeError):
            return {"id": None, "ok": False, "error": "INVALID_JSON"}
        if isinstance(request, dict) and "cmd" not in request and "text" in request:
            rid, text = request.get("id"), request["text"]
            if type(rid) is int and 0 <= rid <= self.MAX_ID and isinstance(text, str) and len(text.encode("utf-8")) <= 512:
                return {"id": rid, "ok": True, "result": "来自 Xiao 开发板：" + text,
                        "bytes": len(text.encode("utf-8"))}
            return {"id": None, "ok": False, "error": "INVALID_TEXT"}
        return self.handle(request)

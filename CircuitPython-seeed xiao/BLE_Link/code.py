"""XIAO text BLE, v3: guarded reconnect loop + bounded recovery.

CircuitPython 10.x, adafruit_ble. Set ENABLE_WATCHDOG=False before REPL debugging:
nRF's hardware watchdog cannot be stopped after it has been enabled.
"""
import gc
import json
import time
import microcontroller
from watchdog import WatchDogMode
from adafruit_ble import BLERadio
from adafruit_ble.services import Service
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.characteristics.stream import StreamIn, StreamOut
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement


print("--- 串口连接测试开始 ---")

# Keep disabled during USB/REPL development: watchdog expiry enters CircuitPython
# safe mode, which deliberately skips main.py. Enable only with an explicit policy.
ENABLE_WATCHDOG = False
WATCHDOG_SECONDS = 20
MAX_RECOVERY_FAILURES = 5


class TextService(Service):
    uuid = VendorUUID("A8E00001-9D4B-4F2A-A8A6-6C33F8D11E01")
    rx = StreamIn(uuid=VendorUUID("A8E00002-9D4B-4F2A-A8A6-6C33F8D11E01"),
                  timeout=0.1, buffer_size=512)
    tx = StreamOut(uuid=VendorUUID("A8E00003-9D4B-4F2A-A8A6-6C33F8D11E01"),
                   timeout=1.0, buffer_size=512)


class LinkLost(Exception):
    """The current transport session cannot be reused."""
    pass


def process_text(text):
    return "来自 Xiao 开发板：" + text


def response_for(frame):
    """Only validate/process the message here; transport exceptions stay outside."""
    request_id = None
    try:
        request = json.loads(frame.decode("utf-8"))
        if not isinstance(request, dict):
            raise ValueError("Expected JSON object")
        request_id = request.get("id")
        text = request.get("text")
        if not isinstance(request_id, int) or not isinstance(text, str):
            raise ValueError("Expected integer id and string text")
        size = len(text.encode("utf-8"))
        if size > 512:
            raise ValueError("Text exceeds 512 UTF-8 bytes")
        print("RX:", text)
        result = process_text(text)
        return {"id": request_id, "ok": True, "result": result, "bytes": size}
    except (ValueError, UnicodeError, TypeError) as exc:
        return {"id": request_id, "ok": False, "error": str(exc)}


def feed():
    if ENABLE_WATCHDOG:
        microcontroller.watchdog.feed()


def pause(seconds):
    """Keep the watchdog alive during intentional waits, not blocked BLE calls."""
    feed()
    time.sleep(seconds)


def restart(reason):
    print("[RECOVERY] Restarting board:", reason)
    microcontroller.reset()
    # reset() does not normally return. Do not keep feeding a stalled board.
    while True:
        time.sleep(1)


def reply(ble, service, obj):
    wire = (json.dumps(obj) + "\n").encode("utf-8")
    for start in range(0, len(wire), 20):
        feed()
        if not ble.connected:
            # Abort the whole session; never continue an old reply on a new link.
            raise LinkLost("Disconnected during reply")
        service.tx.write(wire[start:start + 20])
        pause(0.015)
    if obj.get("ok"):
        print("TX:", obj["result"])


def serve(ble, service):
    # These variables belong to one connection only.
    pending = bytearray()
    dropping = False
    last_byte = time.monotonic()
    while ble.connected:
        feed()
        count = service.rx.in_waiting
        if count:
            data = service.rx.read(min(count, 128))
            if data:
                last_byte = time.monotonic()
            for value in data or b"":
                if value == 10:
                    if dropping:
                        response = {"id": None, "ok": False,
                                    "error": "Frame exceeds 4096 bytes"}
                    else:
                        response = response_for(bytes(pending))
                    pending = bytearray()
                    dropping = False
                    reply(ble, service, response)
                elif not dropping:
                    pending.append(value)
                    if len(pending) > 4096:
                        pending = bytearray()
                        dropping = True
        if (pending or dropping) and time.monotonic() - last_byte > 10:
            raise LinkLost("Incomplete request timed out")
        pause(0.005)


def disconnect_all(ble):
    # Disconnect is asynchronous; wait for completion before restarting advertising.
    for connection in ble.connections:
        try:
            connection.disconnect()
        except Exception as exc:
            print("[RECOVERY] Disconnect request:", repr(exc))
    end = time.monotonic() + 3
    while ble.connected:
        if time.monotonic() >= end:
            raise LinkLost("Link did not close within 3 seconds")
        pause(0.02)
    if ble.advertising:
        ble.stop_advertising()
    pause(0.25)


def run(ble, service, advertisement, scan_response):
    failures = 0
    while True:
        try:
            feed()
            disconnect_all(ble)
            # Clear old RX bytes only after the old link has gone, before advertising.
            service.rx.reset_input_buffer()
            gc.collect()
            ble.start_advertising(advertisement, scan_response=scan_response)
            print("[ADVERTISING] XIAO-Text; advertising:", ble.advertising)
            while not ble.connected:
                # Some stacks stop advertising without throwing: restart it here too.
                if not ble.advertising:
                    ble.start_advertising(advertisement, scan_response=scan_response)
                    print("[ADVERTISING] Restored")
                pause(0.02)
            if ble.advertising:
                ble.stop_advertising()
            print("[CONNECTED] iPhone connected")
            serve(ble, service)
            failures = 0
            print("[DISCONNECTED] Preparing to advertise again")
        except Exception as exc:
            failures += 1
            print("[RECOVERY] Error", failures, "of", MAX_RECOVERY_FAILURES, repr(exc))
            if failures >= MAX_RECOVERY_FAILURES:
                restart("Repeated BLE errors")
            # Every cleanup operation is guarded. Retry even if this cleanup fails.
            try:
                disconnect_all(ble)
            except Exception as cleanup_error:
                print("[RECOVERY] Cleanup failed:", repr(cleanup_error))
            pause(min(failures * 0.25, 1.0))


def main():
    print("XIAO-Text recovery v3")
    if ENABLE_WATCHDOG:
        microcontroller.watchdog.timeout = WATCHDOG_SECONDS
        microcontroller.watchdog.mode = WatchDogMode.RESET
        feed()
        print("[WATCHDOG] Enabled, timeout:", WATCHDOG_SECONDS)
    else:
        print("[WATCHDOG] Disabled for USB/REPL development")
    ble = BLERadio()
    ble.name = "XIAO-Text"
    service = TextService()
    advertisement = ProvideServicesAdvertisement(service)
    advertisement.short_name = "XIAO"
    scan_response = Advertisement()
    scan_response.complete_name = "XIAO-Text"
    print("Advertising packet:", bytes(advertisement))
    run(ble, service, advertisement, scan_response)


if __name__ == "__main__":
    main()

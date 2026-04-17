"""
macOS hotkey helpers.
"""

import time

import AppKit
import Quartz


KEY_CODES = {
    "enter": 0x24,
    "return": 0x24,
    "tab": 0x30,
    "space": 0x31,
    "delete": 0x33,
    "escape": 0x35,
    "command": 0x37,
    "shift": 0x38,
    "capslock": 0x39,
    "option": 0x3A,
    "alt": 0x3A,
    "control": 0x3B,
    "rightshift": 0x3C,
    "rightoption": 0x3D,
    "rightcontrol": 0x3E,
    "function": 0x3F,
    "leftarrow": 0x7B,
    "rightarrow": 0x7C,
    "downarrow": 0x7D,
    "uparrow": 0x7E,
    "a": 0x00,
    "b": 0x0B,
    "c": 0x08,
    "d": 0x02,
    "e": 0x0E,
    "f": 0x03,
    "g": 0x05,
    "h": 0x04,
    "i": 0x22,
    "j": 0x26,
    "k": 0x28,
    "l": 0x25,
    "m": 0x2E,
    "n": 0x2D,
    "o": 0x1F,
    "p": 0x23,
    "q": 0x0C,
    "r": 0x0F,
    "s": 0x01,
    "t": 0x11,
    "u": 0x20,
    "v": 0x09,
    "w": 0x0D,
    "x": 0x07,
    "y": 0x10,
    "z": 0x06,
    "0": 0x1D,
    "1": 0x12,
    "2": 0x13,
    "3": 0x14,
    "4": 0x15,
    "5": 0x17,
    "6": 0x16,
    "7": 0x1A,
    "8": 0x1C,
    "9": 0x19,
}

def _quartz_flag(*names: str, default: int) -> int:
    """
    Resolve Quartz event flag constants across PyObjC versions.

    Different versions expose slightly different symbol names. We prefer the
    modern ``kCGEventFlagMask*`` names and fall back to literal bit masks.
    """
    for name in names:
        if hasattr(Quartz, name):
            return getattr(Quartz, name)
    return default


MODIFIER_FLAGS = {
    "command": _quartz_flag("kCGEventFlagMaskCommand", default=0x00100000),
    "cmd": _quartz_flag("kCGEventFlagMaskCommand", default=0x00100000),
    "shift": _quartz_flag("kCGEventFlagMaskShift", default=0x00020000),
    "control": _quartz_flag("kCGEventFlagMaskControl", default=0x00040000),
    "ctrl": _quartz_flag("kCGEventFlagMaskControl", default=0x00040000),
    "option": _quartz_flag("kCGEventFlagMaskAlternate", default=0x00080000),
    "alt": _quartz_flag("kCGEventFlagMaskAlternate", default=0x00080000),
    "function": _quartz_flag("kCGEventFlagMaskSecondaryFn", default=0x00800000),
}


def _contains_lark_identity(name: str, bundle_id: str) -> bool:
    """Whether app metadata suggests this is a Lark/Feishu-related process."""
    text = f"{name} {bundle_id}".lower()
    return any(token in text for token in ("lark", "feishu", "飞书"))


def _is_background_helper(name: str, bundle_id: str) -> bool:
    """Detect helper/updater/agent processes that should not receive shortcuts."""
    text = f"{name} {bundle_id}".lower()
    helper_tokens = (
        "helper",
        "updater",
        "update",
        "crash",
        "agent",
        "service",
        "renderer",
        "gpu",
        "plugin",
    )
    return any(token in text for token in helper_tokens)


def _app_score(app) -> int:
    """Rank candidate apps so we can pick the best foreground Lark target."""
    name = (app.localizedName() or "").strip()
    bundle_id = (app.bundleIdentifier() or "").strip()

    if not _contains_lark_identity(name, bundle_id):
        return -10_000

    score = 0
    text = f"{name} {bundle_id}".lower()

    if name.lower() in ("lark", "feishu", "飞书"):
        score += 100
    elif "lark" in name.lower() or "feishu" in name.lower() or "飞书" in name:
        score += 50

    if _is_background_helper(name, bundle_id):
        score -= 120

    # Prefer regular foreground apps.
    if app.activationPolicy() == AppKit.NSApplicationActivationPolicyRegular:
        score += 20
    else:
        score -= 20

    if ".helper" in text:
        score -= 80

    return score


def activate_lark_app() -> bool:
    """Bring the Lark application to the foreground."""
    try:
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()

        candidates = []
        for app in running_apps:
            score = _app_score(app)
            if score > -10_000:
                candidates.append((score, app))

        if not candidates:
            print("未找到飞书应用")
            return False

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_app = candidates[0]

        # If the best candidate still looks like helper, bail out explicitly.
        best_name = (best_app.localizedName() or "").strip()
        best_bundle = (best_app.bundleIdentifier() or "").strip()
        if _is_background_helper(best_name, best_bundle):
            print(f"找到的飞书进程看起来是后台进程，已跳过: {best_name} ({best_bundle})")
            return False

        best_app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
        print(
            "已激活飞书应用："
            f"{best_name} "
            f"(pid={best_app.processIdentifier()}, score={best_score})"
        )
        time.sleep(0.3)
        return True
    except Exception as exc:
        print(f"激活飞书应用失败：{exc}")
        return False


def press(key: str) -> None:
    """Press a single key."""
    key_code = KEY_CODES.get(key.lower())
    if key_code is None:
        if len(key) == 1:
            type_string(key)
            return
        print(f"未知键：{key}")
        return

    key_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
    key_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)
    print(f"按键：{key}")


def hotkey(*keys) -> None:
    """Press a hotkey combination."""
    modifiers = []
    normal_keys = []

    for key in keys:
        key_name = key.lower()
        if key_name in MODIFIER_FLAGS:
            modifiers.append(key_name)
        else:
            normal_keys.append(key_name)

    modifier_flags = 0
    for modifier in modifiers:
        modifier_flags |= MODIFIER_FLAGS[modifier]

    for modifier in modifiers:
        modifier_code = KEY_CODES.get(modifier)
        if modifier_code:
            key_down = Quartz.CGEventCreateKeyboardEvent(None, modifier_code, True)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
            time.sleep(0.05)

    for key_name in normal_keys:
        key_code = KEY_CODES.get(key_name)
        if key_code is None:
            continue

        key_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
        if modifier_flags:
            Quartz.CGEventSetFlags(key_down, modifier_flags)
        key_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)

        Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

    for modifier in reversed(modifiers):
        modifier_code = KEY_CODES.get(modifier)
        if modifier_code:
            key_up = Quartz.CGEventCreateKeyboardEvent(None, modifier_code, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)
            time.sleep(0.05)

    print(f"组合键：{'+'.join(keys)}")


def type_string(text: str) -> None:
    """Type a short Unicode string."""
    for char in text:
        key_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        Quartz.CGEventKeyboardSetUnicodeString(key_down, len(char), char)
        key_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(key_up, len(char), char)

        Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

    print(f"输入文本：{text}")


def open_search(window_info: dict | None = None) -> None:
    """Open the Lark search input with Cmd+K."""
    del window_info
    activated = activate_lark_app()
    if not activated:
        print("警告：未能确认激活主飞书应用，仍尝试发送 Cmd+K")
    hotkey("command", "k")
    time.sleep(0.5)


def send_message() -> None:
    """Send the current message."""
    press("enter")


def delete_text(count: int = 1) -> None:
    """Delete characters with the delete key."""
    for _ in range(count):
        press("delete")
        time.sleep(0.05)


if __name__ == "__main__":
    print("测试：按 Cmd+K...")
    time.sleep(1)
    open_search()

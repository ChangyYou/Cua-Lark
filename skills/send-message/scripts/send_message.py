"""
Send-message skill runtime adapter.

This is the canonical runtime script for the send-message skill.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"

DEFAULT_NAME = "send-message"
DEFAULT_DESCRIPTION = (
    "Use when user asks to send a message to a contact in Lark."
)

SEND_TRIGGER_PATTERN = r"(?:帮我)?给(?P<recipient>.+?)(?:发送|发消息说|发消息|发|说)(?P<message>.+)$"

STAGE_OPEN_SEARCH = 0
STAGE_INPUT_RECIPIENT = 1
STAGE_CLICK_RECIPIENT = 2
STAGE_INPUT_MESSAGE = 3
STAGE_SEND_ENTER = 4
STAGE_DONE = 5


@dataclass(frozen=True)
class SkillDoc:
    """Skill markdown data loaded from SKILL.md."""

    name: str
    description: str
    body: str


def _clean_text(value: str) -> str:
    return value.strip().strip(" ：:，,。！？!?")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def load_skill_doc() -> SkillDoc:
    """Parse codex-style SKILL.md with optional frontmatter."""
    try:
        raw = SKILL_MD.read_text(encoding="utf-8")
    except OSError:
        return SkillDoc(name=DEFAULT_NAME, description=DEFAULT_DESCRIPTION, body="")

    text = raw.strip()
    if not text.startswith("---"):
        return SkillDoc(name=DEFAULT_NAME, description=DEFAULT_DESCRIPTION, body=text)

    lines = text.splitlines()
    if len(lines) < 3:
        return SkillDoc(name=DEFAULT_NAME, description=DEFAULT_DESCRIPTION, body=text)

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return SkillDoc(name=DEFAULT_NAME, description=DEFAULT_DESCRIPTION, body=text)

    fields: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = _strip_quotes(value)

    body = "\n".join(lines[end_index + 1 :]).strip()
    name = fields.get("name") or DEFAULT_NAME
    description = fields.get("description") or DEFAULT_DESCRIPTION
    return SkillDoc(name=name, description=description, body=body)


def match_send_intent(user_command: str) -> dict[str, str] | None:
    """Extract recipient and message when command matches send-message pattern."""
    text = (user_command or "").strip()
    if not text:
        return None

    match = re.search(SEND_TRIGGER_PATTERN, text)
    if not match:
        return None

    recipient = _clean_text(match.group("recipient"))
    message = _clean_text(match.group("message"))
    if not recipient or not message:
        return None
    return {"recipient": recipient, "message": message}


@dataclass
class SendMessageSkill:
    """Prompt + gate hybrid skill to reduce wrong-contact sends."""

    recipient: str
    message: str
    doc: SkillDoc
    stage: int = STAGE_OPEN_SEARCH
    contact_click_retry: int = 0

    @property
    def name(self) -> str:
        return self.doc.name

    @property
    def description(self) -> str:
        return self.doc.description

    @property
    def trigger_condition(self) -> str:
        return SEND_TRIGGER_PATTERN

    @classmethod
    def try_create(cls, user_command: str) -> "SendMessageSkill | None":
        intent = match_send_intent(user_command)
        if not intent:
            return None
        return cls(
            recipient=intent["recipient"],
            message=intent["message"],
            doc=load_skill_doc(),
        )

    def _guidance_block(self) -> str:
        return (
            f"[Active Skill]\n"
            f"name: {self.name}\n"
            f"description: {self.description}\n"
            f"trigger_condition: {self.trigger_condition}\n"
            f"recipient: {self.recipient}\n"
            f"message_intent: {self.message} (注意：这只是用户的意图摘要。如果是纯文本消息，请将其扩写为一句完整、自然、得体的问候语或通知。如果是发送表情包、图片等操作，你应该直接点击 UI 上对应的图标按钮来完成操作，不要仅仅输入文字。)\n\n"
            f"[Skill Main Content]\n{self.doc.body}"
        ).strip()

    def plan_guidance(self) -> str:
        return self._guidance_block()

    def react_guidance(self) -> str:
        stage_hint = {
            STAGE_OPEN_SEARCH: "下一步必须先打开搜索框（open_search 或 press_key(command+k/cmd+k/ctrl+k)）",
            STAGE_INPUT_RECIPIENT: f"下一步必须在搜索框输入联系人：{self.recipient}",
            STAGE_CLICK_RECIPIENT: "下一步必须点击搜索结果中的目标联系人（优先顶部精确匹配）",
            STAGE_INPUT_MESSAGE: f"已进入聊天窗口。若意图“{self.message}”是发送表情包，请直接点击输入框右侧的表情图标打开面板并选择；若是文本，请直接输入一句完整、得体的社交语言。不要强行把非文本意图转成文字。",
            STAGE_SEND_ENTER: "下一步必须按回车发送（如果前面是点击发送按钮或点击表情发送的，也可以直接 done）",
            STAGE_DONE: "下一步必须 done",
        }.get(self.stage, "按目标继续")
        click_policy = (
            "[Click Policy]\n"
            f"- 目标联系人必须是“{self.recipient}”精确匹配。\n"
            "- 只能点击“联系人”结果行，不要点群聊/话题/文档结果。\n"
            "- 优先点击联系人结果第一条（通常位于搜索结果上方）。\n"
            "- 不确定时先 wait 或重新搜索，不要盲点。"
        )
        return f"{self._guidance_block()}\n\n[Stage Constraint]\n{stage_hint}\n\n{click_policy}"

    @staticmethod
    def _is_open_search_action(action: dict[str, object]) -> bool:
        action_type = str(action.get("action", "")).lower()
        if action_type == "open_search":
            return True
        if action_type != "press_key":
            return False
        key = str(action.get("key", "")).lower().strip()
        return key in ("command+k", "cmd+k", "ctrl+k", "control+k")

    def enforce_action(self, action: dict[str, object]) -> dict[str, object]:
        """Enforce minimal reliable sequence for send-message."""
        action_type = str(action.get("action", "")).lower().strip()

        if self.stage == STAGE_OPEN_SEARCH:
            if not self._is_open_search_action(action):
                print("技能门控(send-message)：先打开搜索框。")
                return {"action": "open_search", "reason": "skill gate: 打开搜索框"}
            return action

        if self.stage == STAGE_INPUT_RECIPIENT:
            text = str(action.get("text", ""))
            if not (action_type == "paste_content" and text == self.recipient):
                print("技能门控(send-message)：先在搜索框输入联系人。")
                return {
                    "action": "paste_content",
                    "text": self.recipient,
                    "reason": "skill gate: 在搜索框输入联系人",
                }
            return action

        if self.stage == STAGE_CLICK_RECIPIENT:
            if action_type != "click_position":
                print("技能门控(send-message)：先点击联系人搜索结果。")
                return {
                    "action": "wait",
                    "seconds": 0.8,
                    "reason": "skill gate: 等待并重新定位联系人结果",
                }
            try:
                y_ratio = float(action.get("y_ratio", 0))
            except (TypeError, ValueError):
                y_ratio = 0
            if y_ratio > 0.4 and self.contact_click_retry < 2:
                self.contact_click_retry += 1
                print("技能门控(send-message)：联系人点击位置偏低，优先点击搜索结果上方第一条精确联系人。")
                return {
                    "action": "wait",
                    "seconds": 0.8,
                    "reason": "skill gate: 重新定位上方联系人条目后再点击",
                }
            return action

        if self.stage == STAGE_INPUT_MESSAGE:
            # 放宽：如果大模型觉得此时需要点击（比如点击表情按钮、发送按钮等），直接放行
            if action_type == "click_position":
                print("技能门控(send-message)：允许大模型在聊天窗口内自由点击（如选择表情/文件）。")
                return action
            
            # 放宽：如果大模型需要等待（比如等待文件选择窗口加载），允许放行
            if action_type == "wait":
                print("技能门控(send-message)：允许大模型等待窗口加载。")
                return action
                
            # 只要是按键动作（如回车发送），也放行并进入下一阶段
            if action_type == "press_key":
                print("技能门控(send-message)：允许大模型按键操作。")
                return action
                
            # 允许大模型自主决定完成任务
            if action_type == "done":
                print("技能门控(send-message)：大模型判断任务已完成，放行。")
                return action
            
            # 只要是输入相关动作，就放宽拦截
            text = str(action.get("text", "")).strip()
            if action_type in ("paste_content", "input_text") and text:
                # 兼容修正：如果模型坚持使用 input_text，在这里把它转成系统支持中文的 paste_content
                if action_type == "input_text":
                    action = dict(action)
                    action["action"] = "paste_content"
                return action
                
            # 彻底放宽：如果大模型没有执行输入、点击、等待，才尝试用默认文本兜底
            print("技能门控(send-message)：兜底输入意图文字...")
            return {
                "action": "paste_content",
                "text": self.message,
                "reason": "skill gate: 输入消息内容兜底",
            }

        if self.stage == STAGE_SEND_ENTER:
            # 放宽：如果大模型还在自由发挥（比如还在点表情/选文件），继续放行
            if action_type in ("click_position", "wait", "paste_content"):
                return action
                
            # 兼容处理：如果大模型觉得选完表情直接就算发送完成了，或者还需要点一下发送按钮
            if action_type == "done":
                return action
                
            key = str(action.get("key", "")).lower().strip()
            if not (action_type == "press_key" and key in ("enter", "return")):
                print("技能门控(send-message)：按回车发送消息兜底。")
                return {"action": "press_key", "key": "enter", "reason": "skill gate: 回车发送兜底"}
            return action

        if action_type != "done":
            print("技能门控(send-message)：流程结束，仅允许 done。")
            return {"action": "done", "reason": "skill gate: 发送流程完成"}
        return action

    def on_action_result(self, action: dict[str, object], success: bool) -> None:
        if not success:
            return

        action_type = str(action.get("action", "")).lower().strip()
        if self.stage == STAGE_OPEN_SEARCH and self._is_open_search_action(action):
            self.stage = STAGE_INPUT_RECIPIENT
            return
        if self.stage == STAGE_INPUT_RECIPIENT and action_type in ("input_text", "paste_content"):
            self.stage = STAGE_CLICK_RECIPIENT
            self.contact_click_retry = 0
            return
        if self.stage == STAGE_CLICK_RECIPIENT and action_type == "click_position":
            self.stage = STAGE_INPUT_MESSAGE
            return
        if self.stage == STAGE_INPUT_MESSAGE and action_type in ("input_text", "paste_content", "click_position", "wait", "press_key", "done"):
            # 如果大模型使用了输入文字操作，我们认为输入阶段完毕，进入发送阶段
            if action_type in ("input_text", "paste_content"):
                self.stage = STAGE_SEND_ENTER
            # 如果大模型觉得已经搞定了，直接允许它完成任务
            elif action_type == "done":
                self.stage = STAGE_DONE
            # 如果是 click_position / wait / press_key，大模型可能在选文件/表情，保持在当前阶段
            return
        if self.stage == STAGE_SEND_ENTER and action_type in ("press_key", "done"):
            self.stage = STAGE_DONE

    def allow_done(self) -> bool:
        return self.stage >= STAGE_DONE


def describe_send_message_skill() -> dict[str, str]:
    """Static descriptor for catalog text and router prompt."""
    doc = load_skill_doc()
    return {
        "name": doc.name,
        "description": doc.description,
        "trigger_condition": SEND_TRIGGER_PATTERN,
    }


__all__ = [
    "SendMessageSkill",
    "describe_send_message_skill",
]


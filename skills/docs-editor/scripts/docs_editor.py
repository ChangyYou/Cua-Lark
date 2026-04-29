"""
Docs-editor skill runtime adapter.

This is the canonical runtime script for the docs-editor skill.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"

DEFAULT_NAME = "docs-editor"
DEFAULT_DESCRIPTION = (
    "Use when user asks to edit or insert content in a Feishu Document."
)

DOCS_EDIT_TRIGGER_PATTERN = r"(?:在文档|文档里|文档中|补充|插入|修改|填写).+(?:内容|表格|待办|图片|文字|产出)"

STAGE_OPEN_SEARCH = 0
STAGE_INPUT_DOC_NAME = 1
STAGE_CLICK_DOC = 2
STAGE_ACTIVATING_DOC = 3
STAGE_EDIT_DOC = 4
STAGE_DONE = 5

@dataclass(frozen=True)
class SkillDoc:
    """Skill markdown data loaded from SKILL.md."""

    name: str
    description: str
    body: str

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

def match_docs_intent(user_command: str) -> dict[str, str] | None:
    text = (user_command or "").strip()
    if not text:
        return None
    
    # check trigger pattern or simple keyword
    if not re.search(DOCS_EDIT_TRIGGER_PATTERN, text) and "文档" not in text:
        return None

    doc_name = ""
    # Extract doc name if specified
    name_match = re.search(r"文档(?:中的?|里的?)?[“\"'](?P<doc_name>[^”\"']+)[\"”']", text)
    if name_match:
        doc_name = name_match.group("doc_name").strip()
        
    return {"doc_name": doc_name, "intent": text}

@dataclass
class DocsEditorSkill:
    """Keyboard-driven document editing skill to avoid mouse coordinate drift."""

    doc: SkillDoc
    target_doc: str = ""
    edit_intent: str = ""
    stage: int = STAGE_EDIT_DOC
    _has_clicked_after_esc: bool = False  # 记录是否在退出搜索框后点过一次了
    
    @property
    def name(self) -> str:
        return self.doc.name

    @property
    def description(self) -> str:
        return self.doc.description

    @property
    def trigger_condition(self) -> str:
        return DOCS_EDIT_TRIGGER_PATTERN

    @classmethod
    def try_create(cls, user_command: str) -> "DocsEditorSkill | None":
        intent_data = match_docs_intent(user_command)
        if not intent_data:
            return None
            
        stage = STAGE_OPEN_SEARCH if intent_data["doc_name"] else STAGE_ACTIVATING_DOC
        return cls(
            doc=load_skill_doc(),
            target_doc=intent_data["doc_name"],
            edit_intent=intent_data["intent"],
            stage=stage
        )

    def _guidance_block(self) -> str:
        return (
            f"[Active Skill]\n"
            f"name: {self.name}\n"
            f"description: {self.description}\n"
            f"trigger_condition: {self.trigger_condition}\n\n"
            f"[Skill Main Content]\n{self.doc.body}"
        ).strip()

    def plan_guidance(self) -> str:
        """Provide guidance for the planning stage."""
        return (
            f"{self._guidance_block()}\n\n"
            "[Plan Constraint]\n"
            "因为当前激活了 docs-editor 技能，你的计划必须严格遵循以下固定步骤（请将这些步骤翻译为标准的 JSON plan 格式）：\n"
            "1. 第一步必须是打开飞书全局搜索框（执行 open_search 或者 press_key ctrl+k），绝对不要尝试鼠标点击导航栏。\n"
            "2. 在搜索框中输入目标文档的名称（input_text 或 paste_content）。\n"
            "3. 确认搜索并点击匹配的云文档以打开它。\n"
            "4. 点击文档正文的中心空白区域以激活编辑焦点。\n"
            "5. 按 ctrl+f 打开文档内搜索框，输入你要寻找的章节标题（例如：第二周期）。\n"
            "6. 按 enter 确认搜索，跳转到匹配项。\n"
            "7. 【极其重要】按 esc 退出文档内搜索框。\n"
            "8. 【极其重要】点击一下文档中的高亮词汇或空白处，将焦点真正激活到正文。\n"
            "9. 使用方向键（up/down/left/right）将光标精确移动到需要填写内容的地方。\n"
            "10. 填写你被要求输入的内容（input_text 或 paste_content）。\n"
            "11. 任务完成（done）。\n\n"
            "请直接将上述 11 个步骤转化为符合格式要求的初始计划，不要遗漏 esc 和点击激活焦点的步骤！"
        )

    def react_guidance(self) -> str:
        stage_hint = {
            STAGE_OPEN_SEARCH: "【阶段：寻找文档】下一步必须先打开全局搜索框（执行 open_search 或 press_key(command+k/cmd+k/ctrl+k)）。",
            STAGE_INPUT_DOC_NAME: f"【阶段：输入文档名】下一步必须在搜索框输入文档名称：{self.target_doc}（执行 paste_content 或 input_text）。",
            STAGE_CLICK_DOC: "【阶段：进入文档】下一步必须点击搜索结果中的目标文档以进入文档编辑区。\n🚫 核心视觉规则：绝对禁止点击最顶部的“飞书知识问答助手”或“AI总结”区域！\n✔️ 正确目标：请仔细向下观察，目标文档是一个带文档图标、具有明确标题的单行列表项。\n如果屏幕上被大面积的 AI 回答占据且看不到云文档列表，请务必先使用 scroll 向下滚动，直到看到带有图标的文档列表项后再使用 click_position。",
            STAGE_ACTIVATING_DOC: "【阶段：激活文档焦点】下一步必须点击文档正文的中心空白区域（例如 x_ratio=0.5, y_ratio=0.5）来强行激活文档的编辑焦点。\n在焦点激活前，不要尝试进行内容输入或搜索。",
            STAGE_EDIT_DOC: "【阶段：编辑文档】强制要求：所有在文档编辑区内的精准定位必须使用 ctrl+f 搜索。\n⭐搜索规范⭐：在 ctrl+f 输入关键词并按 enter 定位到目标后，你必须紧接着按 esc 退出搜索框。\n⚠️【极其重要】飞书的焦点机制要求：在按完 esc 退出搜索框之后，光标会丢失！因此，在按完 esc 之后，你必须再用 click_position 点击一下文档中的高亮词汇或空白处，才能真正把光标激活到正文中！不要在按完 esc 后直接按方向键，必须先点击一次！\n除了上述为了激活焦点的点击外，绝对禁止使用鼠标点击特定文本进行微操定位，微操必须由键盘（快捷键、方向键）完成。",
            STAGE_DONE: "【阶段：任务完成】下一步必须 done",
        }.get(self.stage, "按目标继续")
        
        return f"{self._guidance_block()}\n\n[Stage Constraint]\n{stage_hint}"

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
        """Enforce keyboard usage for document editing."""
        action_type = str(action.get("action", "")).lower().strip()
        
        if self.stage == STAGE_OPEN_SEARCH:
            if not self._is_open_search_action(action):
                print("技能门控(docs-editor)：寻找文档阶段，必须先打开搜索框。")
                return {"action": "open_search", "reason": "skill gate: 强制打开搜索框"}
            return action
            
        if self.stage == STAGE_INPUT_DOC_NAME:
            text = str(action.get("text", ""))
            if not (action_type in ("paste_content", "input_text") and text == self.target_doc):
                print(f"技能门控(docs-editor)：在搜索框输入文档名称 {self.target_doc}。")
                return {
                    "action": "paste_content",
                    "text": self.target_doc,
                    "reason": "skill gate: 强制输入文档名称"
                }
            return action
            
        if self.stage == STAGE_CLICK_DOC:
            if action_type not in ("click_position", "scroll", "wait"):
                print("技能门控(docs-editor)：请定位文档位置（可滑动）并点击。")
                return {"action": "wait", "seconds": 1.0, "reason": "skill gate: 等待或滑动以定位文档并点击"}
            # 放宽：如果大模型觉得此时需要等待（比如等待搜索结果加载），允许放行
            if action_type == "wait":
                print("技能门控(docs-editor)：允许大模型等待搜索结果加载。")
                return action
            return action
            
        if self.stage == STAGE_ACTIVATING_DOC:
            if action_type not in ("click_position", "wait"):
                print("技能门控(docs-editor)：必须先点击文档空白处激活焦点。")
                return {"action": "wait", "seconds": 1.0, "reason": "skill gate: 等待或点击空白处激活焦点"}
            return action

        if self.stage == STAGE_EDIT_DOC:
            # 监控 esc 按键，重置点击状态
            if action_type == "press_key" and str(action.get("key", "")).lower().strip() == "esc":
                self._has_clicked_after_esc = False
                return action
                
            # 强制拦截鼠标微操
            if action_type == "click_position":
                try:
                    y_ratio = float(action.get("y_ratio", 0))
                except (TypeError, ValueError):
                    y_ratio = 0
                
                if y_ratio > 0.15:
                    if not self._has_clicked_after_esc:
                        # 允许在刚退出搜索框时的第一次点击
                        print("⚠️ 技能门控(docs-editor)：检测到按完 esc 后的首次坐标点击。已允许该点击通过以激活焦点。")
                        self._has_clicked_after_esc = True
                        return action
                    else:
                        # 已经点过一次激活了，后续的点击全部拦截并报错，强制大模型自己决定按方向键
                        print("🚫 技能门控(docs-editor)：检测到重复的坐标点击！焦点已激活，请使用方向键微调！")
                        return {
                            "action": "wait",
                            "seconds": 1.0,
                            "reason": "skill gate 拦截: 你已经点击激活了光标。由于飞书光标可能较小，请不要怀疑自己，绝对禁止再次使用 click_position！如果当前位置不对，请必须且只能使用方向键（up/down/left/right）来移动光标！"
                        }
            
            return action
            
        return action

    def on_action_result(self, action: dict[str, object], success: bool) -> None:
        if not success:
            return
            
        action_type = str(action.get("action", "")).lower().strip()
        
        if self.stage == STAGE_OPEN_SEARCH and self._is_open_search_action(action):
            self.stage = STAGE_INPUT_DOC_NAME
            return
            
        if self.stage == STAGE_INPUT_DOC_NAME and action_type in ("input_text", "paste_content"):
            self.stage = STAGE_CLICK_DOC
            return
            
        # 修复之前的问题：增加延时状态流转或者放宽编辑阶段顶部的点击
        # 即使在这里切到了 STAGE_EDIT_DOC，我们在 enforce_action 里也应该允许在文档未加载完成时
        # 继续点击搜索结果，但这在上面的 enforce_action 中已经通过 y_ratio > 0.15 的条件限制了。
        # 如果还在搜索页，点击卡片通常 y_ratio 较大，会被误拦截。
        # 这里最稳妥的方式是：只有在确实完成了搜索意图并且有一定的时间间隔后才真正进入编辑状态，
        # 但既然您要求改回原来的流程，我们就原样恢复，因为您可能更倾向于用前面说的分两步执行（prompt engineering）来规避这个代码层面的死结。
        if self.stage == STAGE_CLICK_DOC and action_type == "click_position":
            self.stage = STAGE_ACTIVATING_DOC
            return
            
        if self.stage == STAGE_ACTIVATING_DOC and action_type == "click_position":
            self.stage = STAGE_EDIT_DOC
            return
            
        if self.stage == STAGE_EDIT_DOC and action_type == "done":
            self.stage = STAGE_DONE
            return

    def allow_done(self) -> bool:
        return self.stage >= STAGE_EDIT_DOC

def describe_docs_editor_skill() -> dict[str, str]:
    """Static descriptor for catalog text and router prompt."""
    doc = load_skill_doc()
    return {
        "name": doc.name,
        "description": doc.description,
        "trigger_condition": DOCS_EDIT_TRIGGER_PATTERN,
    }

__all__ = [
    "DocsEditorSkill",
    "describe_docs_editor_skill",
]

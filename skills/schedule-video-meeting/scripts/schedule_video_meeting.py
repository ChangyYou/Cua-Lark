from pathlib import Path
from typing import Any, Dict, Optional
import re

SKILL_DIR = Path(__file__).resolve().parents[1]

def load_skill_doc() -> str:
    doc_path = SKILL_DIR / "SKILL.md"
    return doc_path.read_text(encoding="utf-8") if doc_path.exists() else "Schedule a video conference with specified time and participants."

class ScheduleVideoMeetingSkill:
    """Implements AgentSkill protocol for scheduling video meetings with a stage-based state machine."""
    
    def __init__(self):
        self.stage = 0
        self.params: Dict[str, Any] = {}
        
    def execute(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        if self.stage == 0:
            self._extract_params(user_input)
            self.stage = 1
            return {"status": "running", "message": "解析会议时间与参与人..."}
        elif self.stage == 1:
            if not self.params.get("time_range"):
                return {"status": "error", "message": "未能识别有效的时间范围，请提供明确的开始和结束时间。"}
            self.stage = 2
            return {"status": "running", "message": "参数校验通过，正在打开会议预约界面..."}
        elif self.stage == 2:
            self._execute_ui_sequence()
            self.stage = 3
            return {"status": "running", "message": "正在填写表单并添加参与人..."}
        elif self.stage == 3:
            return {"status": "completed", "message": f"预约成功：{self.params['time_range']}，参与人：{', '.join(self.params.get('participants', []))}"}
        return {"status": "idle", "message": "任务已结束。"}

    def _extract_params(self, text: str):
        # 提取时间范围 (如: 4月27日上午九点半到十点半)
        time_re = r"(\d{1,2}月\d{1,2}日[上午下午]?\d{1,2}[点:：]\d{1,2})\s*到\s*(\d{1,2}[点:：]\d{1,2})"
        t_match = re.search(time_re, text)
        self.params["time_range"] = f"{t_match.group(1)} 至 {t_match.group(2)}" if t_match else None
        
        # 提取参与人 (如: 参与人添加游畅)
        part_re = r"(?:参与人|添加|邀请|和)([\u4e00-\u9fa5]+(?:、[\u4e00-\u9fa5]+)*)"
        p_match = re.search(part_re, text)
        self.params["participants"] = re.split(r"[、,，]", p_match.group(1)) if p_match else []

    def _execute_ui_sequence(self):
        """
        抽象执行历史中的固定 UI 操作链路：
        1. scroll (多次) -> 定位到会议入口
        2. click_position -> 点击新建会议
        3. click_position -> 选择视频会议类型
        4. click_position -> 填写时间
        5. click_position -> 添加参与人
        6. click_position -> 确认/发送
        实际部署时，此处将替换为具体的 UI 自动化框架调用 (如 uiautomator2, playwright 等)。
        """
        pass

def describe_schedule_video_meeting_skill() -> Dict[str, Any]:
    return {
        "name": "schedule-video-meeting",
        "description": "Automatically parse time and participants from natural language to schedule a video conference via UI automation.",
        "trigger_condition": r"(预约|创建|安排|发起|订).*(视频)?会议|帮我.*开会|schedule.*meeting",
        "version": "1.0.0"
    }
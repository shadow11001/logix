from openai import OpenAI
import json
from src.config import Config

class LogAnalyzer:
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def analyze(self, logs: str, model: str) -> dict:
        """
        Sends logs to the OpenRouter/LLM and returns a structured analysis.
        """
        system_prompt = """
        You are an expert Linux System Administrator AI. 
        Your task is to review the provided system logs, identify any errors, warnings, or anomalies, and suggest potential fixes.
        
        Output your analysis in valid JSON format with the following structure:
        {
            "has_issues": boolean,
            "summary": "Brief summary of the log status",
            "findings": [
                {
                    "log_entry": "The specific log line or block indicating the issue",
                    "severity": "critical|error|warning|info",
                    "explanation": "What this error means",
                    "suggested_fix": {
                        "description": "Human readable description of the fix",
                        "command": "The exact shell command to run to fix it (or null if unrelated to a command)",
                        "requires_sudo": boolean
                    }
                }
            ]
        }
        If existing logs are just information or empty, set has_issues to false.
        """

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[ 
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Logs to analyze:\n\n{logs}"}
                ],
                response_format={"type": "json_object"} # Force JSON if model supports it, but prompt helps too
            )
            
            content = response.choices[0].message.content
            # Basic cleanup if the model adds markdown code blocks around json
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)
        except Exception as e:
            return {
                "has_issues": True,
                "summary": f"Failed to analyze logs due to technical error: {str(e)}",
                "findings": []
            }

    def analyze_health(self, specs: dict, metrics: dict, logs: str, model: str) -> dict:
        """
        Analyzes system health metrics and logs to diagnose performance issues.
        """
        system_prompt = """
        You are an expert System Performance Analyst. 
        Your task is to analyze the provided system specifications, real-time metrics, and recent logs to diagnose lag, crashes, or bottlenecks.
        
        Output your analysis in valid JSON format with the following structure:
        {
            "has_issues": boolean,
            "overall_status": "Healthy|Degraded|Critical",
            "summary": "Executive summary of system health",
            "findings": [
                {
                    "issue": "High CPU Usage / Memory Leak / etc",
                    "severity": "critical|warning|info",
                    "evidence": "Description of the data point proving the issue",
                    "recommendation": "Technical recommendation to resolve the issue"
                }
            ]
        }
        """

        data_payload = json.dumps({
            "system_specs": specs,
            "performance_metrics": metrics,
            "recent_logs": logs
        }, indent=2)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[ 
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"System Health Data:\n\n{data_payload}"}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)
        except Exception as e:
            return {
                "has_issues": True,
                "overall_status": "Unknown",
                "summary": f"Failed to analyze health data: {str(e)}",
                "findings": []
            }
    def analyze_config(self, content: str, file_path: str, model: str, user_prompt: str = None) -> dict:
        """
        Analyzes a configuration file for syntax, security, and best practices.
        """
        system_prompt = f"""
        You are an expert DevOps Engineer and Security Specialist.
        Your task is to review the provided configuration file (path: {file_path}) for:
        1. Syntax errors.
        2. Security vulnerabilities (e.g., weak passwords, exposed keys, permissive permissions).
        3. Deprecated settings.
        4. Best practice violations.

        Output your analysis in valid JSON format:
        {{
            "has_issues": boolean,
            "summary": "Brief executive summary",
            "findings": [
                {{
                    "line_number": integer (or null if not applicable),
                    "parameter": "The specific config key/section",
                    "issue": "Description of the problem",
                    "severity": "critical|warning|info",
                    "suggestion": "How to fix it",
                    "suggested_value": "The optimized value (if applicable)"
                }}
            ]
        }}
        """

        user_content = f"Config File Content:\n\n{content}"
        if user_prompt:
            user_content += f"\n\nAdditional Instruction: {user_prompt}"

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[ 
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)
        except Exception as e:
            return {
                "has_issues": True,
                "summary": f"Failed to analyze config due to error: {str(e)}",
                "findings": []
            }

    def generate_config(self, prompt: str, model: str) -> dict:
        """
        Generates a configuration file based on the user's prompt.
        """
        system_prompt = """
        You are an expert DevOps Engineer.
        Your task is to generate a configuration file based on the user's requirements.
        Ensure the configuration is secure, follows lines best practices, and includes comments explaining key settings.
        
        Output valid JSON:
        {
            "content": "The full content of the generated configuration file"
        }
        """

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[ 
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}
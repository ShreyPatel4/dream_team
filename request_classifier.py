import json
import os
from enum import Enum
from typing import List, Optional

class RequestType(Enum):
    NEW_PROJECT = "NEW_PROJECT"
    CONTINUATION = "CONTINUATION"
    UNBLOCK = "UNBLOCK"
    NEW_PHASE = "NEW_PHASE"
    QUESTION = "QUESTION"
    ESCALATION = "ESCALATION"

class Project:
    def __init__(self, name: str, status: str, keywords: List[str]):
        self.name = name
        self.status = status
        self.keywords = keywords

class ProjectContext:
    def __init__(self, active_projects: List[Project]):
        self.active_projects = active_projects

class IncomingRequest:
    def __init__(self, raw_content: str, source: str):
        self.raw_content = raw_content
        self.source = source

class RequestClassifier:
    """Deterministic routing to categorize Slack intakes without using API calls."""

    def classify(self, request: IncomingRequest, context: ProjectContext) -> RequestType:
        # Match against active projects
        if context.active_projects:
            for project in context.active_projects:
                if self._matches_project(request.raw_content, project):
                    if project.status == "IN_SPRINT": return RequestType.CONTINUATION
                    elif project.status == "BLOCKED":  return RequestType.UNBLOCK
                    elif project.status == "COMPLETE": return RequestType.NEW_PHASE

        # Question detection
        question_signals = ["?", "what is", "how do", "can you explain",
                           "tell me about", "what's the status"]
        if any(s in request.raw_content.lower() for s in question_signals):
            return RequestType.QUESTION

        # Escalation source detection (if another agent triggered this)
        if request.source == "agent_escalation":
            return RequestType.ESCALATION

        return RequestType.NEW_PROJECT

    def _matches_project(self, content: str, project: Project) -> bool:
        keywords = [project.name.lower()] + [k.lower() for k in project.keywords]
        return any(kw in content.lower() for kw in keywords)

# Helper to load context
def load_project_context(json_path: str) -> ProjectContext:
    if not os.path.exists(json_path):
        return ProjectContext([])
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            projects = []
            for p in data.get("projects", []):
                projects.append(Project(p.get("name", ""), p.get("status", ""), p.get("keywords", [])))
            return ProjectContext(projects)
    except Exception as e:
        print(f"Error loading project context: {e}")
        return ProjectContext([])

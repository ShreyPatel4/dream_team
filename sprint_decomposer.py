from typing import List, Dict, Any
from collections import deque

class Task:
    def __init__(self, id: str, title: str, description: str, department: str, effort: str):
        self.id = id
        self.title = title
        self.description = description
        self.department = department
        self.effort = effort

class ExecutionPlan:
    def __init__(self, tasks: List[Task], task_dependencies: Dict[str, List[str]]):
        self.tasks = tasks
        self.task_dependencies = task_dependencies

class Sprint:
    def __init__(self, number: int, tasks: List[Task]):
        self.number = number
        self.tasks = tasks

class SprintDecomposer:
    """Mathematical topological sort to decouple dependencies into Sprints without LLM usage."""

    def _topological_sort(self, tasks: List[Task], dependencies: Dict[str, List[str]]) -> List[Task]:
        # Build graph and in-degrees
        graph = {task.id: [] for task in tasks}
        in_degree = {task.id: 0 for task in tasks}
        
        for tgt, sources in dependencies.items():
            for src in sources:
                if src in graph and tgt in in_degree:
                    graph[src].append(tgt)
                    in_degree[tgt] += 1
                    
        # Queue for nodes with 0 in-degree
        queue = deque([k for k, v in in_degree.items() if v == 0])
        sorted_ids = []
        
        while queue:
            node = queue.popleft()
            sorted_ids.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        # Map sorted IDs back to Task objects
        task_map = {t.id: t for t in tasks}
        # In case of cycles, append remaining tasks
        for t in tasks:
            if t.id not in sorted_ids:
                sorted_ids.append(t.id)

        return [task_map[tid] for tid in sorted_ids]

    def decompose(self, plan: ExecutionPlan, max_per_sprint: int = 10) -> List[Sprint]:
        sorted_tasks = self._topological_sort(plan.tasks, plan.task_dependencies)
        sprints, current = [], []

        for task in sorted_tasks:
            deps = plan.task_dependencies.get(task.id, [])
            deps_satisfied = all(
                any(t.id == dep for s in sprints for t in s) for dep in deps)

            # If task depends on something not in established sprints, bump to new sprint
            if not deps_satisfied and current:
                sprints.append(current)
                current = []
            
            current.append(task)
            
            if len(current) >= max_per_sprint:
                sprints.append(current)
                current = []

        if current: 
            sprints.append(current)
            
        return [Sprint(number=i+1, tasks=t) for i, t in enumerate(sprints)]

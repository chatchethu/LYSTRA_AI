import pytest
import uuid
from datetime import datetime
from backend.agent.planner import Planner, Plan, PlanStep, PlanValidationError

class MockLLMGateway:
    pass

def test_planner_validation_missing_dep():
    planner = Planner(MockLLMGateway())
    plan = Plan(
        id=uuid.uuid4(),
        goal="Test",
        estimated_duration=None,
        requires_approval=False,
        created_at=datetime.utcnow(),
        steps=[
            PlanStep(
                id="step1", title="Step 1", description="", tool_name="valid_tool", tool_input={}, depends_on=["missing_step"], status="pending", result=None, error=None
            )
        ]
    )
    with pytest.raises(PlanValidationError, match="depends on missing step"):
        planner.validate_plan(plan, ["valid_tool"])

def test_planner_validation_self_dep():
    planner = Planner(MockLLMGateway())
    plan = Plan(
        id=uuid.uuid4(),
        goal="Test",
        estimated_duration=None,
        requires_approval=False,
        created_at=datetime.utcnow(),
        steps=[
            PlanStep(
                id="step1", title="Step 1", description="", tool_name="valid_tool", tool_input={}, depends_on=["step1"], status="pending", result=None, error=None
            )
        ]
    )
    with pytest.raises(PlanValidationError, match="depends on itself"):
        planner.validate_plan(plan, ["valid_tool"])

def test_planner_validation_cycle():
    planner = Planner(MockLLMGateway())
    plan = Plan(
        id=uuid.uuid4(),
        goal="Test",
        estimated_duration=None,
        requires_approval=False,
        created_at=datetime.utcnow(),
        steps=[
            PlanStep(
                id="step1", title="Step 1", description="", tool_name="valid_tool", tool_input={}, depends_on=["step2"], status="pending", result=None, error=None
            ),
            PlanStep(
                id="step2", title="Step 2", description="", tool_name="valid_tool", tool_input={}, depends_on=["step1"], status="pending", result=None, error=None
            )
        ]
    )
    with pytest.raises(PlanValidationError, match="Cycle detected"):
        planner.validate_plan(plan, ["valid_tool"])

def test_planner_validation_invalid_tool():
    planner = Planner(MockLLMGateway())
    plan = Plan(
        id=uuid.uuid4(),
        goal="Test",
        estimated_duration=None,
        requires_approval=False,
        created_at=datetime.utcnow(),
        steps=[
            PlanStep(
                id="step1", title="Step 1", description="", tool_name="hack_system", tool_input={}, depends_on=[], status="pending", result=None, error=None
            )
        ]
    )
    with pytest.raises(PlanValidationError, match="uses invalid tool"):
        planner.validate_plan(plan, ["valid_tool"])

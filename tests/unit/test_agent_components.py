import pytest
from unittest.mock import MagicMock

def test_topic_detector():
    td = MagicMock()
    td.detect.return_value = "sports"
    assert td.detect("Did you see the game last night?") == "sports"

def test_intent_router():
    ir = MagicMock()
    ir.route.return_value = "query_database"
    assert ir.route("Find user John") == "query_database"

def test_context_manager():
    cm = MagicMock()
    cm.add_message.return_value = True
    cm.get_context.return_value = ["msg1", "msg2"]
    assert cm.add_message("msg3") is True
    assert cm.get_context() == ["msg1", "msg2"]

def test_planner():
    planner = MagicMock()
    planner.create_plan.return_value = ["step1", "step2"]
    assert planner.create_plan("do something complex") == ["step1", "step2"]

def test_executor():
    executor = MagicMock()
    executor.execute_step.return_value = "success"
    assert executor.execute_step("step1") == "success"

def test_verifier():
    verifier = MagicMock()
    verifier.verify.return_value = True
    assert verifier.verify("result", "expected") is True

def test_replanner():
    replanner = MagicMock()
    replanner.replan.return_value = ["new_step"]
    assert replanner.replan(["failed_step"], "error") == ["new_step"]

def test_model_router():
    mr = MagicMock()
    mr.route_model.return_value = "gpt-4"
    assert mr.route_model("complex task") == "gpt-4"
    mr.route_model.return_value = "gpt-3.5"
    assert mr.route_model("simple task") == "gpt-3.5"

def test_tool_registry():
    tr = MagicMock()
    tr.get_tool.return_value = "calculator_tool"
    assert tr.get_tool("calc") == "calculator_tool"

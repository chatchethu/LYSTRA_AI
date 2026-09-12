import ast
import operator
from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

# Safe mathematical operations
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg
}

class CalculatorTool(BaseTool):
    name = "calculate"
    description = "Perform mathematical calculations safely"
    permission_level = ToolPermissionLevel.READ
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression"}
            },
            "required": ["expression"]
        }
        
    def _eval(self, node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return _SAFE_OPERATORS[type(node.op)](self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return _SAFE_OPERATORS[type(node.op)](self._eval(node.operand))
        else:
            raise TypeError(f"Unsupported mathematical operation: {node}")
            
    async def execute(self, user_id, task_id, conversation_id, request_id, expression: str) -> ToolResult:
        try:
            # Parse the expression safely
            parsed = ast.parse(expression, mode='eval')
            result = self._eval(parsed.body)
            return ToolResult(success=True, data={"result": result})
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Calculation error: {str(e)}")

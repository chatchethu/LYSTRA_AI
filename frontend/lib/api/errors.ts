export const ErrorMessages: Record<string, string> = {
  AUTH_ERROR: "Your session has expired. Please sign in again.",
  FORBIDDEN: "You do not have permission to perform this action.",
  VALIDATION_ERROR: "Please check your inputs and try again.",
  RATE_LIMITED: "You are doing that too often. Please slow down.",
  MODEL_UNAVAILABLE: "The AI model is currently offline. Please try another.",
  MODEL_TIMEOUT: "The AI took too long to respond. Please try again.",
  MODEL_ERROR: "The AI encountered an unexpected error.",
  TOOL_NOT_FOUND: "The requested tool is not installed.",
  TOOL_PERMISSION_DENIED: "The AI lacks permission to use this tool.",
  TOOL_TIMEOUT: "The tool took too long to execute.",
  TOOL_ERROR: "A tool execution failed.",
  FILE_ERROR: "There was a problem processing your file.",
  MEMORY_ERROR: "Failed to access long-term memory.",
  CONTEXT_LIMIT: "The conversation is too long. Please start a new one.",
  TASK_ERROR: "The background task failed.",
  TASK_CANCELLED: "The operation was cancelled successfully.",
  SERVER_ERROR: "An unexpected server error occurred.",
  NETWORK_ERROR: "Unable to connect to the server. Please check your connection."
};

export function getFriendlyErrorMessage(code: string, fallback: string = "An unexpected error occurred."): string {
  return ErrorMessages[code] || fallback;
}

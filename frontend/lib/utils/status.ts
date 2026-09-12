export function getSafeStatusMessage(rawStatus: string): string {
  if (!rawStatus) return "Thinking...";
  const lower = rawStatus.toLowerCase();
  
  if (lower.includes("plan") || lower.includes("step")) return "Planning";
  if (lower.includes("search") || lower.includes("find")) return "Searching";
  if (lower.includes("tool") || lower.includes("execut")) return "Using tool";
  if (lower.includes("verify") || lower.includes("check")) return "Verifying";
  if (lower.includes("approv")) return "Waiting for approval";
  if (lower.includes("fail") || lower.includes("error")) return "Failed";
  if (lower.includes("cancel")) return "Cancelled";
  if (lower.includes("done") || lower.includes("complet")) return "Completed";
  
  // Suppress everything else like `<think> I should do this... </think>`
  return "Understanding";
}

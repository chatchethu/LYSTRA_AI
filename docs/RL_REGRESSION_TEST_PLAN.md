# RL Regression Test Plan

## PHASE RL-64 — RESPONSE FORMAT REGRESSION TESTS
We have mandated continuous testing of response formatting across the following modes:
- casual, question, explanation, planning, comparison, technical, web search, code, table, long response, short response.

## PHASE RL-65 — VISUAL REGRESSION TEST SUITE
A visual regression framework (e.g., Playwright + Percy/Chromatic) must capture screenshot tests for:
- simple response
- paragraph response
- heading response
- bullet response
- numbered response
- code response
- table response
- mixed response
- web response
- long response
- streaming response
- error response

## PHASE RL-66 — PERFORMANCE REGRESSION TEST
Performance measurements must track:
- response parse time
- render time
- stream update rate
- component renders
- DOM node growth
- memory usage

Thresholds should be maintained against the current baseline.

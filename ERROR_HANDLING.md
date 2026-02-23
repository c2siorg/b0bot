PR Title

fix: Implement resilient startup and offline mode for missing credentials

Description

This PR enhances the application's resilience by introducing a robust "Offline Mode" and graceful degradation strategy. It resolves a critical fragility where the application would terminate immediately upon startup if the PINECONE_API_KEY or HUGGINGFACE_TOKEN were missing or invalid.

This improvement decouples the application's initialization from external service availability, significantly improving the onboarding experience for new developers and ensuring system stability during partial outages.

Problem Statement

The legacy architecture utilized eager initialization for external services (Pinecone, HuggingFace) at the module level.

    The Defect: Missing or invalid environment variables triggered unhandled exceptions (e.g., UnauthorizedException) during the Python import phase, crashing the process before the Flask server could start.

    The Impact: New contributors were blocked from running the application locally to test UI changes or non-database features without first provisioning valid third-party credentials.

Technical Solution

I have refactored the service layer to employ Lazy Initialization and Defensive Programming patterns. The application now validates service availability at runtime and degrades gracefully to a "Demo Mode" when external dependencies are unreachable.

Architecture Modifications

1. Configuration Layer (config/Database.py)

    Change: Wrapped Pinecone client initialization in a try-except block.

    Effect: The client acts as a safe singleton, initializing only when valid credentials are present. Returns None safely instead of raising a KeyError or UnauthorizedException.

2. Data Persistence Layer (models/NewsModel.py)

    Change: Introduced an is_available() status check.

    Effect: Database operations now verify connectivity before execution. If the service is unavailable, methods return empty datasets or demo data rather than propagating connection errors.

3. Service Logic Layer (services/NewsService.py)

    Change: Implemented a get_demo_response() fallback method.

    Effect: When the LLM service is unreachable, the system synthesizes structured demo data (marked with [DEMO]), ensuring the frontend continues to render and function for UI testing.

4. Routing Layer (routes/NewsRoutes.py)

    Change: Enclosed all route handlers within comprehensive error handling blocks.

    Effect: Prevents 500 Internal Server Error responses during partial outages, instead rendering the UI with appropriate fallback states or user-friendly error messages.

Verification & Testing

I have validated this implementation across four distinct environment configurations:
Scenario	Credentials Status	Result
1. Fresh Clone	Missing (.env empty)	Application starts. Warnings logged. Demo data served.
2. Config Error	Invalid API Keys	Application starts. Auth errors logged. Demo data served.
3. Partial Outage	Missing HF Token Only	Application starts. LLM fallback active. DB works.
4. Production	Valid Credentials	Full functionality. Real data served.

Verification Commands

Maintainers can verify the fix using the following commands:
Bash

# Test 1: Simulate missing credentials (Offline Mode)
echo "" > .env
python app.py
# Expectation: Server starts on port 5000; UI accessible with demo data.

# Test 2: Verify logging
# Check console output for: "[WARNING] Pinecone failed: [Error Details]"

Impact Analysis

    Developer Experience (DX): Reduces "Time to First Run" from minutes (setup required) to seconds (immediate start).

    System Reliability: Transforms a "hard crash" failure mode into a "soft fallback," allowing the application to survive configuration errors.

    Backwards Compatibility: 100%. No changes to the database schema, API contracts, or existing valid configurations.

Note: This PR serves as a foundational stability fix required for my upcoming work on Redis Caching (Issue #37), as it enables the local benchmarking required to measure performance improvements without external dependencies.

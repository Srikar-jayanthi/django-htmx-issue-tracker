# Re-export all tests for test runner discovery under tracker/tests/
from tests.test_tracker import (
    DatabaseSchemaTests,
    IssueTrackerStandardTests,
    IssueTrackerEnhancedTests,
    HealthCheckAndGeneralViewTests,
)

__all__ = [
    'DatabaseSchemaTests',
    'IssueTrackerStandardTests',
    'IssueTrackerEnhancedTests',
    'HealthCheckAndGeneralViewTests',
]

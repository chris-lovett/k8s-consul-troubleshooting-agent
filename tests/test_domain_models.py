"""Tests for typed domain models used by workflow diagnostics/remediation."""

from src.domain.models import AutomatedFix, DiagnosticsResult, RemediationPlan


def test_diagnostics_result_to_dict_and_error():
    result = DiagnosticsResult()
    result.with_entry("pod_status", "Running")
    result.with_error("boom")

    payload = result.to_dict()

    assert payload["pod_status"] == "Running"
    assert payload["error"] == "boom"
    assert result.error == "boom"


def test_remediation_plan_automated_fixes_as_dicts():
    plan = RemediationPlan(root_cause="test")
    plan.add_step("Step 1")
    plan.add_automated_fix(
        AutomatedFix(
            pattern="CrashLoopBackOff",
            fix_type="manual",
            description="Restart pod",
            safe=True,
        )
    )

    fixes = plan.automated_fixes_as_dicts()

    assert plan.remediation_steps == ["Step 1"]
    assert len(fixes) == 1
    assert fixes[0]["pattern"] == "CrashLoopBackOff"
    assert fixes[0]["safe"] is True

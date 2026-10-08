from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSafetyInput:
    dataset_type: str
    mode: str
    requested_action: str
    source_data_class: str | None
    learning_eligibility: bool
    live_kpi_eligibility: bool
    accounting_eligibility: bool
    external_execution_eligibility: bool
    do_not_contact: bool
    dataset_jurisdiction: str | None
    request_jurisdiction: str | None
    dataset_business_scope: str | None
    request_business_scope: str | None


@dataclass(frozen=True)
class DatasetSafetyResult:
    allowed: bool
    reason: str


def evaluate_dataset_safety(payload: DatasetSafetyInput) -> DatasetSafetyResult:
    action = (payload.requested_action or "").strip().lower()
    mode = (payload.mode or "").strip().lower()
    dataset_type = (payload.dataset_type or "").strip().upper()

    contact_actions = {"outreach", "contact", "send", "real_contact"}
    external_actions = {"external_execute", "money_move", "contract_send", "outreach", "real_contact"}

    if mode in {"practice", "test"} and action in external_actions:
        return DatasetSafetyResult(False, "shadow/practice mode blocks external execution actions")

    if payload.do_not_contact and action in contact_actions:
        return DatasetSafetyResult(False, "dataset has do_not_contact enabled")

    if action in external_actions and not payload.external_execution_eligibility:
        return DatasetSafetyResult(False, "dataset is not eligible for external execution")

    if ("accounting" in action or action in {"bookkeeping"}) and not payload.accounting_eligibility:
        return DatasetSafetyResult(False, "dataset is not eligible for accounting actions")

    if ("live_kpi" in action or action == "kpi") and not payload.live_kpi_eligibility:
        return DatasetSafetyResult(False, "dataset is not eligible for live KPI use")

    if mode == "live" and dataset_type in {"SYNTHETIC_OPERATIONAL", "PRACTICE", "FAILURE_SCENARIO", "LOAD_TEST"}:
        return DatasetSafetyResult(False, "synthetic/practice datasets cannot be used in live mode")

    if payload.request_jurisdiction and payload.dataset_jurisdiction and payload.request_jurisdiction != payload.dataset_jurisdiction:
        return DatasetSafetyResult(False, "jurisdiction mismatch")

    if payload.request_business_scope and payload.dataset_business_scope and payload.request_business_scope != payload.dataset_business_scope:
        return DatasetSafetyResult(False, "business scope mismatch")

    return DatasetSafetyResult(True, "dataset use approved")

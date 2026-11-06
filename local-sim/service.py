"""Business rules shared by the HTTP API and automated tests."""

from __future__ import annotations

from typing import Any

from database import Database
from simulated_ai import classify


CATEGORIES = ("Access", "Hardware", "Software", "Microsoft 365", "Network", "Other")
PRIORITIES = ("Low", "Medium", "High", "Critical")
STATUSES = ("Awaiting review", "Approved", "Rejected")


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class RequestService:
    def __init__(self, database: Database):
        self.database = database
        self.database.initialize()

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = _required_text(payload, "title", 120)
        description = _required_text(payload, "description", 2000)
        requester = _required_text(payload, "requester", 120)
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters.")
        proposal = classify(title, description)
        return self.database.create_request(
            {
                "title": title,
                "description": description,
                "requester": requester,
                **proposal,
            }
        )

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        if status and status not in STATUSES:
            raise ValidationError("Unknown status filter.")
        return self.database.list_requests(status)

    def get(self, request_id: int) -> dict[str, Any]:
        request = self.database.get_request(request_id)
        if request is None:
            raise NotFoundError("Request not found.")
        return request

    def decide(self, request_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get(request_id)
        decision = _optional_text(payload, "decision", "").lower()
        if decision not in {"approve", "reject"}:
            raise ValidationError("Decision must be approve or reject.")
        reviewer = _required_text(payload, "reviewed_by", 120)
        comment = _optional_text(payload, "review_comment", "")
        if len(comment) > 1000:
            raise ValidationError("Review comment must be 1,000 characters or fewer.")
        if decision == "reject" and not comment:
            raise ValidationError("A reason is required when rejecting a request.")

        category = _optional_text(payload, "category", current["category"])
        priority = _optional_text(payload, "priority", current["priority"])
        summary = _optional_text(payload, "ai_summary", current["ai_summary"])
        reply = _optional_text(payload, "suggested_reply", current["suggested_reply"])
        if category not in CATEGORIES:
            raise ValidationError("Choose a supported category.")
        if priority not in PRIORITIES:
            raise ValidationError("Choose a supported priority.")
        if not summary or len(summary) > 500:
            raise ValidationError("Summary must contain 1 to 500 characters.")
        if not reply or len(reply) > 1200:
            raise ValidationError("Suggested reply must contain 1 to 1,200 characters.")

        try:
            reviewed = self.database.review_request(
                request_id,
                status="Approved" if decision == "approve" else "Rejected",
                reviewed_by=reviewer,
                review_comment=comment,
                category=category,
                priority=priority,
                ai_summary=summary,
                suggested_reply=reply,
            )
        except RuntimeError as error:
            raise ConflictError(str(error)) from error
        if reviewed is None:
            raise NotFoundError("Request not found.")
        return reviewed


def _required_text(payload: dict[str, Any], field: str, maximum: int) -> str:
    value = _optional_text(payload, field, "")
    if not value:
        raise ValidationError(f"{field.replace('_', ' ').title()} is required.")
    if len(value) > maximum:
        raise ValidationError(
            f"{field.replace('_', ' ').title()} must be {maximum} characters or fewer."
        )
    return value


def _optional_text(payload: dict[str, Any], field: str, default: str) -> str:
    if field not in payload:
        return default
    value = payload[field]
    if not isinstance(value, str):
        raise ValidationError(f"{field.replace('_', ' ').title()} must be text.")
    return value.strip()

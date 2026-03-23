"""Tests for review-queue markdown contract."""

from __future__ import annotations

import pytest
import yaml

from kms.app.review_queue import parse_review_queue_markdown, render_review_queue


def test_parse_roundtrip_minimal() -> None:
    md = render_review_queue(
        "Test",
        [
            {
                "proposal_id": 1,
                "item_id": 10,
                "decision": "pending",
                "reviewer": "",
                "override_target": None,
                "body_md": "Hello",
            }
        ],
    )
    blocks = parse_review_queue_markdown(md)
    assert len(blocks) == 1
    assert blocks[0].proposal_id == 1
    assert blocks[0].item_id == 10
    assert blocks[0].decision == "pending"
    assert "Hello" in blocks[0].raw_body


def test_parse_invalid_decision_still_roundtrips_string() -> None:
    md = render_review_queue(
        "T",
        [
            {
                "proposal_id": 2,
                "item_id": 20,
                "decision": "approve",
                "reviewer": "alice",
                "override_target": None,
                "body_md": "x",
            }
        ],
    )
    b = parse_review_queue_markdown(md)[0]
    assert b.decision == "approve"
    assert b.reviewer == "alice"


def test_parse_raises_on_unclosed_block() -> None:
    with pytest.raises(ValueError, match="Unclosed"):
        parse_review_queue_markdown("<!-- kms:begin -->\n```yaml\nproposal_id: 1\nitem_id: 1\n```\n")


def test_parse_raises_on_invalid_yaml_mapping() -> None:
    md = """# Queue

<!-- kms:begin -->
```yaml
proposal_id: [not-valid
item_id: 1
```
<!-- kms:end -->
"""
    with pytest.raises(yaml.YAMLError):
        parse_review_queue_markdown(md)


def test_parse_raises_on_missing_required_field() -> None:
    md = """# Queue

<!-- kms:begin -->
```yaml
proposal_id: 7
decision: pending
reviewer: ""
```
<!-- kms:end -->
"""
    with pytest.raises(KeyError):
        parse_review_queue_markdown(md)

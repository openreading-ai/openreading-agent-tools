"""Retrieval acceptance requires supporting pages and exact verified read spans."""

import unittest
from types import SimpleNamespace as Box
from unittest.mock import Mock


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.task = {
            "id": "one",
            "task_kind": "cross_page",
            "queries": ["notice", "exception"],
            "support": {"3": ["60 days"], "9": ["signed declaration"]},
        }
        self.passages = [
            Box(evidence_id="p3", page=3, text="Provide 60 days notice.", text_origin="native"),
            Box(
                evidence_id="p9",
                page=9,
                text="A signed declaration is required.",
                text_origin="native",
            ),
        ]
        self.service = Mock()
        self.service.search.side_effect = lambda artifact, query, limit: Box(
            hits=[
                Box(
                    evidence_id=p.evidence_id,
                    page=p.page,
                    excerpt=p.text,
                    excerpt_start=0,
                    excerpt_end=len(p.text),
                )
                for p in self.passages
                if (p.page == 3) == (query == "notice")
            ],
            next_cursor=None,
        )
        self.service.read.side_effect = lambda artifact, ids: Box(
            passages=[p for p in self.passages if p.evidence_id in ids], next_cursor=None
        )

    def test_queries_individually_and_union_require_all_support(self):
        from measurement.retrieval import evaluate

        row = evaluate(self.service, "artifact", self.task, self.passages)
        self.assertTrue(row["passed"])
        self.assertEqual([q["recall"] for q in row["queries"]], [0.5, 0.5])
        self.assertEqual(row["retrieved_support_pages"], [3, 9])
        self.assertEqual(len(row["citations"]), 2)
        self.service.search.assert_any_call("artifact", "notice", limit=5)

    def test_missing_facts_are_not_positive_recall_successes(self):
        from measurement.retrieval import evaluate

        self.task.update(task_kind="missing_fact", support={})
        row = evaluate(self.service, "artifact", self.task, self.passages)
        self.assertIsNone(row["passed"])
        self.assertEqual(row["quality_status"], "requires_scoped_refusal_review")
        self.service.search.assert_not_called()

    def test_lost_pages_and_missing_qualifiers_fail(self):
        from measurement.retrieval import evaluate

        self.task["support"]["9"] = ["missing qualifier"]
        self.assertFalse(evaluate(self.service, "artifact", self.task, self.passages)["passed"])
        self.service.search.side_effect = lambda *a, **kw: Box(hits=[], next_cursor=None)
        self.assertFalse(evaluate(self.service, "artifact", self.task, self.passages)["passed"])

    def test_wrong_page_quote_identifier_and_read_are_refused(self):
        from measurement.retrieval import evaluate

        for fields in [
            dict(page=99),
            dict(excerpt="fabrication"),
            dict(evidence_id="unknown"),
            dict(excerpt_end=999),
        ]:
            with self.subTest(fields=fields):
                hit = dict(
                    evidence_id="p3",
                    page=3,
                    excerpt=self.passages[0].text,
                    excerpt_start=0,
                    excerpt_end=len(self.passages[0].text),
                )
                hit.update(fields)
                self.service.search.side_effect = lambda *a, hit=hit, **kw: Box(
                    hits=[Box(**hit)], next_cursor=None
                )
                with self.assertRaises(ValueError):
                    evaluate(self.service, "artifact", self.task, self.passages)
        self.service.search.side_effect = lambda *a, **kw: Box(
            hits=[
                Box(
                    evidence_id="p3",
                    page=3,
                    excerpt=self.passages[0].text,
                    excerpt_start=0,
                    excerpt_end=len(self.passages[0].text),
                )
            ],
            next_cursor=None,
        )
        for values, cursor in [
            ([], None),
            ([Box(evidence_id="p3", page=3, text="changed", text_origin="native")], None),
            (self.passages, "unexpected"),
        ]:
            self.service.read.side_effect = lambda *a, values=values, cursor=cursor, **kw: Box(
                passages=values, next_cursor=cursor
            )
            with self.assertRaises(ValueError):
                evaluate(self.service, "artifact", self.task, self.passages)

    def test_search_cannot_exceed_five_hits(self):
        from measurement.retrieval import evaluate

        self.service.search.side_effect = lambda *a, **kw: Box(hits=[None] * 6)
        with self.assertRaisesRegex(ValueError, "top-five"):
            evaluate(self.service, "artifact", self.task, self.passages)

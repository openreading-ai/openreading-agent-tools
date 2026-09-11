"""Evaluate frozen top-five queries without treating retrieval as answer quality.

Each quote must match a verified retained passage before it can support page recall.
Required qualifiers are checked in the union of returned exact reads on their physical
pages. Missing-fact tasks retain a separate human/model scoped-refusal requirement.
"""


def evaluate(service, artifact, task, passages):
    if task["task_kind"] == "missing_fact":
        return {
            "task_id": task["id"],
            "passed": None,
            "quality_status": "requires_scoped_refusal_review",
        }
    expected = {int(page): values for page, values in task["support"].items()}
    verified = {p.evidence_id: p for p in passages}
    found = {}
    queries = []
    for query in task["queries"]:
        result = service.search(artifact, query, limit=5)
        pages = set()
        if len(result.hits) > 5:
            raise ValueError("Search exceeded the frozen top-five limit.")
        for hit in result.hits:
            passage = verified.get(hit.evidence_id)
            if (
                passage is None
                or hit.page != passage.page
                or not 0 <= hit.excerpt_start < hit.excerpt_end <= len(passage.text)
                or hit.excerpt != passage.text[hit.excerpt_start : hit.excerpt_end]
            ):
                raise ValueError("Search citation does not match verified source evidence.")
            read = service.read(artifact, [hit.evidence_id])
            if (
                read.next_cursor is not None
                or len(read.passages) != 1
                or read.passages[0] != passage
            ):
                raise ValueError("Read citation does not match verified source evidence.")
            found[passage.evidence_id] = passage
            pages.add(passage.page)
        queries.append(
            {
                "query": query,
                "pages": sorted(pages),
                "recall": len(pages & expected.keys()) / len(expected),
            }
        )
    retained = {
        page: "\n".join(p.text for p in found.values() if p.page == page).casefold()
        for page in expected
    }
    missing = {
        str(page): [value for value in values if value.casefold() not in retained[page]]
        for page, values in expected.items()
    }
    missing = {page: values for page, values in missing.items() if values}
    support = sorted({p.page for p in found.values()} & expected.keys())
    return {
        "task_id": task["id"],
        "passed": not missing and len(support) == len(expected),
        "quality_status": "not_model_evaluated",
        "queries": queries,
        "retrieved_support_pages": support,
        "missing_qualifiers": missing,
        "citations": [
            {
                "evidence_id": p.evidence_id,
                "page": p.page,
                "text_origin": p.text_origin,
                "quote": p.text,
            }
            for p in found.values()
        ],
    }

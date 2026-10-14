#!/usr/bin/env python3
"""Read-only structural ATDD check against an independently prepared source inventory."""

import argparse
import importlib.util
import os
import hashlib
import json
import re
import sys
from pathlib import Path

SOURCE_HEADER = ["Source", "Location", "SHA-256"]
COVERAGE_HEADER = ["Obligation", "Source", "Locator", "Disposition", "Cases", "Reason"]
RETIRED_HEADER = ["Retired case", "Reason", "Replaced by"]
REQUIRED_FIELDS = ("Sources", "Priority", "Level", "Platform", "Category", "Automation",
                   "Status", "Preconditions", "Test data", "Scenario", "Verification", "Cleanup")
EVIDENCE_FIELDS = ("Evidence", "Revision", "Environment", "Executed at")
STATUS_VALUES = {"Not Run", "Passed", "Failed", "Blocked", "Stale"}
SCOPES = {"Required", "Excluded", "Deferred"}
TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
CASE_HEADING = re.compile(r"^(#{2,6}) Case (\S+): (.+)$")
FIELD = re.compile(r"^\*\*([^*\n]+):\*\*[ \t]*(.*)$", re.M)


def output_wording_errors(paths):
    """Use the shared final-output check; a missing checker is a failure."""
    helper = Path(os.environ.get('PERSONAL_WORDING_CHECKER', str(Path(__file__).resolve().parents[3] / 'resources' / 'wording' / 'check_output_wording.py')))
    if not helper.is_file():
        return ['Output wording checker missing; validate with the shared personal checker before delivery.']
    spec = importlib.util.spec_from_file_location('personal_output_wording', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    findings, errors = module.scan_paths(paths)
    return ['Output wording: '+message for message in findings+errors]


class InvalidInput(ValueError):
    pass


def required_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise InvalidInput(f"{label} must be a nonempty string")
    return value.strip()


def token(value, label):
    value = required_text(value, label)
    if not TOKEN.fullmatch(value):
        raise InvalidInput(f"{label} must be a single identifier token")
    return value


def unique_records(records, label):
    if not isinstance(records, list):
        raise InvalidInput(f"{label} must be an array")
    result = {}
    for record in records:
        if not isinstance(record, dict):
            raise InvalidInput(f"{label} entries must be objects")
        key = token(record.get("id"), f"{label}.id")
        if key in result:
            raise InvalidInput(f"duplicate {label} ID: {key}")
        result[key] = record
    if not result:
        raise InvalidInput(f"{label} must not be empty")
    return result


def unfenced_lines(text):
    """Hide fenced examples from register, heading and metadata discovery."""
    lines = text.splitlines(keepends=True)
    visible = []
    fence = None
    for line in lines:
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1] and not tail.strip():
                fence = None
            visible.append("\n" if line.endswith("\n") else "")
        elif fence:
            visible.append("\n" if line.endswith("\n") else "")
        else:
            visible.append(line)
    if fence:
        raise InvalidInput("unclosed Markdown code fence")
    return lines, visible


def cell(value):
    return value.strip().strip("`").replace(r"\|", "|")


def link_target(value):
    match = re.fullmatch(r"\[[^\]]*\]\(([^)]+)\)", value)
    return match[1] if match else value


def table_rows(visible, header, errors, required=True):
    def split(line):
        return [cell(part) for part in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
    starts = [i for i, line in enumerate(visible) if line.lstrip().startswith("|") and split(line) == header]
    if len(starts) != 1:
        if starts or required:
            errors.append(f"expected one register with header {header}; found {len(starts)}")
        return []
    index = starts[0] + 1
    if index >= len(visible) or not all(re.fullmatch(r":?-{3,}:?", x) for x in split(visible[index])) or len(split(visible[index])) != len(header):
        errors.append(f"invalid table delimiter after {header[0]} register")
        return []
    rows = []
    for line in visible[index + 1:]:
        if not line.lstrip().startswith("|"):
            break
        values = split(line)
        if len(values) != len(header):
            errors.append(f"wrong column count in {header[0]} register")
            continue
        rows.append(dict(zip(header, values)))
    return rows


def ids(value):
    return [part.strip() for part in value.split(",") if part.strip() and part.strip() != "—"]


def read_document(path):
    text = path.read_text(encoding="utf-8")
    raw, visible = unfenced_lines(text)
    errors = []
    cases = {}
    for index, line in enumerate(visible):
        match = CASE_HEADING.fullmatch(line.rstrip("\n"))
        if not match:
            continue
        level, key, title = len(match[1]), match[2], match[3]
        token(key, "case ID")
        end = index + 1
        while end < len(raw):
            heading = re.match(r"^(#{1,6}) ", visible[end])
            if heading and len(heading[1]) <= level:
                break
            end += 1
        body = "".join(raw[index + 1:end])
        body_lines, body_visible = unfenced_lines(body)
        # A trailing thematic rule separates cases/sections; it is not a field value.
        last = len(body_lines) - 1
        while last >= 0 and not body_lines[last].strip():
            last -= 1
        while last >= 0 and re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", body_visible[last].strip()):
            body = "".join(body_lines[:last])
            body_lines, body_visible = unfenced_lines(body)
            last = len(body_lines) - 1
            while last >= 0 and not body_lines[last].strip():
                last -= 1
        offsets, position = [], 0
        for original, shown in zip(body_lines, body_visible):
            if FIELD.match(shown):
                offsets.append(position)
            position += len(original)
        fields = {}
        for n, start in enumerate(offsets):
            field_match = FIELD.match(body, start)
            name = field_match[1]
            stop = offsets[n + 1] if n + 1 < len(offsets) else len(body)
            if name in fields:
                errors.append(f"{key}: duplicate field {name}")
            fields[name] = body[field_match.start(2):stop].strip()
        if key in cases:
            errors.append(f"duplicate case ID: {key}")
        cases[key] = {"title": title, "fields": fields}
    sources = table_rows(visible, SOURCE_HEADER, errors)
    coverage = table_rows(visible, COVERAGE_HEADER, errors)
    retired = table_rows(visible, RETIRED_HEADER, errors, required=False)
    return {"cases": cases, "sources": sources, "coverage": coverage, "retired": retired, "errors": errors}


def index_rows(rows, key, errors):
    result = {}
    for row in rows:
        value = row[key]
        if value in result:
            errors.append(f"duplicate {key} register ID: {value}")
        result[value] = row
    return result


def compare_members(actual, expected, label, errors):
    for key in sorted(set(expected) - set(actual)):
        errors.append(f"missing {label}: {key}")
    for key in sorted(set(actual) - set(expected)):
        errors.append(f"unknown {label}: {key}")


def substantive(value):
    return bool(value and not re.match(r"^(?:none|not run|not executed|pending|unknown|n/?a|not applicable)(?:\b|$)", value, re.I))


def case_fingerprint(case):
    omitted = set(EVIDENCE_FIELDS) | {"Status", "Blocker", "Impact review"}
    fields = {k: v for k, v in case["fields"].items() if k not in omitted}
    return json.dumps({"title": case["title"], "fields": fields}, sort_keys=True)


def check(inventory_path, document_path, previous_path=None):
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if not isinstance(inventory, dict) or type(inventory.get("schema_version")) is not int or inventory.get("schema_version") != 1:
        raise InvalidInput("inventory schema_version must be 1")
    if previous_path and previous_path.resolve() == document_path.resolve():
        raise InvalidInput("previous document must be a separate snapshot")
    sources = unique_records(inventory.get("sources"), "source")
    obligations = unique_records(inventory.get("obligations"), "obligation")
    doc = read_document(document_path)
    errors, gaps = doc["errors"], []
    errors.extend(output_wording_errors([document_path]))
    source_rows = index_rows(doc["sources"], "Source", errors)
    coverage = index_rows(doc["coverage"], "Obligation", errors)
    retired = index_rows(doc["retired"], "Retired case", errors)
    compare_members(source_rows, sources, "source register entry", errors)
    compare_members(coverage, obligations, "obligation register entry", errors)
    for key, source in sources.items():
        expected_hash = required_text(source.get("sha256"), f"{key}.sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise InvalidInput(f"{key}: invalid SHA-256")
        location = required_text(source.get("location"), f"{key}.location")
        path = Path(required_text(source.get("path"), f"{key}.path"))
        path = path if path.is_absolute() else inventory_path.parent / path
        if path.resolve() == document_path.resolve() or (previous_path and path.resolve() == previous_path.resolve()):
            errors.append(f"{key}: ATDD output cannot serve as its own requirement source")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append(f"{key}: source fingerprint changed; reconcile inventory")
        if key in source_rows and (source_rows[key]["SHA-256"] != expected_hash or link_target(source_rows[key]["Location"]) != location):
            errors.append(f"{key}: source register differs from independent inventory")
    for key, obligation in obligations.items():
        source = token(obligation.get("source"), f"{key}.source")
        locator = required_text(obligation.get("locator"), f"{key}.locator")
        required_text(obligation.get("statement"), f"{key}.statement")
        scope = obligation.get("scope")
        if scope not in SCOPES or source not in sources:
            raise InvalidInput(f"{key}: unknown source or invalid scope")
        if scope != "Required":
            required_text(obligation.get("reason"), f"{key}.reason")
        row = coverage.get(key)
        if not row:
            continue
        if row["Source"] != source or row["Locator"] != locator:
            errors.append(f"{key}: coverage source/locator differs from inventory")
        disposition, mapped = row["Disposition"], ids(row["Cases"])
        allowed = {"Covered", "Gap"} if scope == "Required" else {scope}
        if disposition not in allowed:
            errors.append(f"{key}: disposition {disposition!r} contradicts scope {scope}")
        if disposition == "Covered" and not mapped:
            errors.append(f"{key}: Covered without cases")
        if disposition in {"Gap", "Excluded", "Deferred"} and not row["Reason"]:
            errors.append(f"{key}: {disposition} needs a reason")
        if scope != "Required" and row["Reason"] != obligation["reason"]:
            errors.append(f"{key}: exclusion/deferral reason differs from inventory")
        if scope != "Required" and mapped:
            errors.append(f"{key}: out-of-scope obligation has active cases")
        if disposition == "Gap":
            gaps.append(key)
        if len(mapped) != len(set(mapped)):
            errors.append(f"{key}: duplicate case mapping")
        for case_id in mapped:
            if case_id not in doc["cases"]:
                errors.append(f"{key}: unknown case {case_id}")
            elif key not in ids(doc["cases"][case_id]["fields"].get("Sources", "")):
                errors.append(f"{key}/{case_id}: missing reverse case reference")
    duplicates = {}
    for key, case in doc["cases"].items():
        fields = case["fields"]
        for field in REQUIRED_FIELDS:
            if not fields.get(field):
                errors.append(f"{key}: missing field {field}")
        refs = ids(fields.get("Sources", ""))
        if not refs:
            errors.append(f"{key}: Sources needs at least one obligation ID")
        if len(refs) != len(set(refs)):
            errors.append(f"{key}: duplicate source reference")
        for ref in refs:
            if ref not in obligations:
                errors.append(f"{key}: unknown obligation {ref}")
            elif ref not in coverage or key not in ids(coverage[ref]["Cases"]):
                errors.append(f"{key}/{ref}: missing forward coverage reference")
        if fields.get("Category") not in {"Positive", "Negative", "Edge"}:
            errors.append(f"{key}: invalid Category")
        if fields.get("Automation") not in {"Candidate", "Manual", "Undecided"}:
            errors.append(f"{key}: invalid Automation")
        status = fields.get("Status")
        if status not in STATUS_VALUES:
            errors.append(f"{key}: invalid Status")
        if status in {"Passed", "Failed"}:
            for field in EVIDENCE_FIELDS:
                if not substantive(fields.get(field, "")):
                    errors.append(f"{key}: {status} requires substantive {field}")
        if status == "Blocked" and not substantive(fields.get("Blocker", "")):
            errors.append(f"{key}: Blocked requires Blocker")
        scenario = fields.get("Scenario", "")
        fenced = re.search(r"(?ms)^```gherkin\s*\n(.*?)^```\s*$", scenario)
        if not fenced or any(not re.search(r"(?m)^\s*" + word + r"\s+\S", fenced[1]) for word in ("Given", "When", "Then")):
            errors.append(f"{key}: Scenario needs a gherkin fence with Given, When and Then")
        elif "Scenario Outline:" in fenced[1] and not re.search(r"(?m)^\s*Examples:\s*\n(?:\s*\|.+\|\s*\n){2,}", fenced[1] + "\n"):
            errors.append(f"{key}: Scenario Outline needs Examples rows")
        signature = tuple(re.sub(r"\s+", " ", fields.get(field, "")).strip() for field in ("Preconditions", "Test data", "Scenario", "Verification"))
        if signature in duplicates:
            errors.append(f"{key}: exact duplicate scenario of {duplicates[signature]}")
        duplicates[signature] = key
    for key, row in retired.items():
        if key in doc["cases"]:
            errors.append(f"{key}: both active and retired")
        if not row["Reason"]:
            errors.append(f"{key}: retirement needs a reason")
        for replacement in ids(row["Replaced by"]):
            if replacement not in doc["cases"]:
                errors.append(f"{key}: unknown replacement case {replacement}")
    if previous_path:
        previous = read_document(previous_path)
        if previous["errors"]:
            errors.append("previous document has structural parse errors: " + "; ".join(previous["errors"]))
        old_sources = {r["Source"]: r["SHA-256"] for r in previous["sources"]}
        old_retired = {r["Retired case"] for r in previous["retired"]}
        for key in old_retired:
            if key not in retired or key in doc["cases"]:
                errors.append(f"{key}: retired history lost or ID reused")
        for key, old_case in previous["cases"].items():
            if key not in doc["cases"]:
                if key not in retired:
                    errors.append(f"{key}: removed without retirement record")
                continue
            case = doc["cases"][key]
            fields, old_fields = case["fields"], old_case["fields"]
            relevant_sources = {obligations[ref]["source"] for ref in ids(fields.get("Sources", "")) if ref in obligations}
            changed = case_fingerprint(case) != case_fingerprint(old_case) or any(old_sources.get(s) != sources[s]["sha256"] for s in relevant_sources)
            if changed and fields.get("Status") in {"Passed", "Failed"}:
                fresh_evidence = any(fields.get(f) != old_fields.get(f) for f in EVIDENCE_FIELDS)
                impact_review = substantive(fields.get("Impact review", "")) and fields.get("Impact review") != old_fields.get("Impact review")
                if not fresh_evidence and not impact_review:
                    errors.append(f"{key}: changed expectations/source retain execution status without new evidence or impact review; mark Stale")
    result = {"status": "invalid" if errors else "gaps" if gaps else "structurally_valid",
              "sources": len(sources), "obligations": len(obligations), "cases": len(doc["cases"]),
              "gaps": sorted(gaps), "errors": sorted(set(errors)),
              "assurance": "Structural mapping only; semantic completeness and execution evidence require review."}
    return result, 1 if errors else 2 if gaps else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args()
    try:
        result, status = check(args.inventory, args.document, args.previous)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        result, status = {"status": "invalid", "errors": [str(exc)]}, 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return status


if __name__ == "__main__":
    sys.exit(main())

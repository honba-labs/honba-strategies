"""A small JSON Schema validator (the subset ``schema/step.schema.json`` uses).

The catalog CI installs no ``jsonschema``; this keeps validation dependency-free. Supported:
``$ref`` (local ``#/...``), ``type``, ``enum``, ``const``, ``required``, ``properties``,
``additionalProperties``, ``propertyNames``, ``items``, ``minItems``, ``uniqueItems``,
``minLength``, ``pattern``, ``minimum``, ``exclusiveMinimum``, ``allOf``, ``anyOf``, ``not``
and ``if``/``then``/``else``. Unknown keywords are ignored, as in the specification.
"""

from __future__ import annotations

import re
from typing import Any

_TYPES: dict[str, Any] = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}


def _resolve(root: dict, ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported $ref {ref!r}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def validate(
    instance: Any, schema: dict, root: dict | None = None, path: str = "$"
) -> list[str]:
    """Return a list of error strings (empty when ``instance`` conforms to ``schema``)."""
    root = schema if root is None else root
    if "$ref" in schema:
        errs = validate(instance, _resolve(root, schema["$ref"]), root, path)
        rest = {k: v for k, v in schema.items() if k != "$ref"}
        return errs + (validate(instance, rest, root, path) if rest else [])
    errs: list[str] = []
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_TYPES[t](instance) for t in types):
            return [
                f"{path}: expected {'|'.join(types)}, got {type(instance).__name__}"
            ]
    if "const" in schema and instance != schema["const"]:
        errs.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in {schema['enum']}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errs.append(f"{path}: {instance!r} does not match {schema['pattern']!r}")
    if _TYPES["number"](instance):
        if "minimum" in schema and instance < schema["minimum"]:
            errs.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            errs.append(f"{path}: {instance} <= {schema['exclusiveMinimum']}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if schema.get("uniqueItems") and any(
            instance[i] == instance[j] for i in range(len(instance)) for j in range(i)
        ):
            errs.append(f"{path}: items must be unique")
        if "items" in schema:
            for i, item in enumerate(instance):
                errs += validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errs.append(f"{path}: missing required {key!r}")
        props = schema.get("properties", {})
        for key, value in instance.items():
            sub = f"{path}.{key}"
            if "propertyNames" in schema:
                errs += validate(key, schema["propertyNames"], root, f"{sub}(name)")
            if key in props:
                errs += validate(value, props[key], root, sub)
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unexpected key {key!r}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += validate(value, schema["additionalProperties"], root, sub)
    for sub_schema in schema.get("allOf", []):
        errs += validate(instance, sub_schema, root, path)
    if "anyOf" in schema and not any(
        not validate(instance, s, root, path) for s in schema["anyOf"]
    ):
        errs.append(f"{path}: matches none of anyOf")
    if "not" in schema and not validate(instance, schema["not"], root, path):
        errs.append(f"{path}: matches a forbidden schema")
    if "if" in schema:
        branch = "then" if not validate(instance, schema["if"], root, path) else "else"
        if branch in schema:
            errs += validate(instance, schema[branch], root, path)
    return errs

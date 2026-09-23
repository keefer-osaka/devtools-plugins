import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
PLUGINS = MARKETPLACE["plugins"]


def _plugin_json(name, ref=None):
    rel = f"plugins/{name}/.claude-plugin/plugin.json"
    if ref is None:
        return json.loads((ROOT / rel).read_text())
    return json.loads(_git("show", f"{ref}:{rel}"))


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def _last_tag():
    try:
        return _git("describe", "--tags", "--abbrev=0").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


@pytest.mark.parametrize("entry", PLUGINS, ids=lambda e: e["name"])
def test_marketplace_matches_plugin_json(entry):
    plugin = _plugin_json(entry["name"])
    assert entry["version"] == plugin["version"]
    assert entry.get("keywords") == plugin.get("keywords")


def test_obsidian_kb_payload_version():
    payload = (ROOT / "plugins/obsidian-kb/vault-payload/.claude/skills/_version").read_text().strip()
    assert payload == _plugin_json("obsidian-kb")["version"]


@pytest.mark.parametrize("entry", PLUGINS, ids=lambda e: e["name"])
def test_changed_plugin_is_bumped(entry):
    tag = _last_tag()
    if tag is None:
        pytest.skip("no git tag")
    name = entry["name"]
    changed = _git("diff", "--name-only", tag, "--", f"plugins/{name}").strip()
    if not changed:
        return
    assert _plugin_json(name)["version"] != _plugin_json(name, tag)["version"], (
        f"{name} changed since {tag} but version not bumped:\n{changed}"
    )

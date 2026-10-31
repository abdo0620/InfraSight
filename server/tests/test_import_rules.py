"""Tier boundaries from the architecture doc, enforced by folder placement."""
import ast
from pathlib import Path

SERVER = Path(__file__).resolve().parent.parent

FORBIDDEN = {
    'services/core': ('services.admin', 'services.compliance', 'services.workflow', 'adapters',
                      'db.models.admin', 'db.models.compliance'),
    'services/admin': ('services.compliance', 'services.workflow', 'adapters', 'db.models.compliance'),
}


def _imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_tier_import_rules():
    violations = []
    for folder, banned in FORBIDDEN.items():
        for f in (SERVER / folder).rglob('*.py'):
            for mod in _imports(f):
                if any(mod == b or mod.startswith(b + '.') for b in banned):
                    violations.append(f'{f.relative_to(SERVER)} imports {mod}')
    assert not violations, '\n'.join(violations)

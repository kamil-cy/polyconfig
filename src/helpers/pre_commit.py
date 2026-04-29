#!/usr/bin/env python
import sys

from simplegithooks import GitHook, PreCommitConfig

pre_commit = GitHook(__file__, PreCommitConfig())
pre_commit.add_ignored_file("helpers/pre_*.py")
pre_commit.check_content_for("FIXME", "❌", "error")
pre_commit.check_content_for("NotImplemented", "🚧", "fail")
pre_commit.check_content_for("TODO", "⚠️", "warning", prevent=False)
pre_commit.check_command("ruff check")
pre_commit.check_command("pytest", prevent=False)
# pre_commit.check_command("mypy --explicit-package-bases --ignore-missing-imports .", prevent=False)
print(pre_commit.results())
print(pre_commit.summary())
sys.exit(pre_commit.rc)

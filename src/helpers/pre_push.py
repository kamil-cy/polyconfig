#!/usr/bin/env python
import sys

from simplegithooks import GitHook, PrePushConfig

pre_push = GitHook(__file__, PrePushConfig())
pre_push.add_ignored_file("helpers/pre_*.py")
pre_push.check_command("pytest")
print(pre_push.results())
print(pre_push.summary())
sys.exit(pre_push.rc)

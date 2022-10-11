# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Mkdocs documentation macros."""

import subprocess

UNTAGGED_DOC_WARNING = """\
!!! warning "Warning"
    <span style="color:red">**You are currently viewing documentation compiled
    from a non-release commit (untagged). Hashes for components, agents or
    services referenced in this compilation might be inconsistent.**</span>
    """

def define_env(env):
    """Hook function"""
    
    @env.macro
    def check_untagged_doc() -> str:
        """Displays a warning if docs are compiled from a non-release commit"""
        if subprocess.call(['git', 'describe', '--tags', '--exact-match']) != 0:
            return UNTAGGED_DOC_WARNING
        
        return ""

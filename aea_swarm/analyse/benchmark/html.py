# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""HTML templates for benchmark outputs."""

HTML_TEMPLATE = """<html>
<head>
    <title>
        Benchmarks
    </title>
    <style>
        *{{
            padding: 0;
            margin: 0;
        }}
        body{{
            padding: 5;
        }}
        td{{
            height: 24px;
            min-width: 96px;
            max-width: fit-content;
            font-size: 14px;
            padding: 3px;
        }}

        th{{
            height: 24px;
            min-width: 96px;
            max-width: fit-content;
            font-size: 14px;
            padding: 3px;
        }}
    </style>
</head>
<body>
    {tables}
</body>
</hmtl>"""

TABLE_TEMPLATE = """
<div style="margin: 16px 8px;">
    <div style="height: 3vh; width: 100%; font-size: 14px;">
        Period: {period} | Block: {block}
    </div>
    {table}
</div>"""

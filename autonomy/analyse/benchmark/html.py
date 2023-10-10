# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

BLOCK_TEMPLATE = """
    <div style="margin: 16px 8px;">
        {table}
    </div>"""

TABLE_TEMPLATE = """
<table border="1" style="width: 100%; border: 1px solid black; border-collapse: collapse;">
    <thead>
        <th style="text-align: center;" colspan="{colspan}">Block: {block_type}</th>
    </thead>
    <thead>{thead}</thead>
    <tbody>{tbody}</tbody>
</table>"""

TROW_TEMPLATE = """
<tr style="text-align: left;">
{}
</tr>
"""

TH_TEMPLATE = """
        <th>{}</th>"""

TD_TEMPLATE = """
        <td>{}</td>"""

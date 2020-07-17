#!/usr/bin/env python
"""
Simple no-dependencies script to convert openeoct JSON result file to a
easier to read HTML report.
"""
import sys
import json


def main(input_path=None, output_path=None):
    input = open(input_path, "r") if input_path else sys.stdin
    with input as f:
        report = json.load(f)

    output = open(output_path, "w") if output_path else sys.stdout
    with output as f:
        output.write("<!DOCTYPE html>\n<html>\n")
        output.write("""<style>
            body { font-size: 10pt; }
            table {  border-collapse: collapse; }
            table td { border: 1px solid #aaa; }
            td { padding: .2em .5em; }
            .state { background-color: #ddd; }
            .state-error, .state-invalid, .state-missing { background-color: #fcc; color: #400; }
            .state-notsupported { background-color: #fed; color: #432; }
            .state-valid { background-color: #cfc; color: #040; }
            td.message { font-size: 80%; }
            </style>
        """)
        output.write("<body>\n")
        output.write("<dl>{ds}</dl>".format(ds="".join(
            "<dt>{f}: {t}</dt><dd>{d}</dd>".format(f=f, t=k, d=v)
            for f in ["backend", "spec"]
            for k, v in report["stats"][f].items()
        )))
        for group_name, group in report["result"].items():
            output.write('<h1 class="state state-{s}">{g}: {s}</h1>\n'.format(g=group_name, s=group["group_summary"].lower()))
            output.write("<table>\n")
            output.write("<thead><tr>{ths}</tr></thead>\n".format(
                ths="".join("<th>{h}</th>".format(h=h) for h in ["name", "method", "url", "state", "message"])
            ))
            for endpoint_name, endpoint in group["endpoints"].items():
                output.write('''<tr class="state state-{s}"><td>{n}</td><td><code>{m}</code></td><td><code>{u}</code></td>
                    <td>{s}</td><td class="message">{g}</td></tr>
                '''.format(
                    n=endpoint_name, m=endpoint["type"], u=endpoint["url"], s=endpoint["state"].lower(),
                    g=endpoint.get("message")
                ))
            output.write("</table>\n")

        output.write("</body></html>\n")


if __name__ == '__main__':
    main(*sys.argv[1:])

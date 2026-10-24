"""Package init.

Runs before any `src.*` module, so it is the one place that can guarantee the
console can encode the output the rest of the package writes.

On Windows `sys.stdout`/`sys.stderr` default to the locale codepage (cp1252
here), so printing the status emoji this template uses -- the "❌" in
`global_error_handler`, `config`, `delete_uploaded_files` and
`generate_module` -- raises UnicodeEncodeError. In the error handler that is
fatal: the handler dies before it can build the JSON envelope and every
handled error (a 400 validation failure, a 401) turns into a bare 500
"Internal Server Error".
"""

import sys

for _stream in (sys.stdout, sys.stderr):
    reconfigure = getattr(_stream, "reconfigure", None)
    if reconfigure is not None:
        # errors="replace" so an exotic character degrades to "?" rather than
        # taking down the caller, whatever codepage the console is using.
        reconfigure(encoding="utf-8", errors="replace")

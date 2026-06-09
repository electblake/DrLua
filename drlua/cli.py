from __future__ import annotations

import typer
from drlua.create_bins import create_bins_app
from drlua.create_from_efu import create_from_efu_app
from drlua.copy import copy_app
from drlua.clean_create_bins_done import clean_create_bins_done_app
from drlua.clean_short_clips import clean_short_clips_app

app = typer.Typer(add_completion=False, no_args_is_help=True, pretty_exceptions_enable=False)
app.add_typer(create_bins_app)
app.add_typer(create_from_efu_app)
app.add_typer(copy_app)
app.add_typer(clean_create_bins_done_app)
app.add_typer(clean_short_clips_app)

if __name__ == "__main__":
    app()

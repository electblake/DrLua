from __future__ import annotations

import typer
from drlua.create_bins import create_bins_app
from drlua.organize_media_bin import organize_media_bin_app

app = typer.Typer(add_completion=False, no_args_is_help=True, pretty_exceptions_enable=False)
app.add_typer(create_bins_app)
app.add_typer(organize_media_bin_app)

if __name__ == "__main__":
    app()

from datetime import datetime
import json
import os
from pathlib import Path
import shutil

import click
from dynaconf import settings  # type: ignore

import librsync

from rschunks.delta import parse_delta_from_file
from rschunks.chunk import (
    read_chunks_from_file,
    update_chunks,
    serialize_file_chunks,
    deserialize_file_chunks,
)


storage_folder = Path(settings.STORAGE_FOLDER)
metadata_folder = Path(settings.METADATA_FOLDER)


@click.group()
@click.pass_context
def cli(ctx):
    pass


@cli.command()
@click.pass_context
@click.argument("filename")
def parse_delta(ctx, filename):
    for command in parse_delta_from_file(filename):
        print(command)


@cli.command()
@click.pass_context
@click.argument("filename")
def signature(ctx, filename: str):
    assert storage_folder in Path(filename).parents
    file_metadata_dir = metadata_folder / Path(filename).name

    if not file_metadata_dir.exists():
        file_metadata_dir.mkdir(parents=True)

    signature = os.fspath(file_metadata_dir / "signature")
    librsync.signature_from_paths(filename, signature, block_len=settings.CHUNK_SIZE)
    with open(file_metadata_dir / "base-chunks.json", "wt") as f:
        json.dump(serialize_file_chunks(read_chunks_from_file(filename)), f, indent=2)


@cli.command()
@click.pass_context
@click.argument("filename")
def update(ctx, filename: str):
    assert storage_folder in Path(filename).parents
    file_metadata_dir = metadata_folder / Path(filename).name
    signature = os.fspath(file_metadata_dir / "signature")
    delta = os.fspath(file_metadata_dir / "delta")
    librsync.delta_from_paths(signature, filename, delta)
    delta_commands = list(parse_delta_from_file(delta))
    with open(file_metadata_dir / "base-chunks.json", "rt") as f:
        base_chunks = deserialize_file_chunks(json.load(f))

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    shutil.move(
        file_metadata_dir / "chunks.json",
        file_metadata_dir / f"chunks-{timestamp}.json"
    )

    new_chunks = update_chunks(base_chunks, delta_commands, filename)
    with open(file_metadata_dir / "chunks.json", "wt") as f:
        json.dump(serialize_file_chunks(new_chunks), f, indent=2)


if __name__ == "__main__":
    cli(obj={})

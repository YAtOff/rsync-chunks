import os
from random import randint

import click
from faker import Faker, providers


fake = Faker()
fake.add_provider(providers.misc)


@click.command()
@click.argument("filename")
@click.option("--position", default=-1, type=int)
@click.option("--size", default=-1, type=int)
def mutate(filename: str, position: int, size: int):
    with open(filename, "r+b") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        position = position if position != -1 \
            else randint(0, file_size)
        assert position < file_size

        size = size if size != -1 else randint(1, file_size - position)
        assert size < file_size - position

        f.seek(position, os.SEEK_SET)

        f.write(fake.binary(size))


if __name__ == "__main__":
    mutate()

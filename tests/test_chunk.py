import random
from functools import reduce


from rschunks.chunk import (
    merge_chunks,
    split_chunks,
    get_chunks_in_range,
    handle_delta_commands,
    Chunk,
)
from rschunks.delta import LiteralDeltaCommand, CopyDeltaCommand


CHUNK_SIZE = 1024


def make_chunk(prev):
    size_ranges = [
        (0, CHUNK_SIZE),
        (CHUNK_SIZE, CHUNK_SIZE),
        (CHUNK_SIZE, CHUNK_SIZE * 10),
    ]
    size_range = random.choice(size_ranges)
    size = random.randint(*size_range)
    offset = 0 if prev is None else prev.offset + prev.size
    return Chunk(offset=offset, size=size)


def make_chunks(count):
    return reduce(
        lambda chunks, _: chunks + [make_chunk(chunks[-1])], range(count - 1), [make_chunk(None)]
    )


def test_merge_chunks():
    chunks = make_chunks(10)
    merged = list(merge_chunks(chunks, normal_chunk_size=CHUNK_SIZE))

    assert all(any(c.size >= CHUNK_SIZE for c in pair) for pair in zip(merged, merged[1:]))


def test_split_chunks():
    chunks = make_chunks(10)
    merged = merge_chunks(chunks, normal_chunk_size=CHUNK_SIZE)
    splitted = list(split_chunks(merged, min_size=CHUNK_SIZE))

    assert all(c.size <= CHUNK_SIZE for c in splitted)


def test_get_chunks_in_range():
    base_chunks = make_chunks(10)
    first = base_chunks[3]
    last = base_chunks[6]

    chunks = list(get_chunks_in_range(base_chunks, first.offset, last.offset + last.size))

    assert chunks == base_chunks[3:7]


def test_handle_delta_literal():
    chunks = list(
        handle_delta_commands([], [LiteralDeltaCommand(length=1), LiteralDeltaCommand(length=1)])
    )
    assert chunks == [Chunk(offset=0, size=1), Chunk(offset=1, size=1)]


def test_handle_delta_copy():
    base_chunks = make_chunks(10)
    first, last = base_chunks[3], base_chunks[6]
    start = first.offset
    end = last.offset + last.size
    chunks = list(
        handle_delta_commands(base_chunks, [CopyDeltaCommand(start=start, length=end - start)])
    )

    assert chunks == [
        Chunk(offset=c.offset - base_chunks[3].offset, size=c.size, hash=c.hash)
        for c in base_chunks[3:7]
    ]

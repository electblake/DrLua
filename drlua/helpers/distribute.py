from typing import Iterable, NamedTuple


class VideoItem(NamedTuple):
    filename: str
    frame_length: int


def split_videos_by_frame_count(
    videos: Iterable[VideoItem],
    group_count: int = 3,
) -> list[list[VideoItem]]:
    groups: list[list[VideoItem]] = [[] for _ in range(group_count)]
    totals = [0] * group_count

    # largest first gives better balance
    for video in sorted(videos, key=lambda v: v.frame_length, reverse=True):
        group_index = min(range(group_count), key=lambda i: totals[i])
        groups[group_index].append(video)
        totals[group_index] += video.frame_length

    # optional: shortest-to-longest inside each group
    for group in groups:
        group.sort(key=lambda v: v.frame_length)

    return groups

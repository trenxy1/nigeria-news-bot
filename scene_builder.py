"""
Groups TTS word-boundary timing data into scenes — each scene is one
complete sentence-level beat with a REAL start/end time taken directly from
when those words were actually spoken. Each scene also keeps its individual
word-level boundaries (in "words") so captions can be rendered word-by-word,
synced exactly to speech, instead of showing a whole sentence at once.
"""
MIN_WORDS_PER_SCENE = 5
MAX_WORDS_PER_SCENE = 22


def _group_into_sentences(boundaries: list[dict]) -> list[list[dict]]:
    groups = []
    current = []
    for b in boundaries:
        current.append(b)
        if b["word"].strip().endswith((".", "!", "?")):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _split_long_group(group: list[dict], max_words: int) -> list[list[dict]]:
    if len(group) <= max_words:
        return [group]
    return [group[i:i + max_words] for i in range(0, len(group), max_words)]


def _merge_short_groups(groups: list[list[dict]], min_words: int) -> list[list[dict]]:
    merged = []
    buffer: list[dict] = []
    for g in groups:
        buffer.extend(g)
        if len(buffer) >= min_words:
            merged.append(buffer)
            buffer = []
    if buffer:
        if merged:
            merged[-1] = merged[-1] + buffer
        else:
            merged.append(buffer)
    return merged


def build_scenes(boundaries: list[dict], total_audio_duration: float | None = None) -> list[dict]:
    """Returns [{"text": str, "duration": float, "words": list[dict]}, ...].
    "words" is the list of individual word-boundary dicts belonging to this
    scene, each with its own real "start"/"end" timestamp — this is what
    lets captions render word-by-word instead of a static full-sentence
    block."""
    if not boundaries:
        return []

    sentence_groups = _group_into_sentences(boundaries)

    split_groups = []
    for g in sentence_groups:
        split_groups.extend(_split_long_group(g, MAX_WORDS_PER_SCENE))

    final_groups = _merge_short_groups(split_groups, MIN_WORDS_PER_SCENE)

    scenes = []
    prev_end = 0.0
    for group in final_groups:
        text = " ".join(b["word"] for b in group)
        start = prev_end
        end = group[-1]["end"]
        duration = max(end - start, 0.1)
        scenes.append({"text": text, "duration": duration, "words": group})
        prev_end = end

    if total_audio_duration and scenes:
        covered = sum(s["duration"] for s in scenes)
        leftover = total_audio_duration - covered
        if leftover > 0:
            scenes[-1]["duration"] += leftover

    return scenes


if __name__ == "__main__":
    sample_boundaries = [
        {"word": "The", "start": 0.0, "end": 0.2},
        {"word": "house", "start": 0.2, "end": 0.5},
        {"word": "was", "start": 0.5, "end": 0.7},
        {"word": "quiet.", "start": 0.7, "end": 1.1},
    ]
    for s in build_scenes(sample_boundaries):
        print(s)

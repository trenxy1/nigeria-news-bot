"""
Groups TTS word-boundary timing data into scenes — each scene is one
complete sentence-level beat with a REAL start/end time taken directly from
when those words were actually spoken (not estimated). This is what
eliminates caption/image drift over the course of a long video.
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
    """boundaries: word-timing list from tts_generator.generate_audio_with_timing.
    Returns [{"text": str, "duration": float}, ...] with durations taken from
    real speech timing, contiguous (no gaps/overlaps). If total_audio_duration
    is given, the final scene is stretched to cover any trailing silence
    after the last word, so captions don't end early."""
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
        scenes.append({"text": text, "duration": duration})
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
        {"word": "Too", "start": 1.3, "end": 1.5},
        {"word": "quiet.", "start": 1.5, "end": 1.9},
    ]
    for s in build_scenes(sample_boundaries):
        print(s)

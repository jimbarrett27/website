def hello_world(game, taps: int = 3) -> dict:
    """Tap left `taps` times, then right `taps` times, noting each tap.

    An example of a library script: one function, named after its file, taking
    `game` first, with a docstring. It reports back with game.note() and its
    return value. It doesn't check where the player ends up; the screenshots in
    its trace show that.
    """
    for i in range(taps):
        game.tap("left", hold=8, after=16)
        game.note(f"tapped left ({i + 1} of {taps})")
    for i in range(taps):
        game.tap("right", hold=8, after=16)
        game.note(f"tapped right ({i + 1} of {taps})")
    return {"taps": taps * 2, "frames": game.frames_used}

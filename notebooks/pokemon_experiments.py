import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from pathlib import Path
    from pyboy import PyBoy
    import requests
    from enum import StrEnum
    import json

    return Path, PyBoy, StrEnum, json, requests


@app.cell
def _(Path):
    rom_path = Path('~/Downloads/pkmsil.gbc').expanduser()
    return (rom_path,)


@app.cell
def _(PyBoy, rom_path):
    pyboy = PyBoy(rom_path, window='null')
    with open('./pokemon/states/bedroom.state', 'rb') as f:
        pyboy.load_state(f)
    return (pyboy,)


@app.cell
def _(pyboy):
    for _ in range(120):
        pyboy.tick()
    return


@app.cell
def _(pyboy):
    pyboy.screen.image
    return


@app.cell
def _(requests):
    import base64
    import io

    OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
    OLLAMA_MODEL = "qwen3.6:35b"

    # measured on this box: 10 threads is the peak (13.5 tok/s), the default is
    # 7.6 and 32 collapses to 1.1 — dual socket, so threads must stay off the
    # second NUMA node. num_ctx has to hold a whole thinking pass, which runs to
    # ~6k tokens; ollama's 4096 default silently truncates it to nothing.
    OLLAMA_OPTIONS = {"num_thread": 10, "num_ctx": 16384}


    def _as_base64(image) -> str:
        """A PIL image as the bare base64 png that ollama's images field wants"""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()


    def prompt_qwen(
        system_prompt: str,
        user_prompt: str,
        thinking: bool = True,
        schema: dict | None = None,
        image=None,
        options: dict | None = None,
    ) -> str:

        user_message = {"role": "user", "content": user_prompt}
        if image is not None:
            user_message["images"] = [_as_base64(image)]

        body = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                user_message,
            ],
            # ollama keeps reasoning in its own field, so it coexists with format
            "think": thinking,
            "stream": False,
            "options": OLLAMA_OPTIONS | (options or {}),
        }
        if schema is not None:
            body["format"] = schema

        response = requests.post(OLLAMA_URL, json=body, timeout=1800)
        response.raise_for_status()
        return response.json()["message"]["content"]

    return (prompt_qwen,)


@app.cell
def _(StrEnum):
    class Button(StrEnum):
        A = "A"
        B = "B"
        START = "Start"
        UP = "Up"
        DOWN = "Down"
        LEFT = "Left"
        RIGHT = "Right"


    BUTTON_LIST = "\n".join(Button)
    BUTTON_SCHEMA = {
        "type": "object",
        "properties": {
            "button": {"type": "string", "enum": [_button.value for _button in Button]}
        },
        "required": ["button"],
        "additionalProperties": False,
    }
    return BUTTON_LIST, BUTTON_SCHEMA


@app.cell
def _(BUTTON_LIST):
    NAVIGATION_PROMPT = f"""
    You are playing pokemon silver on the gameboy colour. You will be given an image of the current situation and your goal, and should propose button presses to get you closer to your goal. 

    You should respond with JSON of the form {{"button": "A"}}, where the button is one of the following
    {BUTTON_LIST}
    """

    return (NAVIGATION_PROMPT,)


@app.cell
def _(StrEnum):
    class Situation(StrEnum):

        NAVIGATION = 'Navigation'
        BATTLE = 'Battle'
        DIALOGUE = 'Dialogue'
        MENU = 'Menu'
        OTHER = 'Other'

    SITUATION_LIST = "\n".join(Situation)
    SITUATION_SCHEMA = {
        "type": "object",
        "properties": {
            "situation": {"type": "string", "enum": [_situation.value for _situation in Situation]}
        },
        "required": ["situation"],
        "additionalProperties": False,
    }
    return (SITUATION_LIST,)


@app.cell
def _(SITUATION_LIST):
    SITUATION_PROMPT = f"""
    You are playing pokemon silver on the gameboy colour. You will be given an image of the current situation and your goal, and should decide which situation description best fits what you see, so that it can be passed to the right expert.

    For example, if you can see a dialogue box at the bottom of the screen, you should respond with Dialogue. If the character is navigating the world, respond with Navigate.

    You should respond with JSON of the form {{"situation": "..."}}, where the situation is one of the following
    {SITUATION_LIST}
    """
    return


@app.cell
def _():
    test_user_prompt = """
    Your current long term goal is to: Get to professor Elm
    Your current immediate goal is to: Get out of the bedroom
    """
    return (test_user_prompt,)


@app.cell
def _(
    BUTTON_SCHEMA,
    NAVIGATION_PROMPT,
    json,
    mo,
    prompt_qwen,
    pyboy,
    test_user_prompt,
):
    img = pyboy.screen.image
    for _ in range(10):
        img = pyboy.screen.image
        resp = prompt_qwen(NAVIGATION_PROMPT, test_user_prompt, schema=BUTTON_SCHEMA, image=img, thinking=True) 
        resp_parsed = json.loads(resp)
        pyboy.button(resp_parsed['button'], delay=10)
        mo.output.append(mo.hstack([mo.image(img, width=320), mo.md(f"### {resp_parsed['button']}")], align="center"))
        pyboy.tick(120)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

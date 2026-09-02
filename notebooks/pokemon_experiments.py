import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys, os

    REPO_ROOT = os.getcwd()
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    return


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
    from dataclasses import dataclass

    return Path, PyBoy, StrEnum, dataclass, requests


@app.cell
def _(Path):
    rom_path = Path('./pokemon/roms/pkmsil.gbc').expanduser()
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
def _(dataclass, requests):
    import base64
    import io

    LLAMACPP_URL = "http://127.0.0.1:8080/v1/chat/completions"
    LLAMACPP_MODEL = "qwen3.6-35b-vision"

    @dataclass
    class QwenResponse:
        response: str
        reasoning: str


    def _as_data_uri(image) -> str:
        """A PIL image as the base64 data: URI the OpenAI-style image_url wants"""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


    def prompt_qwen(
        system_prompt: str,
        user_prompt: str,
        thinking: bool = True,
        schema: dict | None = None,
        image=None,
        options: dict | None = None,
        verbose: bool = False
    ) -> str:

        if image is not None:
            user_content = [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": _as_data_uri(image)}},
            ]
        else:
            user_content = user_prompt

        body = {
            "model": LLAMACPP_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "chat_template_kwargs": {"enable_thinking": thinking},
            "stream": False,
        } | (options or {})
        if schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema},
            }

        response = requests.post(LLAMACPP_URL, json=body, timeout=1800)
        response.raise_for_status()

        first_response = response.json()["choices"][0]["message"]

        return QwenResponse(first_response["content"], first_response["reasoning_content"])

    return LLAMACPP_MODEL, base64, io


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
    return (BUTTON_LIST,)


@app.cell
def _(BUTTON_LIST, pyboy):
    from langchain_core.tools import tool


    @tool
    def press_button(button: str) -> str:
        """Press a button on the Game Boy and advance the emulator a few frames.

        button must be one of: A, B, Start, Up, Down, Left, Right
        """
        if button not in BUTTON_LIST.split("\n"):
            return f"'{button}' is not a valid button. Choose one of: {BUTTON_LIST}"
        pyboy.button(button, delay=10)
        pyboy.tick(120)
        return f"Pressed {button}."

    return press_button, tool


@app.cell
def _(tool):
    @tool
    def finish_task(summary: str) -> str:
        """Call this once, instead of press_button, when the screen shows the goal has been achieved.

        summary should briefly describe what on screen confirms it.
        """
        return f"Task marked finished: {summary}"

    return (finish_task,)


@app.cell
def _(HumanMessage, base64, io, mo, pokemon_agent, pyboy):
    def _image_to_data_uri(image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


    def navigate(goal: str, max_steps: int = 15) -> None:
        for step in range(max_steps):
            img = pyboy.screen.image

            step_events = []
            pokemon_agent.set_on_event(lambda name, kind, data, ev=step_events: ev.append((kind, data)))

            message = HumanMessage(content=[
                {"type": "text", "text": f"Goal: {goal}"},
                {"type": "image_url", "image_url": {"url": _image_to_data_uri(img)}},
            ])
            result = pokemon_agent.invoke([message])
            final_text = result["messages"][-1].content

            tool_calls = [d for kind, d in step_events if kind == "tool_call"]
            finish_calls = [d for d in tool_calls if d['tool'] == 'finish_task']

            summary = "; ".join(f"{d['tool']}({d['args']})" for d in tool_calls) or final_text[:200]
            mo.output.append(mo.hstack([mo.image(img, width=320), mo.md(f"**step {step}**: {summary}")], align="center"))

            if finish_calls:
                print(f"finished after {step + 1} step(s): {finish_calls[0]['args'].get('summary')}")
                return

        print(f"stopped after {max_steps} steps without finishing")

    return


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
def _(LLAMACPP_MODEL, finish_task, press_button):
    from agents import Agent
    from langchain_core.messages import HumanMessage
    from langchain_deepseek import ChatDeepSeek

    local_llm = ChatDeepSeek(
        model=LLAMACPP_MODEL,
        api_base="http://127.0.0.1:8080/v1",
        api_key="not-needed",
    ).bind(extra_body={"chat_template_kwargs": {"enable_thinking": True}})

    pokemon_agent = Agent(
        name="pokemon_agent",
        system_prompt='You are playing Pokemon Silver on a Game Boy Color. Each turn you are shown the current screen and a goal. Decide the single next button press that makes progress toward the goal and call press_button exactly once. You will be shown a fresh screenshot after it takes effect, so do not call press_button more than once per turn or guess ahead. If the screenshot already shows the goal achieved, call finish_task instead of press_button.',
        tools=[press_button, finish_task],
        llm=local_llm,
    )
    return HumanMessage, pokemon_agent


if __name__ == "__main__":
    app.run()

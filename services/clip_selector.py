import json

from google import genai
from google.genai import types

from config import settings
from models import ClipInfo


class SelectedClip(ClipInfo):
    in_time: float
    out_time: float
    order: int


class ClipSelector:
    def __init__(self):
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def select_and_order(
        self, clips: list[ClipInfo], prompt: str
    ) -> list[SelectedClip]:
        """
        Use Gemini to select and order clips that best fit the prompt, with in/out times.

        :param clips: List of analyzed ClipInfo objects.
        :param prompt: Creative direction describing the desired video.
        :return: Ordered list of SelectedClip with in/out times set.
        """
        clips_summary = "\n".join(
            f'{i}. path="{c.path}" duration={c.duration:.2f}s description="{c.description}"'
            for i, c in enumerate(clips)
        )

        system_prompt = (
            "You are a professional video editor. Given a list of video clips and a creative brief, "
            "select the best clips and determine edit points (in/out times) to assemble a compelling video. "
            "Respond ONLY with a valid JSON array — no markdown, no explanation. "
            'Each element must have: "clip_index" (int), "in_time" (float seconds), '
            '"out_time" (float seconds), "order" (int, starting at 0).'
        )

        user_message = (
            f"Creative brief: {prompt}\n\n"
            f"Available clips:\n{clips_summary}\n\n"
            "Select and order the clips. Use in_time=0 and out_time=duration when the full clip is wanted."
        )

        response = self._client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[system_prompt + "\n\n" + user_message],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        selections: list[dict] = json.loads(raw)

        selected: list[SelectedClip] = []
        for sel in sorted(selections, key=lambda x: x["order"]):
            idx = sel["clip_index"]
            source = clips[idx]
            in_time = float(sel["in_time"])
            out_time = float(sel["out_time"])
            in_time = max(0.0, min(in_time, source.duration))
            out_time = max(in_time + 0.1, min(out_time, source.duration))
            selected.append(
                SelectedClip(
                    path=source.path,
                    duration=source.duration,
                    description=source.description,
                    thumbnail_path=source.thumbnail_path,
                    in_time=in_time,
                    out_time=out_time,
                    order=sel["order"],
                )
            )

        return selected

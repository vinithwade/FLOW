# FLOW

**The keyboard moved.**

It's on your hands now.

---

A webcam. Three hand poses *you* invented. Your Mac doing what your fingers used to do.

FLOW watches your camera, learns the gestures **you** recorded — not the ones a product manager picked for you — and fires keystrokes when it sees them. Hold a pose, hold a key. Flash a pose, tap a key. That's the entire idea.

No drivers. No accessories. No cloud. Nothing leaves the machine.

---

## What it does today

| The gesture *you* recorded | What macOS feels |
| --- | --- |
| Left-hand pose held | `Fn` stays pressed |
| Left-hand pose dropped | `Fn` releases |
| Right-hand "send" pose appears | `Enter` tap |
| Right-hand "kill" pose appears | `Backspace` tap |

Three templates. Three triggers. Every one of them yours.

---

## Run it

You'll need a Mac, a webcam, Python 3.12, and [uv](https://github.com/astral-sh/uv).

```bash
uv sync                       # install dependencies
uv run capture.py left        # record the Fn-hold pose
uv run capture.py enter       # record the Enter pose
uv run capture.py delete      # record the Backspace pose
uv run handfn.py              # go
```

When the recorder counts down, **hold completely still** for seven seconds. Steady hand, sharp trigger. The lower the variance of your recording, the more precise the match.

The first launch will ask for Camera and Accessibility permission. Grant both.

---

## How it works

MediaPipe lands 21 points on each visible hand. The script normalizes them — wrist at the origin, scaled by the geometry of your palm — and compares them against the templates you saved. When the live pose lands inside the threshold, a Quartz `CGEvent` is piped straight to macOS.

Not magic. Geometry.

---

## What you should know

- **macOS only.** Quartz is the keyboard backend.
- **Accessibility permission is required.** Python has to be allowed to synthesize keystrokes.
- **`Fn` is half-special.** FLOW sets the Fn-modifier flag, so combos like `Fn`+arrows work. OS-level Fn behaviors (globe key, dictation) live below the CGEvent layer and won't fire.

---

## Recapture anytime

Don't like a pose? Replace it.

```bash
uv run capture.py left     # overwrites left_gesture.json
uv run capture.py enter    # overwrites enter_gesture.json
uv run capture.py delete   # overwrites delete_gesture.json
```

Next launch of FLOW picks up the new templates automatically.

---

## What's next

- Bind **any** pose to **any** key.
- A menubar app. No terminal.
- Apple Vision hand detection for sub-25ms latency.
- Multi-monitor calibration.

Until then: your hands are the input device. Bring them up.

<h1 align="center">FLOW</h1>

<p align="center">
  <a href="https://github.com/vinithwade/FLOW">
    <img src="https://readme-typing-svg.demolab.com?font=Inter&size=28&weight=700&pause=1500&color=FFFFFF&background=00000000&center=true&width=900&height=60&lines=Type+without+typing.;Hold+a+pose.+Hold+a+key.;Wispr+Flow%2C+now+hands-free." alt="Type without typing." />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-only-000000?style=for-the-badge&logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/MediaPipe-0097A7?style=for-the-badge" />
  <img src="https://img.shields.io/badge/built%20for-Wispr%20Flow-7C3AED?style=for-the-badge" />
</p>

---

## Why this exists

I use **Wispr Flow** every day. It's how I write almost everything now.

But every sentence starts the same way: tap `Fn`. Speak. Tap `Enter` to commit. Or `Backspace` to throw it away.

A tiny, modern miracle — still anchored to three physical keys.

That bothered me.

So I built FLOW. A script that watches my webcam, recognizes hand poses **I** designed, and presses those keys for me. Now I dictate while pacing the room. Slouched on the couch. Hands a foot from the laptop, never on it.

The keyboard didn't disappear. I just stopped touching it.

---

## What it does

| Your gesture | What macOS feels | Use it for |
| --- | --- | --- |
| Left-hand pose **held** | `Fn` stays pressed | Start dictating in Wispr Flow |
| Left-hand pose **dropped** | `Fn` releases | Stop dictating |
| Right-hand "send" pose | `Enter` tap | Commit the sentence |
| Right-hand "kill" pose | `Backspace` tap | Throw it away |

Three poses. Three triggers. Every one of them yours — you design them, FLOW remembers them.

---

## Run it

You'll need a Mac, a webcam, Python 3.12, and [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/vinithwade/FLOW.git
cd FLOW

uv sync                       # install dependencies
uv run capture.py left        # record the Fn-hold pose
uv run capture.py enter       # record the Enter pose
uv run capture.py delete      # record the Backspace pose
uv run handfn.py              # go
```

During each capture, **hold completely still** for the full seven seconds. The lower your variance, the sharper the trigger.

The first launch will ask for Camera and Accessibility permission. Grant both — FLOW needs the camera to see you, and Accessibility to press keys on your behalf.

---

## A typical session

```
    Walk into the kitchen.
    Raise your left hand.        → Fn pressed. Wispr Flow listens.
    Talk through your idea.
    Drop the pose.               → Fn released. Wispr Flow stops.
    Flash your "send" pose.      → Enter. The sentence lands in your editor.
    Walk back to the desk.
```

Never touched the laptop.

---

## How it works

MediaPipe lands 21 points on each visible hand. FLOW normalizes them — wrist at the origin, scaled by the geometry of your palm — and compares each live pose to the three templates you recorded. When the match falls inside the threshold, FLOW pipes a Quartz `CGEvent` straight to macOS.

Not magic. Geometry.

```
  webcam  →  MediaPipe (21 landmarks/hand)  →  normalize  →  template match  →  CGEvent  →  macOS
```

Every step runs locally. Nothing leaves the machine. No cloud, no telemetry, no account.

---

## What you should know

- **macOS only.** Quartz is the keyboard backend.
- **Accessibility permission required.** Python has to be allowed to synthesize keystrokes.
- **`Fn` is half-special.** FLOW sets the Fn-modifier flag, so Wispr Flow's `Fn`-hold-to-talk works perfectly. OS-level Fn behaviors that live below `CGEvent` (globe-key dictation, emoji picker shortcut) won't fire — but those aren't what you're after.
- **Lighting matters.** Bright, even lighting on your hand. Backlight from a window kills detection.

---

## Recapture anytime

Don't like a pose? Replace it in fifteen seconds.

```bash
uv run capture.py left     # overwrites left_gesture.json
uv run capture.py enter    # overwrites enter_gesture.json
uv run capture.py delete   # overwrites delete_gesture.json
```

Next launch of FLOW picks up the new templates automatically.

---

## What's next

- Bind **any** pose to **any** key. Not just Fn / Enter / Backspace.
- A menubar app. No terminal.
- Apple Vision hand detection for sub-25ms latency.
- Per-app profiles — different poses in different apps.
- Multi-monitor calibration.

---

<p align="center">
  <em>Your hands are the input device.<br/>Bring them up.</em>
</p>

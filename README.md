# Umamusume Auto Train

Like the title says, this is a simple auto training for Umamusume.

This project is inspired by [shiokaze/UmamusumeAutoTrainer](https://github.com/shiokaze/UmamusumeAutoTrainer)

[Demo video](https://youtu.be/CXSYVD-iMJk)

![Screenshot](screenshot.png)

## Features

- Automatically trains Uma
- Keeps racing until fan count meets the goal, and always picks races with matching aptitude
- Checks mood
- Handle debuffs
- Rest
- Prioritizes G1 races if available for fan farming

## Getting Started

### Requirements

- [Python 3.10+](https://www.python.org/downloads/)

### Setup

#### Clone repository

```
git clone https://github.com/samsulpanjul/umamusume-auto-train.git
```

#### Install dependencies

```
pip install -r requirements.txt
```

### BEFORE YOU START

Make sure these conditions are met:

- Screen resolution must be 1920x1080
- The game should be in fullscreen
- Your Uma must have already won the trophy for each race (the bot will skips the race)
- Turn off all confirmation pop-ups in game settings
- The game must be in the career lobby screen (the one with the Tazuna hint icon)

### Configuration

You can edit your configuration in `config.json`

```
{
  "priority_stat": ["spd", "sta", "wit", "pwr", "guts"],
  "minimum_mood": "NORMAL",
  "maximum_failure": 10,
  "prioritize_g1_race": false
}
```

`priority_stat` (array of strings)

Determines the training stat priority. The bot will focus on these stats in the given order of importance.
Accepted values: `"spd"`, `"sta"`, `"pwr"`, `"guts"`, `"wit"`

`minimum_mood` (string)

The lowest acceptable mood the bot will tolerate when deciding to train.
Accepted values (case-sensitive): `"GREAT"`, `"GOOD"`, `"NORMAL"`, `"BAD"`, `"AWFUL"`

**Example**: If set to `"NORMAL"`, the bot will train as long as the mood is `"NORMAL"` or better. If the mood drops below that, it’ll go for recreation instead.

`maximum_failure` (integer)

Sets the maximum acceptable failure chance (in percent) before skipping a training option.
Example: 10 means the bot will avoid training with more than 10% failure risk.

`prioritize_g1_race` (boolean)

If `true`, the bot will prioritize G1 races except during July and August (summer).
Useful for fan farming.

Make sure the values match exactly as expected, typos might cause errors.

### Start

```
python main.py
```

To stop the bot, just press `Ctrl + C` in your terminal, or move your mouse to the top-left corner of the screen.

### Training Logic

There are 2 training logics used:

1. Train in the area with the most support cards.
2. Train in an area with a rainbow support bonus.

During the first year, the bot will prioritize the first logic to quickly unlock rainbow training.

Starting from the second year, it switches to the second logic. If there’s no rainbow training and the failure chance is still below the threshold, it falls back to the first one.

### Known Issue

- Some Uma that has special event/target goals (like Restricted Train Goldship or 2 G1 Race Oguri Cap) may not working.
- OCR might misread failure chance (e.g., reads 33% as 3%) and proceeds with training anyway.
- Sometimes it misdetects debuffs and clicks the infirmary unnecessarily (not a big deal).
- Automatically picks the top option during chain events. Be careful with Acupuncture event, it always picks the top option.
- If you bring a friend support card (like Tazuna/Aoi Kiryuin) and do recreation, the bot can't decide whether to date with the friend support card or the Uma.
- When `prioritize_g1_race` is set to `true`, the bot will always prioritize racing, even if your energy is low or you've already done 3 or more consecutive races.

### TODO

- ~~Prioritize G1 races for farm fans~~
- Auto-purchase skills
- Automate Claw Machine event
- Add stat target feature, if a stat already hits the target, skip training that one

### Contribute

If you run into any issues or something doesn’t work as expected, feel free to open an issue.
Contributions are also very welcome, I would truly appreciate any support to help improve this project further.

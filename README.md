# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Below is a real run of `python main.py` (the temporary CLI testing ground). It
seeds owner Jordan with five pets — four common species plus Eomuk the sugar
glider (deliberately not in `SPECIES_DEFAULTS`, to exercise `DEFAULT_FALLBACK`)
— prints two pets' merged `care_needs`, honors the owner's busy hours, generates
the day, resolves a scheduling conflict, and regenerates a recurring task:

```text
$ python main.py
=== Biscuit (dog) - care_needs ===
  needs_walks: True
  needs_litter: False
  needs_habitat_cleaning: False
  needs_nail_trim: True
  needs_feeding: True
  needs_companion: False
  needs_temperature_control: False
  feeding_frequency_per_day: 2
  habitat: None
  supplies: ['food', 'waste bags']
  vet_frequency_days: 30
  vet_notes: None
  enrichment_note: None
  health_conditions: ['heart condition']

=== Eomuk (sugar glider) - care_needs ===
  needs_walks: False
  needs_litter: False
  needs_habitat_cleaning: True
  needs_nail_trim: False
  needs_feeding: True
  needs_companion: True
  needs_temperature_control: True
  feeding_frequency_per_day: 1
  habitat: cage
  supplies: ['food', 'glider diet mix', 'calcium supplement', 'pouch', 'climbing branches', 'exercise wheel']
  vet_frequency_days: 180
  vet_notes: requires exotic-animal vet
  enrichment_note: daily bonding/pouch time

Owner busy today:  [('12:00', '13:00')]
Owner free windows: [('00:00', '12:00'), ('13:00', '23:59')]

Daily plan for Jordan - 2026-07-07
Pets: Biscuit (dog), Mochi (cat), Nemo (fish), Kiwi (bird), Eomuk (sugar glider)
------------------------------------------------
  07:30 - Feed Biscuit breakfast (10 min) [priority: high]
  07:45 - Give Biscuit heart medication (5 min) [priority: high]
  08:00 - Feed Mochi breakfast (10 min) [priority: medium]
  08:15 - Feed Nemo (5 min) [priority: medium]
  08:30 - Feed Kiwi (5 min) [priority: medium]
  09:00 - Take Biscuit out for a walk (30 min) [priority: high]
  09:45 - Clean Mochi's litter box (10 min) [priority: low]
  10:30 - Clean Eomuk's cage (20 min) [priority: medium]
  11:30 - Buy a heating pad for Eomuk (20 min) [priority: low]
  13:00 - Midday playtime with Biscuit (20 min) [priority: low]
  13:30 - Clean Nemo's tank (20 min) [priority: low]
  14:00 - Vet appointment for Biscuit (monthly heart check) (45 min) [priority: high]
  15:30 - Clean Kiwi's cage (20 min) [priority: medium]
  18:00 - Feed Biscuit dinner (10 min) [priority: high]
  18:15 - Give Biscuit heart medication (5 min) [priority: high]
  18:30 - Feed Mochi dinner (10 min) [priority: medium]
  20:00 - Feed Eomuk evening meal (15 min) [priority: high]
  20:45 - Bonding/pouch time with Eomuk (20 min) [priority: medium]

Needs your decision (conflicts):
  - Grooming appointment for Mochi (wanted 13:45, couldn't fit)

Owner reschedules 'Grooming appointment for Mochi' -> 16:30
  moved into the plan

Updated plan for Jordan - 2026-07-07
------------------------------------------------
  07:30 - Feed Biscuit breakfast (10 min) [priority: high]
  07:45 - Give Biscuit heart medication (5 min) [priority: high]
  08:00 - Feed Mochi breakfast (10 min) [priority: medium]
  08:15 - Feed Nemo (5 min) [priority: medium]
  08:30 - Feed Kiwi (5 min) [priority: medium]
  09:00 - Take Biscuit out for a walk (30 min) [priority: high]
  09:45 - Clean Mochi's litter box (10 min) [priority: low]
  10:30 - Clean Eomuk's cage (20 min) [priority: medium]
  11:30 - Buy a heating pad for Eomuk (20 min) [priority: low]
  13:00 - Midday playtime with Biscuit (20 min) [priority: low]
  13:30 - Clean Nemo's tank (20 min) [priority: low]
  14:00 - Vet appointment for Biscuit (monthly heart check) (45 min) [priority: high]
  15:30 - Clean Kiwi's cage (20 min) [priority: medium]
  16:30 - Grooming appointment for Mochi (30 min) [priority: medium]
  18:00 - Feed Biscuit dinner (10 min) [priority: high]
  18:15 - Give Biscuit heart medication (5 min) [priority: high]
  18:30 - Feed Mochi dinner (10 min) [priority: medium]
  20:00 - Feed Eomuk evening meal (15 min) [priority: high]
  20:45 - Bonding/pouch time with Eomuk (20 min) [priority: medium]

Complete 'Take Biscuit out for a walk' (repeats every 1 day)...
  original marked done: True
  next occurrence 't6-next' generated, next_due: 2026-07-08
  (next_due is tomorrow, so it would NOT show in today's plan)
```

What this run demonstrates: species defaults vs. `DEFAULT_FALLBACK` (Eomuk), an
individual `care_needs` override (Biscuit's heart condition -> monthly vet + twice-daily
meds), list-stacking merges (Eomuk's supplies), owner **availability** (the noon
playtime nudged past the 12:00-13:00 busy block), mixed priorities and fixed/flexible
placement, a priority-decided conflict resolved by the owner (`pending_conflicts` ->
`apply_owner_time`), and **recurrence** (completing the daily walk regenerates it for
tomorrow via `next_due`).

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```text
$ python -m pytest
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\shuma\Desktop\AI 110\ai110-project2
plugins: anyio-4.13.0
collected 2 items

tests\test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.07s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority` | Orders by priority (high > medium > low), then earlier `time` |
| Filtering | `Scheduler.expand_recurring`, `Scheduler.get_tasks_by_category` | Keeps only tasks due today (`next_due <= date`); narrows a plan to one category |
| Conflict handling | `Scheduler.resolve_conflicts`, `Scheduler.apply_owner_time` | Detects overlaps (higher priority keeps the slot); flags losers to the owner, who picks a new time (no double-booking) |
| Recurring tasks | `Task.frequency` / `next_due`, `Pet.complete_task`, `Task.generate_next_occurrence` | Completing a task regenerates the next occurrence `frequency` days out |
| Availability | `Owner.get_free_slots`, `Scheduler.generate_daily_plan` | Flexible tasks nudge into free windows around the owner's busy blocks |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

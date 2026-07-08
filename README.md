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

## ✨ Features

- **Species-aware pet profiles** — each pet's `care_needs` is seeded from a species lookup (dog/cat/fish/bird) or a generic fallback, then merged with individual facts (list extras stack, scalars override).
- **Suggested tasks from care profile** — `get_default_tasks()` derives feeding, walks, litter, habitat cleaning, temperature checks, nail trims, enrichment, restocks, vet visits, and condition care straight from `care_needs`.
- **Sorting** — by priority then time (`sort_by_priority`) and chronologically (`sort_by_time`).
- **Filtering** — by completion status (`filter_by_status`), by pet (`Owner.get_tasks_for_pet`), and by category (`get_tasks_by_category`).
- **Daily recurrence** — recurring tasks carry a `next_due`; completing one regenerates the next occurrence `frequency` days out.
- **Conflict detection & resolution** — overlapping fixed tasks are flagged (higher priority keeps the slot) with human-readable warnings; the owner reschedules via `apply_owner_time` (no double-booking).
- **Availability-aware planning** — flexible tasks nudge into free windows around the owner's busy blocks.

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
— prints two pets' merged `care_needs`, derives suggested starter tasks for a
pet from its care profile (`get_default_tasks`), honors the owner's busy hours,
generates the day, resolves a scheduling conflict, and regenerates a recurring
task:

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

=== Suggested starter tasks for Eomuk (derived from care_needs) ===
  07:30 Feed Eomuk [feed] (every 1d)
  10:00 Clean Eomuk's cage [grooming] (every 7d)
  12:00 Check Eomuk's heating/temperature [maintenance] (every 1d)
  19:00 Enrichment for Eomuk: daily bonding/pouch time [enrichment] (every 1d)
  18:00 Restock food [restock_supply] (every 7d)
  18:00 Restock glider diet mix [restock_supply] (every 7d)
  18:00 Restock calcium supplement [restock_supply] (every 7d)
  18:00 Restock pouch [restock_supply] (every 7d)
  18:00 Restock climbing branches [restock_supply] (every 7d)
  18:00 Restock exercise wheel [restock_supply] (every 7d)
  10:00 Vet visit for Eomuk [vet] (every 180d)

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
collected 20 items

tests\test_pawpal.py ..                                                  [ 10%]
tests\test_scheduler.py ..................                               [100%]

============================= 20 passed in 0.04s ==============================
```

`test_pawpal.py` holds the two basic Step 3 tests (task completion, task
addition). `test_scheduler.py` covers the important scheduling behaviors:
care_needs merging (species defaults, fallback, list-stacking, scalar
override, case-insensitive lookup), priority and chronological sorting,
filtering (status / pet / category), fixed/flexible placement, owner
availability, conflict detection + `apply_owner_time`'s no-double-booking
guarantee, and recurrence via `next_due`.

**Confidence level:** ⭐⭐⭐⭐☆ (4 / 5) — the 21 tests cover the core scheduling
behaviors and all pass. Docked one star for edge cases not yet tested
(multiple busy blocks in a day, tasks crossing midnight, and multi-day
recurrence runs).

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority`, `Scheduler.sort_by_time` | Order by priority (high > medium > low) then time; or purely chronologically |
| Filtering | `Scheduler.filter_by_status`, `Owner.get_tasks_for_pet`, `Scheduler.get_tasks_by_category`, `Scheduler.expand_recurring` | By completion status, by pet name, by category; and by due-today (`next_due <= date`) |
| Conflict handling | `Scheduler.resolve_conflicts`, `Scheduler.get_conflict_warnings`, `Scheduler.apply_owner_time` | Detects overlaps (higher priority keeps the slot), emits warning strings, and lets the owner reschedule (no double-booking) |
| Recurring tasks | `Task.frequency` / `next_due`, `Pet.complete_task`, `Task.generate_next_occurrence` | Completing a task regenerates the next occurrence `frequency` days out |
| Availability | `Owner.get_free_slots`, `Scheduler.generate_daily_plan` | Flexible tasks nudge into free windows around the owner's busy blocks |

## 📸 Demo Walkthrough

Run the app with `streamlit run app.py`, then:

1. **Set the owner.** Enter the owner's name in the *Owner* section (defaults to "Jordan").
2. **Add a pet.** In *Add a pet*, enter a name and species (dog/cat/fish/bird, or "other" + a custom species like sugar glider) and an optional breed. Leave *Seed suggested tasks* checked to auto-populate its care tasks from the species/fallback care profile.
3. **Review & add tasks.** Expand a pet under *Your pets* to see its tasks, and use its *Add a task* form to add your own (description, duration, time, priority, and repeat interval).
4. **Generate the daily plan.** In *Generate daily plan*, pick the date, optionally block off a busy window, and click **Generate plan**. The plan lists each task at its scheduled time — fixed tasks held exactly, flexible ones ordered by priority and slotted into free time.
5. **Resolve conflicts.** If two fixed tasks collide, the loser is flagged; pick a new time and click **Reschedule** to slot it back in (the app refuses to double-book).

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

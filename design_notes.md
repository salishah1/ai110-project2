# PawPal Plus — Design Notes

## How It All Works (Plain English)

You create an **Owner** — your name and your general availability (when you're free versus tied up with work or other responsibilities). You add **Pets** to that owner, each needing just a name and a species.

The moment a Pet is created, its `care_needs` gets seeded automatically from a species lookup — a dog gets `needs_walks: True`, a cat gets `needs_litter: True`, a fish or bird gets `needs_habitat_cleaning: True` with its `habitat` set to `tank`/`cage`, and every pet gets baseline feeding (with a per-day frequency), supplies, and a vet-visit frequency. If the species isn't recognized, it falls back to a generic baseline instead. This copy happens once, right when the pet is created — nothing is typed in manually.

From there, anything specific to *that individual pet* — an allergy, a health condition, extra supplies, grooming needs — gets added into that same `care_needs` dict, right alongside the seeded baseline. There's no separation between "this came from the species" and "this is specific to this pet" — it's all one flat, complete picture of everything that pet needs. When an individual fact is a list — extra supplies, for example — it stacks on top of the species baseline rather than replacing it; scalar facts (a `True`/`False`, a number) overwrite the baseline value.

**Tasks are derived directly from that dict.** Every entry in `care_needs` — needs_walks, needs_litter, the supply list, the vet frequency, any health condition — becomes one suggested task. You review the suggestions and decide what actually gets added to that pet's real task list.

Each Task carries a target time it should happen at, whether that time is locked in stone or just a rough anchor, how long it takes, how important it is, and whether it repeats.

**Scheduler** builds the actual day. It doesn't hold tasks of its own — it asks the Owner for everything, across every pet, in one flat list. It figures out which recurring tasks are due today, places anything locked to an exact time first, then fits flexible tasks in near their own anchor time, using priority to decide who gets first pick when two things want the same slot.

**When two things genuinely collide**, Scheduler doesn't guess. It flags the conflict and sets the losing task aside, waiting for you to say where it should go. You tell it the new time, and it slots back into the real plan.

Day to day: view the whole plan, or narrow it to just one category (feeding times, shopping list). Check something off, and if it repeats, the next occurrence is generated automatically for whenever it's next due.

---

## Class Reference

### Task
A single pet-care activity — the smallest unit in the system.

| Attribute | Type | Meaning |
|---|---|---|
| `task_id` | str | Unique reference |
| `pet_id` | str | Which pet this belongs to — auto-set by `Pet.add_task()` |
| `description` | str | Human-readable label |
| `category` | str | Type tag (feed/walk/vet/grooming/restock_supply) |
| `duration` | int | Minutes |
| `priority` | str | Drives placement order |
| `time` | time | Always set — the anchor/target time |
| `is_flexible` | bool | False = must happen exactly at `time`. True = anchored there, but Scheduler may shift it |
| `frequency` | int or None | Days between repeats; None = one-time |
| `next_due` | date or None | Date this occurrence is due; None = due any day (undated) |
| `completed` | bool | Done or not |

**Methods:** `mark_complete()`, `generate_next_occurrence(completed_on=None) → Task or None` (dates the next occurrence `frequency` days after this one's `next_due`, or after `completed_on`), `edit(**fields)`

### Pet
One pet — its identity, its full care profile, and its own tasks.

| Attribute | Type | Meaning |
|---|---|---|
| `pet_id` | str | Unique reference |
| `name` | str | Display name |
| `species` | str | Drives the seed lookup |
| `breed` | str or None | Informational only — no effect on the seed lookup or merge |
| `care_needs` | dict | Everything this pet needs — species baseline + individual facts, merged into one dict at creation |
| `tasks` | list[Task] | This pet's own tasks |

*Class-level:* `SPECIES_DEFAULTS` (dog, cat, fish, bird), `DEFAULT_FALLBACK` — used once, at creation, to seed `care_needs`. Species lookup is case-insensitive. Every species dict and the fallback share an identical set of keys, so `care_needs` has the same shape regardless of species.

**Methods:** `add_task()`, `remove_task()`, `complete_task(task_id, on_date=None) → Task or None` (marks done and, if recurring, generates + adds the next occurrence), `add_condition()`, `remove_condition()`, `update_care_needs()`, `get_default_tasks(start_date=None) → list[Task]` (derives suggested tasks from the merged `care_needs` — feeding tasks per `feeding_frequency_per_day`, plus walks, litter, habitat cleaning, temperature checks, nail trims, enrichment, supply restocks, vet visits, and health conditions as applicable; each suggestion gets `next_due=start_date`)

### Owner
Manages pets, exposes their combined workload.

| Attribute | Type | Meaning |
|---|---|---|
| `owner_id` | str | Unique reference |
| `name` | str | Display name |
| `availability` | dict | Busy time blocks — a constraint only, never generates a task |
| `pets` | list[Pet] | This owner's pets |

**Methods:** `add_pet()`, `remove_pet()`, `get_free_slots(day) → list`, `get_all_tasks() → list[Task]` (flattens every pet's tasks — this is how Scheduler gets its data), `edit(**fields)`

### Scheduler
The brain. Not a dataclass — almost entirely behavior, little data of its own.

| Attribute | Type | Meaning |
|---|---|---|
| `date` | date | Day it's planning for |
| `owner` | Owner | Reference it pulls data from |
| `current_plan` | list[Task] | Cached result of the last generated plan |
| `pending_conflicts` | list[Task] | Tasks needing the owner's decision |

**Methods:** `expand_recurring(tasks, date)` (returns tasks due on `date` — incomplete and `next_due <= date`), `sort_by_priority()`, `generate_daily_plan() → list[Task]`, `resolve_conflicts(placements) → list[Task]` (given `(start, end, task)` placements in priority order, returns the overlap losers; detects, doesn't auto-fix), `apply_owner_time(task_id, new_time) → bool` (slots the task back in, or returns False and leaves it pending if the new time also collides — never double-books), `get_tasks_by_category()`, `get_plan_view()`

### How the classes connect
- **Owner owns Pets** (one owner, many pets)
- **Pet owns Tasks directly** (composition — tasks live inside the pet's own list)
- **Scheduler reads from Owner** — it has no tasks of its own; it calls `owner.get_all_tasks()` to get everything, and `owner.get_free_slots()` to know what time is actually open

---

## Design Changelog

### Phase 1 — Initial collaborative build
Worked through Owner, Pet, Task, and a class originally called **Schedule** through extended back-and-forth. Landed on `SPECIES_DEFAULTS` + `DEFAULT_FALLBACK` specifically to solve one problem: not wanting to manually re-type basic per-species facts (needs_walks, needs_litter) into every new pet. At this stage, `care_needs` held *only* the individual-specific facts (allergies, conditions, grooming) — separate from the species lookup, which lived independently on the class and got checked separately every time tasks were generated. This is the point where your original idea — one unified dict — got missed in favor of two separate mechanisms.

Task also had `is_recurring` + `recurrence_interval_days` as two fields, plus a `fixed_time` boolean, and an optional `pet_id` (since Task wasn't yet owned by Pet directly).

### Phase 2 — Aligned to the official assignment spec (your screenshots)
The course's Phase 2 instructions describe Task as "a single activity (description, time, frequency, completion status)," Pet as "stores pet details **and a list of tasks**," Owner as "manages multiple pets and provides access to all their tasks," and Scheduler as "the brain that retrieves, organizes, and manages tasks across pets."

This caused real structural changes:
- **Renamed Schedule → Scheduler** to match the spec exactly.
- **Moved tasks into Pet directly** — Pet now owns a `tasks` list (composition), with `add_task()`/`remove_task()` added. Previously Task only loosely referenced a pet; now containment is real.
- **Added `Owner.get_all_tasks()`** — directly answers the spec's hint about how Scheduler should retrieve tasks from an Owner's pets.
- **Scheduler stopped holding a persistent task list of its own** — it pulls from Owner on demand instead, keeping only `current_plan` as a cache.
- **Simplified Task's fields** to match the spec's wording: `is_recurring` + `recurrence_interval_days` merged into a single `frequency` field.

### Phase 3 — Time and flexibility redesign
You raised that a task marked "flexible" still needs an actual target time (a flexible breakfast shouldn't land at 8pm). This led to the final Task time model: `time` is **always set** as the anchor, and `is_flexible` is a separate bool controlling whether Scheduler is allowed to nudge it. No new field needed for "how far can it drift" — that's judgment Scheduler applies using `priority`, `category`, and `duration`, which were already there.

You then pushed for the owner to be asked before things get moved, rather than the app deciding — leading to `pending_conflicts` and `apply_owner_time()` on Scheduler, and `resolve_conflicts()` being redefined to *detect and report* conflicts rather than silently auto-resolving them.

### Phase 4 — care_needs unification (correcting Phase 1's miss)
You pointed out that Task and `care_needs` should be directly connected — `care_needs` should hold *everything* about a pet, and tasks should be derived straight from it, one per entry. This was your original framing from early on, which got split into two separate mechanisms back in Phase 1.

Fix: `SPECIES_DEFAULTS` (or `DEFAULT_FALLBACK`) now gets copied into `care_needs` **once, at Pet creation** — via `__post_init__`. After that, `care_needs` is one flat, self-contained dict with no distinction between species-derived facts and individual ones. `get_default_tasks()` no longer checks two separate sources — it loops through the now-unified `care_needs` and produces one task per relevant entry. `SPECIES_DEFAULTS`/`DEFAULT_FALLBACK` still exist as class-level lookups; they're just used once as seed data instead of being checked on every call.

### Phase 5 — Species expansion & merge hardening
Added **fish** and **bird** to `SPECIES_DEFAULTS` alongside dog and cat, and broadened the `care_needs` schema so those species' real needs are expressible:
- New keys: `needs_feeding` + `feeding_frequency_per_day` (dogs/cats ~2×/day, fish 1×, birds 2×), `needs_habitat_cleaning` + `habitat` (fish `tank`, bird `cage`), and `needs_nail_trim` (kept species-level — genuinely species-true for dogs/cats/birds, not an individual trait). Fish/bird supplies filled out (`water conditioner`, `bedding`).
- **Merge fix:** individual `care_needs` passed at creation now *combine* with the baseline for list values (extras stack) instead of overwriting the whole list; scalars still overwrite. Previously `supplies=["cat tree"]` would wipe out the seeded `["food", "litter"]`.
- **Case-insensitive species lookup:** `"Dog"` now resolves to the dog defaults instead of silently falling through to `DEFAULT_FALLBACK`.
- `get_default_tasks()` extended to emit feeding (one per daily feeding), habitat-cleaning, and nail-trim tasks from the new keys — keeping tasks derived straight from `care_needs`.

### Phase 6 — Sugar glider fallback test + breed attribute
The goal: verify `DEFAULT_FALLBACK` actually works in practice — not in isolation, but interacting correctly with `SPECIES_DEFAULTS`, the merge/override logic, and the rest of the classes end to end.

**Why a sugar glider specifically.** Picked a real, permanent pet whose species is deliberately *not* one of the four built-out ones (dog, cat, fish, bird), and whose needs differ from all of them in almost every category — temperature control, a required companion animal, a highly specialized diet, and a completely different kind of habitat. The logic: if the fallback-plus-override mechanism can produce accurate, complete care data for something this different from what it was originally tested against, that's real evidence the mechanism generalizes to any future species, not just a coincidence of the four already hardcoded.

**Research.** Catalogued everything a sugar glider owner actually manages: housing (tall cage, narrow bar spacing, nest pouch, climbing branches), temperature control (75–80°F), diet (specialized glider mix, calcium supplement, fed once in the evening), social needs (must have a companion, daily bonding time), enrichment (silent exercise wheel, chew toys), grooming (minimal, no nail trims needed), habitat cleaning, vet care (requires an exotic-animal specialist), legal/permit restrictions in some states, and a 10–15 year lifespan.

**Sorting the facts.** Each item mapped to one of three buckets: already covered by existing keys (no walks, no litter, habitat cleaning, no nail trim — all correctly False/True in `DEFAULT_FALLBACK` by coincidence), needs a new key, or genuinely out of scope for `care_needs` (feeding *time* belongs on the Task itself, not the pet's facts; legal/permit info and lifespan aren't actionable and don't generate any task).

**New schema-wide concepts.** Two genuinely new facts emerged that no existing key covered: needing a companion animal, and needing temperature control. Rather than treating these as one-off entries just for the glider, added `needs_companion` and `needs_temperature_control` to *every* species dict (dog, cat, fish, bird) and `DEFAULT_FALLBACK`, so every pet's `care_needs` keeps the same shape regardless of species — a requirement the merge logic and `get_default_tasks()` both depend on.

**A misstep, caught and reverted.** At one point the sugar glider was given its own dedicated `SPECIES_DEFAULTS` entry. That defeated the actual purpose — the point was proving the fallback path produces accurate results for an uncommon pet, not building a fifth hardcoded species. Reverted: sugar glider stays deliberately absent from `SPECIES_DEFAULTS`, and its accuracy comes entirely from `DEFAULT_FALLBACK` plus individual `care_needs` overrides.

**A side discovery.** Auditing all four species dicts while adding the two new keys surfaced an existing inaccuracy: bird's `needs_companion` and `needs_temperature_control` had defaulted to False. Corrected to True — pet birds are social flock animals and are sensitive to cold, so both facts are genuinely true for the species.

**Breed attribute.** Added `breed` as a new field on `Pet` — informational only, with zero effect on the species lookup or merge logic. Considered and rejected building out a full breed-level defaults tier (a third layer beneath species): individual differences like an overweight dog needing more walks or less food already flow correctly through individual `care_needs`, the same mechanism used for every other individual fact — a breed tier would add real complexity (a breed lookup table that could never be complete) without solving a problem the existing two-tier system doesn't already handle.

Note: The breed issue and the misstep of adding the sugar glider to secies default was entirely AI's mistake. It wasn't something I had considered doing, but rather was AI jumping the gun. I rejected and corrected it upon seeing it and redirected it to what I wanted the system design to be like. 

**Final schema additions.** Added `vet_notes` and `enrichment_note` as standard keys across every species dict and `DEFAULT_FALLBACK` (defaulted to None), since owners need an ongoing place to record individual notes for any pet, not just unusual ones. Confirmed `update_care_needs()` already handles editing either of these — or any other key — generically, so no new method was required.

**Net result.** Every `care_needs` dict — dog, cat, fish, bird, and the fallback — now shares an identical set of keys. Eomuk the sugar glider (in `main.py`) demonstrates the fallback mechanism correctly producing complete, accurate care data for a real, uncommon pet with no dedicated species entry, which is the actual proof this part of the design works as intended.

### Phase 7 — Real recurrence, completion flow, and scheduler hardening
Tightened the behaviors that were still stubbed-simple after the first implementation, in preparation for writing tests:

- **Real recurrence.** Added a `next_due` (date) field to `Task`. `expand_recurring()` now returns only incomplete tasks whose `next_due` is on or before the planning date (`next_due=None` = undated, due any day). This is what makes daily-vs-weekly actually work — a weekly task done today won't reappear until its regenerated occurrence's `next_due` arrives. To guarantee this everywhere, `Task.__post_init__` gives any recurring task (frequency set) a concrete starting `next_due` (today if none was passed) — so a weekly/monthly task created anywhere (including hand-typed ones in `main.py`) isn't mistakenly treated as "due any day." One-time tasks keep `next_due=None`.
- **Completion → next occurrence.** `generate_next_occurrence(completed_on=None)` now dates the next task `frequency` days after this one's `next_due` (or after `completed_on`). New `Pet.complete_task(task_id, on_date=None)` marks a task done and, if it recurs, generates + adds the next occurrence — wiring up the "check it off and the next one appears" behavior end to end. (`mark_complete()` stays a simple flag-flip; the regeneration lives on `Pet`, which owns the task list.)
- **`resolve_conflicts()` is now a real detector.** It takes `(start, end, task)` placements in priority order and returns the overlap losers (earlier/higher-priority tasks keep their slot). `generate_daily_plan()` uses it for fixed-task collisions instead of the old inline check, so conflict detection is independently testable.
- **`apply_owner_time()` won't double-book.** It now validates the owner's chosen time against availability and the current plan; if the new time also collides it returns False and leaves the task in `pending_conflicts` rather than silently overlapping something.
- **Owner availability exercised.** Fixed tasks that fall in the owner's busy blocks are flagged; flexible tasks nudge past them. `main.py` now sets a midday busy block to demonstrate this.

### Phase 8 — Implementation, tests, and UI integration
Turned the design into a working, verified system and connected it to the UI.

- **Logic implemented.** Filled in every method across `Task`, `Pet`, `Owner`, and `Scheduler` (previously logic-free stubs). `Scheduler` pulls tasks only through `Owner.get_all_tasks()` (and `get_free_slots()`), never reaching into `owner.pets` directly — keeping it ignorant of how Owner/Pet store data (encapsulation). Every method has at least a one-line docstring.
- **CLI demo (`main.py`).** A temporary testing ground: owner Jordan with five pets (dog, cat, fish, bird, and Eomuk the sugar glider), an individual heart-condition override on the dog (monthly vet + twice-daily meds), a busy block, a priority-decided conflict, and a completion→regeneration demo. Task descriptions are built from each pet's `.name` attribute, and `get_default_tasks()`'s suggestions are printed to show the care_needs→tasks derivation.
- **`get_default_tasks()` completed.** Now also derives a temperature-control check (`needs_temperature_control`) and an enrichment task (`enrichment_note`), which it previously ignored — so a pet like the sugar glider gets its heating and bonding needs suggested straight from `care_needs`. Every suggestion is stamped with a starting `next_due` (via a `start_date` argument, today by default) so recurring suggestions honor their frequency.
- **Tests (`tests/`).** `test_pawpal.py` holds the two required basic tests (task completion, task addition); `test_scheduler.py` adds fuller coverage of care_needs merging, priority sorting, fixed/flexible placement, availability, conflict detection, `apply_owner_time`'s no-double-booking guarantee, and recurrence via `next_due`. 21 tests pass under `python -m pytest`.
- **Streamlit UI (`app.py`).** The UI is a thin bridge over the same classes: it imports Owner/Pet/Task/Scheduler, persists the `Owner` in `st.session_state` so pets/tasks survive Streamlit's reruns, and wires the Add-a-pet / Add-a-task forms to `Owner.add_pet()` / `Pet.add_task()` (optionally seeding via `get_default_tasks()`). The *Generate daily plan* action calls `Scheduler.generate_daily_plan()`, shows the ordered plan with its reasoning, and resolves conflicts through `apply_owner_time()`.

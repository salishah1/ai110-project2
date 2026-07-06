# PawPal Plus — Design Notes

## How It All Works (Plain English)

You create an **Owner** — your name and your general availability (when you're free versus tied up with work or other responsibilities). You add **Pets** to that owner, each needing just a name and a species.

The moment a Pet is created, its `care_needs` gets seeded automatically from a species lookup — a dog gets `needs_walks: True`, a cat gets `needs_litter: True`, every pet gets baseline supplies and a baseline vet-visit frequency. If the species isn't recognized, it falls back to a generic baseline instead. This copy happens once, right when the pet is created — nothing is typed in manually.

From there, anything specific to *that individual pet* — an allergy, a health condition, extra supplies, grooming needs — gets added into that same `care_needs` dict, right alongside the seeded baseline. There's no separation between "this came from the species" and "this is specific to this pet" — it's all one flat, complete picture of everything that pet needs.

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
| `completed` | bool | Done or not |

**Methods:** `mark_complete()`, `generate_next_occurrence() → Task`, `edit(**fields)`

### Pet
One pet — its identity, its full care profile, and its own tasks.

| Attribute | Type | Meaning |
|---|---|---|
| `pet_id` | str | Unique reference |
| `name` | str | Display name |
| `species` | str | Drives the seed lookup |
| `care_needs` | dict | Everything this pet needs — species baseline + individual facts, merged into one dict at creation |
| `tasks` | list[Task] | This pet's own tasks |

*Class-level:* `SPECIES_DEFAULTS`, `DEFAULT_FALLBACK` — used once, at creation, to seed `care_needs`.

**Methods:** `add_task()`, `remove_task()`, `add_condition()`, `remove_condition()`, `update_care_needs()`, `get_default_tasks() → list[Task]` (derives one suggested task per relevant `care_needs` entry)

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

**Methods:** `expand_recurring()`, `sort_by_priority()`, `generate_daily_plan() → list[Task]`, `resolve_conflicts()` (detects, doesn't auto-fix), `apply_owner_time(task_id, new_time)`, `get_tasks_by_category()`, `get_plan_view()`

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

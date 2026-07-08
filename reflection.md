# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started from three core actions: make a profile, add a pet, and see today's schedule. Working backward from that, four classes fell out:

- **Owner** — holds the person's name and availability, manages a list of pets, and exposes every pet's tasks as one combined list.
- **Pet** — holds identity (name, species), a `care_needs` profile of everything true about that pet, and its own list of tasks.
- **Task** — one care activity (description, category, duration, priority, target time, flexibility, recurrence, completion status).
- **Scheduler** — the "brain" that holds no tasks of its own but pulls them from the Owner to build the daily plan (originally named `Schedule`).

*The full description of everything I did, my complete system design, and every change I made is documented in detail in `design_notes.md` — see that file for the full details.*

**b. Design changes**

Yes. Originally the species baseline facts (a dog needs walks, a cat needs litter) lived in a separate lookup checked independently from each pet's `care_needs` dict — two mechanisms. I had always pictured `care_needs` as the single, complete picture of a pet, so I restructured it: the species defaults are now copied into `care_needs` once, at pet creation, making the dict the one source of truth. I also renamed `Schedule` to `Scheduler` and moved tasks to live inside each Pet's own list (composition) after checking the design against the course's official class responsibilities. *(Full changelog in `design_notes.md`.)*

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers fixed vs. flexible time (a task with `is_flexible=False` must land exactly at its `time`, while a flexible one is only anchored there), priority (who gets first pick when two tasks want the same slot), duration, owner availability (the free windows the plan has to fit into), and recurrence (which repeating tasks are actually due that day). Time and priority mattered most, because those are the constraints that force a decision when the day is crowded: fixed-time tasks are placed first, then flexible ones are fit near their anchor, with priority breaking ties.

**b. Tradeoffs**

When two fixed-time tasks genuinely collide, the scheduler does **not** try to auto-resolve it — it keeps the higher-priority task in its slot, flags the loser in `pending_conflicts`, and waits for the owner to pick a new time (`apply_owner_time`). The tradeoff is autonomy for correctness: the app can't magically pick a good replacement time because it has no context about the person's actual day. Handing the decision back — rather than guessing and silently double-booking — is the safer, more trustworthy behavior for a real owner.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI throughout: brainstorming the class breakdown, pressure-testing the design against concrete pet examples (an overweight cat, an allergy, a sugar glider), generating the class skeleton, implementing the scheduling logic, writing the tests, and hunting for bugs before I trusted it. The most helpful prompts were concrete ("is this a *fact* about the pet or a *task* on a schedule?"), scenario-driven ("run this design through a busy day"), and adversarial ("what's missing or broken before I write tests?").

**b. Judgment and verification**

Several times I didn't take a suggestion as-is. When the species defaults got split into a separate lookup, I pushed back and unified everything into `care_needs`. When a suggested fix for the recurring-task bug only patched `get_default_tasks()`, I moved the guard onto `Task.__post_init__` so it held everywhere. I even caught one of my own tests encoding a wrong assumption about recurrence. I verified by actually running the code — the `main.py` CLI demo, `python -m pytest`, and Streamlit's `AppTest` — and by tracing specific cases (the priority-decided conflict, the busy-block nudge) against the output rather than trusting explanations.

---

## 4. Testing and Verification

**a. What you tested**

Two basic tests cover task completion (`mark_complete`) and task addition (`Pet.add_task` growing the list). A fuller suite covers the scheduling logic: `care_needs` merging (species defaults, fallback for unknown species, list-stacking, scalar override, case-insensitive lookup), priority sorting, fixed-exact vs. flexible-nudged placement, owner availability, conflict detection keeping the higher priority, `apply_owner_time`'s no-double-booking guarantee, and recurrence via `next_due` (due-date filtering, completion regenerating the next occurrence, anchoring to the due date). These matter because scheduling correctness is the app's whole promise — if recurrence, placement, or conflicts are wrong, the plan is wrong.

**b. Confidence**

Fairly confident in the backend: 21 tests pass, and I exercised the flow end to end through both the CLI and the Streamlit app. If I had more time I'd test: multiple busy blocks in one day, a task longer than any free window, tasks near the midnight boundary, and many colliding fixed tasks at once — plus a multi-day run to confirm recurring tasks advance exactly on their `next_due`.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with `care_needs` as a single source of truth and the fact that I kept catching and correcting my own mistakes — the split lookup, the flexible-task-with-no-time flaw, and the recurring-task due-date bug — rather than defending them. Making recurrence actually work (not just "shows every day") felt like the design becoming real.

**b. What you would improve**

I'd read the full assignment spec before designing so I didn't restructure twice, and I'd wire the UI earlier to catch integration issues sooner. In the code, completed tasks accumulate in a pet's list forever (they're filtered from the plan but never removed) — I'd add history/purge handling — and flexible placement only nudges forward, never earlier, which I'd make smarter.

**c. Key takeaway**

The best decisions came from holding two lenses at once — clean, non-redundant code *and* a real pet owner's experience. And working with AI, the real skill is verification: it's a fast collaborator, but the recurring-task bug slipped through plausible-looking code and only surfaced because I ran it and wrote tests. Trust, but check.

"""
main.py — temporary testing ground for PawPal+.

Builds owner Jordan with the four common species plus Eomuk, a sugar glider
(the DEFAULT_FALLBACK stress test). Biscuit the dog also gets an individual
heart condition layered on top of the dog species defaults, to show
per-pet care_needs overrides driving extra tasks (meds + more frequent vet).
Then adds a varied day — mixed priorities, fixed vs flexible, interleaved
timings — and prints the schedule.
Run with:  python main.py
"""

from datetime import date, time

from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo_owner() -> Owner:
    owner = Owner(owner_id="o1", name="Jordan")

    biscuit = Pet(pet_id="p1", name="Biscuit", species="dog", breed="Golden Retriever")
    mochi = Pet(pet_id="p2", name="Mochi", species="cat")
    nemo = Pet(pet_id="p3", name="Nemo", species="fish")
    kiwi = Pet(pet_id="p4", name="Kiwi", species="bird")
    # Eomuk is a sugar glider — NOT in SPECIES_DEFAULTS. Its care_needs comes
    # from DEFAULT_FALLBACK plus these individual overrides.
    eomuk = Pet(
        pet_id="p5",
        name="Eomuk",
        species="sugar glider",
        care_needs={
            "habitat": "cage",
            "needs_companion": True,
            "needs_temperature_control": True,
            "supplies": [
                "glider diet mix", "calcium supplement", "pouch",
                "climbing branches", "exercise wheel",
            ],
            "vet_notes": "requires exotic-animal vet",
            "enrichment_note": "daily bonding/pouch time",
        },
    )

    # Biscuit has an individual heart condition — layered on top of the dog
    # species defaults via the care_needs edit methods. This is a per-pet
    # fact, not a species one, so it lives in the individual's care_needs.
    biscuit.add_condition("heart condition")
    biscuit.update_care_needs("vet_frequency_days", 30)  # monthly vet, not yearly

    for pet in (biscuit, mochi, nemo, kiwi, eomuk):
        owner.add_pet(pet)

    # Tasks, written the way an owner naturally would — each pet's name is
    # pulled from its .name attribute via f-strings, never hard-coded. pet_id
    # is left blank; add_task() stamps it automatically. Priorities,
    # flexibility, and times are deliberately mixed and interleaved.
    def task(tid, description, category, duration, priority, at, flexible=True, freq=1):
        return Task(
            task_id=tid, pet_id="", description=description, category=category,
            duration=duration, priority=priority, time=at,
            is_flexible=flexible, frequency=freq,
        )

    # --- Morning: meals, then Biscuit's post-meal heart meds (fixed) ---
    biscuit.add_task(task("t1", f"Feed {biscuit.name} breakfast", "feed", 10, "high", time(7, 30), flexible=False))
    biscuit.add_task(task("t2", f"Give {biscuit.name} heart medication", "medication", 5, "high", time(7, 45), flexible=False))
    mochi.add_task(task("t3", f"Feed {mochi.name} breakfast", "feed", 10, "medium", time(8, 0)))
    nemo.add_task(task("t4", f"Feed {nemo.name}", "feed", 5, "medium", time(8, 15)))
    kiwi.add_task(task("t5", f"Feed {kiwi.name}", "feed", 5, "medium", time(8, 30)))

    # --- Interleaved daytime care (mixed priorities + flexible) ---
    biscuit.add_task(task("t6", f"Take {biscuit.name} out for a walk", "walk", 30, "high", time(9, 0)))
    mochi.add_task(task("t7", f"Clean {mochi.name}'s litter box", "grooming", 10, "low", time(9, 45)))
    eomuk.add_task(task("t8", f"Clean {eomuk.name}'s cage", "grooming", 20, "medium", time(10, 30)))
    # One-time purchase — sugar gliders need a warm climate, so a heating pad.
    eomuk.add_task(task("t9", f"Buy a heating pad for {eomuk.name}", "restock_supply", 20, "low", time(11, 30), freq=None))
    nemo.add_task(task("t10", f"Clean {nemo.name}'s tank", "grooming", 20, "low", time(13, 0), freq=7))
    # Monthly heart check — a fixed appointment that must hold its time.
    biscuit.add_task(task("t11", f"Vet appointment for {biscuit.name} (monthly heart check)", "vet", 45, "high", time(14, 0), flexible=False, freq=30))
    kiwi.add_task(task("t12", f"Clean {kiwi.name}'s cage", "grooming", 20, "medium", time(15, 30)))
    # Midday playtime anchored at noon — but the owner is busy 12:00-13:00
    # (see availability in main), so the Scheduler nudges it past the busy
    # block into the afternoon.
    biscuit.add_task(task("t19", f"Midday playtime with {biscuit.name}", "enrichment", 20, "low", time(12, 0)))
    # A groomer booking that collides with the fixed vet appointment above.
    # Both are fixed, but grooming is only MEDIUM priority vs the vet's HIGH —
    # and grooming is even booked slightly EARLIER (13:45). The Scheduler still
    # places the higher-priority vet first and flags the grooming as the
    # conflict for the owner to resolve, so priority (not time) decides.
    mochi.add_task(task("t18", f"Grooming appointment for {mochi.name}", "grooming", 30, "medium", time(13, 45), flexible=False, freq=None))

    # --- Evening: dinners, second heart-med dose, nocturnal glider care ---
    biscuit.add_task(task("t13", f"Feed {biscuit.name} dinner", "feed", 10, "high", time(18, 0), flexible=False))
    biscuit.add_task(task("t14", f"Give {biscuit.name} heart medication", "medication", 5, "high", time(18, 15), flexible=False))
    mochi.add_task(task("t15", f"Feed {mochi.name} dinner", "feed", 10, "medium", time(18, 30)))
    eomuk.add_task(task("t16", f"Feed {eomuk.name} evening meal", "feed", 15, "high", time(20, 0)))
    eomuk.add_task(task("t17", f"Bonding/pouch time with {eomuk.name}", "enrichment", 20, "medium", time(20, 45)))

    return owner


def print_care_needs(pet: Pet) -> None:
    print(f"=== {pet.name} ({pet.species}) - care_needs ===")
    for key, value in pet.care_needs.items():
        print(f"  {key}: {value}")


def main() -> None:
    owner = build_demo_owner()
    today = date.today()

    # Biscuit: individual heart condition layered on the dog species defaults.
    biscuit = next(p for p in owner.pets if p.name == "Biscuit")
    print_care_needs(biscuit)
    print()

    # Eomuk: fallback stress test — no SPECIES_DEFAULTS entry, so its
    # care_needs proves DEFAULT_FALLBACK + overrides produce complete data.
    eomuk = next(p for p in owner.pets if p.name == "Eomuk")
    print_care_needs(eomuk)
    print()

    # get_default_tasks() turns a pet's care profile into suggested starter
    # tasks — what the app would offer the owner to review/accept when a pet
    # is added (and what will feed the "suggested tasks" step in the UI).
    print("=== Suggested starter tasks for Eomuk (derived from care_needs) ===")
    for t in eomuk.get_default_tasks(start_date=today):
        freq = f"every {t.frequency}d" if t.frequency else "one-time"
        print(f"  {t.time.strftime('%H:%M')} {t.description} [{t.category}] ({freq})")
    print()

    # The owner has a busy block midday (a meeting/lunch), keyed to today's
    # weekday — the Scheduler treats it as unavailable time.
    owner.availability = {today.strftime("%A").lower(): [(time(12, 0), time(13, 0))]}

    def fmt_windows(windows):
        return [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in windows]

    busy = owner.availability.get(today.strftime("%A").lower(), [])
    print(f"Owner busy today:  {fmt_windows(busy)}")
    print(f"Owner free windows: {fmt_windows(owner.get_free_slots(today))}")
    print()

    scheduler = Scheduler(date=today, owner=owner)
    scheduler.generate_daily_plan()

    print(f"Daily plan for {owner.name} - {today.isoformat()}")
    print(f"Pets: {', '.join(f'{p.name} ({p.species})' for p in owner.pets)}")
    print("-" * 48)
    for line in scheduler.get_plan_view():
        print(f"  {line}")

    if scheduler.pending_conflicts:
        print("\nNeeds your decision (conflicts):")
        for task in scheduler.pending_conflicts:
            print(f"  - {task.description} (wanted {task.time.strftime('%H:%M')}, couldn't fit)")

        # The owner steps in and picks a new time for the flagged task —
        # apply_owner_time() slots it back in (and refuses to double-book).
        conflict = scheduler.pending_conflicts[0]
        new_time = time(16, 30)
        print(f"\nOwner reschedules '{conflict.description}' -> {new_time.strftime('%H:%M')}")
        moved = scheduler.apply_owner_time(conflict.task_id, new_time)
        print(f"  {'moved into the plan' if moved else 'new time also busy - still pending'}")

        print("\nUpdated plan for {} - {}".format(owner.name, today.isoformat()))
        print("-" * 48)
        for line in scheduler.get_plan_view():
            print(f"  {line}")

    # --- Sorting & filtering (Scheduler.sort_by_time / filter_by_status,
    #     Owner.get_tasks_for_pet) ---
    all_tasks = owner.get_all_tasks()
    print("\nAll tasks earliest-first (sort_by_time), first 5:")
    for t in scheduler.sort_by_time(all_tasks)[:5]:
        print(f"  {t.time.strftime('%H:%M')} {t.description}")
    pending = scheduler.filter_by_status(all_tasks, completed=False)
    done = scheduler.filter_by_status(all_tasks, completed=True)
    print(f"Status filter -> pending: {len(pending)}, completed: {len(done)}")
    print(f"Pet filter -> Biscuit has {len(owner.get_tasks_for_pet('Biscuit'))} task(s)")

    # --- Recurrence: completing a recurring task regenerates the next one ---
    walk = next(t for t in biscuit.tasks if t.category == "walk")
    print(f"\nComplete '{walk.description}' (repeats every {walk.frequency} day)...")
    nxt = biscuit.complete_task(walk.task_id, on_date=today)
    print(f"  original marked done: {walk.completed}")
    print(f"  next occurrence '{nxt.task_id}' generated, next_due: {nxt.next_due}")
    print("  (next_due is tomorrow, so it would NOT show in today's plan)")


if __name__ == "__main__":
    main()

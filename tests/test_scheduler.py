"""
Fuller tests for PawPal+'s scheduling behaviors.

Covers the logic beyond the two basic tests in test_pawpal.py: care_needs
merging (species defaults + fallback), priority sorting, fixed/flexible
placement, owner availability, conflict detection + resolution, and
recurrence via next_due. Deterministic — all dates/times are passed in.

Run from the project root with:  python -m pytest
"""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler

# A fixed reference date (a Tuesday) so tests never depend on "today".
DAY = date(2026, 7, 7)


def make_task(tid, at, duration=10, priority="high", flexible=True,
              freq=None, next_due=None, category="feed"):
    """Builds a Task with sensible defaults for the field under test."""
    return Task(
        task_id=tid, pet_id="", description=tid, category=category,
        duration=duration, priority=priority, time=at, is_flexible=flexible,
        frequency=freq, next_due=next_due,
    )


# --- care_needs merging -----------------------------------------------------

def test_species_defaults_seeded():
    dog = Pet(pet_id="p", name="Rex", species="dog")
    assert dog.care_needs["needs_walks"] is True


def test_fallback_for_unknown_species():
    glider = Pet(pet_id="p", name="Eomuk", species="sugar glider")
    assert glider.care_needs["needs_habitat_cleaning"] is True  # from fallback
    assert glider.care_needs["needs_walks"] is False


def test_list_values_stack_not_overwrite():
    cat = Pet(pet_id="p", name="Milo", species="cat", care_needs={"supplies": ["cat tree"]})
    assert cat.care_needs["supplies"] == ["food", "litter", "cat tree"]


def test_scalar_values_override():
    cat = Pet(pet_id="p", name="Milo", species="cat", care_needs={"needs_walks": True})
    assert cat.care_needs["needs_walks"] is True


def test_species_lookup_is_case_insensitive():
    dog = Pet(pet_id="p", name="Rex", species="DOG")
    assert dog.care_needs["needs_walks"] is True


# --- get_default_tasks sets next_due (the recurrence bug fix) ----------------

def test_default_tasks_get_starting_next_due():
    dog = Pet(pet_id="p", name="Rex", species="dog")
    suggestions = dog.get_default_tasks(start_date=DAY)
    assert suggestions  # non-empty
    assert all(t.next_due == DAY for t in suggestions)


def test_completed_recurring_task_does_not_reappear_next_day():
    """
    After completing a weekly default task, its regenerated occurrence is due
    a frequency-cycle out — so it does NOT show the next day (this is the
    behavior the next_due-at-creation fix enables).
    """
    dog = Pet(pet_id="p", name="Rex", species="dog")
    dog.tasks = dog.get_default_tasks(start_date=DAY)
    vet = next(t for t in dog.tasks if t.task_id == "p-vet")
    nxt = dog.complete_task("p-vet", on_date=DAY)
    assert nxt.next_due == DAY + timedelta(days=vet.frequency)

    next_day = DAY + timedelta(days=1)
    sched = Scheduler(date=next_day, owner=Owner("o", "x"))
    due_ids = {t.task_id for t in sched.expand_recurring(dog.tasks, next_day)}
    assert "p-vet" not in due_ids      # completed original is filtered out
    assert nxt.task_id not in due_ids  # regenerated one isn't due for a week


def test_next_due_anchors_recurrence_to_due_date_not_completion():
    """A task due DAY but completed late still recurs from its due date."""
    pet = Pet("p", "B", "dog")
    pet.add_task(make_task("weekly", time(8, 0), freq=7, next_due=DAY))
    nxt = pet.complete_task("weekly", on_date=DAY + timedelta(days=2))  # 2 days late
    assert nxt.next_due == DAY + timedelta(days=7)  # anchored to due date, not completion


# --- Owner ------------------------------------------------------------------

def test_get_all_tasks_flattens_across_pets():
    owner = Owner("o", "Jordan")
    p1, p2 = Pet("p1", "A", "dog"), Pet("p2", "B", "cat")
    owner.add_pet(p1)
    owner.add_pet(p2)
    p1.add_task(make_task("a", time(8, 0)))
    p2.add_task(make_task("b", time(9, 0)))
    assert {t.task_id for t in owner.get_all_tasks()} == {"a", "b"}


def test_get_free_slots_subtracts_busy_blocks():
    owner = Owner("o", "Jordan")
    owner.availability = {DAY.strftime("%A").lower(): [(time(12, 0), time(13, 0))]}
    free = owner.get_free_slots(DAY)
    assert (time(0, 0), time(12, 0)) in free
    assert (time(13, 0), time(23, 59)) in free


# --- Scheduler: sorting & placement -----------------------------------------

def test_sort_by_priority_then_time():
    sched = Scheduler(date=DAY, owner=Owner("o", "x"))
    tasks = [
        make_task("lo", time(7, 0), priority="low"),
        make_task("hi", time(9, 0), priority="high"),
        make_task("mid", time(8, 0), priority="medium"),
    ]
    assert [t.task_id for t in sched.sort_by_priority(tasks)] == ["hi", "mid", "lo"]
    # equal priority -> earlier time first
    tie = [make_task("late", time(10, 0)), make_task("early", time(8, 0))]
    assert [t.task_id for t in sched.sort_by_priority(tie)] == ["early", "late"]


def test_fixed_placed_exactly_flexible_nudged():
    owner = Owner("o", "x")
    pet = Pet("p1", "B", "dog")
    owner.add_pet(pet)
    pet.add_task(make_task("fixed", time(9, 0), duration=30, flexible=False))
    pet.add_task(make_task("flex", time(9, 0), duration=30, flexible=True))
    sched = Scheduler(date=DAY, owner=owner)
    sched.generate_daily_plan()
    assert sched.scheduled_times["fixed"] == time(9, 0)   # held its anchor
    assert sched.scheduled_times["flex"] == time(9, 30)   # nudged past the fixed one


def test_fixed_task_in_busy_time_is_flagged():
    owner = Owner("o", "x")
    owner.availability = {DAY.strftime("%A").lower(): [(time(12, 0), time(13, 0))]}
    pet = Pet("p1", "B", "dog")
    owner.add_pet(pet)
    pet.add_task(make_task("lunchwalk", time(12, 15), duration=20, flexible=False))
    sched = Scheduler(date=DAY, owner=owner)
    sched.generate_daily_plan()
    assert "lunchwalk" in {t.task_id for t in sched.pending_conflicts}


# --- Scheduler: conflict detection & resolution -----------------------------

def test_conflict_detection_keeps_higher_priority():
    owner = Owner("o", "x")
    pet = Pet("p1", "B", "dog")
    owner.add_pet(pet)
    pet.add_task(make_task("vet", time(14, 0), duration=45, priority="high", flexible=False))
    pet.add_task(make_task("groom", time(14, 15), duration=30, priority="medium", flexible=False))
    sched = Scheduler(date=DAY, owner=owner)
    sched.generate_daily_plan()
    assert "vet" in {t.task_id for t in sched.current_plan}       # high kept its slot
    assert {t.task_id for t in sched.pending_conflicts} == {"groom"}


def test_apply_owner_time_refuses_double_booking():
    owner = Owner("o", "x")
    pet = Pet("p1", "B", "dog")
    owner.add_pet(pet)
    pet.add_task(make_task("vet", time(14, 0), duration=45, priority="high", flexible=False))
    pet.add_task(make_task("groom", time(14, 15), duration=30, priority="medium", flexible=False))
    sched = Scheduler(date=DAY, owner=owner)
    sched.generate_daily_plan()

    # A colliding time is rejected; the task stays pending.
    assert sched.apply_owner_time("groom", time(14, 0)) is False
    assert "groom" in {t.task_id for t in sched.pending_conflicts}

    # A free time is accepted and slotted into the plan.
    assert sched.apply_owner_time("groom", time(16, 30)) is True
    assert "groom" in {t.task_id for t in sched.current_plan}
    assert sched.pending_conflicts == []


# --- Recurrence -------------------------------------------------------------

def test_expand_recurring_filters_by_due_date():
    sched = Scheduler(date=DAY, owner=Owner("o", "x"))
    tasks = [
        make_task("today", time(8, 0), next_due=DAY),
        make_task("past", time(8, 0), next_due=date(2026, 7, 1)),
        make_task("future", time(8, 0), next_due=date(2026, 7, 8)),
        make_task("undated", time(8, 0), next_due=None),
        make_task("done", time(8, 0), next_due=DAY),
    ]
    tasks[-1].completed = True
    due = {t.task_id for t in sched.expand_recurring(tasks, DAY)}
    assert due == {"today", "past", "undated"}


def test_complete_task_regenerates_next_occurrence():
    pet = Pet("p1", "B", "dog")
    pet.add_task(make_task("walk", time(8, 0), freq=7, next_due=DAY))
    nxt = pet.complete_task("walk", on_date=DAY)
    assert pet.tasks[0].completed is True
    assert nxt is not None
    assert nxt.next_due == date(2026, 7, 14)  # DAY + 7 days
    assert len(pet.tasks) == 2                # original + regenerated


def test_complete_one_time_task_returns_none():
    pet = Pet("p1", "B", "dog")
    pet.add_task(make_task("bath", time(8, 0), freq=None))
    assert pet.complete_task("bath") is None
    assert len(pet.tasks) == 1

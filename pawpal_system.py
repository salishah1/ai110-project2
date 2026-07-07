"""
Pawpal System — Core classes for PawPal Plus

Four classes: Task, Pet, Owner, Scheduler.
See design_notes.md for the full design rationale and changelog.
"""

import copy
from dataclasses import dataclass, field
from typing import List, Optional, ClassVar, Dict, Any
from datetime import date, time, datetime, timedelta


# Priority ordering used across scheduling (higher rank = placed first).
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """
    Represents a single pet-care activity.
    Belongs to exactly one Pet — pet_id is set automatically by
    Pet.add_task(), not assigned manually.
    """
    task_id: str
    pet_id: str
    description: str
    category: str
    duration: int  # minutes
    priority: str
    time: time  # anchor/target time — always set, whether fixed or flexible
    is_flexible: bool  # False = must occur exactly at `time`; True = Scheduler may shift it
    frequency: Optional[int] = None  # days between repeats; None = one-time
    completed: bool = False

    def mark_complete(self) -> None:
        """Marks this task as done."""
        self.completed = True

    def generate_next_occurrence(self) -> "Task":
        """
        For recurring tasks (frequency is not None), builds and returns
        the next Task instance for the following cycle (fresh, not completed).
        Returns None for one-time tasks.
        """
        if self.frequency is None:
            return None
        return Task(
            task_id=f"{self.task_id}-next",
            pet_id=self.pet_id,
            description=self.description,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            time=self.time,
            is_flexible=self.is_flexible,
            frequency=self.frequency,
            completed=False,
        )

    def edit(self, **fields) -> None:
        """Updates one or more of this task's own fields in place."""
        for key, value in fields.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class Pet:
    """
    Represents one pet, including its full care profile and task list.

    care_needs is seeded from SPECIES_DEFAULTS (or DEFAULT_FALLBACK if the
    species isn't listed) once, at creation, then merged with anything
    specific to this individual pet — resulting in one flat dict describing
    everything this pet needs. get_default_tasks() derives suggested tasks
    directly from that merged dict.
    """

    SPECIES_DEFAULTS: ClassVar[Dict[str, Dict[str, Any]]] = {
        "dog": {
            "needs_walks": True,
            "needs_litter": False,
            "needs_habitat_cleaning": False,
            "needs_nail_trim": True,
            "needs_feeding": True,
            "needs_companion": False,
            "needs_temperature_control": False,
            "feeding_frequency_per_day": 2,
            "habitat": None,
            "supplies": ["food", "waste bags"],
            "vet_frequency_days": 365,
            "vet_notes": None,
            "enrichment_note": None,
        },
        "cat": {
            "needs_walks": False,
            "needs_litter": True,
            "needs_habitat_cleaning": False,
            "needs_nail_trim": True,
            "needs_feeding": True,
            "needs_companion": False,
            "needs_temperature_control": False,
            "feeding_frequency_per_day": 2,
            "habitat": None,
            "supplies": ["food", "litter"],
            "vet_frequency_days": 365,
            "vet_notes": None,
            "enrichment_note": None,
        },
        "fish": {
            "needs_walks": False,
            "needs_litter": False,
            "needs_habitat_cleaning": True,
            "needs_nail_trim": False,
            "needs_feeding": True,
            "needs_companion": False,
            "needs_temperature_control": False,
            "feeding_frequency_per_day": 1,
            "habitat": "tank",
            "supplies": ["food", "water conditioner"],
            "vet_frequency_days": 180,
            "vet_notes": None,
            "enrichment_note": None,
        },
        "bird": {
            "needs_walks": False,
            "needs_litter": False,
            "needs_habitat_cleaning": True,
            "needs_nail_trim": True,
            "needs_feeding": True,
            "needs_companion": True,
            "needs_temperature_control": True,
            "feeding_frequency_per_day": 2,
            "habitat": "cage",
            "supplies": ["food", "bedding"],
            "vet_frequency_days": 365,
            "vet_notes": None,
            "enrichment_note": None,
        },
    }

    DEFAULT_FALLBACK: ClassVar[Dict[str, Any]] = {
        "needs_walks": False,
        "needs_litter": False,
        "needs_habitat_cleaning": True,
        "needs_nail_trim": False,
        "needs_feeding": True,
        "needs_companion": False,
        "needs_temperature_control": False,
        "feeding_frequency_per_day": 1,
        "habitat": None,
        "supplies": ["food"],
        "vet_frequency_days": 180,
        "vet_notes": None,
        "enrichment_note": None,
    }

    pet_id: str
    name: str
    species: str
    breed: Optional[str] = None  # informational only — no effect on seed lookup or merge
    care_needs: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)

    def __post_init__(self):
        """
        Seed care_needs from the species lookup (or the generic fallback),
        merged with anything passed in at creation. Scalars from the
        individual pet override the baseline; lists get combined instead of
        replaced, so individual supplies/extras stack on top of the species
        baseline rather than wiping it out. Lookup is case-insensitive.
        Runs once.
        """
        seed = self.SPECIES_DEFAULTS.get(self.species.lower(), self.DEFAULT_FALLBACK)
        merged = copy.deepcopy(seed)

        for key, value in self.care_needs.items():
            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key] = merged[key] + value  # stack extras on the baseline
            else:
                merged[key] = value  # scalars overwrite

        self.care_needs = merged

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet's list and stamps it with this pet's ID."""
        task.pet_id = self.pet_id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Removes a task from this pet's list by ID."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def add_condition(self, condition: str) -> None:
        """Adds a health condition into care_needs."""
        conditions = self.care_needs.setdefault("health_conditions", [])
        if condition not in conditions:
            conditions.append(condition)

    def remove_condition(self, condition: str) -> None:
        """Removes a health condition from care_needs."""
        conditions = self.care_needs.get("health_conditions", [])
        if condition in conditions:
            conditions.remove(condition)

    def update_care_needs(self, key: str, value: Any) -> None:
        """Controlled way to update a single entry in care_needs."""
        self.care_needs[key] = value

    def get_default_tasks(self) -> List[Task]:
        """
        Derives suggested Task objects directly from this pet's care_needs —
        one task per relevant entry. Returns suggestions only; the caller
        decides what to actually add via add_task().
        """
        suggestions: List[Task] = []

        def suggest(key, description, category, duration, priority, at, freq):
            suggestions.append(
                Task(
                    task_id=f"{self.pet_id}-{key}",
                    pet_id=self.pet_id,
                    description=description,
                    category=category,
                    duration=duration,
                    priority=priority,
                    time=at,
                    is_flexible=True,
                    frequency=freq,
                )
            )

        cn = self.care_needs
        if cn.get("needs_feeding"):
            feed_times = [time(7, 30), time(18, 0), time(12, 30)]
            times_per_day = cn.get("feeding_frequency_per_day", 1)
            for i in range(times_per_day):
                at = feed_times[i] if i < len(feed_times) else time(7, 30)
                suggest(
                    f"feed-{i + 1}", f"Feed {self.name}", "feed",
                    10, "high", at, 1,
                )
        if cn.get("needs_walks"):
            suggest("walk", f"Walk {self.name}", "walk", 30, "high", time(8, 0), 1)
        if cn.get("needs_litter"):
            suggest("litter", f"Clean {self.name}'s litter box", "grooming", 10, "medium", time(9, 0), 1)
        if cn.get("needs_habitat_cleaning") and cn.get("habitat"):
            suggest(
                "habitat", f"Clean {self.name}'s {cn['habitat']}", "grooming",
                20, "medium", time(10, 0), 7,
            )
        if cn.get("needs_nail_trim"):
            suggest(
                "nail-trim", f"Trim {self.name}'s nails", "grooming",
                15, "low", time(11, 0), 30,
            )
        for supply in cn.get("supplies", []):
            suggest(
                f"restock-{supply}", f"Restock {supply}", "restock_supply",
                15, "low", time(18, 0), 7,
            )
        if cn.get("vet_frequency_days"):
            suggest(
                "vet", f"Vet visit for {self.name}", "vet",
                60, "medium", time(10, 0), cn["vet_frequency_days"],
            )
        for condition in cn.get("health_conditions", []):
            suggest(
                f"cond-{condition}", f"Medication/care for {condition}", "vet",
                5, "high", time(8, 0), 1,
            )
        return suggestions


@dataclass
class Owner:
    """
    Represents the pet owner/profile. Manages pets and exposes their
    combined task list. availability holds busy time blocks per weekday —
    a constraint only; it never generates tasks itself.
    """
    owner_id: str
    name: str
    availability: Dict[str, Any] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to this owner's list."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Removes a pet by ID."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_free_slots(self, day: date) -> list:
        """
        Returns the owner's open time windows for the given day as a list of
        (start_time, end_time) tuples: the whole day minus the busy blocks
        stored in availability (keyed by lowercase weekday name).
        """
        day_start, day_end = time(0, 0), time(23, 59)
        busy = sorted(self.availability.get(day.strftime("%A").lower(), []))
        if not busy:
            return [(day_start, day_end)]

        free = []
        cursor = day_start
        for start, end in busy:
            if start > cursor:
                free.append((cursor, start))
            if end > cursor:
                cursor = end
        if cursor < day_end:
            free.append((cursor, day_end))
        return free

    def get_all_tasks(self) -> List[Task]:
        """
        Flattens every pet's tasks into one combined list. This is the ONLY
        way Scheduler gets task data — it never reaches into owner.pets
        directly (keeps Scheduler ignorant of how Owner/Pet store things).
        """
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def edit(self, **fields) -> None:
        """Updates the owner's own info (name, availability) in place."""
        for key, value in fields.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Scheduler:
    """
    The 'brain' — builds and manages the daily plan.

    Not a dataclass: this class is almost entirely behavior, not stored
    data. It pulls tasks from Owner on demand rather than holding its
    own permanent task list.
    """

    def __init__(self, date: date, owner: Owner):
        self.date = date
        self.owner = owner
        self.current_plan: List[Task] = []
        self.pending_conflicts: List[Task] = []
        # Actual placed start time per task_id (may differ from a flexible
        # task's own anchor time once the Scheduler nudges it).
        self.scheduled_times: Dict[str, time] = {}

    def expand_recurring(self, tasks: List[Task], date: date) -> List[Task]:
        """
        Determines which tasks are due on the given date. (The current data
        model has no per-task next-due date, so this treats every incomplete
        task — one-time and recurring alike — as due today.)
        """
        return [t for t in tasks if not t.completed]

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Orders tasks so higher-priority (and then earlier) ones come first."""
        return sorted(
            tasks,
            key=lambda t: (_PRIORITY_RANK.get(t.priority, 1), t.time),
        )

    def _to_dt(self, t: time) -> datetime:
        return datetime.combine(self.date, t)

    def _slot_is_free(self, start: datetime, dur: timedelta, free_windows, placed) -> bool:
        end = start + dur
        within_free = any(
            self._to_dt(fs) <= start and end <= self._to_dt(fe)
            for fs, fe in free_windows
        )
        if not within_free:
            return False
        overlaps = any(
            not (end <= s or start >= e) for s, e, _ in placed
        )
        return not overlaps

    def generate_daily_plan(self) -> List[Task]:
        """
        Pulls all tasks via self.owner.get_all_tasks(), keeps those due today,
        places fixed-time (is_flexible=False) tasks exactly, fits flexible
        tasks near their anchor inside the owner's free slots, and stores the
        result in self.current_plan. Anything that can't be placed goes to
        self.pending_conflicts.
        """
        self.pending_conflicts = []
        self.scheduled_times = {}

        todays = self.expand_recurring(self.owner.get_all_tasks(), self.date)
        ordered = self.sort_by_priority(todays)
        free_windows = self.owner.get_free_slots(self.date)

        placed = []  # (start_dt, end_dt, task)
        day_end = self._to_dt(time(23, 59))
        step = timedelta(minutes=15)

        for task in ordered:
            dur = timedelta(minutes=task.duration)
            anchor = self._to_dt(task.time)

            if not task.is_flexible:
                # Must land exactly at its anchor, or it's a conflict.
                if self._slot_is_free(anchor, dur, free_windows, placed):
                    placed.append((anchor, anchor + dur, task))
                    self.scheduled_times[task.task_id] = task.time
                else:
                    self.pending_conflicts.append(task)
                continue

            # Flexible: try the anchor, then scan forward until end of day.
            chosen = None
            cursor = anchor
            while cursor + dur <= day_end:
                if self._slot_is_free(cursor, dur, free_windows, placed):
                    chosen = cursor
                    break
                cursor += step
            if chosen is not None:
                placed.append((chosen, chosen + dur, task))
                self.scheduled_times[task.task_id] = chosen.time()
            else:
                self.pending_conflicts.append(task)

        placed.sort(key=lambda p: p[0])
        self.current_plan = [t for _, _, t in placed]
        return self.current_plan

    def resolve_conflicts(self, plan: List[Task]) -> List[Task]:
        """
        Detects (does not auto-fix) collisions. Returns the tasks that need
        the owner's decision — the ones set aside in pending_conflicts.
        """
        return self.pending_conflicts

    def apply_owner_time(self, task_id: str, new_time: time) -> None:
        """
        Applies the owner's chosen time to a previously flagged task and moves
        it back into current_plan, re-sorted by scheduled time.
        """
        task = next((t for t in self.pending_conflicts if t.task_id == task_id), None)
        if task is None:
            return
        self.pending_conflicts.remove(task)
        task.time = new_time
        self.scheduled_times[task_id] = new_time
        self.current_plan.append(task)
        self.current_plan.sort(
            key=lambda t: self.scheduled_times.get(t.task_id, t.time)
        )

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Filters current_plan down to a single category."""
        return [t for t in self.current_plan if t.category == category]

    def get_plan_view(self) -> list:
        """Formats current_plan for display, sorted by scheduled time."""
        lines = []
        for task in self.current_plan:
            at = self.scheduled_times.get(task.task_id, task.time)
            lines.append(
                f"{at.strftime('%H:%M')} - {task.description} "
                f"({task.duration} min) [priority: {task.priority}]"
            )
        return lines

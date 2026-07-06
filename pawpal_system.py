"""
Pawpal System — Core class skeleton for PawPal Plus

Four classes: Task, Pet, Owner, Scheduler.
Method bodies are intentionally left as stubs — fill in logic per the
design notes (design_notes.md) using your AI coding assistant.
"""

from dataclasses import dataclass, field
from typing import List, Optional, ClassVar, Dict, Any
from datetime import date, time


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
        pass

    def generate_next_occurrence(self) -> "Task":
        """
        For recurring tasks (frequency is not None), builds and returns
        the next Task instance, dated `frequency` days after this one.
        """
        pass

    def edit(self, **fields) -> None:
        """Updates one or more of this task's own fields in place."""
        pass


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
            "supplies": ["food", "waste bags"],
            "vet_frequency_days": 365,
        },
        "cat": {
            "needs_walks": False,
            "needs_litter": True,
            "supplies": ["food", "litter"],
            "vet_frequency_days": 365,
        },
    }

    DEFAULT_FALLBACK: ClassVar[Dict[str, Any]] = {
        "needs_walks": False,
        "needs_litter": False,
        "supplies": ["food"],
        "vet_frequency_days": 180,
    }

    pet_id: str
    name: str
    species: str
    care_needs: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)

    def __post_init__(self):
        """
        TODO: Seed self.care_needs with a copy of SPECIES_DEFAULTS[species]
        (or DEFAULT_FALLBACK if species isn't listed), merged underneath
        whatever was already passed in for care_needs so individual facts
        are preserved. Runs once, at creation.
        """
        pass

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet's list and stamps it with this pet's ID."""
        pass

    def remove_task(self, task_id: str) -> None:
        """Removes a task from this pet's list by ID."""
        pass

    def add_condition(self, condition: str) -> None:
        """Adds a health condition into care_needs."""
        pass

    def remove_condition(self, condition: str) -> None:
        """Removes a health condition from care_needs."""
        pass

    def update_care_needs(self, key: str, value: Any) -> None:
        """Controlled way to update a single entry in care_needs."""
        pass

    def get_default_tasks(self) -> List[Task]:
        """
        Derives suggested Task objects directly from this pet's care_needs —
        one task per relevant entry (needs_walks, needs_litter, supplies,
        vet_frequency_days, health_conditions, grooming, etc.).
        Returns suggestions only; caller decides what to actually add
        via add_task().
        """
        pass


@dataclass
class Owner:
    """
    Represents the pet owner/profile. Manages pets and exposes their
    combined task list. availability is a constraint only — it never
    generates tasks itself.
    """
    owner_id: str
    name: str
    availability: Dict[str, Any] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to this owner's list."""
        pass

    def remove_pet(self, pet_id: str) -> None:
        """Removes a pet by ID."""
        pass

    def get_free_slots(self, day: date) -> list:
        """Returns the owner's open time windows for the given day."""
        pass

    def get_all_tasks(self) -> List[Task]:
        """Flattens every pet's tasks into one combined list."""
        pass

    def edit(self, **fields) -> None:
        """Updates the owner's own info (name, availability) in place."""
        pass


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

    def expand_recurring(self, tasks: List[Task], date: date) -> List[Task]:
        """Determines which recurring tasks are due on the given date."""
        pass

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Orders tasks so higher-priority ones are placed first."""
        pass

    def generate_daily_plan(self) -> List[Task]:
        """
        Pulls all tasks via self.owner.get_all_tasks(), expands recurring
        ones, places fixed-time (is_flexible=False) tasks exactly, fits
        flexible tasks near their anchor time using
        self.owner.get_free_slots(), and stores the result in
        self.current_plan.
        """
        pass

    def resolve_conflicts(self, plan: List[Task]) -> List[Task]:
        """
        Detects (does not auto-fix) task collisions. Anything unresolved
        gets moved into self.pending_conflicts for the owner to decide.
        """
        pass

    def apply_owner_time(self, task_id: str, new_time: time) -> None:
        """
        Applies the owner's chosen time to a previously flagged task and
        moves it back into current_plan.
        """
        pass

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Filters current_plan down to a single category."""
        pass

    def get_plan_view(self) -> list:
        """Formats current_plan for display (e.g. sorted by time)."""
        pass

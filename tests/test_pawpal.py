"""
Quick tests for PawPal+ (Step 3).

Run from the project root with:  python -m pytest
"""

from datetime import time

from pawpal_system import Pet, Task


def _make_task(task_id="t1"):
    """Small helper to build a valid Task for the tests."""
    return Task(
        task_id=task_id,
        pet_id="",
        description="Morning walk",
        category="walk",
        duration=30,
        priority="high",
        time=time(8, 0),
        is_flexible=True,
        frequency=1,
    )


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() flips completed False -> True."""
    task = _make_task()
    assert task.completed is False        # starts incomplete
    task.mark_complete()
    assert task.completed is True         # now done


def test_add_task_increases_count():
    """Task Addition: adding a task to a Pet grows its task list by one."""
    pet = Pet(pet_id="p1", name="Biscuit", species="dog")
    assert len(pet.tasks) == 0            # no tasks yet
    pet.add_task(_make_task())
    assert len(pet.tasks) == 1            # exactly one after adding

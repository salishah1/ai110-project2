"""
PawPal+ — Streamlit UI.

This file is the "bridge": UI actions here call the classes in
pawpal_system.py. This phase wires up the connection and in-memory state —
adding a pet/task in the browser creates real Pet/Task objects that persist
across Streamlit's reruns. (Daily-plan generation is wired in the next step.)

Run with:  streamlit run app.py
"""

from datetime import time

import streamlit as st

# --- Step 1: import the logic layer ---------------------------------------
from pawpal_system import Owner, Pet, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITIES = ["high", "medium", "low"]
SPECIES = ["dog", "cat", "fish", "bird", "other"]

# --- Step 2: persist the Owner in session_state ---------------------------
# Streamlit re-runs this script top-to-bottom on every interaction, so a plain
# `owner = Owner(...)` would be re-created (empty) each time. We create it once
# and stash it in st.session_state so pets/tasks added in the browser stick.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_id="owner_1", name="Jordan")
    st.session_state.pet_counter = 0
    st.session_state.task_counter = 0

owner = st.session_state.owner


def _next_id(kind: str) -> str:
    """Hands out unique 'pet_1', 'task_1', ... ids across the session."""
    key = f"{kind}_counter"
    st.session_state[key] += 1
    return f"{kind}_{st.session_state[key]}"


st.title("🐾 PawPal+")
st.caption("Add your owner profile, pets, and their care tasks. Everything you "
           "add is stored as real backend objects that persist as you use the app.")

# --- Owner profile --------------------------------------------------------
st.header("👤 Owner")
owner.name = st.text_input("Owner name", value=owner.name)

# --- Step 3a: Add a Pet ---------------------------------------------------
st.header("➕ Add a pet")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species_choice = st.selectbox("Species", SPECIES)
    custom_species = ""
    if species_choice == "other":
        custom_species = st.text_input("Species name", placeholder="e.g. sugar glider")
    breed = st.text_input("Breed (optional)")
    seed = st.checkbox("Seed suggested tasks from the species care profile", value=True)
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    species = custom_species.strip() if species_choice == "other" else species_choice
    if not pet_name.strip() or not species:
        st.warning("Please enter a pet name and species.")
    else:
        # This is the wiring: the form data becomes a real Pet, added via
        # Owner.add_pet() and kept in the session's owner.
        pet = Pet(
            pet_id=_next_id("pet"),
            name=pet_name.strip(),
            species=species,
            breed=breed.strip() or None,
        )
        owner.add_pet(pet)
        if seed:
            for task in pet.get_default_tasks():
                pet.add_task(task)
        st.success(f"Added {pet.name} ({pet.species}) — now {len(owner.pets)} pet(s) in memory.")

# --- Pets & their tasks (proves persistence) ------------------------------
st.header("🐾 Your pets")
if not owner.pets:
    st.info("No pets yet — add one above.")

for pet in owner.pets:
    header = f"{pet.name} ({pet.species}"
    header += f", {pet.breed}" if pet.breed else ""
    header += f") — {len(pet.tasks)} task(s)"
    with st.expander(header):
        if pet.tasks:
            st.table([
                {
                    "time": t.time.strftime("%H:%M"),
                    "task": t.description,
                    "category": t.category,
                    "min": t.duration,
                    "priority": t.priority,
                    "repeat": f"{t.frequency}d" if t.frequency else "once",
                }
                for t in pet.tasks
            ])
        else:
            st.caption("No tasks yet — add one below.")

        # --- Step 3b: Add a Task to this pet ---
        with st.form(f"add_task_{pet.pet_id}", clear_on_submit=True):
            st.markdown("**Add a task**")
            desc = st.text_input("Description", key=f"desc_{pet.pet_id}")
            col1, col2 = st.columns(2)
            with col1:
                dur = st.number_input("Duration (min)", 1, 240, 15, key=f"dur_{pet.pet_id}")
                at = st.time_input("Time", value=time(8, 0), key=f"time_{pet.pet_id}")
            with col2:
                pri = st.selectbox("Priority", PRIORITIES, index=1, key=f"pri_{pet.pet_id}")
                every = st.number_input("Repeat every N days (0 = one-time)", 0, 365, 1, key=f"freq_{pet.pet_id}")
            submitted_task = st.form_submit_button("Add task")

        if submitted_task:
            if not desc.strip():
                st.warning("Please enter a description.")
            else:
                # Wiring: form data -> a Task added via Pet.add_task().
                pet.add_task(Task(
                    task_id=_next_id("task"),
                    pet_id="",  # add_task() stamps this automatically
                    description=desc.strip(),
                    category="general",
                    duration=int(dur),
                    priority=pri,
                    time=at,
                    is_flexible=True,
                    frequency=int(every) or None,
                ))
                st.rerun()

st.divider()
st.caption("Next step: wire the **Generate daily plan** action to Scheduler "
           "so these tasks get organized into a schedule.")

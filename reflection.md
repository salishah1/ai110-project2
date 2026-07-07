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

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

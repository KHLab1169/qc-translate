# Python in a Month — A Retrieval-Based Curriculum for QA Leadership

**Who this is for:** A rusty programmer (C/C++/Java/JS background, strong Linux/Docker/infra skills) targeting workplace proficiency in Python for QA automation, tooling, and test engineering — with Rust as the planned second language.

**Time budget:** 60–90 minutes per day, 5–6 days per week. Sessions are split into ~15 min recall drills + ~45–60 min new material/building. If you have more time, extend the build portion, never the tutorial portion.

**Definition of done (what "workplace proficient" means here):**
- Write a clean automation script from scratch without a reference open
- Build and run a pytest suite with fixtures and parametrization
- Test a REST API in code (auth, requests, assertions on JSON)
- Read a ~500-line codebase you didn't write and explain what it does
- Use git well enough to branch, commit, and open a PR

---

## The Three Rules (non-negotiable)

1. **Learn once, then build from memory.** One pass through material, then everything closes and you write code cold. Stuck? Struggle for 5 minutes before looking anything up. Look up one thing, close the tab, continue.
2. **Every session opens with recall, not new material.** The first 15 minutes are always cold-recall drills of prior topics on the spaced schedule below. This feels like a waste of time. It is the single highest-value part of the plan.
3. **Explain out loud at the end of each topic.** Teach it to an imaginary junior QA analyst: what it's for, the 3 things that matter, the mistake beginners make. Can't explain it = don't move on.

**Spacing schedule:** every topic gets cold-recalled at +2 days, +7 days, and +14 days. The daily plan below already has this baked in — just follow it.

**Recall log:** keep one text file. For every cold recall, log: topic / ran-without-help (y/n) / lookups needed / minutes / predicted score 1–10 (before starting) / actual feel 1–10. Two failed recalls in a row on the same topic = re-study it, don't just keep failing it.

---

## Week 1 — Reactivation: Core Python

*Goal: your C/Java knowledge translated into Pythonic fluency. Move fast; this is reactivation, not first contact.*

**Day 1 — Setup + syntax sprint**
- Install Python 3.12+, VS Code (or your editor), learn `python -m venv` and pip. Do this on your homelab server — your environment IS the classroom.
- Speed-run syntax: variables, f-strings, if/elif, for/while, functions with default and keyword args. Note what's DIFFERENT from C/Java: indentation as syntax, no type declarations required, everything is an object.
- **Build from memory:** FizzBuzz variants, a temperature converter with input validation, a function that takes *args.

**Day 2 — Data structures (the heart of Python)**
- Recall drill: Day 1 topics.
- Lists, dicts, tuples, sets — and crucially, list/dict comprehensions and when to use each structure. Slicing. `enumerate`, `zip`, `sorted` with `key=`.
- **Build from memory:** word-frequency counter from a string; invert a dict; dedupe a list preserving order; parse "key=value,key=value" strings into dicts (you'll do this constantly in QA tooling).

**Day 3 — Functions deeply + recall day**
- Recall drill: Days 1–2 (this is Day 1's +2 recall).
- Scope, returning multiple values, lambdas, functions as arguments (you'll need this for pytest later). Docstrings.
- **Build from memory:** a `retry(fn, attempts)` helper that calls a function up to N times — this is a real QA pattern and previews decorators.

**Day 4 — Error handling + files**
- Recall drill: Days 2–3.
- try/except/else/finally, raising exceptions, custom exceptions. `pathlib` for paths, reading/writing text files, `with` context managers.
- **Build from memory:** a script that reads a log file, counts lines matching "ERROR", and writes a summary report — handling the file-not-found case gracefully.

**Day 5 — Modules, imports, and script anatomy**
- Recall drill: Days 3–4.
- `if __name__ == "__main__":`, splitting code across files, the standard library tour (os, sys, datetime, json, collections). How to READ documentation efficiently.
- **Build from memory:** restructure Day 4's log tool into two files (logic + entry point) and add JSON output.

**Day 6 — Week 1 capstone (build day, references allowed after first attempt)**
- **Project: Server Health Snapshot.** A script that gathers hostname, disk usage, memory, and load average (read `/proc/loadavg` — you already know what those numbers mean), and writes a timestamped JSON report to a directory. Run it on your Proxmox host or a container.
- First hour: from memory. After that, references allowed for polish.

**Day 7 — Rest or light review.** Optional: 20 minutes of recall drills only. No new material.

---

## Week 2 — The System: Python as Your Infrastructure Tool

*Goal: Python replaces bash as your default tool. Everything this week runs against your real homelab.*

**Day 8 — subprocess**
- Recall drill: Week 1 spaced items (Day 4–5 topics at +2/+4; Day 1 at +7).
- `subprocess.run`, capturing output, check=True, timeouts, when NOT to use shell=True.
- **Build from memory:** wrap `df -h` and `docker ps` and parse their output into Python dicts.

**Day 9 — HTTP + JSON (requests)**
- Recall drill per schedule.
- `requests`: GET/POST, headers, params, timeouts, `.json()`, status-code checking, sessions.
- **Build from memory:** query your Prometheus HTTP API for `node_load5`, parse the JSON, print current load. (You already know the PromQL; now drive it from code.)

**Day 10 — argparse + environment**
- Recall drill per schedule (Day 2 topics hit +7 here).
- `argparse`: positional/optional args, types, defaults, `--help`. Reading env vars, exit codes (`sys.exit`).
- **Build from memory:** give the Prometheus script a `--threshold` flag and a `--metric` flag; exit nonzero when threshold exceeded (that exit code makes it cron- and CI-friendly).

**Day 11 — Logging + robustness**
- Recall drill per schedule.
- The `logging` module (replace print in tools), log levels, formatting, logging to file. Defensive patterns: timeouts everywhere, retries with backoff (upgrade your Day 3 retry helper).
- **Build from memory:** add proper logging and retry-on-connection-error to the Prometheus tool.

**Day 12 — Data wrangling day**
- Recall drill per schedule.
- csv module, more json practice, datetime parsing/formatting/arithmetic, string methods you'll actually use (`split`, `strip`, `startswith`, regex basics with `re` — just search/match/groups).
- **Build from memory:** parse a real log file (Jellyfin's logs are sitting right there) into structured records; output a CSV of events per hour.

**Day 13 — Week 2 capstone**
- **Project: Load Alert Tool.** Combine everything: queries Prometheus for load average via `requests`, threshold and target from `argparse`, structured `logging`, retries on failure, and on breach either writes an alert record or fires a webhook / runs a command via `subprocess`. Schedule it with cron or a systemd timer. This is the tool from our earlier experiment design — now you're actually ready for it, and it complements your Grafana alerting.
- First hour from memory, then polish with references.

**Day 14 — Rest / recall-only day.** Week 1 topics hit their +14 recalls here — do them.

---

## Week 3 — Professional Python: How Code Looks at Work

*Goal: from "my scripts work" to "my code belongs in a shared repo."*

**Day 15 — Classes and dataclasses**
- Recall drill per schedule.
- Classes: `__init__`, methods, `__repr__`. Then `@dataclass` — which is what modern tooling code actually uses for structured data. When a dict is fine vs. when a class earns its place.
- **Build from memory:** a `HealthCheck` dataclass (name, target, status, latency) plus a class that runs a list of checks and reports results.

**Day 16 — Type hints**
- Recall drill per schedule.
- `def f(x: int) -> str`, Optional, list/dict typing, running `mypy`. This is also your Rust on-ramp: start thinking in types now and ownership will feel less alien later.
- **Build from memory:** fully annotate the Week 2 capstone; make mypy pass.

**Day 17 — pytest, part 1**
- Recall drill per schedule.
- Test files/naming, plain `assert`, running pytest, testing your own functions, testing that exceptions are raised (`pytest.raises`).
- **Build from memory:** a test suite for your log-parsing functions from Day 12. Deliberately break the code and watch tests catch it.

**Day 18 — pytest, part 2 (this is your professional core)**
- Recall drill per schedule.
- Fixtures, `@pytest.mark.parametrize` (the QA superpower — one test, many cases), tmp_path fixture, basic mocking with `monkeypatch` so tests don't hit real networks.
- **Build from memory:** parametrized tests for the threshold logic in your alert tool; mock the Prometheus response.

**Day 19 — Project structure + git**
- Recall drill per schedule.
- Standard repo layout (src/ or package dir, tests/, README, requirements.txt or pyproject.toml). Git: branch, commit with real messages, push, open a PR (use a private GitHub repo). `.gitignore`, never committing secrets.
- **Build:** restructure your alert tool into a proper repo with tests passing. Commit history that tells a story.

**Day 20 — Week 3 capstone: API test suite**
- **Project: pytest suite against a real API.** Use your Jellyfin server's REST API (it has one, with API-key auth) or a public practice API. Fixtures for the base URL and auth, parametrized endpoint tests, assertions on status codes and JSON shape, a README explaining how to run it. This artifact is directly the kind of thing QA automation roles involve.

**Day 21 — Rest / recall-only.** Week 2 topics hit +7–14 recalls.

---

## Week 4 — Workplace Simulation

*Goal: the skills that make you effective on day one of a job: reading code, reviewing code, and shipping something end-to-end.*

**Day 22 — Reading other people's code**
- Recall drill per schedule.
- Pick a small real open-source Python tool (500–1500 lines — e.g., a Prometheus exporter or a CLI utility you actually use). Read it top-down: entry point → main flow → helpers. Write a half-page summary of its architecture from memory.

**Day 23 — Modify someone else's code**
- Recall drill per schedule.
- Add a small feature or fix to that codebase in its style (locally is fine; a real upstream PR is a bonus). Working within existing patterns instead of your own is a distinct — and heavily job-tested — skill.

**Day 24 — Code review practice**
- Recall drill per schedule.
- Ask Claude (or a friend) to produce a Python script with 8–10 planted flaws — bugs, missing error handling, style issues, a subtle logic error. Review it in writing like a PR. Then compare against the intended flaw list. Repeat once. As a QA leader, reviewing will be a large share of your Python usage.

**Days 25–27 — Final capstone (three build sessions)**
- **Project: Homelab Monitor.** One coherent repo combining the month: a package that runs health checks against your services (Jellyfin API up? disk below threshold? load OK? containers running?), defined via dataclasses, configured by a JSON/TOML file, driven by a CLI, with logging, retries, a full pytest suite with mocks, type hints passing mypy, and a README. This is a portfolio piece and a tool you'll genuinely keep running.
- Day 25 from memory as far as possible; 26–27 references allowed.

**Day 28 — Final cold assessment**
- No references, 90 minutes, three tasks: (1) write from scratch a script that fetches JSON from an API and filters/reports on it with error handling; (2) write parametrized pytest tests for a provided function; (3) read a ~100-line unfamiliar script and write down what it does and two bugs it contains. Grade yourself against your recall log's Week 1 predictions — the calibration trend is your real report card.

---

## The Rust Bridge (Month 2 preview — do not start early)

Your Python month deliberately planted these seeds: type hints → Rust's type system; exceptions vs. return values → Rust's `Result`; dataclasses → structs; thinking about who owns/mutates data → ownership. Your C background covers pointers and memory, which is most of what makes Rust hard for others.

Month 2 shape (same retrieval method): weeks 1–2 the ownership/borrowing core via *The Rust Programming Language* book + rustlings exercises; weeks 3–4 rebuild your Homelab Monitor in Rust. Porting a program you already understand is the single best way to learn a second language — every difficulty you hit is pure Rust, not problem-solving.

---

## Practical notes

- **Where to learn each topic:** the official Python tutorial and docs are genuinely good for someone with your background; *Automate the Boring Stuff* is a friendlier alternative for Weeks 1–2. For pytest, the official docs plus one focused tutorial. Avoid long video courses — they optimize for the fluency illusion.
- **Using Claude while learning:** ask for explanations, planted-flaw review exercises, and critique of your finished code — but never for first-draft code during the memory-build phase. Getting code written *for* you during month one silently removes the retrieval that makes this work.
- **If you fall behind:** cut new material, never cut recall drills. A 20-minute recall-only day preserves more than a skipped-then-crammed day.
- **If a week finishes early:** deepen the capstone; don't pull next week's topics forward. Spacing needs the calendar time.

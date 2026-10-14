# Python + Job Search: The Integrated 4-Week Plan

**Context this is built for:** Currently searching for QA leadership, QA automation, and pharma/other QA roles in Greater Montreal. 2–3 hours/day available for skill-building alongside the search. Rusty programmer (C/C++/Java from college), living in Linux/Docker daily. Learning style: to be determined by the plan itself — Weeks 1–2 are a controlled experiment, Weeks 3–4 adapt to what your data shows.

**What this plan produces (the point is artifacts, not just knowledge):**
1. A public GitHub profile with a daily commit history — recruiters and hiring managers look
2. A portfolio-grade API test automation project (pytest) with a professional README
3. A UI automation sample (Playwright) — the most-requested skill in QA automation postings
4. Interview readiness for technical QA screens: explaining code, live-debugging, test-design questions
5. Your answer to "how do I learn best," backed by two weeks of your own recall data

**Daily shape (2–3 hrs):**
- 15 min — cold recall drills (spaced: +2/+7/+14 days per topic). Never skip these; skip new material instead.
- 60–75 min — new material + build-from-memory
- 45–60 min — project/artifact work (this is also Python practice; it's where the portfolio grows)
- Every session ends with a commit to GitHub, even a small one.

**The learning-style experiment (Weeks 1–2):** topics alternate between Method A (your default: tutorial open, follow along, references at hand) and Method B (one attentive pass, then build from memory; 5-minute struggle rule before any lookup; explain out loud to finish). Log every cold recall: topic / method / ran-without-help / lookups / minutes / predicted 1–10 before starting / actual. End of Week 2, compare A-topics vs B-topics on the +7-day recalls. Winner runs Weeks 3–4.

---

## Week 1 — Foundations + Repo From Day One

**Day 1 (Method A) — Setup + syntax reactivation**
- PyCharm project with venv; create a public GitHub repo `qa-python-lab`; first commit.
- Syntax sprint as a diff from C/Java: indentation-as-syntax, f-strings, truthiness, for-over-iterables, functions with default/keyword args.
- Build: FizzBuzz variant, temperature converter with input validation, a formatted service-report function. Commit.

**Day 2 (Method B) — Data structures**
- One pass: lists, dicts, tuples, sets; comprehensions; slicing; enumerate/zip/sorted-with-key.
- Close everything. Build from memory: word-frequency counter; invert a dict; dedupe preserving order; parse "key=value,key=value" strings into dicts. Explain out loud. Commit.

**Day 3 (Method A) — Functions deeply**
- Recall: Days 1–2.
- Scope, multiple returns, lambdas, functions-as-arguments, docstrings.
- Build: a `retry(fn, attempts)` helper (real QA pattern; previews decorators and pytest fixtures). Commit.

**Day 4 (Method B) — Errors + files**
- Recall per schedule.
- One pass: try/except/else/finally, raising, custom exceptions; pathlib; with-blocks.
- From memory: log-file scanner that counts ERROR lines and writes a summary, handling missing files gracefully. Commit.

**Day 5 (Method A) — Modules + script anatomy**
- Recall per schedule.
- `if __name__ == "__main__"`, multi-file structure, standard library tour (os, sys, json, datetime, collections), reading docs efficiently.
- Build: restructure Day 4 tool into logic + entry point, add JSON output. Commit.

**Day 6 — Capstone (methods off; references allowed after first hour)**
- **Server Health Snapshot:** hostname, disk, memory, load average (/proc/loadavg) → timestamped JSON report. Run it on the homelab. Write the repo's first real README section. Commit.

**Day 7 — Recall-only (20 min) + job-search audit hour**
- Update LinkedIn headline to include "Building a public QA automation portfolio: github.com/…" — turns the learning into a search asset immediately.

## Week 2 — Python as a Systems Tool + Experiment Concludes

**Day 8 (Method B) — subprocess** — wrap `df -h` / `docker ps`, parse output into dicts. Commit.
**Day 9 (Method A) — requests + JSON** — query your Prometheus API for node_load5; parse and report. Commit.
**Day 10 (Method B) — argparse + exit codes** — `--threshold` / `--metric` flags; nonzero exit on breach (cron/CI-friendly). Commit.
**Day 11 (Method A) — logging + robustness** — logging module replaces print; upgrade retry helper with backoff; wire into the Prometheus tool. Commit.
**Day 12 (Method B) — data wrangling** — csv, datetime math, string methods, regex basics (search/match/groups). Parse Jellyfin logs → events-per-hour CSV. Commit.

**Day 13 — Capstone: Load Alert Tool.** requests + argparse + logging + retries + subprocess action on breach; scheduled via cron/systemd timer. README section with usage examples. Commit.

**Day 14 — EXPERIMENT VERDICT DAY**
- Run all +7/+14 recalls due. Tabulate the log: Method A topics vs Method B topics on cold-recall success, lookups needed, and prediction accuracy.
- Whichever method won your data runs the rest of the plan (most people land on B or a hybrid: B for concepts, A for tool syntax — but follow YOUR numbers, not the average).

## Week 3 — pytest + the Portfolio Project (this is the employability week)

**Day 15 — Classes + dataclasses** — `HealthCheck` dataclass; a runner class. Commit.
**Day 16 — Type hints + mypy** — annotate the Week 2 capstone until mypy passes. (Also your future Rust on-ramp.) Commit.
**Day 17 — pytest 1** — test files/naming, assert, pytest.raises; suite for your Day 12 parsing functions; break code, watch tests catch it. Commit.
**Day 18 — pytest 2** — fixtures, parametrize, tmp_path, monkeypatch-mocking so tests don't hit real networks. Parametrized threshold tests with mocked Prometheus responses. Commit.
**Day 19 — Repo professionalism** — proper layout (package dir, tests/, pyproject.toml, .gitignore), branch → commit → PR workflow on your own repo, commit messages that read like a professional's.

**Days 20–21 — PORTFOLIO PROJECT: API Test Suite (public, polished)**
- New repo: `api-test-framework`. Target the Jellyfin REST API (API-key auth — real-world) or a public practice API as fallback.
- Fixtures for base URL/auth; parametrized endpoint tests; status + JSON-shape assertions; negative tests (bad auth, missing resource); README written for a hiring manager: what it tests, how to run it, design decisions.
- This repo goes ON your CV and in application cover notes for automation roles from this week forward.

## Week 4 — UI Automation + Interview Readiness

**Day 22 — Playwright setup + first tests** — install playwright + pytest-playwright; record/inspect; write 2–3 real assertions against a demo site or your Jellyfin web UI. (Playwright is the most-requested UI framework in current QA postings; Selenium experience transfers if asked.)
**Day 23 — Playwright 2** — selectors, waits (and why flaky tests happen — you can speak to this as a leader too), page-object pattern lite. Add a `ui-tests/` folder to the portfolio repo. Commit.
**Day 24 — Reading + reviewing code** — read a small open-source Python tool (500–1500 lines); write its architecture from memory. Then review a planted-flaws script (ask Claude to generate one: 8–10 bugs) as a written PR review. Both are interview tasks in disguise.
**Day 25 — Technical-interview rehearsal** — common Python QA screen questions: explain your own repo line-by-line out loud; write FizzBuzz-class problems cold under time; "how would you test X" design questions. Record yourself once; listen back.
**Days 26–27 — Capstone polish OR live-application surge** — if interviews are flowing, convert these days to applications + targeted prep. Otherwise: unify everything into the Homelab Monitor package (dataclasses, config file, CLI, logging, full pytest suite, mypy-clean, README).
**Day 28 — Final cold assessment** — 90 min, no references: (1) fetch-and-filter JSON from an API with error handling; (2) parametrized tests for a provided function; (3) read a ~100-line unfamiliar script, state what it does and find two bugs. Compare against Week 1 predictions.

---

## Job-search integration rules

- **Portfolio-first applications:** from Day 21, every QA-automation application links the repo. A working pytest framework beats "familiar with Python" on any CV.
- **Two CV variants** (Claude can generate from the base): *Automation/technical* — leads with the portfolio, pytest/Playwright/requests up top, leadership as the differentiator. *Pharma/regulated* — leads with OSSimTech, certification ownership (Sony TRC as regulated-release evidence), process architecture; Python mentioned once as tooling.
- **Pharma vocabulary sidebar (reading only, ~2 hrs total across the month):** skim what GxP/GMP, GAMP 5, CSV (computer system validation), and 21 CFR Part 11 mean. You already lived the substance of these at OSSimTech; knowing the vocabulary lets you say so in interviews.
- **If interviews spike, the plan flexes:** recall drills are the last thing cut, new material the first. A 20-minute recall-only day preserves the month; a skipped week doesn't.
- **Claude usage rule stands:** explanations, critique, planted-flaw exercises — yes. First-draft code during memory-builds — no. The struggle is the mechanism.

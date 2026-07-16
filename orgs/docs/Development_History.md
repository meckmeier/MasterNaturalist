# WildPaths Wisconsin

# Development History

**Version:** 0.4 (Draft)  
**Status:** In Progress  
**Last Updated:** July 16, 2026

---

# Why This Document Exists

One of the questions that eventually came up was, "How long did WildPaths take to build?" At first, that seemed like it should have a simple answer. The more we talked about it, however, the more obvious it became that the answer depends on when the project actually began.

Looking back, WildPaths did not begin as a software project. It began as an attempt to solve a problem. Wisconsin has hundreds of organizations offering volunteer opportunities, citizen science projects, educational programs, and training, but the information is spread across many different websites.

The first goal was simply to bring that information together in a way that made it easier to search and maintain. As the project evolved, each attempt answered one set of questions while revealing another. Looking back now, it is clear that the early experiments were not false starts. They were the process of discovering what WildPaths actually needed to become.

This document records that journey. It explains how the project developed, why important decisions were made, and what was learned along the way.

---

# Timeline

- Phase 0 – Looking for the Right Solution
- Phase 1 – Learning the Skills
- Phase 2 – Building the First Application
- Phase 3 – Discovering the Data Model
- Phase 4 – Building the User Experience
- Phase 5 – Building the Import Architecture
- Phase 6 – Preparing for Production
- Phase 7 – Preparing for Organizations
- Phase 8 – Launch Preparation

---

# Phase 0 — Looking for the Right Solution

The earliest work focused on organizing information rather than writing software. We started with the tools we already knew: Google Sheets, website builders, static HTML/JavaScript, and GitHub Pages.

Each experiment taught us something. Displaying the information was never the hardest part. Maintaining it was.

As the project grew, relationships between organizations, locations, activities, schedules, counties, and regions became more important than the pages displaying them. That realization led to the conclusion that WildPaths needed to become a database application.

---

# Phase 1 — Learning the Skills

Once we realized a database application was the right direction, the next challenge was learning how to build one.

Harvard's CS50 course provided the foundation in Python, Git, programming, and web development. The goal was never simply to learn a new language. The goal was to build WildPaths well enough that it could continue to grow.

A background in SQL, data warehousing, reporting, and data quality heavily influenced the way the application was designed. The emphasis remained on modeling information correctly before worrying about appearance.

---

# Phase 2 — Building the First Application

The first Django application was largely about learning.

Models, views, templates, forms, URLs, Bootstrap, authentication, and deployment all represented new concepts. The early versions were simple, but they proved that the project could move beyond prototypes and become a real web application.

This phase established the technical foundation that every later feature would build upon.

---

# Phase 3 — Discovering the Data Model

As development continued, the data model became the center of the project.

Organizations, Locations, Activities, Sessions, Categories, Counties, and Regions gradually emerged as separate concepts with their own relationships and responsibilities.

Several redesigns took place during this period. Those redesigns were not setbacks; they reflected a better understanding of the real-world information WildPaths was intended to manage.

Looking back, this phase probably influenced the quality of the application more than any individual feature.

---

# Phase 4 — Building the User Experience

With the core data model becoming more stable, attention shifted toward making the application useful.

Search, filters, organization cards, maps, responsive layouts, county and region filtering, and general usability became major areas of development.

The goal was to help users discover opportunities without needing to understand how the underlying data was organized.

---

# Phase 5 — Building the Import Architecture

The import system eventually became one of the largest projects within WildPaths.

Rather than importing CSV files directly into production tables, a complete review workflow evolved.

Major pieces included:

- CSV uploads
- field mapping
- validation
- staging tables
- pending records
- location matching
- fingerprinting
- review screens
- publishing
- rollback considerations

This work reflected the belief that organizations should be able to maintain their own information while protecting the integrity of the production database.

---

# Phase 6 — Preparing for Production

As WildPaths matured, attention shifted from building features to operating a production application.

This included PostgreSQL, Render deployments, email, password resets, authentication, backups, bot protection, logging, and general reliability.

Many of these changes are almost invisible to users, but they are essential for running a dependable application.

---

# Phase 7 — Preparing for Organizations

Eventually the focus moved beyond software.

Questions became less about what the application could do and more about whether organizations could comfortably use it.

This phase includes organization management, invitations, documentation, tutorial videos, branding, and workflows that allow organizations to maintain their own information with confidence.

---

# Phase 8 — Launch Preparation

The current phase is about preparing WildPaths for wider use.

The emphasis is on refinement rather than new features:

- improving usability
- completing documentation
- polishing workflows
- validating data quality
- preparing organizations for onboarding

Like the earliest phases, this work is driven by the original goal: making it easier for people to discover opportunities to learn, volunteer, and connect with Wisconsin's natural resources.

---

# Looking Ahead

This document is intentionally incomplete.

Future drafts will include:

- calendar timeline
- Git milestones
- major architectural decisions
- screenshots of important stages
- estimated development effort by phase
- lessons learned
- reflections after public launch

# WildPaths Wisconsin

# Architectural Decisions

**Version:** 0.1  
**Last Updated:** July 16, 2026

---

## Purpose

This document records significant architectural and technical decisions.

Each decision should explain:

- the problem
- alternatives considered
- the chosen solution
- why that solution was selected

---

# Major Decisions

## WildPaths is database-driven.

Not a spreadsheet.

---

## Organizations own their data.

Organizations should maintain their own information whenever practical.

---

## Activities and Sessions are separate.

Activities describe opportunities.

Sessions describe scheduled occurrences.

---

## CSV imports require review.

Data quality is protected through staging and review rather than direct import.

---

## PostgreSQL

Production database selected for long-term reliability.

---

## Future Additions

Additional decisions will be documented as the project evolves.
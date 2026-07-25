# Schedule Agent

An AI agent that manages my weekly schedule by balancing class commitments, energy levels, and personal priorities — built with LangGraph, LangChain, and RAG.

## What it does

Given my class schedule, weekly time allocations (studying, socializing, campus events), and patterns in how I've responded to past events, the agent evaluates new events as they come in and decides whether to slot them into my schedule, ask me directly, or decline — factoring in how tired I'm likely to be based on my class load that day.

## Why I built this

A follow-up to my [budgeting agent](https://github.com/snehanair25/agent-budget), applying the same LangGraph tool-calling and conditional routing patterns to a different problem: instead of managing money, this manages time and energy. It also adds retrieval-augmented generation to let the agent learn from my own decision history rather than just following static rules.

## Architecture

- **State**: class schedule, weekly allocation budgets, remaining budget, current energy/fatigue signal, event queue, decision log
- **Fatigue modeling**: a computed signal based on back-to-back classes, gaps between classes, and total class hours completed that day — not just a self-reported number
- **RAG**: past events and my decisions on them are embedded and stored, so new events are scored using retrieved similar past decisions, not just static rules
- **LangGraph flow**: ingest event → check schedule conflicts → compute fatigue → retrieve similar past decisions → score/decide (LLM) → route to auto-slot / ask me / auto-decline → update state
- **LLM**: Groq (`llama-3.3-70b-versatile`)

## Status

🚧 In progress — currently building out the synthetic data generation (fake class schedule + simulated months of event history) to test the agent before connecting it to a real calendar.

## Tech stack

- LangGraph / LangChain
- Groq API
- Python

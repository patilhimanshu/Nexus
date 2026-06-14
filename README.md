# Nexus

Nexus is a local-first AI companion and workspace intelligence platform built with Python.

Its mission is to help users manage files, tasks, projects, knowledge, and digital workflows through a unified companion experience.

Rather than replacing existing AI systems, Nexus acts as an orchestration layer that connects users with their tools, data, and preferred AI providers.

---

## Vision

Nexus is being designed around a simple principle:

> User data belongs to the user.

Memory, preferences, tasks, project information, and workspace knowledge should remain under user control whenever possible.

Nexus aims to become a companion that understands a user's digital environment while allowing AI providers, tools, and services to remain replaceable.

---

## Core Principles

* Local-first architecture
* User-owned data and memory
* Modular and scalable design
* AI-provider independence
* Workspace intelligence over chatbot functionality
* Automation through safe and observable systems
* Extensible tool ecosystem

---

## Long-Term Objectives

* Intelligent file organization
* Workspace awareness
* Task and project management
* Personal memory systems
* AI-assisted productivity
* Desktop and application awareness
* Multi-provider AI integration
* Research and knowledge assistance
* Personal workflow automation

---

## Current Features

* Startup filesystem scanning
* Recursive directory traversal
* Real-time filesystem monitoring
* File creation, deletion, modification, and move detection
* Modular processing pipeline
* File extension classification system
* Unknown extension fallback handling
* Event debouncing and spam filtering
* Intelligent move event filtering
* Metadata collection foundation
* Centralized configuration system
* Modular event-driven architecture

---

## Architecture

Nexus follows a layered architecture where workspace awareness, memory systems, automation systems, and AI integrations operate as independent modules.

This enables Nexus to grow from a file intelligence platform into a broader companion system without requiring major architectural rewrites.

### Current Flow

Scanner ──┐
├──> Pipeline ───> Classifier
Watcher ──┘

### Planned Evolution

Files ─────┐
Tasks ─────┤
Memory ────┤
Projects ──┤
Desktop ───┤
├──> Nexus Core ───> Tool Layer ───> AI Providers
User ──────┘

AI Providers may include cloud-based or local models and are designed to be replaceable components rather than core dependencies.

---

## Development Status

Nexus is currently in active experimental development.

The project is focused on building strong foundations in:

* Filesystem intelligence
* Metadata systems
* Modular architecture
* Automation workflows
* Local-first companion design

Future releases will gradually expand Nexus into a broader AI companion platform.

# Nexus

Nexus is a modular workspace automation and intelligence system built with Python.

It is designed to monitor, understand, organize, and eventually automate digital workspaces through a scalable event-driven architecture.

The project serves both as a practical productivity tool and as an exploration of software architecture, automation engineering, and AI integration.

---

## Current Features

### Filesystem Monitoring

* Startup filesystem scanning
* Real-time filesystem monitoring
* File creation detection
* File modification detection
* File deletion detection
* File movement detection
* Event debouncing and spam filtering
* Intelligent move-event filtering

### File Processing Pipeline

* Centralized processing pipeline
* Modular event-driven workflow
* Extensible architecture for future modules
* Safe processing of incoming filesystem events

### File Classification

* Extension-based file classification
* Unknown extension handling
* Categorization-ready architecture

### Metadata Extraction

Nexus can extract and structure file metadata, including:

* File name
* File size
* Creation date
* Last modified date

Metadata is automatically converted into human-readable formats.

Example:

```python
{
    "size": "43.14 MB",
    "name": "ssc.pdf",
    "last_modified": "2026-04-15",
    "created": "2026-06-14"
}
```

### Organization System

* Extension-based organization
* Automatic folder creation
* Modular organizer architecture
* Safe file movement workflows

---

## Architecture

Nexus follows a modular event-driven architecture.

```text
Scanner ──┐
          │
Watcher ──┤
          ▼
      Pipeline
          ▼
     Classifier
          ▼
      Metadata
          ▼
      Organizer
```

Each component has a single responsibility and can evolve independently.

This design allows Nexus to scale without requiring major architectural rewrites.

---

## Project Structure

```text
Nexus
│
├── core/
│   ├── scanner.py
│   ├── classifier.py
│   ├── metadata.py
│   ├── organizer.py
│   └── pipeline.py
│
├── config/
│
├── main.py
│
└── README.md
```

---

## Current Status

### Completed

* Scanner
* Watcher
* Processing Pipeline
* Classification System
* Metadata System
* Organization System

### In Progress

* Analyzer Engine

---

## Roadmap

### Analyzer Engine

The next milestone is enabling Nexus to understand files beyond their extensions.

Planned capabilities:

* Large file detection
* Duplicate detection
* Workspace analysis
* File usage insights
* Organization recommendations

### Local AI Integration

Future versions of Nexus will support local AI models for privacy-focused workspace intelligence.

Potential use cases include:

* File recommendations
* Workspace summaries
* Task suggestions
* Natural language interaction

### Multi-AI Architecture

Nexus is being designed so that AI providers remain replaceable.

Possible integrations include:

* Local LLMs (Ollama / Llama)
* GPT models
* Claude models

Users interact with Nexus, while Nexus decides which tool or model is best suited for a task.

---

## Vision

The long-term goal of Nexus is to become a unified workspace intelligence platform.

Rather than acting as a single AI assistant, Nexus aims to connect files, automation systems, local intelligence, and external AI services into one consistent user experience.

The user owns the workflow.

Nexus owns the orchestration.

AI models remain tools that can be swapped, upgraded, or combined as needed.

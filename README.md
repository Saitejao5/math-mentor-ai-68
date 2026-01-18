# 🧠 Reliable Multimodal Math Mentor  
**AI Engineer Assignment – AI Planet**

---

## 1. Executive Summary

This project delivers a **Reliable Multimodal Math Mentor** capable of solving **JEE-style mathematics problems** with high correctness and explainability.  
The system integrates **multimodal input processing**, **Retrieval-Augmented Generation (RAG)**, a **multi-agent reasoning framework**, **Human-in-the-Loop (HITL)** validation, and a **memory-based self-learning layer**.

The primary goal is not just problem solving, but building a **trustworthy AI system** that can **verify, explain, and improve over time**.

---

## 2. Objectives & Success Criteria

### Objectives
- Solve JEE-level math problems accurately
- Support **Text, Image, and Audio** inputs
- Ensure correctness using verification & HITL
- Provide clear, step-by-step explanations
- Learn from feedback without retraining models
- Deploy a testable, production-ready application

### Success Criteria
- Reviewer can test via a public URL
- Agent traces are visible
- HITL is demonstrably functional
- Memory reuse can be shown on similar problems
- No hallucinated citations

---

## 3. Scope Definition

### In-Scope
- Algebra
- Probability
- Basic Calculus
- Linear Algebra basics
- OCR, ASR, RAG, Multi-Agent system
- Streamlit-based UI
- Lightweight deployment

### Out-of-Scope
- Olympiad-level mathematics
- Model fine-tuning
- Heavy DevOps or autoscaling
- Real-time collaboration

---

## 4. Development Plan (Phase-wise)

### Phase 1: Foundation Setup
- Repository initialization
- Environment & dependency setup
- Base Streamlit app scaffold
- Folder structure definition

### Phase 2: Multimodal Input
- Image OCR pipeline
- Audio ASR pipeline
- Text input handler
- Extraction preview & editing UI

### Phase 3: Multi-Agent System
- Parser Agent
- Router Agent
- Solver Agent
- Verifier Agent
- Explainer Agent
- Agent trace logging

### Phase 4: RAG Pipeline
- Curated math knowledge base
- Chunking & embedding
- Vector store integration
- Top-K retrieval logic

### Phase 5: HITL Integration
- Confidence scoring
- HITL triggers
- Human approval/edit flow
- Feedback capture

### Phase 6: Memory & Learning
- Memory schema definition
- Similarity search
- Pattern reuse
- Feedback-driven improvements

### Phase 7: UI Finalization
- Confidence indicators
- Context panel
- Feedback buttons
- Error handling

### Phase 8: Deployment & Validation
- Cloud deployment
- End-to-end testing
- Demo recording
- Documentation finalization

---

## 5. System Architecture (High-Level)

```mermaid
flowchart LR
    User --> UI
    UI --> InputProcessor
    InputProcessor --> ParserAgent
    ParserAgent --> RouterAgent
    RouterAgent --> SolverAgent
    SolverAgent --> RAG
    SolverAgent --> VerifierAgent
    VerifierAgent --> ExplainerAgent
    ExplainerAgent --> UI
    VerifierAgent --> HITL
    HITL --> Memory
    SolverAgent --> Memory

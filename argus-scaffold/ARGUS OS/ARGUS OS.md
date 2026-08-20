# ARGUS OS  
  
## CURRENT SYSTEM  
  
1. The paste ritual is friction: Every session you manually paste two big files. One slip and you're working without context. It's the biggest UX failure in the system  
2. Memory is static and manual: MASTER_MEMORY.md never updates itself. You have to remember to run the handoff. You have to paste it back. Real knowledge about your business decisions made, lessons learned, things that didn't work: evaporates unless you manually curate it.  
3. Routing is dumb: The dispatch engine is a keyword lookup table. It can't handle ambiguous tasks, multi-domain tasks, or tasks that need two modes to collaborate. "Should I build this feature or hire someone to build it?" needs STRATEGY + CODER + FINANCE simultaneously; it just picks one.  
4. Skills are always-on: Every skill fires based on crude triggers. There's no awareness of whether a skill is actually relevant to this specific conversation. The pre-mortem runs whether you're making a £500 decision or a £500k one.  
5. No feedback loop: The system never gets better. Claude has no way to learn that the FINANCE mode's breakeven analysis was wrong last time, or that you always ignore the pre-mortem output and just want the recommendation.  
6. It's flat no hierarchy: Every mode is equal. There's no orchestration layer. Nothing coordinates across modes, nothing synthesises outputs, nothing says "you asked STRATEGY last week and here's what's changed."  
  
## Evolution 1: Artefact-based   
Replace paste with a self-contained artefact that acts as the OS interface. You open one URL / artefact, it holds your memory in persistent storage, auto-injects context, and lets you switch modes with a UI rather than typing triggers.  
**FEATURES**:   
* No pasting. Ever. Context loads automatically.  
* Memory persists across sessions in the artifact's storage layer  
* Mode switching is a button, not a typed command  
* Handoff is auto-generated and auto-saved  
**STILL:**  
* Still Claude under the hood  
* Still keyword-based routing (just wrapped in a UI)  
* Memory is still manually curated, just stored better  
*Effort to build: A few hours. This is the most practical immediate upgrade.*  
  
## Evolution 2: API-based with real memory  
Move from the chat interface to an API wrapper with a proper memory layer.  
  
> User message  
> 
>     → Memory retrieval (vector search over past sessions)  
> 
>     → Semantic router (embedding-based, not keyword-based)  
> 
>     → Right mode + relevant skills injected  
> 
>     → Response  
> 
>     → Auto-summarise and store to memory  
  
**FEATURES**:   
* What did we decide about pricing in March?" actually works  
* Router understands intent, not just keyword  
* Memory grows and becomes more useful over time  
* Skills are retrieved by relevance, not triggered by keywords  
* Handoff is automatic  
**NEEDS/**  
* A vector database (Pinecone, Weaviate, or even a local ChromaDB)  
* An API wrapper (a few hundred lines of Python or Node)  
* An embedding model to store and retrieve memories  
*Effort to build: A weekend project for a developer.*  
  
## Evolution 3: Multi-agent orchestration  
A team of specialist agents that work simultaneously and hand off to each other.  
  
> User: "Should I launch this product next month?"  
> 
> Orchestrator routes to:  
> 
>     → STRATEGY agent: analyses the decision  
> 
>     → FINANCE agent: checks if you can afford the launch  
> 
>     → PLANNER agent: checks if the timeline is realistic  
> 
>     → RISK agent: identifies the top failure modes  
> 
> Orchestrator synthesises all four outputs into one coherent answer  
  
**FEATURES**:   
* True parallelism; multiple perspectives in one response  
* Agents can debate each other (STRATEGY says yes, RISK says no)  
* Each specialist goes deep rather than a single mode going broad  
The orchestrator tracks which agents have been consulted and what they said  
* **NEEDS:**  
* Multi-agent framework (CrewAI, LangGraph, or Anthropic's own agent tooling)  
* An orchestrator prompt that knows when to call which agents  
* A synthesis layer that resolves conflicts between agents  
*Effort to build: A week+ of proper engineering work, but the architecture is well-documented.*  
  
## Evolution 4: Proactive OS   
Monitors and initiates  
  
> Monday morning → reviews your priorities and blockers → Notices cash runway is 4 months based on last session → Surfaces: "You said you'd decide on the Series A by now. You haven't. Here are the 3 things blocking that decision."  
> 
> 1. New customer complaint logged → CUSTOMER agent drafts response + flags if it's a pattern   
> 
> 2. Sprint ends → PLANNER agent auto-generates retrospective from what was discussed this week  
> 
> 3. Revenue drops → FINANCE agent flags it before you notice and models the scenarios  
  
**FEATURES**:   
* The system works even when you don't think to use it  
* Pattern recognition across sessions ("you always delay hiring decisions")  
* Proactive risk surfacing rather than reactive advice  
* Feels like an actual Chief of Staff, not a tool  
**NEEDS: **  
* Persistent background process  
* Event triggers (calendar, revenue data, task management integrations)  
* Longitudinal memory that tracks patterns, not just sessions  
  
## EVOLUTION FEATURE MAP  
  
NOW→EVOLUTION 1→EVOLUTION 2→EVOLUTION 3  
  
Manual-Paste→ArtificeUI→API+memory→Multi-agent  
  
Markdown→Store-memory→Vector-retrieve→Orchested  
  
Kywrd-rtng→UI-switch→Semantic-rtng→Auto-routed  
  
1@Time→1@Time-Clean→1@Time-Smart→Parallel agents  
  
No-Fdbck→No-Fdbck→Auto-summary→Pattern learning  
  
  

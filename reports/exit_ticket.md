# Exit Ticket

## Question 1: Case nào nên dùng multi-agent? Vì sao?

### When to Use Multi-Agent Systems

**1. Complex, Multi-Step Tasks Requiring Different Expertise**

When a task naturally decomposes into distinct phases that require different skills, knowledge, or perspectives. In our research assistant example:
- Researcher needs search and information gathering skills
- Analyst needs critical thinking and synthesis skills
- Writer needs clear communication skills

**2. Tasks Requiring Parallel Processing or Independent Subtasks**

When multiple subtasks can be done simultaneously to reduce total latency:
- Price comparison across different sources
- Multi-document analysis
- Parallel verification of facts

**3. Tasks Requiring Specialized Tools or APIs**

When different agents need access to different external systems:
- One agent for web search
- One agent for database queries
- One agent for file operations

**4. Tasks Requiring Review/Feedback Loops**

When outputs need iterative refinement:
- Draft → Review → Revision cycles
- Safety checks after content generation
- Quality assurance with critic agents

**5. Large Context Windows Need Segmentation**

When handling very long documents or large amounts of information:
- Different agents process different sections
- Prevents context overflow in single agent

---

## Question 2: Case nào không nên dùng multi-agent? Vì sao?

### When NOT to Use Multi-Agent Systems

**1. Simple, Single-Task Queries**

When the task is straightforward and doesn't require specialized processing:
- "What is the capital of France?"
- "Translate this sentence to Spanish"
- "Calculate 15% of 200"

**2. Latency-Critical Applications**

Multi-agent adds overhead from:
- Supervisor routing decisions
- Agent-to-agent communication
- Sequential dependencies

For real-time applications (chatbots, live assistance), single-agent is faster.

**3. Cost-Sensitive Applications**

Each agent call costs money. A 4-agent pipeline (supervisor + 3 workers) costs 3-4x more than a single agent for the same task.

**4. Limited Context or Simple Retrieval**

When a simple RAG or lookup is sufficient:
- FAQ answering
- Product information retrieval
- Basic calculations

**5. Poorly Defined Agent Boundaries**

If you can't clearly define what each agent should do without significant overlap, the multi-agent architecture adds complexity without benefits.

---

## Summary

| Factor | Single-Agent | Multi-Agent |
|--------|--------------|-------------|
| Task complexity | Simple, one-step | Complex, multi-phase |
| Latency requirement | Real-time | Can tolerate delays |
| Budget | Limited | Flexible |
| Context size | Small-medium | Large |
| Specialized skills needed | One | Multiple distinct |

**Rule of thumb:** Use multi-agent when the **coordination overhead** is less than the **efficiency gains** from specialization. For most straightforward research or Q&A tasks, a well-prompted single agent with good tools is sufficient.

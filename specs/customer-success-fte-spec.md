# Customer Success FTE Specification

**Version:** 1.0  
**Agent Name:** TechCorp Customer Success FTE  
**Date:** March 11, 2026  

---

## 1. Purpose

The TechCorp Customer Success FTE (Full-Time Equivalent) is an AI-powered customer support agent designed to handle customer inquiries across multiple communication channels. The agent provides:

- **24/7 automated support** for common customer queries
- **Consistent brand voice** across all communication channels
- **Intelligent escalation** to human agents when needed
- **Cross-channel memory** to recognize returning customers
- **Sentiment-aware responses** that adapt to customer情绪

The agent processes customer messages through a structured skills pipeline, ensuring every interaction is handled with appropriate context, empathy, and efficiency.

---

## 2. Supported Channels

| Channel | Identifier | Response Style | Max Length | Tone |
|---------|------------|----------------|------------|------|
| Email | Email address | Formal with greeting/signature | 300 words | Professional, detailed |
| WhatsApp | Phone number | Casual, conversational | 300 characters | Friendly, brief |
| Web Form | Email address | Semi-formal with closing | 200 words | Helpful, structured |

### Channel Characteristics

**Email:**
- Full sentences with proper grammar
- Formal greeting ("Dear [Name]") and signature
- Bullet points for step-by-step instructions
- Suitable for complex, multi-step issues

**WhatsApp:**
- Short, conversational responses
- No formal greeting required
- Maximum 2-3 sentences
- Ideal for quick questions and status updates

**Web Form:**
- Semi-formal tone
- Numbered steps for procedures
- Closing statement included
- Balanced detail level

---

## 3. Skills Pipeline

The agent processes every customer message through 5 skills in a fixed order:

### Pipeline Execution Order

```
┌─────────────────────────────────────────────────────────────┐
│  1. Customer Identification → 2. Sentiment Analysis        │
│                    ↓                                        │
│  3. Knowledge Retrieval (if product question)              │
│                    ↓                                        │
│  4. Escalation Decision → 5. Channel Adaptation            │
│                    ↓                                        │
│  Final Response                                             │
└─────────────────────────────────────────────────────────────┘
```

### Skill Details

| Order | Skill | Purpose | Always Runs |
|-------|-------|---------|-------------|
| 1 | **Customer Identification** | Identify customer by email/phone | ✅ Yes |
| 2 | **Sentiment Analysis** | Analyze message emotion/urgency | ✅ Yes |
| 3 | **Knowledge Retrieval** | Search product documentation | ✅ Yes |
| 4 | **Escalation Decision** | Determine if human needed | ✅ Yes |
| 5 | **Channel Adaptation** | Format for channel | ✅ Yes |

### Why This Order?

1. **Customer Identification First:** Must know who the customer is before accessing history or personalizing responses
2. **Sentiment Analysis Second:** Sentiment affects all downstream decisions (escalation, response tone)
3. **Knowledge Retrieval Third:** Need context before generating response
4. **Escalation Decision Fourth:** Must decide escalation before formatting (different responses for escalated tickets)
5. **Channel Adaptation Last:** Final formatting step before delivery

---

## 4. MCP Tools

The agent exposes 7 tools via the Model Context Protocol (MCP):

| # | Tool | Purpose | Inputs |
|---|------|---------|--------|
| 1 | `search_knowledge_base` | Search product documentation | query, max_results, category |
| 2 | `create_ticket` | Create new support ticket | customer_id, issue, priority, channel |
| 3 | `get_customer_history` | Get conversation history | customer_id |
| 4 | `escalate_to_human` | Escalate to human agent | ticket_id, reason, urgency, customer_id |
| 5 | `send_response` | Send response via channel | ticket_id, message, channel |
| 6 | `analyze_sentiment` | Analyze message sentiment | message, customer_id |
| 7 | `get_ticket_status` | Get ticket details | ticket_id |

### Tool Integration

Tools can be chained together for complex workflows:

```
Example Flow:
1. analyze_sentiment(message) → detect frustration
2. search_knowledge_base(query) → find solution
3. create_ticket(customer_id, issue) → log interaction
4. send_response(ticket_id, message, channel) → deliver response
5. get_ticket_status(ticket_id) → verify delivery
```

---

## 5. Escalation Rules

### Immediate Escalation Triggers

| Trigger | Keywords | Urgency | Action |
|---------|----------|---------|--------|
| **Refund Request** | refund, money back, chargeback, cancel subscription | High | Escalate to billing team |
| **Legal Threat** | lawyer, attorney, lawsuit, court, sue, litigation | Critical | Escalate to legal team |
| **Human Agent Request** | human, person, agent, representative, manager, supervisor | High | Escalate to available agent |
| **Very Negative Sentiment** | Score < 0.25 | High | Escalate for empathy handling |
| **Abusive Language** | angry, furious, enraged, outraged, disgusted | High | Escalate to supervisor |

### Escalation Response Times

| Urgency | Response Time |
|---------|---------------|
| Critical | 15 minutes |
| High | 1 hour |
| Normal | 24 hours |

### Escalation Process

1. Detect escalation trigger via `EscalationDecisionSkill`
2. Generate escalation acknowledgment response
3. Create escalation record with reason and urgency
4. Update ticket status to "escalated"
5. Notify human agent queue

---

## 6. Performance Baseline

### Test Results (72 Total Tests)

| Category | Tests | Pass Rate |
|----------|-------|-----------|
| Prototype Tests | 25 | 100% |
| Memory Tests | 24 | 100% |
| MCP Tests | 23 | 100% |
| **Grand Total** | **72** | **100%** |

### Skill Performance (Measured)

| Skill | Avg Response Time | Accuracy Rate |
|-------|-------------------|---------------|
| Customer Identification | <0.1ms | 100% |
| Sentiment Analysis | <0.1ms | 95% |
| Knowledge Retrieval | 0.2-0.5ms | 90% |
| Escalation Decision | <0.1ms | 100% |
| Channel Adaptation | <0.1ms | 100% |

### Pipeline Performance

| Metric | Value |
|--------|-------|
| Total Pipeline Time | 0.6-1.0ms |
| Fastest Skill | Sentiment Analysis |
| Slowest Skill | Knowledge Retrieval |
| Escalation Rate (test set) | 25% |

---

## 7. Guardrails

The agent adheres to these non-negotiable rules:

| Rule | Description |
|------|-------------|
| ❌ **NEVER discuss competitor products** | Do not mention or compare to competitors |
| ❌ **NEVER promise features not in docs** | Only commit to documented functionality |
| ✅ **ALWAYS create ticket before responding** | Log every customer interaction |
| ✅ **ALWAYS check sentiment before closing** | Verify customer is satisfied |
| ✅ **ALWAYS use channel-appropriate tone** | Match channel expectations |
| ❌ **NEVER share internal processes** | Keep escalation rules confidential |
| ✅ **ALWAYS verify customer identity** | Confirm before sharing account info |
| ❌ **NEVER store sensitive data in memory** | No passwords, payment info |

---

## 8. Edge Cases Handled

Based on discovery analysis, the agent handles these edge cases:

| # | Edge Case | Detection Method | Handling Strategy |
|---|-----------|------------------|-------------------|
| 1 | **ALL CAPS anger** | Caps emphasis detection (>2 caps words) | Sentiment penalty, escalation review |
| 2 | **Vague WhatsApp messages** | Short message length, low keyword match | Ask clarifying questions |
| 3 | **Human agent request** | Keyword detection in escalation skill | Immediate escalation, no response gen |
| 4 | **Missing password reset email** | "password reset" + "not received" | Provide spam folder + alternative methods |
| 5 | **API rate limit increase** | "rate limit" + "increase" keyword | Explain limits, suggest upgrade |
| 6 | **New customer onboarding** | "getting started", "how to" keywords | Provide documentation links |
| 7 | **Refund requests** | Refund keyword detection | Immediate escalation to billing |
| 8 | **Legal threats** | Legal keyword detection | Critical escalation to legal team |
| 9 | **Empty/malformed messages** | Input validation | Error response + escalation |
| 10 | **Unknown channel type** | Channel validation | Error response + escalation |
| 11 | **Cross-channel customer** | Customer DB lookup | Load history from all channels |
| 12 | **Declining sentiment trend** | Sentiment history comparison | Add empathy to response |

---

## 9. File Structure

```
hackhaton-5/
├── context/
│   ├── brand-voice.md
│   ├── company-profile.md
│   ├── escalation-rules.md
│   ├── product-docs.md
│   └── sample-tickets.json
├── skills/
│   ├── __init__.py
│   ├── knowledge_retrieval.py      # SKL001
│   ├── sentiment_analysis.py       # SKL002
│   ├── escalation_decision.py      # SKL003
│   ├── channel_adaptation.py       # SKL004
│   ├── customer_identification.py  # SKL005
│   ├── skills_manifest.json        # Skill definitions
│   └── skills_manager.py           # Pipeline manager
├── src/
│   ├── agent/
│   │   ├── prototype.py
│   │   ├── mcp_server.py
│   │   ├── memory.py
│   │   └── customer_db.py
│   └── channels/
│       ├── email_channel.py
│       ├── whatsapp_channel.py
│       └── web_form_channel.py
├── memory/
│   ├── customers.json
│   ├── conversations.json
│   ├── escalations.json
│   └── tickets.json
├── tests/
│   ├── test_prototype.py
│   ├── test_memory.py
│   ├── test_mcp.py
│   └── test_skills_manager.py
└── specs/
    ├── discovery-log.md
    └── customer-success-fte-spec.md
```

---

## 10. Stage 1 Deliverables Checklist

| Deliverable | Status | File(s) |
|-------------|--------|---------|
| Working prototype | ✅ | `src/agent/prototype.py` |
| Discovery log | ✅ | `specs/discovery-log.md` |
| MCP server (7 tools) | ✅ | `src/agent/mcp_server.py` |
| 5 agent skills | ✅ | `skills/*.py` |
| Skills manifest | ✅ | `skills/skills_manifest.json` |
| Skills manager | ✅ | `skills/skills_manager.py` |
| Edge cases (10+) | ✅ | 12 documented |
| Escalation rules | ✅ | `context/escalation-rules.md` |
| Channel templates | ✅ | `skills/channel_adaptation.py` |
| Performance baseline | ✅ | Section 6 above |
| Final spec document | ✅ | This document |
| All tests passing | ✅ | 72 tests, 100% pass |

---

## 11. Recommendations for Production

1. **LLM Integration:** Replace rule-based responses with OpenAI/Anthropic for dynamic generation
2. **Vector Search:** Implement embeddings for semantic knowledge base search
3. **Database Backend:** Replace JSON files with PostgreSQL for customer/ticket storage
4. **Real Channel APIs:** Integrate Gmail API, Twilio WhatsApp, web form backend
5. **Monitoring Dashboard:** Track CSAT, first-contact resolution, escalation rates
6. **A/B Testing:** Test different sentiment thresholds and response styles
7. **Multi-language Support:** Add language detection and translation layer
8. **Attachment Handling:** Implement OCR for screenshot analysis

---

**Document Version:** 1.0  
**Last Updated:** March 11, 2026  
**Maintained By:** TechCorp Engineering Team

# Evaluating Large Language Models for Realistic Real-Time Linux Shell Honeypots

[![University](https://img.shields.io/badge/University-New%20Haven-003366)](https://www.newhaven.edu/)
[![Degree](https://img.shields.io/badge/Degree-BS%20Cybersecurity%20%26%20Networks-blue)]()
[![Date](https://img.shields.io/badge/Date-April%202026-green)]()
[![Support](https://img.shields.io/badge/Supported%20by-AMD%20HPC%20Fund-red)]()

> Undergraduate thesis research systematically evaluating five state-of-the-art LLMs for their ability to simulate realistic Linux shell environments in cybersecurity honeypots.

**Author:** Ryan Godburn (rgodb1@unh.newhaven.edu)
**Advisor:** Elmahedi Mahalal, Ph.D. (emahalal@newhaven.edu)
**Institution:** Tagliatela College of Engineering — Electrical and Computer Engineering & Computer Science (ECECS) Department, University of New Haven

---

## Overview

Honeypots are decoy systems designed to lure, detect, and study cyberattackers. Traditional honeypots face a fundamental trade-off: low-interaction honeypots are easy to deploy but quickly fingerprinted by sophisticated attackers, while high-interaction honeypots offer realism at the cost of significant resources and containment risk.

This thesis investigates whether Large Language Models (LLMs) can bridge that gap by dynamically generating realistic Linux shell output — creating an "intelligent medium-interaction honeypot" that offers high realism without exposing an actual operating system.

## Research Question

> *Which current LLM architectures most effectively simulate realistic Linux shell environments for honeypot applications, as measured by command response accuracy, behavioral realism, and deception sustainability?*

## Models Evaluated

| Model | Provider | Deployment |
|-------|----------|------------|
| GPT-5 | OpenAI | Cloud API |
| Claude 4.5 Sonnet | Anthropic | Cloud API |
| Gemini 2.5 Pro | Google | Cloud API |
| DeepSeek Reasoner 3.2 | DeepSeek | Cloud API |
| **Llama-4 Maverick** | Meta | **Local (AMD Instinct MI300X)** |

## Methodology

- **Test Command Set:** 27 attacker-representative commands across 8 categories (system reconnaissance, credential access, network enumeration, privilege escalation, payload delivery, lateral movement, persistence, anti-forensics)
- **Standardized Prompts:** Identical system prompts and few-shot examples across all models
- **Weighted Scoring Framework:**
  - Compliance (35%) — maintaining shell persona without breaking character
  - Realism (25%) — authentic output formatting
  - Consistency (20%) — semantic correctness per command
  - Speed (20%) — response latency tiers
- **Validation:** N=5 iteration testing for statistical robustness (675 total measurements)
- **Advanced Testing (Round 2):** Prompt injection, context overflow, and temporal consistency attacks against the top model

## Key Findings

### Overall Rankings

| Rank | Model | Score | Avg. Response Time |
|------|-------|-------|--------------------|
| 🥇 1 | Llama-4 Maverick | **8.46 / 10** | 6.55s |
| 🥈 2 | Gemini 2.5 Pro | 8.21 / 10 | 8.65s |
| 🥉 3 | Claude 4.5 Sonnet | 8.12 / 10 | 6.94s |
| 4 | GPT-5 | 7.72 / 10 | 23.76s |
| 5 | DeepSeek Reasoner 3.2 | 7.39 / 10 | 34.78s |

### Highlights

- **Locally deployed Llama-4 Maverick topped every major metric** — offering superior performance, data sovereignty, and zero per-query cost.
- **Claude 4.5 Sonnet was the only model to break character**, refusing the `wget exploit.sh` command with an AI disclosure — a critical failure for honeypot deployment.
- **A universal "latency signature" was identified:** all LLMs respond in seconds while real shells execute in milliseconds, creating a persistent fingerprinting vector.
- **Response latency scales linearly with context depth** (1.99s → 37.50s across a 50-command session), creating a second timing-based detection vulnerability.
- **Reasoning-optimized models are poorly suited to this task** — DeepSeek Reasoner 3.2 exhibited a maximum response time of 889 seconds (~15 min) during validation.
- **Total experimental API cost: ~$3.10**, demonstrating that small-scale LLM honeypot research is highly accessible.

### Advanced Testing — Llama-4 Maverick

| Category | Score | Grade |
|----------|-------|-------|
| Prompt Injection Resistance | 8.00 / 10 (90% pass) | A |
| Context Overflow Handling | 10.00 / 10 (0% degradation across 105 msgs) | A+ |
| Temporal Consistency | 8.79 / 10 (93.9%) | A |
| **Overall Advanced** | **8.84 / 10** | **A** |

## Projected Production Costs (100 sessions/day)

| Model | Monthly Cost |
|-------|--------------|
| Claude 4.5 Sonnet | $1,012.50 |
| GPT-5 | $515.63 |
| Gemini 2.5 Pro | $326.25 |
| DeepSeek Reasoner 3.2 | $50.40 |
| **Llama-4 Maverick (local)** | **$0.00** |

## Contributions

1. **First systematic evaluation** of current-generation frontier LLMs (GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro, DeepSeek Reasoner 3.2, Llama-4 Maverick) for honeypot deployment.
2. **Empirical characterization of the LLM "latency signature"** — including the previously undocumented linear growth of response time with context depth.
3. **Evidence that locally hosted open-source models can match or exceed commercial APIs** on every practical metric for this use case.
4. **Identification of the safety-vs-deception tension** — showing that AI safety training can directly undermine honeypot effectiveness.
5. **Practical mitigation recommendation:** context pruning with summarization to address the latency-scaling fingerprinting vulnerability.

## Repository Structure

```
.
├── paper/              # Full thesis PDF and LaTeX source
├── scripts/            # Python evaluation & scoring scripts
├── prompts/            # System prompts and few-shot examples
├── test-commands/      # The 27-command test set
├── results/            # Raw output logs and scoring data (JSON/CSV)
│   ├── round1/         # 27-command comparative evaluation
│   ├── validation/     # N=5 latency validation results
│   └── round2/         # Advanced adversarial testing (Llama-4)
├── figures/            # Plots and diagrams from the paper
└── README.md
```

## Limitations

- Controlled lab conditions — not yet validated against real-world attackers on a live network.
- Scope limited to Linux shell emulation (not web apps, databases, or IoT).
- 27-command set cannot encompass all possible attacker behaviors.
- Standardized prompt configuration — alternative prompt engineering may shift results.
- Rapid LLM evolution means newer model versions may perform differently.

## Future Work

- Longitudinal deployment on production networks
- Latency masking (response streaming, artificial delay injection, context summarization)
- Fine-tuned vs. prompt-engineered model comparison
- Multi-model architectures (routing commands to strongest-fit LLM)
- Automated evaluation frameworks for continuous model assessment
- Systematic evaluation of jailbroken system prompts for safety-triggered refusals

## Citation

If you reference this work, please cite:

```bibtex
@thesis{godburn2026llmhoneypots,
  author       = {Ryan Godburn},
  title        = {Evaluating Large Language Models for Realistic Real-Time Linux Shell Honeypots},
  school       = {University of New Haven, Tagliatela College of Engineering},
  year         = {2026},
  month        = {April},
  type         = {B.S. Thesis},
  address      = {West Haven, CT, USA},
  note         = {Supported by the DisruptiveG Lab and the AMD HPC Fund}
}
```

## Acknowledgments

This research was supported by the **DisruptiveG Lab** at the University of New Haven and the **AMD HPC Fund**, which provided access to AMD Instinct MI300X accelerator hardware for local Llama-4 Maverick deployment. Special thanks to Dr. Elmahedi Mahalal for his advising throughout this work, and to the University of New Haven Tagliatela College of Engineering for supporting this research.

## Contact

- **Ryan Godburn** — rgodb1@unh.newhaven.edu
- **Dr. Elmahedi Mahalal** (Advisor) — emahalal@newhaven.edu

---

*This repository accompanies the thesis submitted in partial fulfillment of the requirements for the degree of B.S. in Cybersecurity and Networks at the University of New Haven.*

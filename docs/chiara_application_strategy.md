# Chiara Segala application strategy

This file defines how the agent should position the default profile.

## Core positioning

Chiara Segala should be positioned as an applied mathematics / scientific computing / research scientist profile, not as a generic software applicant.

Core anchors:

- Postdoctoral researcher at USI; previous postdoc at RWTH Aachen.
- Ph.D. in Mathematics on robust control strategies for mean-field collective dynamics.
- Numerical analysis, optimization, optimal control, model predictive control, sparse control, turnpike control.
- Multi-agent systems, mean-field theory, collective dynamics, opinion/crowd dynamics, multiscale models.
- Machine learning methods: neural networks, kernel methods, large-scale approximation, surrogate modelling.
- Uncertainty quantification: Monte Carlo, stochastic Galerkin, robust control.
- Mathematical finance: American option pricing, optimal stopping, conditional mean embeddings, large-scale kernel methods in financial economics.

## Best-fit roles

Prioritize:

1. Research Scientist / Applied Scientist
2. Numerical Analyst / Scientific Computing Researcher
3. Optimization Scientist / Control Scientist
4. Machine Learning Researcher with strong mathematical modelling component
5. Quantitative Researcher in mathematical finance or scientific computing
6. Computational Scientist / Mathematical Modeller
7. Research Engineer when the role is algorithmic and research-heavy

## Secondary roles

Consider if the description is mathematically deep:

- Quant finance research roles
- Industrial AI research roles
- Simulation / modelling roles
- Multi-agent / distributed decision systems roles
- Scientific software roles involving numerical algorithms
- Life-sciences quantitative modelling roles, only when the requirement is mathematical/computational rather than wet-lab/domain-specific

## Roles to down-rank

Down-rank or ignore:

- Generic frontend/backend/product software jobs
- Pure data analyst jobs with dashboard/reporting focus
- Sales, marketing, customer success, recruiting, legal, compliance
- Senior management roles requiring large team management rather than research
- Biology/pharma roles requiring experimental lab expertise rather than modelling/computation

## Geographic preference

Primary regions:

- Ticino / Lugano
- Zurich / Switzerland
- Paris / Île-de-France
- Northern Italy / Milan / Turin

Secondary:

- Other strong European research hubs
- London only for very strong fit

## Ranking notes

The score should not be interpreted as absolute truth. Use it as a triage signal.

Suggested workflow:

```bash
job-agent search
job-agent import-csv examples/manual_jobs_template.csv
job-agent rescore
job-agent rank --min-score 55
job-agent explain --job-id <ID>
job-agent prepare --job-id <ID>
```

For Chiara, a job is high-quality if the explanation shows contributions from at least two of:

- numerical_analysis
- optimization_control
- multi_agent_systems
- machine_learning
- math_physics
- finance, only for mathematical finance roles

## Application package emphasis

For scientific/research roles, emphasize:

- rigorous mathematical modelling
- numerical methods
- control and optimization
- multi-agent / mean-field systems
- kernel methods and large-scale approximation
- publication record and invited talks

For finance/quant roles, emphasize:

- American option pricing
- optimal stopping
- conditional mean embeddings
- large-scale kernel methods in financial economics
- numerical methods and uncertainty quantification

For ML/AI research roles, emphasize:

- theoretical foundations of deep learning project exposure
- kernel methods
- neural networks
- surrogate modelling
- multi-agent systems
- large-scale approximation

# DESIGN.md

## 1. Multiple Users: Onboarding with Limited Overhead

To be discussed in the meeting, I need more clarity on
`How can many users be onboarded to the platform with limited overhead (off the shelf components) ? `


---

## 2. Multi-Model Comparison

The current DAG is already parametrized to received as params the data path and the model. As such,
the users can submit the different jobs and download the results. Potentially, in the future,
if there's a strong user use-case, we could create a dedicated api that can trigger currently
multiple DAGs and linked them via some metadata

---

## 3. Failure Handling: OOM Resilience

The first option is to add retries to the dag tasks, though if the problem is OOM it will only
prevent the error if the retry happens when there's less memory pressure from other tasks.

Ideally, inference tasks could reduce the memory pressure by partially loading the inference set,
inferring, storing the result and then repeating (kind of moving to stream) instead of batch processing.

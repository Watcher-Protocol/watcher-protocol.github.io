# EDGE-05: Negative Anchor Count Passing as IMMUTABLE

**Status:** FIXED  
**Severity:** High  
**Discovered:** March 2026  
**Fixed in:** Phase 1 final  

---

## Description

A negative anchor count in D6 (Source Independence) was passing through
the governance gate without triggering a rejection. The condition checked
`anchor_count < 0` instead of `anchor_count <= 0`, allowing a count of
exactly zero to pass as if it were valid.

This meant a claim with zero independent anchors could reach IMMUTABLE
tier — the highest trust designation — without any independent
corroboration.

## Root Cause

Off-by-one error in the flood sub-gate boundary condition:

```python
# BEFORE (incorrect)
if anchor_count < 0:
    raise GovernanceError("negative anchor count")

# AFTER (fixed)
if anchor_count <= 0:
    raise GovernanceError("zero or negative anchor count")
```

## Impact

Any claim processed with an empty or zero-anchor evidence pool during
the affected window could have been assigned IMMUTABLE status
incorrectly.

## Fix

Changed boundary check from `< 0` to `<= 0` in the D6 scorer.
All claims with zero anchors now correctly trigger a gate failure
and receive REJECTED tier.

## Test Coverage

Added explicit test for zero-anchor edge case:

```python
def test_zero_anchor_rejected():
    claim = Claim(id="EDGE-05", text="test claim", evidence_pool=[])
    result = run_petrus(claim)
    assert result.tier == ClaimTier.REJECTED
```

---

*Bug identified and documented as part of Phase 1 validation.
Honest disclosure is a governance principle, not a liability.*

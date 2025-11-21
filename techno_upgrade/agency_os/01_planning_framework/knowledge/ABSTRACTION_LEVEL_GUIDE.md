# Abstraction Level Guide (v1.2)

**Version:** 1.2.0
**Purpose:** Guide for how `abstraction_level` affects planning across VIBE Framework tasks

---

## Overview

The `abstraction_level` field in `project_manifest.json` classifies projects by their abstraction level, which fundamentally affects:
- **Feature Complexity Estimation** (multipliers)
- **FAE Rule Applicability** (filtering)
- **NFR Priority Boosting** (which NFRs are critical)

---

## Abstraction Levels

### CONCRETE (Default)
**Definition:** Standard applications, websites, APIs with concrete user-facing features

**Examples:**
- E-commerce platform
- Blog CMS
- REST API service
- Mobile app

**Characteristics:**
- Features are concrete (e.g., "User Login", "Shopping Cart")
- Story points estimation is straightforward
- All FAE rules generally apply
- Standard NFR priorities (Performance, Security)

**Planning Impact:**
```yaml
complexity_multiplier: 1.0 (baseline)
fae_filter: all (no filtering needed)
nfr_priority_boost:
  - PERF-CAPACITY (Critical for user-facing apps)
  - SECU-CONFIDENTIALITY (Protect user data)
```

---

### LIBRARY
**Definition:** Reusable components, SDKs, packages with API-focused features

**Examples:**
- React component library
- Python SDK for API
- npm package
- Shared UI components

**Characteristics:**
- Features are API-focused (e.g., "Export Component", "Theme System")
- Complexity higher due to API design requirements
- App-specific FAE rules don't apply (e.g., no user authentication)
- Reusability and testability are critical

**Planning Impact:**
```yaml
complexity_multiplier: 1.2 (20% harder to estimate)
fae_filter: exclude_app_specific
  # Excluded FAE rules:
  # - FAE-009 (offline_first_data_sync - not relevant for libraries)
  # - FAE-010 (user_authentication - libraries don't have users)
nfr_priority_boost:
  - MAIN-REUSABILITY (Critical - must work across projects)
  - MAIN-TESTABILITY (Critical - SDKs need high test coverage)
  - COMP-INTEROPERABILITY (High - must integrate with other tools)
```

---

### FRAMEWORK
**Definition:** Tools to build tools, meta-features, template systems

**Examples:**
- VIBE Planning Framework
- Code generation framework
- Build system (like Webpack)
- CLI framework (like Click)

**Characteristics:**
- Features are abstract/meta (e.g., "Interview Engine", "Plugin System")
- Complexity estimation is hard (meta-work is ambiguous)
- Many app-specific FAE rules don't apply
- Modularity and reusability are CRITICAL

**Planning Impact:**
```yaml
complexity_multiplier: 1.5 (50% harder - meta-work is ambiguous)
fae_filter: framework_applicable
  # Excluded FAE rules:
  # - FAE-013 (dynamic_plugin_architecture) - Context different for frameworks
  #   (Interview templates ≠ runtime plugins)
  # - FAE-009 (offline_first_data_sync) - Not relevant
  # - FAE-010 (user_authentication) - Frameworks don't have end-users
nfr_priority_boost:
  - MAIN-MODULARITY (Critical - extensibility is core value)
  - MAIN-REUSABILITY (Critical - components must be reusable)
  - MAIN-TESTABILITY (Critical - meta-features need thorough testing)
```

**Special Considerations for Frameworks:**
- **Dogfooding Opportunities:** Frameworks often reuse components from their own ecosystem
  - Example: VIBE Coding Framework reuses NFR_CATALOG.yaml from Planning Framework
- **Meta-Complexity:** Estimating "Interview Engine" is harder than estimating "User Login"
  - Solution: Use abstraction_multiplier (1.5x) to account for uncertainty
- **NFR Shifts:** Scalability often becomes LOW priority (frameworks aren't user-facing at scale)
  - But MAIN-MODULARITY becomes CRITICAL (extensibility is the framework's value)

---

### PLATFORM
**Definition:** Multi-tenant ecosystems, infrastructure-focused systems

**Examples:**
- AWS-like cloud platform
- Plugin marketplace
- SaaS platform with multiple orgs
- Infrastructure-as-a-Service

**Characteristics:**
- Features are infrastructure-focused (e.g., "Tenant Isolation", "Resource Quotas")
- Complexity is highest (multi-tenancy, scale, security)
- Most FAE rules apply, but with platform-specific nuances
- Scalability, security, and reliability are all CRITICAL

**Planning Impact:**
```yaml
complexity_multiplier: 2.0 (100% harder - highest complexity)
fae_filter: platform_applicable
  # All rules apply, but with multi-tenancy considerations
nfr_priority_boost:
  - PERF-CAPACITY (Critical - must handle many tenants)
  - SECU-ACCOUNTABILITY (Critical - audit logging for compliance)
  - RELI-AVAILABILITY (Critical - downtime affects many users)
```

---

## How to Use in Planning Tasks

### Task 01: LEAN_CANVAS_VALIDATOR (Canvas Interview)

**No changes needed** - abstraction_level doesn't affect business validation

---

### Task 02: VIBE_ALIGNER (Feature Extraction + Feasibility)

#### Feature Extraction
When extracting features, consider abstraction level:

```python
# Example: Extracting "Interview Engine" feature
if abstraction_level == "FRAMEWORK":
    # This is a meta-feature, ask clarifying questions about:
    # - What types of questions can it ask?
    # - Is it template-based or dynamic?
    # - How are interview flows defined?
elif abstraction_level == "CONCRETE":
    # Standard feature, ask about:
    # - What inputs does the user provide?
    # - What outputs are generated?
```

#### Complexity Estimation
Apply multiplier to story points:

```python
base_complexity = estimate_story_points(feature)
multiplier = {
    "CONCRETE": 1.0,
    "LIBRARY": 1.2,
    "FRAMEWORK": 1.5,
    "PLATFORM": 2.0
}[abstraction_level]

final_complexity = base_complexity * multiplier
```

**Example:**
- Feature: "Interview Engine"
- Base Complexity: 8 points (medium-complex feature)
- Abstraction Level: FRAMEWORK
- **Final Complexity:** 8 × 1.5 = **12 points**

#### FAE Rule Filtering
Filter out non-applicable FAE rules:

```python
# Load FAE constraints
fae_rules = load_fae_constraints()

# Filter based on abstraction level
if abstraction_level == "LIBRARY":
    fae_rules = [rule for rule in fae_rules
                 if "app" not in rule.get("applicable_to", ["all"])]
elif abstraction_level == "FRAMEWORK":
    fae_rules = [rule for rule in fae_rules
                 if rule.get("framework_applicable", True)]
```

---

### Task 03: GENESIS_BLUEPRINT (Architecture Design)

#### NFR Priority Boosting
Adjust NFR priorities based on abstraction level:

```python
# Default NFR priorities (for CONCRETE)
nfr_priorities = {
    "PERF-CAPACITY": "HIGH",
    "SECU-CONFIDENTIALITY": "HIGH",
    "MAIN-MODULARITY": "MEDIUM",
    "MAIN-REUSABILITY": "LOW"
}

# Apply boost for FRAMEWORK
if abstraction_level == "FRAMEWORK":
    nfr_priorities["MAIN-MODULARITY"] = "CRITICAL"
    nfr_priorities["MAIN-REUSABILITY"] = "CRITICAL"
    nfr_priorities["PERF-CAPACITY"] = "LOW"  # Frameworks aren't user-facing at scale
```

---

## Migration Guide

### For Existing Projects (v1.0 → v1.2)

1. **Add `abstraction_level` to project_manifest.json:**
   ```json
   {
     "project_id": "...",
     "project_name": "...",
     "project_type": "commercial",
     "abstraction_level": "CONCRETE",  // ← ADD THIS
     "current_state": "PLANNING"
   }
   ```

2. **Infer abstraction level from project type:**
   - If project_name contains "framework", "SDK", "library" → `FRAMEWORK` or `LIBRARY`
   - If project_name contains "platform", "marketplace" → `PLATFORM`
   - Otherwise → `CONCRETE` (default)

3. **Re-validate FAE and NFR:**
   - Review FAE warnings - some may no longer apply
   - Review NFR priorities - adjust based on new boost rules

---

## Examples from Test #3 (VIBE Coding Framework)

### Before v1.2 (No abstraction_level)
```json
{
  "feature": "Conversational Interview Engine",
  "complexity": 8,  // Underestimated - treated as concrete feature
  "fae_warnings": [
    "FAE-013: dynamic_plugin_architecture flagged"  // False positive
  ],
  "nfr_priorities": {
    "PERF-CAPACITY": "HIGH",  // Wrong for framework
    "MAIN-MODULARITY": "MEDIUM"  // Should be CRITICAL
  }
}
```

### After v1.2 (abstraction_level: FRAMEWORK)
```json
{
  "feature": "Conversational Interview Engine",
  "base_complexity": 8,
  "abstraction_multiplier": 1.5,
  "final_complexity": 12,  // Correctly adjusted for meta-work
  "fae_warnings": [
    // FAE-013 excluded - not applicable to framework
  ],
  "nfr_priorities": {
    "PERF-CAPACITY": "LOW",  // Correct for framework
    "MAIN-MODULARITY": "CRITICAL",  // Boosted
    "MAIN-REUSABILITY": "CRITICAL"  // Boosted
  }
}
```

---

## FAE Rule Applicability Matrix

| FAE Rule ID | CONCRETE | LIBRARY | FRAMEWORK | PLATFORM |
|-------------|----------|---------|-----------|----------|
| FAE-001 (email_parsing) | ✅ | ✅ | ✅ | ✅ |
| FAE-009 (offline_sync) | ✅ | ❌ | ❌ | ✅ |
| FAE-010 (auth) | ✅ | ❌ | ❌ | ✅ |
| FAE-013 (plugin_arch) | ✅ | ⚠️ | ⚠️ (different context) | ✅ |

**Legend:**
- ✅ Always applicable
- ❌ Not applicable (excluded)
- ⚠️ Applicable but with different interpretation

---

## Summary

| Abstraction Level | Complexity Multiplier | Key NFR Priorities | FAE Filtering |
|-------------------|----------------------|-------------------|---------------|
| **CONCRETE** | 1.0x | PERF, SECU | All rules apply |
| **LIBRARY** | 1.2x | REUSABILITY, TESTABILITY | Exclude app-specific |
| **FRAMEWORK** | 1.5x | MODULARITY, REUSABILITY | Framework-applicable only |
| **PLATFORM** | 2.0x | CAPACITY, ACCOUNTABILITY | Platform-applicable |

---

**Document Version:** 1.2.0
**Last Updated:** 2025-11-13
**Related Files:**
- `planning_project_manifest.schema.json`
- `task_02_feature_extraction.md`
- `NFR_CATALOG.yaml`
- `FAE_constraints.yaml`

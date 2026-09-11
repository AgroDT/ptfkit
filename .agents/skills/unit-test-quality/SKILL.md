---
name: unit-test-quality
description: Write, strengthen, or review unit tests for meaningful behavioral protection. Use when adding tests, reviewing test changes, investigating misleading coverage, or checking generated tests. Focuses on contracts, independent oracles, preconditions, and defect detection; it does not require TDD, property-based testing, mutation frameworks, or coverage targets.
---

# Unit Test Quality

Treat a passing test as evidence only when it distinguishes conforming behavior from a plausible defect. Optimize for fault detection, not test count, assertion count, or line coverage.

## Establish what the test proves

For each new or materially changed non-trivial test, identify:

- the externally observable contract or invariant;
- the plausible production defect the test must detect;
- why the assertion would differ under that defect;
- the source of the expected result.

Do this in working notes or the final explanation; do not add ceremonial comments to every test. If no plausible defect would change the assertion, remove or redesign the test.

Infer contracts from authoritative specifications, public API documentation, issue reports, compatibility promises, and accepted domain rules. Existing implementation behavior is evidence, not automatically the contract. If the intended behavior is genuinely ambiguous, say so instead of canonizing the current output in a test.

## Keep the oracle independent

Derive expected values independently of the path being tested. Prefer, in order:

1. an explicit specification or hand-derived example;
2. a simpler, structurally different reference calculation;
3. a well-established independent implementation;
4. an invariant or relation whose truth does not depend on the same algorithm.

Do not compute expectations with the function under test, its policy resolver, its parser/serializer pair when both share the same defect, or a helper that merely mirrors the implementation. Do not copy constants, branch tables, or formulas from production code unless the contract itself defines them and the test cites that independent source.

When exact expected values are impractical, use strong invariants, metamorphic relations, differential checks, or bounded properties. Property-based generation is optional; ordinary examples are often enough.

## Verify the setup can reach the behavior

Check that the arranged state actually activates the branch, boundary, error, side effect, or interaction being claimed. Assert a precondition only when it is not already obvious from a small literal fixture and when a false precondition could let the main assertion pass vacuously.

Watch especially for:

- empty parameterized or generated case sets;
- filters or skips that remove the intended case;
- fixtures that never create the relevant state;
- assertions inside callbacks that are never called;
- exceptions accepted from the wrong operation;
- numeric inputs that do not straddle the specified boundary.

## Test behavior at the right boundary

Exercise the public or stable unit boundary that owns the contract. Calling a private helper can be useful diagnostically, but it does not protect the public path unless the public path is also exercised.

Mocks may isolate nondeterministic, slow, or external boundaries. Do not assert merely that a mock returned what it was configured to return. Preserve side effects and response structure that the unit relies on, and assert the unit's observable result or required interaction contract. If mock setup dominates the test or replaces the behavior being claimed, use a real collaborator, fake, or a broader test.

## Use discriminating cases

Choose cases that separate common wrong implementations from the correct one. Include boundaries and negative cases when they expose distinct plausible faults, not to satisfy a checklist. For policy code, derive cases from the policy rather than from the implementation's resolved value.

For generated tests, inspect both the generator and representative generated output. Ensure the generated test invokes the production entry point it claims to protect and that its expected values are independent of generator/runtime helpers implementing the same rule.

Avoid tests that only prove:

- code did not throw;
- a value is non-null, has a type, or contains a key when its meaning matters;
- an object reproduces the fixture that created it;
- a mock exists or was called without checking meaningful arguments/effects;
- the current implementation is internally consistent;
- a snapshot changed without establishing what must remain stable.

## Challenge important tests

For a new regression test or a test protecting a non-trivial contract, identify one small semantic mutation representing the named defect: change a boundary operator, use a wrong constant, remove validation or a side effect, select the wrong branch, or return a plausible default.

When safe and cheap, apply that mutation temporarily and run the narrowest relevant test. The test must fail for the intended reason. Restore the production file immediately, verify restoration, then run the unmodified test. Never leave a probe mutation in the worktree or mix it with unrelated user changes. If the worktree cannot be safely restored, use an isolated copy or perform a reasoned mutation review instead.

Do not require an executed mutation for trivial accessors, framework wiring, destructive or external behavior, expensive suites, or cases where the test already demonstrably failed on the exact defect. Record why it was skipped when the test's protective value is otherwise uncertain.

## Review outcome

When reviewing, report concrete findings rather than grading style. For each weak test, state:

- claimed contract;
- weakness in oracle, setup, boundary, or assertion;
- a plausible defect that survives;
- the smallest strengthening that would detect it.

Distinguish “code executed” from “behavior protected.” Treat coverage only as a map of code not exercised; never use a percentage as proof of test quality.

Before completion, run the focused tests and then the relevant broader suite when practical. Report commands and outcomes truthfully. Do not weaken assertions, update expected values to buggy output, add skips, or reduce scope merely to make CI green.

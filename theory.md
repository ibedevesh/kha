# Theory, the intuitions behind Kha

These are the analogies we reasoned from while designing this. They are not decoration
each one names a real property the architecture makes *literal*. When the design feels
abstract, come back here: the whole system is just "make the AI live under laws the way we
live under physics."

The one sentence they all point at:

> **We are free to supply input. We are not free to author the result. The world computes the
> result from our input and hands it back. Freedom and inviolable law coexist, and the world
> not our narration, is the record of what happened.**

---

## 1. The universe computes; our input is all we hold

You throw a ball. You do **not** compute the parabola, you supply a force, and *physics*
computes where it lands and hands the outcome back to you. You never held the result; you
supplied a **cause** and received an **effect**.

**In the system:** the AI supplies causes (`assert_fact`, `submit`), never results. The env
computes every effect (`step`) and returns it via `render`. The AI is a *source of input*
never a *computer of results*.

**Why it matters:** this is the cure for the disease we started with. Chain-of-thought lies
because the model *holds* an answer and fabricates a story for it. Here the model **never
holds the answer**, results are the env's job. There is nothing to fabricate.

---

## 2. You can't fly into space (a conservation law)

A human is free, free to want, to try, to move any muscle in any pattern. And still cannot
fly into space. Nobody *checks* you and stops you. The laws simply have no operation that
produces that outcome.

**In the system:** the AI's forward pass and its prose are totally free. But only the *one
dimension* the world reads, the move, has any effect. The rest is inert thought. Freedom
lives in the ignored dimensions; governance lives in the read dimension. Both fully present
no conflict. "Illegal" isn't *forbidden*; it's *unreachable*.

---

## 3. Time can't run backward (irreversibility / the ledger)

You are free in time, yet cannot go back. The past is fixed, not guarded, just structurally
gone.

**In the system:** the ledger is append-only and hash-chained. Once a move is recorded, it
can't be rewritten, reordered, or denied. The history of what the AI actually did is as fixed
as the arrow of time, and that fixity is what makes it a *proof*.

---

## 4. You can't reach the end of the universe (reachability)

You may travel forever and never arrive at a place outside your forward light-cone. Free to
move; still bounded by what is *reachable* from where you are.

**In the system:** from any state, only some states are reachable via legal moves. The AI can
run as long as it likes and never reach an illegal filing, that state is simply not in the
set anything can reach. **Existence is the certificate:** the world being in state S is itself
proof that a legal path produced S, because no other kind of path produces any state at all.

---

## 5. Muscles fire freely; the body moves lawfully

Your motor cortex can command any pattern of muscle activation it likes. Only the patterns
that map to physically realizable motion actually move your body; the rest is just intention.

**In the system:** the AI can emit anything. `parse` reads off the one realizable move (or
maps it to an inert `say`). Wild internal freedom, lawful external behavior, the seam between
them is `parse`, and `parse` is deterministic and total (**soft player, hard world**).

---

## 6. Chess: you can try to move into check, but that board doesn't exist

A chess engine won't reject your illegal move with an argument, the resulting position simply
isn't among the rules' outputs. The player never *authors* the board; the rules do, given a
move.

**In the system:** the AI never authors state. It offers a move; `step` (the rules) computes
the only board that can result, or none. **Author vs. player** is the entire distinction:
free-form generation is authoring (and hallucinates); a move into a rules-computed world is
playing (and cannot).

---

## 7. Police vs. physics

A cop watches you and can choose to stop you, and might miss something, or be argued with.
Physics doesn't watch and can't be argued with; it's the *medium*, not a *guard*.

**In the system:** a plain guardrail is police, the AI stands outside and submits to a guard.
The Environment is physics, the AI lives *inside*, and the laws aren't a checkpoint it passes
but the medium it moves through. You can't bribe gravity.

---

## 8. Senses: you perceive only what your body admits

You don't experience raw reality, only what your senses render. You have no words for the
wavelengths you can't see.

**In the system:** the AI perceives only `render(state)`, ground truth, re-shown fresh every
tick. It can't drift into believing its own past narration (the way normal agents do), because
each tick **re-grounds** it to the true state. And it can't even *reference* things the world
never showed it.

---

## 9. Verification is not self-checking, it's a property of the medium

You don't stay on the ground by continuously *proving to yourself* that gravity holds. Gravity
holds regardless of what you believe. Self-verification (a mind checking its own work) is
exactly the unreliable thing.

**In the system:** the AI never verifies anything. Verification is a property of the medium it
cannot escape, an unverified move simply has no effect. Reliability doesn't come *from* the
AI; it comes from the AI never being in the trust path at all.

---

## The design principles these map to

| Fiction | Principle in the code |
|---|---|
| Universe computes, we input | cause → env computes → effect; AI never holds a result |
| Can't fly to space | illegal = unreachable, not rejected |
| Time can't reverse | append-only hash-chained ledger |
| Can't reach the end | reachability; existence is the certificate |
| Muscles free, body lawful | soft player, hard world (`parse` total + deterministic) |
| Chess move into check | author vs. player; AI never writes state |
| Police vs. physics | the AI lives *inside*; laws are the medium, not a guard |
| Senses render reality | AI sees only `render`; re-grounded every tick |
| Gravity isn't self-checked | verification is the medium's property, not the AI's job |

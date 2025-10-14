# Chinese Syntax Analysis Reference Table

## Syntax Categories (Color-coded)

 Category 	 Code 	 Description 	 Purpose 
            
 **Subject** 	 `S` 	 Sentence subject 	 Who/what performs the action 
 **Object** 	 `O` 	 Sentence object 	 Who/what receives the action 
 **Verb** 	 `V` 	 Action/state 	 What happens/is 
 **Adjunct** 	 `A` 	 Modifiers 	 How/when/where/why 
 **Conjunction** 	 `C` 	 Connectors 	 And/but/or 
 **Preposition** 	 `P` 	 Relationship words 	 In/on/at/to 
 **Punctuation** 	 `PUNCT` 	 Marks 	 。，！？ 

## POS Tags Mapping

### Core POS Categories

| POS Tag | Category | Description | Examples |
|---------|----------|-------------|----------|
| **Verbs** | | | |
| `v*` (v, vd, vn, etc.) | `V` | All verb types | 吃, 跑, 是, 有 |
| **Nouns & Pronouns** | | | |
| `r`, `nh`, `nr` (at start) | `S` | Pronouns/names as subject | 我, 你, 张三 |
| `r`, `nh`, `nr` (after V/P) | `O` | Pronouns/names as object | 我, 他, 李四 |
| `n*` (at start) | `S` | First noun as subject | 苹果, 学生 |
| `n*` (after V) | `O` | Noun after verb as object | 书, 水 |
| `n*` (after P/C) | `O` | Noun after prep/conj | 学校, 家 |
| **Modifiers (Adjuncts)** | | | |
| `d` | `A` | Adverbs | 很, 非常, 快 |
| `a` | `A` | Adjectives | 大, 红, 漂亮 |
| `b` | `A` | Other modifiers | 其他, 别的 |
| `m`, `q` | `A` | Numbers & quantifiers | 一, 个, 些 |
| `f`, `s` | `A` | Direction & place words | 上, 里, 北京 |
| **Connectors** | | | |
| `c`, `cc` | `C` | Conjunctions | 和, 但是, 或 |
| `p` | `P` | Prepositions | 在, 从, 向 |
| `u`, `y`, `e` | `P` | Particles & auxiliaries | 的, 了, 吗 |
| **Special** | | | |
| Punctuation | `PUNCT` | All punctuation | 。，！？ |
| Others | `X` | Unclassified | - |

## Algorithm Flow

```python
# Simplified Logic Flow
for each word in sentence:
    if punctuation → PUNCT
    elif verb → V
    elif pronoun/name:
        if first word → S
        elif after verb/preposition → O
        else → S
    elif noun:
        if first word → S
        elif after verb → O
        elif after preposition/conjunction → O
        else → S/O (context dependent)
    elif modifier → A
    elif connector → C/P
    else → X
```

## Example Analysis

**Input:** "我今天在学校吃了苹果"
**Output:**
```
我/S  今天/A  在/P  学校/O  吃了/V  苹果/O
```

This table provides a comprehensive reference for understanding how the syntax analysis algorithm maps Chinese POS tags to syntactic categories with the updated color scheme.
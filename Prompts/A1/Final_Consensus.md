# Role
Act as the Master Editor and Senior Norwegian Bokmål Linguist. Your task is to produce the final, "Gold Standard" batch of 10 flashcards.

# Input
1. **Original Output:** The initial attempt at generating 10 cards.
2. **Critiques A-C:** Three expert validation passes (JSON format) containing findings and suggested corrections from Senior Pro Auditors.

# Objective
- Analyze the findings from all THREE critiques.
- **ABSOLUTE PRIORITY:** You MUST ensure the final sentence uses the original Norwegian target word. If a critic suggests swapping the target word for an easier one, IGNORE THAT SUGGESTION. You may use inflected forms (plurals, past tense, definite forms), but the root word must remain.
- **Linguistic Authority:** Critiques A, B, and C are from Senior Pro Auditors. Their judgment on complex grammar or subtle linguistic nuances is paramount. Each critique provides a `verified_line` for every item; compare these side-by-side with the Original Output to select or synthesize the "Gold Standard" version.
- **Target CEFR Level:** A1 (Beginner). Sentences MUST be short (4-8 words) and highly concrete.
- Ensure perfect grammar, gender agreement (en/ei/et), and natural idiomatic phrasing.

**Decision Hierarchy (Priority Order):**
1. **Target Word Integrity:** The root word MUST be present in the Norwegian sentence.
2. **Linguistic Accuracy:** The Norwegian must be natural, grammatically perfect, and appropriate for A1.
3. **Length Constraint:** 4-8 words. If you must choose, favor a natural sentence that is slightly over the limit rather than a "perfect length" sentence that sounds artificial.
4. **Translation:** English must be idiomatic and match the context.

- **English Quality:** English sentences must be natural, idiomatic English, not literal word-for-word translations.

- **Safety Rule:** Do NOT use semicolons within the sentences themselves; use a period or comma instead.

# Quality Control (Final Check)
- **Format:** `Norwegian-Word;Norwegian-Sentence;English-Word;English-Sentence`.
- **Length:** EXACTLY 10 lines of data. If you output 9 or 11 lines, the system pipeline will crash.
- **Punctuation:** All sentences must end with a period or question mark.

# Output Format (Strict)
Return ONLY the final 10 lines of data. 
- Your response must start immediately with the first line of data.
- NO markdown code blocks (```).
- NO extra conversational text.
- Exactly 10 lines of semicolon-delimited text.
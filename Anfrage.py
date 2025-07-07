from openai import OpenAI

client = OpenAI()

prompt = """
Statement:
"We achieved net zero CO₂ emissions in 2023."

Reported Data:
- Year: 2023
- Scope-1 emissions: 1,200,000 t CO₂
- Scope-2 emissions: 450,000 t CO₂
- Scope-3 emissions: 2,300,000 t CO₂
- Total emissions: 3,950,000 t CO₂

Task:
1. Is there a contradiction? Answer true or false.
2. Is this greenwashing? Answer true or false.
3. Explanation in max. 2 sentences.
Return as JSON:
{
  "contradiction": true/false,
  "greenwashing": true/false,
  "explanation": "..."
}
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a sustainability compliance assistant."},
        {"role": "user", "content": prompt}
    ]
)

print(response.choices[0].message.content)

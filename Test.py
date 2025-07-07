import json

with open('testdata.json', 'r') as f:
    test_cases = json.load(f)

# Beispiel Zugriff
print(test_cases[0]['text'])
print(test_cases[0]['kpis'])

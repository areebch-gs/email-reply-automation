from pipeline import answer

question = input("Question: ")
result = answer(question)

print(f"\nAnswer:\n{result['answer']}")
print("\nSources:")
for s in result["sources"]:
    print(f"  - {s['file']} (page {s['page']})")

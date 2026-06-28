"""Quick test: does AI actually work?"""
from app import create_app
from app.services.ai_service import _provider, generate_flashcards

app = create_app()
with app.app_context():
    print("Provider detected:", _provider())
    print("Groq key present:", bool(app.config.get("GROQ_API_KEY")))
    print("Gemini key present:", bool(app.config.get("GEMINI_API_KEY")))
    print()
    print("Generating 3 flashcards on 'Photosynthesis'...")
    try:
        cards = generate_flashcards("Photosynthesis", n=3)
        for i, c in enumerate(cards, 1):
            print(f"\n{i}. Q: {c['question']}")
            print(f"   A: {c['answer']}")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
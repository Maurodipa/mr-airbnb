import sys
from app.agent import app

def main():
    prompt = "run il recommender agent per raccomandarmi le tariffe per notte per il mio appartmento (periodo 1 - 18 agosto)"
    print(f"Running agent with prompt: {prompt}")
    
    # Run the workflow
    try:
        result = app.run(prompt)
        print("\n=== AGENT RESPONSE ===")
        print(result)
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    main()

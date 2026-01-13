import argparse
from audio_generation import run_tests_pt_en, generate_interview_english, generate_interview_spanish

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TTS tests and generate interviews.")
    parser.add_argument("--model", choices=["fast", "reasoning"], default="fast", help="Model type for interview generation.")
    parser.add_argument("--specialist", choices=["grammar", "daily"], help="Specialist type for English generation.")
    
    args = parser.parse_args()
    
    # Testes unitários PT/EN nas vozes instaladas
    run_tests_pt_en()

    # Geração das entrevistas em inglês e espanhol
    generate_interview_english(args.model, args.specialist)
    generate_interview_spanish()

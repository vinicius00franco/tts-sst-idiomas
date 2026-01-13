import argparse
from audio_generation import run_tests_pt_en, generate_interview_english, generate_interview_spanish
from interview_generator import InterviewGeneratorBuilder

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TTS tests and generate interviews.")
    parser.add_argument("--model", choices=["fast", "reasoning"], default="fast", help="Model type for interview generation.")
    parser.add_argument("--specialist", choices=["grammar", "daily"], help="Specialist type for generation.")
    parser.add_argument("--langs", nargs="+", choices=["en", "es"], default=["en", "es"], help="Languages to generate.")
    parser.add_argument("--topic-subject", help="Subject to suggest topics.")
    parser.add_argument("--selected-topic", help="Selected topic text for conversation generation.")

    args = parser.parse_args()

    # Testes unitários PT/EN nas vozes instaladas
    run_tests_pt_en()

    selected_topic = args.selected_topic
    if args.topic_subject and not selected_topic:
        # Apenas sugerir tópicos e sair
        builder = InterviewGeneratorBuilder().set_model_type(args.model)
        if args.specialist:
            builder.set_specialist(args.specialist)
        gen = builder.build()
        # Por simplicidade sugerimos em EN
        topics = gen.suggest_topics(args.topic_subject, target_lang="en")
        print("Topic options:")
        for i, t in enumerate(topics, 1):
            print(f"{i}. {t}")
        print("Use --selected-topic '<texto>' para gerar a conversa.")
        raise SystemExit(0)

    # Geração conforme línguas selecionadas
    if "en" in args.langs:
        generate_interview_english(args.model, args.specialist, selected_topic)
    if "es" in args.langs:
        generate_interview_spanish(args.model, args.specialist, selected_topic)

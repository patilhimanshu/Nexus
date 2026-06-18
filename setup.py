from config.setup_questions import questions
def setup():
    answers = {}
    for q in questions:
        if 'options' in q:
            options = q['options']
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
        answer = input(q['question'])
        answers[q['key']] = answer
    print(answers)
if __name__ == '__main__':
    setup()

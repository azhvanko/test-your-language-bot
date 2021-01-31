from dataclasses import dataclass
from typing import List, NamedTuple


class Question(NamedTuple):
    question_id: int
    question: str
    answers: List[str]
    old_answers_order: List[int]
    right_answer: int

    def get_right_answer(self) -> str:
        return self.answers[self.right_answer]

    def get_whole_question(self) -> str:
        right_answer = self.get_right_answer()
        return self.question.replace('___', right_answer)

    def get_answer_index(self, answer_index: int) -> int:
        return self.old_answers_order[answer_index]


@dataclass
class LanguageTest:
    questions: List[Question]
    user_answers: List[int]
    current_question: int = 0
    number_answers: int = 0

    def register_answer(self, answer: int) -> None:
        self.user_answers[self.current_question] = answer - 1

    def get_current_question(self) -> Question:
        return self.questions[self.current_question]

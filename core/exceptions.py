
class LanguageTestError(Exception):
    pass


class DuplicateQuestionError(LanguageTestError):
    pass


class EmptyQuestionsListError(LanguageTestError):
    pass


class FileError(LanguageTestError):
    pass


class KeyMissingError(LanguageTestError):
    pass


class KeyTypeError(LanguageTestError):
    pass


class LanguageTypeError(LanguageTestError):
    pass


class NumberAnswersError(LanguageTestError):
    pass


class RightAnswerError(LanguageTestError):
    pass


class LanguageTestTypeError(LanguageTestError):
    pass

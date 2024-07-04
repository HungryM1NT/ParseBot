import unittest
from app.parse import get_vacancies, get_resumes


class TestPrime(unittest.TestCase):
    def test_get_clear_vacancies(self):
        result_num, vacancies = get_vacancies("", {})
        self.assertTrue(result_num and vacancies)

    def test_get_filtered_vacancies1(self):
        result_num, vacancies = get_vacancies("", {'Опыт работы': 'от 1 года до 3 лет',
                                                   'Образование': 'среднее профессиональное',
                                                   'График работы': 'полный день'})
        self.assertTrue(result_num and vacancies)

    def test_get_filtered_vacancies2(self):
        result_num, vacancies = get_vacancies("", {'Опыт работы': 'нет опыта',
                                                   'Образование': 'не требуется или не указано',
                                                   'График работы': 'удаленная работа'})
        self.assertTrue(result_num and vacancies)

    def test_get_clear_resumes(self):
        result_num, resumes = get_resumes("", {})
        self.assertTrue(result_num and resumes)

    def test_get_filtered_resumes1(self):
        result_num, resumes = get_resumes("", {'Опыт работы': 'нет опыта',
                                               'Образование': 'среднее специальное',
                                               'График работы': 'вахтовый метод'})
        self.assertTrue(result_num and resumes)

    def test_get_filtered_resumes2(self):
        result_num, resumes = get_resumes("", {'Опыт работы': 'нет опыта',
                                               'Образование': 'не имеет значения',
                                               'График работы': 'не имеет значения'})
        self.assertTrue(result_num and resumes)


if __name__ == '__main__':
    unittest.main()

from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
from multiprocessing import Pool

ua = UserAgent()
headers = {'user-agent': ua.chrome}

filter_dict = {
    "не имеет значения": "",
    "от 1 года до 3 лет": "&experience=between1And3",
    "нет опыта": "&experience=noExperience",
    "от 3 до 6 лет": "&experience=between3And6",
    "более 6 лет": "&experience=moreThan6",
    "полный день": "&schedule=fullDay",
    "сменный график": "&schedule=shift",
    "вахтовый метод": "&schedule=flyInFlyOut",
    "удаленная работа": "&schedule=remote",
    "гибкий график": "&schedule=flexible",
    "не требуется или не указано": "&education=not_required_or_not_specified",
    "среднее профессиональное": "&education=special_secondary",
    "среднее": "&education_level=secondary",
    "среднее специальное": "&education_level=special_secondary",
    "незаконченное высшее": "&education_level=unfinished_higher",
    "бакалавр": "&education_level=bachelor",
    "магистр": "&education_level=master",
    "кандидат наук": "&education_level=candidate",
    "доктор наук": "&education_level=doctor",
    "высшее": ""
}


def get_vacancy_data(url):
    values = []
    page_html = requests.get(url=url, headers=headers)
    page_bs = BeautifulSoup(page_html.text, "html.parser")
    all_vacancies_on_page = page_bs.find_all(class_='vacancy-card--z_UXteNo7bRGzxWVcL7y font-inter')
    for vacancy in all_vacancies_on_page:
        name = vacancy.find(attrs={'data-qa': 'bloko-header-2'}).text
        link = vacancy.find("a", class_="bloko-link")["href"]
        compensation = vacancy.find(class_="compensation-labels--uUto71l5gcnhU2I8TZmz")
        salary = compensation.find("span", class_="bloko-text").text if compensation.find(
            "span", class_="bloko-text") else ""
        exp = compensation.find(attrs={'data-qa': 'vacancy-serp__vacancy-work-experience'}).text if compensation.find(
            attrs={'data-qa': 'vacancy-serp__vacancy-work-experience'}) else ""
        company = vacancy.find(attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).text if vacancy.find(
            attrs={'data-qa': 'vacancy-serp__vacancy-employer'}) else ""
        city = vacancy.find(attrs={'data-qa': 'vacancy-serp__vacancy-address_narrow'}).text if vacancy.find(
            attrs={'data-qa': 'vacancy-serp__vacancy-address_narrow'}) else ""
        values.append((name, link, salary, company, city, exp))
    return values


def get_resume_data(url):
    values = []
    page_html = requests.get(url=url, headers=headers)
    page_bs = BeautifulSoup(page_html.text, "html.parser")
    all_resumes_on_page = page_bs.find_all(attrs={'data-qa': 'resume-serp__resume'})
    for resume in all_resumes_on_page:
        name = resume.find("h3", class_="bloko-header-section-3").text
        link = "https://hh.ru" + resume.find("a", class_="bloko-link")["href"]
        temp_experience = resume.find(attrs={'data-qa': 'resume-serp__resume-excpirience-sum'})
        temp_status = resume.find(class_="tag_job-search-status-active--WAZ6Sx3vDygvcdzNm06h")
        age = resume.find(attrs={'data-qa': 'resume-serp__resume-age'}).text.replace('\xa0', " ") if resume.find(
            attrs={'data-qa': 'resume-serp__resume-age'}) else ""
        experience = temp_experience.text.replace('\xa0', " ") if temp_experience else ""
        status = temp_status.text if temp_status else ""

        values.append((name, link, age, experience, status))
    return values


def get_vacancies(text, our_filter):
    filter_text = ""
    if "высшее" in our_filter.values():
        filter_text += "&education=higher"
    for filter_item in our_filter.values():
        filter_text += filter_dict[filter_item]

    main_url = f"https://hh.ru/search/vacancy?text={text}&salary=&ored_clusters=true&page=0" + filter_text
    main_page = requests.get(url=main_url, headers=headers)

    main_bs = BeautifulSoup(main_page.text, "html.parser")
    pager = main_bs.find_all(class_="pager-item-not-in-short-range")
    page_num = int(pager[-1].text)

    all_urls = []
    for page in range(0, page_num):
        all_urls.append(f"https://hh.ru/search/vacancy?text={text}&salary=&ored_clusters=true&page={page}" +
                        filter_text)
    with Pool(5) as p:
        vacancy_pool = p.map(get_vacancy_data, all_urls)
    vacancies = []
    for vacancy_group in vacancy_pool:
        for vacancy in vacancy_group:
            vacancies.append(vacancy)

    vacancies_num_text = main_bs.find(attrs={'data-qa': 'bloko-header-3'}).text
    vacancies_num_text = vacancies_num_text[vacancies_num_text.find(" ") + 1:vacancies_num_text.find("вакан") - 1]
    vacancies_num = vacancies_num_text.replace("\xa0", '')
    return vacancies_num, vacancies


def get_resumes(text, our_filter):
    filter_text = ""
    if "высшее" in our_filter.values():
        filter_text += "&education_level=higher"
    for filter_item in our_filter.values():
        filter_text += filter_dict[filter_item]

    main_url = f"https://hh.ru/search/resume?text={text}&ored_clusters=true&order_by=relevance" + \
               "&search_period=0&logic=normal&pos=full_text&exp_period=all_time" + \
               "&hhtmFrom=resume_search_result&hhtmFromLabel=resume_search_line" + filter_text
    main_page = requests.get(url=main_url, headers=headers)

    all_urls = [main_url]

    main_bs = BeautifulSoup(main_page.text, "html.parser")
    pager = main_bs.find_all(class_="pager-item-not-in-short-range")
    page_num = int(pager[-1].text)

    for page in range(1, page_num):
        all_urls.append(f"https://hh.ru/search/resume?text={text}&ored_clusters=true&order_by=relevance" +
                        f"&search_period=0&logic=normal&pos=full_text&exp_period=all_time&page={page}" + filter_text)
    with Pool(5) as p:
        resume_pool = p.map(get_resume_data, all_urls)
    resumes = []
    for resume_group in resume_pool:
        for resume in resume_group:
            resumes.append(resume)

    resumes_num_text = main_bs.find(attrs={'data-qa': 'bloko-header-3'}).text
    resumes_num_text = resumes_num_text[resumes_num_text.find(" ") + 1:resumes_num_text.find("резюме") - 1]
    resumes_num = resumes_num_text.replace("\xa0", '')
    return resumes_num, resumes

import json
import re

import requests
from bs4 import BeautifulSoup, Tag
from fake_headers import Headers


def parse_page(url: str):
    headers = Headers(os='win', browser='chrome')
    query = requests.get(url, headers=headers.generate()).text
    return BeautifulSoup(query, 'html.parser')


def get_page_count(search_page: Tag):
    attr = 'data-qa'
    page_wrappers = search_page.find_all(attrs={'data-qa': re.compile(r'pager-page-wrapper-.*')})
    try:
        count = int(page_wrappers[-1].get('data-qa').split('-')[-1])
    except ValueError:
        count = 0
    return count


def vacancy_has_all_keywords(post: Tag, *args):
    description = post.find('div', attrs={'data-qa': 'vacancy-description'}).text.replace(u'\xa0', ' ')
    return all([key in description for key in args])


def parse_vacancy(vacancy: Tag):
    company_name = vacancy.find('a', attrs={'data-qa': 'vacancy-company-name'})
    if company_name:
        company_name = company_name.text.replace(u'\xa0', ' ')
    else:
        company_name = None
    company_location = vacancy.find(attrs={'data-qa': 'vacancy-view-location'})
    company_raw_address = vacancy.find(attrs={'data-qa': 'vacancy-view-raw-address'})
    if company_location:
        city = company_location.text.replace(u'\xa0', ' ')
    elif company_raw_address:
        city = company_raw_address.text.replace(u'\xa0', ' ').split(',')[0]
    else:
        city = None
    salary = vacancy.find('div', attrs={'data-qa': 'vacancy-salary'}).text.replace(u'\xa0', ' ').strip()
    return {'salary': salary,
            'company_name': company_name,
            'city': city}


def main():
    keywords = ['Django', 'Flask']
    query_url = 'https://hh.ru/search/vacancy?text=python&area=1&area=2'

    first_page = parse_page(query_url)

    count = get_page_count(first_page)

    result = []  # list of vacancies: href, salary, company_name, city
    for page_number in range(count + 1):
        page = parse_page(f'{query_url}&page={page_number}')
        posts = page.find_all('div', class_='serp-item')

        for post in posts:
            href = post.find_next('a', attrs={'data-qa': 'serp-item__title'}).get('href')
            vacancy = parse_page(href)
            if vacancy_has_all_keywords(vacancy, *keywords):
                record = {'href': href, **parse_vacancy(vacancy)}
                result.append(record)
    with open('vacancies.json', 'w', encoding='utf-8') as file:
        json.dump(result, file, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()

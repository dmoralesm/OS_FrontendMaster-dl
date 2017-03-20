from bs4      import BeautifulSoup
from config   import ACCOUNT
from selenium import webdriver
from urllib2  import urlopen, URLError, HTTPError

import httplib
import cookielib
import json
import mechanize
import os
import string
import time
import os.path

# Constants
DATA_COURSE_LIST              = './DATA_COURSE_LIST.json'
DATA_COURSE_DETAILED_LIST_CDN = './DATA_COURSE_DETAILED_LIST_CDN.json'
URL_LOG_IN                    = 'https://frontendmasters.com/login/'
URL_COURSE_LIST               = 'https://frontendmasters.com/courses/'

# Global Browser Setup
browser = webdriver.Chrome()

# Func(PASSED): Authentication
def browser_login():
    browser.get(URL_LOG_IN)
    time.sleep(2)

    username = browser.find_element_by_id('rcp_user_login')
    username.send_keys(ACCOUNT['username'])
    password = browser.find_element_by_id('rcp_user_pass')
    password.send_keys(ACCOUNT['password'])

    time.sleep(2)
    browser.find_element_by_id('rcp_login_submit').click()


# Func(PASSED): Retrieve courses list
def _get_course_list():
    BASE_URL = URL_COURSE_LIST
    browser.get(BASE_URL)
    bs_course_page = BeautifulSoup(browser.page_source, "html.parser")
    course_titles = bs_course_page.select('h2.title')
    course_links = []

    for title in course_titles:
        link = title.find('a')

        if link is not None:
            title = link.getText()
            course = {'title': title, 'url': link['href']}
            course_links.append(course)

    return course_links

def save_course_list():
    with open(DATA_COURSE_LIST, 'w') as file:
        file.write(json.dumps(_get_course_list()))

def retrive_course_list():
    with open(DATA_COURSE_LIST, 'r') as file:
        return json.load(file)


# Func(PASSED): Retrieve detailed section list for each course
def _get_videos_data(videos_section_items):
    subsections = []

    for video in videos_section_items:
        # Course subsection data structure
        course_subsection = {
            'title': None,
            'url': None,
            'downloadable_url': None
        }

        course_subsection['url'] = video.find('a')['href']
        course_subsection['title'] = video.find('a').find(
            'span', {'class', 'text'}
        ).find(
            'span', {'class', 'title'}
        ).getText()

        subsections.append(course_subsection)

    return subsections

def _get_section_data(sections_items):
    sections = []
    for item in sections_items:
        # Course section data structure
        course_section = {
            'title': None,
            'subsections': []
        }

        course_section['title'] = item.find(
            'h4', {'class': 'video-nav-section-title'}
        ).getText()

        videos_section = item.find('ul')
        videos_section_items = videos_section.find_all('li')

        videos_data = _get_videos_data(videos_section_items)
        course_section['subsections'].extend(videos_data)

        sections.append(course_section)

    return sections

def _get_detailed_course_list(course_list):
    detailed_course_list = []

    for course in course_list:
        # Course detail data structure
        course_detial = {
            'title': course['title'],
            'url': course['url'],
            'sections': []
        }

        browser.get(course_detial['url'])
        browser.implicitly_wait(2)
        soup_page = BeautifulSoup(browser.page_source, 'html.parser')

        # Find video nav list
        sections = soup_page.find('ul', {'class': 'video-nav-list'})
        sections_items = sections.find_all(
            'li', {'class': 'video-nav-section'}
        )

        sections = _get_section_data(sections_items)
        course_detial['sections'].extend(sections)

        detailed_course_list.append(course_detial)

    return detailed_course_list

def save_course_detailed_list(course_list):
    with open(DATA_COURSE_DETAILED_LIST_CDN, 'w') as file:
        file.write(json.dumps(_get_detailed_course_list(course_list)))

def retrive_course_detailed_list():
    with open(DATA_COURSE_DETAILED_LIST_CDN, 'r') as file:
        return json.load(file)


# Func(PASSED): Retrieve video CDN
def _get_video_source():
    video_tag = browser.find_element_by_tag_name('video')
    source_tag = video_tag.find_element_by_tag_name('source')
    source_link = source_tag.get_attribute('src')
    return source_link

def _write_downloadable_data(courses_data):
    with open(DATA_COURSE_DETAILED_LIST_CDN, 'w') as file:
        file.write(json.dumps(courses_data))
def save_downloadable_links(courses_data):
    for course in courses_data:
        url = course['url']
        for section in course['sections']:
            for subsection in section['subsections']:
                if subsection['downloadable_url'] is None:
                    video_url = url + subsection['url']
                    print("Retriving: {0}/{1}/{2}".format(
                        format_filename(course['title']),
                        format_filename(section['title']),
                        format_filename(subsection['title'])))
                    browser.get(video_url)
                    # browser.implicitly_wait(5)
                    time.sleep(5)
                    url_str = _get_video_source()
                    print("Video URL: {0}".format(url_str))
                    subsection['downloadable_url'] = url_str
                    _write_downloadable_data(courses_data)

def retrive_downloadable_links():
    with open(DATA_COURSE_DETAILED_LIST_CDN, 'r') as file:
        return json.load(file)



# Func(PASSED): Helpers
def download_file(url, path):
    if not os.path.isfile(path):
        buff = urlopen(url)
        print("Downloading: %s" % (path))

        with open(path, 'wb') as local_file:
            local_file.write(buff.read())

def format_filename(filename_str):
    s = filename_str
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')  # I don't like spaces in filenames.
    return filename

def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Func(PASSED): Download resources via CDN
def download_courses(courses_array):
    # Create download directory
    create_path('./Download')

    for i0, course in enumerate(courses_array):
        title = course['title']
        # Create course directory
        course_path = './Download/{0}-{1}'.format(i0+1, title)
        create_path(course_path)

        for i1, section in enumerate(course['sections']):
            section_title = section['title']

            for i2, subsection in enumerate(section['subsections']):
                subsection_title = subsection['title']
                print("Downloading: {0}".format(
                    format_filename(subsection_title)))

                filename = str(i1+1) + '-' + str(i2+1) + '_' + format_filename(
                    section_title) + '_' + format_filename(
                        subsection_title) + '.mp4'

                file_path = course_path + '/' + format_filename(filename)

                download_file(subsection['downloadable_url'], file_path)

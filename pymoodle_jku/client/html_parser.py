import re
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse, unquote, parse_qs

import html2markdown as html2markdown
from lxml import html, etree
from lxml.etree import _ElementUnicodeResult
from lxml.html.clean import Cleaner

from pymoodle_jku.classes.course_data import Url, UrlType, CourseData
from pymoodle_jku.classes.evaluation import Evaluation
from pymoodle_jku.utils.printing import print_exc


def d_utf8(obj) -> str:
    return obj.decode('utf-8')


class MainRegion:
    def __init__(self, response):
        """
        Takes a Response and extracts the region-main-box from it.
        :param response: A Response from a request call.
        """
        tree = html.fromstring(response.content.decode('utf-8'))
        main_region = tree.xpath('//body//div[@id="region-main-box"]')[0]

        self.region = main_region
        self.url = response.request.url


# href="https://moodle.jku.at/jku/mod/quiz/review.php?attempt=661309&cmid=4628980"

class QuizSummary(MainRegion):
    """
    QuizSummary is the Page where you can press "Review Quiz" on moodle.
    """

    def quiz_url(self) -> Optional[Url]:
        """
        The Url to the Moodle Quiz will be extracted.
        :return: A Url object if found, else None.
        """
        all_urls = self.region.xpath('.//a/@href')

        for url in all_urls:
            try:
                if (
                        u := Url(url,
                                 UrlType[
                                     Path(unquote(urlparse(url).path)).parts[3].capitalize()])).type is UrlType.Quiz and \
                        Path(unquote(urlparse(url).path)).parts[4] == 'review.php':
                    return u
            except (KeyError, ValueError, IndexError, AttributeError):
                # print(err)
                pass
        else:
            return None


def convert_elements(elements) -> str:
    """
    Cleans up the elements of a html string.
    Also converts it to markdown.
    :param elements: A List of str.
    :return: A markdown string.
    """

    output = ''
    cleaner = Cleaner()
    cleaner.forms = False
    cleaner.remove_tags = ['span']
    for e in elements:
        if isinstance(e, _ElementUnicodeResult):
            output += '\n'.join([line.strip() for line in str(e).splitlines()]) + '\n'
        else:
            e.attrib.clear()
            conv = html2markdown.convert(cleaner.clean_html(d_utf8(etree.tostring(e))))
            output += '\n'.join([line.strip() for line in conv.splitlines()])
        output += '\n'
    output += '\n'
    return output


class QuizPage(MainRegion):
    def __init__(self, response):
        """
        QuizPage is real Quiz Page, where all answers and questions are visible.
        :param response: A Response to extract the quiz from.
        """
        super().__init__(response)
        self.quiz = self.region.xpath('.//div[@role="main"]')[0]
        self.summary = self.quiz.xpath('.//table[contains(@class,"quizreviewsummary")]')[0]
        self.info = self.quiz.xpath('.//div[contains(@id,"question-")]/div[@class="info"]')
        questions = self.quiz.xpath('.//div[contains(@id,"question-")]/div[@class="content"]')

        images = self.quiz.xpath('.//div[contains(@id,"question-")]/div[@class="content"]//img/@src')
        self.images = list(set(images))

        self.questions = []
        for q in questions:
            divs = q.xpath('./div')
            if len(divs) > 1:
                self.questions.append((divs[0], divs[1]))
            else:
                self.questions.append((divs[0], None))

    def md_quiz(self) -> str:
        """
        Extracts the questions and answers as markdown strings.
        :return: A markdown string.
        """
        questions = zip(self.info, self.questions)

        summary = html2markdown.convert(d_utf8(etree.tostring(self.summary))) + '\n'

        # markdownify isnt parsing tables
        # tomd is removing a lot of stuff ()
        # html2markdown
        output = f'{summary}\n'
        for i, (q, f) in questions:
            subs = i.xpath('./node()')
            info = convert_elements(subs)
            # info = html2markdown.convert(d_utf8(etree.tostring(i)))

            subs = q.xpath('./node()')

            question = convert_elements(subs)
            # question = html2markdown.convert(d_utf8(etree.tostring(q)))

            if f is not None:
                subs = f.xpath('./node()')
                feedback = convert_elements(subs)
            else:
                feedback = '\n'
            # feedback = '' if f is None else html2markdown.convert(d_utf8(etree.tostring(f)))

            output += f'{info}{question}{feedback}'

        return output


class CoursePage(MainRegion):
    """
    CoursePage is the Page of a Moodle Course. There you can see all Urls and sections written by Professors.
    """

    def sections(self):
        """
        Returns all the sections of a CoursePage. Sections are normally different Topics.
        :return: A List of lxml HTML objects.
        """
        sections = []
        for section in self.region.xpath('.//ul[@class=$name]/li', name='topics'):
            subs = section.xpath('./node()')
            sections.append(convert_elements(subs))
        return sections

    def urls(self) -> List[Url]:
        """
        Loads all the URLs on a CoursePage.
        :return: A List of URLs.
        """
        all_url_imgs = self.region.xpath('.//a/img')
        urls = []
        for i in all_url_imgs:
            if (url_p := Path(unquote(urlparse((url := i.getparent().xpath('./@href')[0])).path)).parts)[2] == 'mod':
                try:
                    urls.append(Url(str(url), UrlType[url_p[3].capitalize()]))
                except KeyError as err:
                    print_exc(err)
        return urls

    def to_course_data(self) -> CourseData:
        """
        Converts the CoursePage to CourseData with links and sections.
        :return: A converted CourseData.
        """
        cd = CourseData(links=self.urls(), sections=self.sections())

        for l in cd.links:
            l.course = cd

        return cd


class LoginPage:
    def __init__(self, action, data):
        """
        Login Page is the login page of JKU.
        :param action: Is the form action of a html form.
        :param data: Is the data of this form as dict.
        """
        self.data = data
        self.action = action

    @staticmethod
    def from_response(response) -> 'LoginPage':
        """
        Creates a LoginPage from a Response.
        :param response: A Response from some request.
        :return: The LoginPage of the response.
        """
        tree = html.fromstring(response.content.decode('utf-8'))
        form_action = tree.xpath('//form/@action')[0]
        form = tree.xpath('//form/div/input')
        data = {}
        for inp in form:
            name = inp.xpath('./@name')[0]
            value = inp.xpath('./@value')[0]
            data[name] = value

        return LoginPage(form_action, data)


class MyPage:
    def __init__(self, sesskey, userid):
        """
        The (My) Dashboard Page of Moodle.
        :param sesskey: Extracted Session Key
        :param userid: Extracted User Id
        """
        self.sesskey = sesskey
        self.userid = userid

    @staticmethod
    def from_response(response) -> 'MyPage':
        """
        Creates a MyPage from a Response.

        :param response: Response to create the page from.
        :return: A Parsed MyPage.
        """
        content = response.content.decode('utf-8')
        logout_url = re.escape('https://moodle.jku.at/jku/login/logout.php?sesskey=')
        found_item = re.findall(f'{logout_url}([\w\d]+)', content)
        if len(found_item) > 0:
            sesskey = found_item[0]
        else:
            # regex didn't work. Trying other method
            index = content.find('sesskey')
            sesskey, count, qoute_count, sesskey_text = '', 0, 0, content[index:]
            while True:
                if sesskey_text[count] == '"':
                    qoute_count += 1
                elif qoute_count == 2:
                    sesskey += sesskey_text[count]
                if qoute_count == 3:
                    break
                count += 1
            sesskey = sesskey
        pref_url = re.escape('https://moodle.jku.at/jku/message/notificationpreferences.php?userid=')
        found_item = re.findall(f'{pref_url}(\d+)', content)
        if len(found_item) > 0:
            userid = int(found_item[0])
        else:
            print('No userid found. Basic operations should still work')
            userid = None

        return MyPage(sesskey, userid)


class ValuationOverviewPage(MainRegion):
    def __init__(self, response):
        """
        ValuationOverviewPage is the Page where you can see the summary of all Valuations from all subjects.
        :param response: A Response from where the valuations should be parsed.
        """
        super().__init__(response)
        valuation_values = self.region.xpath('.//table/tbody/tr/td/text()')
        valuation_names = self.region.xpath('.//table/tbody/tr/td/a/text()')
        valuation_urls = self.region.xpath('.//table/tbody/tr/td/a/@href')
        valuation_course_ids = [int(parse_qs(urlparse(u).query)['id'][0]) for u in valuation_urls]

        self.valuation = dict(zip(valuation_course_ids, zip(valuation_names, valuation_values)))


class ValuationPage(MainRegion):
    """
    A Valuation Page is the Valuation Page of each individual course.
    There you can see all points you got for assignments or quiz's.
    """

    def evaluations(self) -> List[Evaluation]:
        """
        Extracts all Evaluations from a Page.
        :return: A List of all Evaluations.
        """
        if len(self.region.xpath('.//table')) == 0:
            return []

        grade = self.region.xpath('.//table/thead/tr/th[@id="grade"]')[0]
        grade_range = self.region.xpath('.//table/thead/tr/th[@id="range"]')[0]

        first_row = self.region.xpath('.//table/thead/tr')[0]
        index_grade = first_row.index(grade)
        index_range = first_row.index(grade_range)

        table_rows = self.region.xpath('.//table/tbody/tr')

        evaluations = []
        for row in table_rows:
            if len(row.xpath('./td')) <= 1 or len(row.xpath('./th/a/text()')) == 0:
                continue
            name, url, criteria = row.xpath('./th/a/text()')[0], row.xpath('./th/a/@href')[0], row.xpath('./td/text()')
            grade, grade_range = criteria[index_grade - 1], criteria[index_range - 1]
            evaluations.append(
                Evaluation(name, str(url), UrlType[Path(unquote(urlparse(url).path)).parts[3].capitalize()], grade,
                           grade_range))
        return evaluations

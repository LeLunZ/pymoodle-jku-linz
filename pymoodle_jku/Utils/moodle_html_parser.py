import re
from pathlib import Path
from urllib.parse import urlparse, unquote

import html2markdown as html2markdown
from lxml import html, etree
from lxml.etree import _ElementUnicodeResult
from lxml.html.clean import Cleaner

from pymoodle_jku.Classes.course_data import Url, UrlType, CourseData
from pymoodle_jku.Classes.evaluation import Evaluation


class Body:
    def __init__(self, url, body):
        self.url = url


def d_utf8(obj):
    return obj.decode('utf-8')


class MainRegion:
    def __init__(self, response):
        tree = html.fromstring(response.content.decode('utf-8'))
        main_region = tree.xpath('//body//div[@id="region-main-box"]')[0]

        self.region = main_region
        self.url = response.request.url


# href="https://moodle.jku.at/jku/mod/quiz/review.php?attempt=661309&cmid=4628980"

class QuizSummary(MainRegion):
    def quiz_url(self):
        all_urls = self.region.xpath('.//a/@href')

        for url in all_urls:
            try:
                if (
                        u := Url(url,
                                 UrlType[
                                     Path(unquote(urlparse(url).path)).parts[3].capitalize()])).type is UrlType.Quiz and \
                        Path(unquote(urlparse((url)).path)).parts[4] == 'review.php':
                    return u
            except Exception as err:
                # print(err)
                pass
        else:
            return None


def convert_elements(elements):
    output = ''
    cleaner = Cleaner()
    cleaner.forms = False
    cleaner.remove_tags = ['span']
    for e in elements:
        if isinstance(e, _ElementUnicodeResult):
            output += str(e)
        else:
            e.attrib.clear()
            output += html2markdown.convert(cleaner.clean_html(d_utf8(etree.tostring(e))))
        output += '\n'
    if not output.endswith('\n'):
        output += '\n'
    return output


class QuizPage(MainRegion):
    def __init__(self, response):
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

    def md_quiz(self):
        questions = zip(self.info, self.questions)

        summary = html2markdown.convert(d_utf8(etree.tostring(self.summary)))

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
    def __init__(self, response):
        super().__init__(response)

    def sections(self):
        return self.region.xpath('.//ul[@class=$name]/li', name='topics')

    def urls(self):
        all_url_imgs = self.region.xpath('.//a/img')
        return [Url(i.getparent().xpath('./@href')[0],
                    UrlType[url_p[3].capitalize()])
                for i in all_url_imgs if
                (url_p := Path(unquote(urlparse((url := i.getparent().xpath('./@href')[0])).path)).parts)[2] == 'mod']

    def to_course_data(self):
        cd = CourseData(links=self.urls(), sections=self.sections())

        for l in cd.links:
            l.course = cd

        return cd


class LoginPage:
    def __init__(self, action, data):
        self.data = data
        self.action = action

    @staticmethod
    def from_response(response):
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
        self.sesskey = sesskey
        self.userid = userid

    @staticmethod
    def from_response(response):
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
        super().__init__(response)
        valuation_values = self.region.xpath('.//table/tbody/tr/td/text()')
        valuation_names = self.region.xpath('.//table/tbody/tr/td/a/text()')

        self.valuation = dict(zip(valuation_names, valuation_values))


class ValuationPage(MainRegion):
    def __init__(self, response):
        super().__init__(response)

    def evaluations(self):
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
                Evaluation(name, url, UrlType[Path(unquote(urlparse((url)).path)).parts[3].capitalize()], grade,
                           grade_range))
        return evaluations


def get_main_region_from_response(response):
    tree = html.fromstring(response.content.decode('utf-8'))
    main_region = tree.xpath('//body//div[@id="region-main-box"]')[0]
    return main_region


def urls_from_course(main_region):
    all_url_imgs = main_region.xpath('.//a/img')
    return [Url(i.getparent().xpath('./@href')[0],
                UrlType[i.getparent().xpath('./@href')[0].split('/')[-2].capitalize()])
            for i in all_url_imgs]


def get_url_from_exam_page(main_region):
    all_urls = main_region.xpath('.//a')
    for url in all_urls:
        link = url.xpath('./@href')[0]
        if (u := Url(link, UrlType(link.split('/')[2].capitalize()))).type is UrlType.Quiz:
            return u
    else:
        return None


def get_course_sections(main_region):
    return main_region.xpath('.//ul[@class=$name]/li', name='topics')

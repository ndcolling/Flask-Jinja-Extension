from flask import Flask
from utils.jinja import get_template_vars
from utils import jinja_filters
import nose


def test_one():
    app = Flask(__name__)
    template_string = '<p>Hello {{ user }}!</p>'
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {"user": ""})


def test_nested():
    app = Flask(__name__)
    template_string = '<p>Hello {{ user.first }} {{ user.last }}!</p>'
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {"user": {"first": "", "last": ""}})


def test_app_config_init():
    app = Flask(__name__)
    app.config.update({"THIS_IS_A_GLOBAL": 1234})
    template_string = '<p>Hello {{ user }}!</p><p>My Favorite number is: {{ THIS_IS_A_GLOBAL }}</p>'
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {"user": "", "THIS_IS_A_GLOBAL": 1234})


def test_filter_init():
    app = Flask(__name__)
    app.jinja_env.filters['datetimeformat'] = jinja_filters.datetimeformat
    app.jinja_env.filter_default_values = {
        'datetimeformat': "01/31/2018T10:00:01",
    }
    template_string = '<p>Hello {{ user }}!</p><p>Your last order was: {{ last_order.date_created|datetimeformat }}</p>'
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {"user": "", "last_order": {"date_created": '01/31/2018T10:00:01'}})


def test_conditional_filter_init():
    app = Flask(__name__)
    app.config.update({"RETAIL_URL": "myapp.retail.com"})
    app.jinja_env.filters['datetimeformat'] = jinja_filters.datetimeformat
    app.jinja_env.filter_default_values = {
        'datetimeformat': "01/31/2018T10:00:01",
    }
    template_string = '<p>Hello {{ user }}!</p><p>{% if last_order %}Your last order was: {{ last_order.date_created|datetimeformat }}{% else %}<a href="{{ RETAIL_URL }}">Place an order today!</a>{% endif %}</p>'
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {'RETAIL_URL': 'myapp.retail.com', 'last_order': {'date_created': '01/31/2018T10:00:01'}, 'user': ''})


def test_for():
    app = Flask(__name__)
    template_string = '''
        {% for a in article_list %}
            <li class="list-item">
            <a href="{{ a.link }}" target="_blank">
            <h3 class="list-item-hdr">{{ a.headline }}</h3></a>
            <div class="list-item-ftr"><span>
            </li>
        {% endfor %}
    '''
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {'article_list': [{'headline': '', 'link': ''}]})


def test_for_with_global_inside():
    app = Flask(__name__)
    app.config.update({"CDN_HOST": "mycdn.host.com"})
    template_string = '''
        {% for a in article_list %}
            <li class="list-item">
            <a href="{{ a.link }}" target="_blank">
            <h3 class="list-item-hdr">{{ a.headline }}</h3></a>
            <div class="list-item-ftr"><span>
            <img src="{{ CDN_HOST }}/img/icons/external-site.png"/>{{ a.publisher }} &middot;</span></div>
            </li>
        {% endfor %}
    '''
    result = get_template_vars(template_string, app)
    nose.tools.assert_dict_equal(result, {'article_list': [{'headline': '', 'link': '', 'publisher': ''}], 'CDN_HOST': 'mycdn.host.com'})


def test_expected_failure_second_level_deep():
    # TODO: Implement deep nesting!
    app = Flask(__name__)
    template_string = '{{ user.name.first }}'
    args = (template_string, app)
    nose.tools.assert_raises(AttributeError, get_template_vars, *args)

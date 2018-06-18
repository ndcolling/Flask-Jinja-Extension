import logging
from jinja2 import meta, nodes


logger = logging.getLogger(__name__)


def get_template_vars(template_string, flask_app):
    """
        Does meta.find_undeclared_variables BUT also gets 1 level deep attrs.
        Perfect for email templates since they are (currently) no more than
        1 level deep.
        (for ex: {{ this.info }}) works, {{ this.info.detail }} does not
        WARNING: does not pick up "includes".
    :param template_string: the raw template
    :param flask_app: the current app
    :return: dictionary with empty strings for required data values.
    """
    parsed = flask_app.jinja_env.parse(template_string)
    data = {}
    # first get the attrs (nested) nodes. For ex: {{ this.something }}
    attrs = parsed.find_all(nodes.Getattr)
    for a in attrs:
        data.setdefault(a.node.name, {})[a.attr] = ""
    # now check meta (name nodes) and set if they are missing:
    _vars = meta.find_undeclared_variables(parsed)
    for v in _vars:
        data.setdefault(v, "")
    # now lets try and figure out the actual types.
    # this is done in 2 ways: 1. from the filters, 2. from comparisons (const)
    # 1. Filters:
    for f in parsed.find_all(nodes.Filter):
        filter_default = flask_app.jinja_env.filter_default_values.get(f.name, "")
        if isinstance(f.node, nodes.Getattr):
            key = f.node.node.name
            subkey = f.node.attr
            # lets filter out mappings, just in case:
            if not isinstance(data.get(key, {}).get(subkey), dict):
                data[key][subkey] = filter_default
        elif isinstance(f.node, nodes.Name):
            key = f.node.name
            if not isinstance(data.get(key), dict):
                data[key] = filter_default
    # 2. Comparisons to (known) constant values:
    for compare in parsed.find_all(nodes.Compare):
        if isinstance(compare.expr, nodes.Name):
            name = compare.expr
            if name:
                name = name.name
            const = compare.find(nodes.Const)
            if const:
                const = const.value
            else:
                logger.warning('Unable to find const for node: %s', compare)
                continue
            if data.get(name) is not None:
                data[name] = const
        elif isinstance(compare.expr, nodes.Getattr):
            key = compare.expr.node.name
            subkey = compare.expr.attr
            const = compare.find(nodes.Const)
            if const:
                const = const.value
            else:
                logger.warning('Unable to find const for node: %s', compare)
                continue
            if isinstance(data.get(key), dict):
                data[key][subkey] = const
        else:
            logger.warning('Unable to get type for compare node: %s', compare)
    # 3. Handle for loops:
    for f in parsed.find_all(nodes.For):
        # the target would have already been parsed earlier
        target = f.target.name
        target_data = data.pop(target, None)
        if target_data is None:
            logger.warning('target (%) was not parsed from data (%s).', target,
                           data)
            continue
        iter_node = f.iter
        if isinstance(iter_node, nodes.Name):
            name = iter_node.name
            data[name] = [target_data]
        else:
            logger.warning('Unable to parse iternode: %s', iter_node)
        # also cleanup the loop var:
        data.pop('loop', None)
    # 4. Config globals:
    for k, v in data.items():
        if k in flask_app.config:
            data[k] = flask_app.config[k]
    return data

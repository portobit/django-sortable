from django import template
from django.conf import settings


register = template.Library()


SORT_ASC_CLASS = getattr(settings, 'SORT_ASC_CLASS' , 'sort-asc')
SORT_DESC_CLASS = getattr(settings, 'SORT_DESC_CLASS' , 'sort-desc')
SORT_NONE_CLASS = getattr(settings, 'SORT_DESC_CLASS' , 'sort-none')

DEFAULT_TH_CLASS = 'sortable-col'

directions = {
  'asc': {'class': SORT_ASC_CLASS, 'inverse': 'desc'},
  'desc': {'class': SORT_DESC_CLASS, 'inverse': 'asc'},
}


def parse_tag_token(token):
  """Parses a tag that's supposed to be in this format: {% sortable_link field title %}
     sortable_header supports a 3rd argument, which will be an extra css class of the th
  """
  bits = [b.strip('"\'') for b in token.split_contents()]
  if len(bits) < 2:
    raise TemplateSyntaxError, "tag takes at least 1 argument"
  try:
    title = bits[2]
  except IndexError:
    if bits[1].startswith(('+', '-')):
      title = bits[1][1:].capitalize()
    else:
      title = bits[1].capitalize()
  try:
    extra_th_class = bits[3]
  except IndexError:
    extra_th_class = DEFAULT_TH_CLASS
  return (bits[1].strip(), title.strip(), extra_th_class.strip())


class SortableLinkNode(template.Node):
  """Build sortable link based on query params."""

  def __init__(self, field_name, title, extra_th_class):
    if field_name.startswith('-'):
      field_name = field_name[1:]
      self.default_direction = 'desc'
    elif field_name.startswith('+'):
      field_name = field_name[1:]
      self.default_direction = 'asc'
    else:
      field_name = field_name
      self.default_direction = 'asc'

    self.field_name = template.Variable(field_name)
    self.title = template.Variable(title)
    self.extra_th_class = template.Variable(extra_th_class)

  def build_link(self, context):
    """Prepare link for rendering based on context."""
    get_params = context['request'].GET.copy()

    field_name = get_params.get('sort', None)
    if field_name:
      del(get_params['sort'])

    direction = get_params.get('dir', None)
    if direction:
      del(get_params['dir'])
    direction = direction if direction in ('asc', 'desc') else 'asc'

    try:
        own_field_name = self.field_name.resolve(context)
    except template.VariableDoesNotExist:
        own_field_name = str(self.field_name.var)
    # if is current field, and sort isn't defined, assume asc otherwise desc
    direction = direction or ((own_field_name == field_name) and 'asc' or 'desc')

    # if current field and it's sorted, make link inverse, otherwise defalut to asc
    if own_field_name == field_name:
      get_params['dir'] = directions[direction]['inverse']
    else:
      get_params['dir'] = self.default_direction

    if own_field_name == field_name:
      css_class = directions[direction]['class']
    else:
      css_class = SORT_NONE_CLASS

    params = "&%s" % (get_params.urlencode(),) if len(get_params.keys()) > 0 else ''
    url = ('%s?sort=%s%s' % (context['request'].path, own_field_name, params)).replace('&', '&amp;')

    return (url, css_class)

  def render(self, context):
    url, css_class = self.build_link(context)
    try:
        title = self.title.resolve(context)
    except template.VariableDoesNotExist:
        title = str(self.title.var)
    return '<a href="%s" class="%s" title="%s">%s</a>' % (url, css_class, title, title)


class SortableTableHeaderNode(SortableLinkNode):
  """Build sortable link header based on query params."""

  def render(self, context):
    url, css_class = self.build_link(context)
    try:
        title = self.title.resolve(context)
    except template.VariableDoesNotExist:
        title = str(self.title.var)
    try:
        extra_th_class = self.extra_th_class.resolve(context)
    except template.VariableDoesNotExist:
        extra_th_class = str(self.extra_th_class.var)
    if extra_th_class and extra_th_class != DEFAULT_TH_CLASS:
        extra_th_class = '{} {}'.format(DEFAULT_TH_CLASS, extra_th_class)
    else:
        extra_th_class = DEFAULT_TH_CLASS
    return '<th class="%s %s"><a href="%s" title="%s">%s</a></th>' % (css_class, extra_th_class, url, title, title)


class SortableURLNode(SortableLinkNode):
  """Build sortable link header based on query params."""

  def render(self, context):
    url, css_class = self.build_link(context)
    return url


class SortableClassNode(SortableLinkNode):
  """Build sortable link header based on query params."""

  def render(self, context):
    url, css_class = self.build_link(context)
    return css_class


def sortable_link(parser, token):
  field, title, extra_th_class = parse_tag_token(token)
  return SortableLinkNode(field, title, extra_th_class)


def sortable_header(parser, token):
  field, title, extra_th_class = parse_tag_token(token)
  return SortableTableHeaderNode(field, title, extra_th_class)


def sortable_url(parser, token):
  field, title, extra_th_class = parse_tag_token(token)
  return SortableURLNode(field, title, extra_th_class)


def sortable_class(parser, token):
  field, title, extra_th_class = parse_tag_token(token)
  return SortableClassNode(field, title, extra_th_class)


sortable_link = register.tag(sortable_link)
sortable_header = register.tag(sortable_header)
sortable_url = register.tag(sortable_url)
sortable_class = register.tag(sortable_class)

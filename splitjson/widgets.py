# -*- coding: utf-8 -*-
import datetime

from django import get_version, forms
from django.forms import Widget
from django import utils
import copy
from distutils.version import StrictVersion
try:
    import simplejson as json
except ImportError:
    import json
if StrictVersion(get_version()) < StrictVersion('1.9.0'):
    from django.forms.util import flatatt
else:
    from django.forms.utils import flatatt


class SplitJSONWidget(forms.Widget):

    def __init__(self, attrs=None, newline='<br/>\n', sep='__', debug=False):
        self.newline = newline
        self.separator = sep
        self.debug = debug
        Widget.__init__(self, attrs)

    def _as_text_field(self, name, key, value, is_sub=False):
        attrs = self.build_attrs(self.attrs, {
            "type": 'text',
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['value'] = utils.encoding.force_text(value)
        attrs['id'] = attrs.get('name', None)
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <input{flatatt(attrs)} />
        """

    def _as_textarea_field(self, name, key, value, is_sub=False):
        attrs = self.build_attrs(self.attrs, {
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['id'] = attrs.get('name', None)
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <textarea{flatatt(attrs)}>
                {utils.encoding.force_text(value)}
            </textarea>
        """

    def _as_number_field(self, name, key, value, is_sub=False):
        attrs = self.build_attrs(self.attrs, {
            "type": 'number',
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['value'] = utils.encoding.force_text(value)
        attrs['id'] = attrs.get('name', None)
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <input{flatatt(attrs)} />
        """

    def _as_float_field(self, name, key, value, is_sub=False):
        attrs = self.build_attrs(self.attrs, {
            "type": 'number',
            "step": '0.01',
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['value'] = utils.encoding.force_text(value)
        attrs['id'] = attrs.get('name', None)
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <input{flatatt(attrs)} />
        """

    def _as_date_field(self, name, key, value, is_sub=False):
        attrs = self.build_attrs(self.attrs, {
            "type": 'date',
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['value'] = utils.encoding.force_text(value)
        attrs['id'] = attrs.get('name', None)
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <input{flatatt(attrs)} />
        """

    def _as_datetime_field(self, name, key, value, is_sub=False):
        attrs = self.build_attrs(self.attrs, {
            "type": 'datetime-local',
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['value'] = utils.encoding.force_text(value)
        attrs['id'] = attrs.get('name', None)
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <input{flatatt(attrs)} />
        """

    def _as_checkbox_field(self, name, key, value, is_sub=False):
        classes = self.attrs['class']
        classes = [c for c in classes.split() if c != 'form-control']
        classes.append("switch")
        attrs = self.build_attrs(self.attrs, {
            "type": 'checkbox',
            "class": " ".join(classes),
            "name": "%s%s%s" % (name, self.separator, key),
        })
        attrs['value'] = utils.encoding.force_text(value)
        attrs['id'] = attrs.get('name', None)
        checked = '' if not bool(value) else 'checked'
        return f"""
            <label for="{attrs['id']}">{key}:</label>
            <input{flatatt(attrs)} {checked}/>
        """

    def _to_build(self, name, json_obj):
        inputs = []
        if isinstance(json_obj, list):
            title = name.rpartition(self.separator)[2]
            _l = ['%s:%s' % (title, self.newline)]
            for key, value in enumerate(json_obj):
                _l.append(self._to_build("%s%s%s" % (name, self.separator, key), value))
            inputs.extend([_l])
        elif isinstance(json_obj, dict):
            title = name.rpartition(self.separator)[2]
            _l = ['%s:%s' % (title, self.newline)]
            for key, value in json_obj.items():
                _l.append(self._to_build("%s%s%s" % (name, self.separator, key), value))
            inputs.extend([_l])
        elif isinstance(json_obj, str):
            name, _, key = name.rpartition(self.separator)
            if len(json_obj) > 50:
                inputs.append(self._as_textarea_field(name, key, json_obj))
            else:
                inputs.append(self._as_text_field(name, key, json_obj))
        elif isinstance(json_obj, bool):
            name, _, key = name.rpartition(self.separator)
            inputs.append(self._as_checkbox_field(name, key, json_obj))
        elif isinstance(json_obj, int):
            name, _, key = name.rpartition(self.separator)
            inputs.append(self._as_number_field(name, key, json_obj))
        elif isinstance(json_obj, float):
            name, _, key = name.rpartition(self.separator)
            inputs.append(self._as_float_field(name, key, json_obj))
        elif isinstance(json_obj, datetime.date):
            name, _, key = name.rpartition(self.separator)
            inputs.append(self._as_date_field(name, key, json_obj))
        elif isinstance(json_obj, datetime.datetime):
            name, _, key = name.rpartition(self.separator)
            inputs.append(self._as_datetime_field(name, key, json_obj))
        elif json_obj is None:
            name, _, key = name.rpartition(self.separator)
            inputs.append(self._as_text_field(name, key, ''))
        return inputs

    def _prepare_as_div(self, l):
        if l:
            result = ''
            for el in l:
                if isinstance(el, list) and len(l) == 1:
                    result += '%s' % self._prepare_as_div(el)
                elif isinstance(el, list):
                    result += '<div class="form-group">'
                    result += '%s' % self._prepare_as_div(el)
                    result += '</div>'
                else:
                    result += '<div class="form-group">%s</div>' % el
            return result
        return ''

    def _to_pack_up(self, root_node, raw_data):

        copy_raw_data = copy.deepcopy(raw_data)
        result = []

        def _to_parse_key(k, v):
            if k.find(self.separator) != -1:
                apx, _, nk = k.rpartition(self.separator)
                try:
                    # parse list
                    int(nk)
                    l = []
                    obj = {}
                    index = None
                    if apx != root_node:
                        for key, val in copy_raw_data.items():
                            head, _, t = key.rpartition(self.separator)
                            _, _, index = head.rpartition(self.separator)
                            if key is k:
                                del copy_raw_data[key]
                            elif key.startswith(apx):
                                try:
                                    int(t)
                                    l.append(val)
                                except ValueError:
                                    if index in obj:
                                        obj[index].update({t: val})
                                    else:
                                        obj[index] = {t: val}
                                del copy_raw_data[key]
                        if obj:
                            for i in obj:
                                l.append(obj[i])
                    l.append(v)
                    return _to_parse_key(apx, l)
                except ValueError:
                    # parse dict
                    d = {}
                    if apx != root_node:
                        for key, val in copy_raw_data.items():
                            _, _, t = key.rpartition(self.separator)
                            try:
                                int(t)
                                continue
                            except ValueError:
                                pass
                            if key is k:
                                del copy_raw_data[key]
                            elif key.startswith(apx):
                                d.update({t: val})
                                del copy_raw_data[key]
                    v = {nk: v}
                    if d:
                        v.update(d)
                    return _to_parse_key(apx, v)
            else:
                return v

        for k, v in raw_data.iteritems():
            if k in copy_raw_data:
                # to transform value from list to string
                v = v[0] if isinstance(v, list) and len(v) is 1 else v
                if k.find(self.separator) != -1:
                    d = _to_parse_key(k, v)
                    # set type result
                    if not len(result):
                        result = type(d)()
                    try:
                        result.extend(d)
                    except:
                        result.update(d)
        return result

    def value_from_datadict(self, data, files, name):
        data_copy = copy.deepcopy(data)
        result = self._to_pack_up(name, data_copy)
        return json.dumps(result)

    def render(self, name, value, attrs=None, renderer=None):
        try:
            value = json.loads(value)
        except (TypeError, KeyError):
            pass
        inputs = self._to_build(name, value or {})
        result = self._prepare_as_div(inputs)
        if self.debug:
            # render json as well
            source_data = u'<hr/>Source data: <br/>%s<hr/>' % str(value)
            result = '%s%s' % (result, source_data)
        return utils.safestring.mark_safe(result)

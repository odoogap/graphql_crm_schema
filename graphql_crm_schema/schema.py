import graphene
import datetime

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.addons.graphql_base import OdooObjectType
from graphene.types import Scalar
import ast

from graphql.language.ast import ListValue


class Domain(Scalar):
    @staticmethod
    def serialize(domain):
        result = []
        for ele in domain:
            # operator
            if len(ele) == 1:
                result.append(ele)
            else:
                result.append(eval(ele))

        return result

    @staticmethod
    def parse_literal(node):
        result = []
        for ele in node.values:
            # operator
            if len(ele.value) == 1:
                result.append(ele.value)
            else:
                result.append(eval(ele.value))

        return result

    @staticmethod
    def parse_value(value):
        return value


class Date(graphene.types.datetime.Date):
    @staticmethod
    def serialize(date):
        if isinstance(date, str):
            date = fields.Date.from_string(date)
        assert isinstance(
            date, datetime.date
        ), 'Received not compatible date "{}"'.format(repr(date))
        return date.isoformat()


class DateTime(graphene.types.datetime.DateTime):
    @staticmethod
    def serialize(dt):
        if isinstance(dt, str):
            dt = fields.Datetime.from_string(dt)
        assert isinstance(
            dt, (datetime.datetime, datetime.date)
        ), 'Received not compatible datetime "{}"'.format(repr(dt))
        return dt.isoformat()


class RelField(Scalar):
    serialize = dict
    parse_value = dict
    parse_literal = dict


schema_list = [
    {
        'name': 'Partner',
        'model': 'res.partner',
        'fields': {
            'id': graphene.Int(),
            'name': graphene.String(),
            'barcode': graphene.String()
        }
    }, {
        'name': 'Users',
        'model': 'res.users',
        'fields': {
            'id': graphene.Int(),
            'name': graphene.String(),
            'parent_id': graphene.String(),
            'customer': graphene.Boolean()
        }
    }, {
        'name': 'State',
        'model': 'res.country.state',
        'fields': {
            'id': graphene.Int(),
            'name': graphene.String()
        }
    }, {
        'name': 'Attachment',
        'model': 'ir.attachment',
        'fields': {
            'res_id': graphene.Int(),
            'res_model': graphene.String(),
            'datas': graphene.String(),
            'datas_fname': graphene.String(),
            'name': graphene.String()
        }
    }, {
        'name': 'Opportunity',
        'model': 'crm.lead',
        'fields': {
            'id': graphene.Int(),
            'date_closed': graphene.types.datetime.DateTime(),
            'create_date': graphene.types.datetime.DateTime(),
            'probability': graphene.Float(),
            'message_last_post': graphene.types.datetime.DateTime(),
            'color': graphene.Int(),
            'date_last_stage_update': graphene.types.datetime.DateTime(),
            'date_action_last': graphene.types.datetime.DateTime(),
            'campaign_id': graphene.Int(),
            'day_close': graphene.Float(),
            'write_uid': graphene.Int(),
            'team_id': graphene.Int(),
            'day_open': graphene.Float(),
            'contact_name': graphene.String(),
            'partner_id': graphene.Int(),
            'date_action_next': graphene.types.datetime.DateTime(),
            'city': graphene.String(),
            'date_conversion': graphene.types.datetime.DateTime(),
            'opt_out': graphene.Boolean(),
            'date_open': graphene.types.datetime.DateTime(),
            'title': graphene.Int(),
            'partner_name': graphene.String(),
            'planned_revenue': graphene.Float(),
            'country_id': graphene.Int(),
            'company_id': graphene.Int(),
            'priority': graphene.String(),
            'next_activity_id': graphene.Int(),
            'email_cc': graphene.String(),
            'type': graphene.String(),
            'function': graphene.String(),
            'fax': graphene.String(),
            'zip': graphene.String(),
            'description': graphene.String(),
            'create_uid': graphene.Int(),
            'street2': graphene.String(),
            'title_action': graphene.String(),
            'phone': graphene.String(),
            'lost_reason': graphene.Int(),
            'write_date': graphene.types.datetime.DateTime(),
            'state_id': graphene.Int(),
            'active': graphene.Boolean(),
            'user_id': graphene.Int(),
            'date_action': graphene.types.datetime.DateTime(),
            'name': graphene.String(),
            'stage_id': graphene.Int(),
            'medium_id': graphene.Int(),
            'date_deadline': graphene.types.datetime.DateTime(),
            'mobile': graphene.String(),
            'street': graphene.String(),
            'source_id': graphene.Int(),
            'email_from': graphene.String(),
            'message_bounce': graphene.Int(),
            'referred': graphene.String(),
        }
    }
]


class OdooField(Scalar):
    serialize = dict
    parse_value = dict

    @staticmethod
    def parse_literal(node):
        result = {}
        for f in node.fields:
            if isinstance(f.value, ListValue):
                result[f.name.value] = f.value
            else:
                result[f.name.value] = f.value.value

        return result


object_mapping = {}


class MutationBase(graphene.Mutation):
    class Arguments:
        ids = graphene.List(graphene.Int)
        operation = graphene.String(required=True)
        fields = OdooField()
        raise_after_create = graphene.Boolean()
        print(fields)

    def mutate(self, info, ids, operation, fields):
        model = object_mapping.get(info.path[0], False)
        odoo_fields = {}

        for sch in schema_list:
            if sch['model'] == model:
                for field in fields:
                    odoo_name = sch['fields'][field].kwargs.get(
                        'source') or field
                    if odoo_name:
                        odoo_fields[odoo_name] = int(fields[field]) if odoo_name in (
                            'res_id', 'project_id', 'task_id') else fields[field]

        env = info.context["env"]
        result = None
        oper = operation.lower()

        if oper == 'create':
            result = env[model].create(odoo_fields)
        else:
            if not ids:
                return None
            records = env[model].browse(ids)
            if oper == 'update':
                records.write(odoo_fields)
                result = records
            elif oper == 'delete':
                records.unlink()
        return result


def field_resolver(self, info, limit=None, offset=0, domain=[], order=None):
    model = object_mapping.get(info.path[0], False)
    odoo_order = None

    result = info.context["env"][model].with_context(active_test=False).search(
        domain, limit=limit, offset=offset, order=order)

    return result


models = {}
models_mut = {}

# stores the odoo model to class object mapping
odoo_map = {}

# Base Models
for _class in schema_list:
    class_name = _class.get('name').lower()

    # swap RelField for class object
    for f in _class.get('fields'):
        field = _class.get('fields')[f]

        if field.get_type() == RelField:
            source = field.kwargs.get('source') or f
            _class.get('fields')[f] = graphene.List(
                lambda x=field.kwargs['model']: odoo_map[x], source=source)

    # Class Model
    class_object = type(_class.get('name'),
                        (OdooObjectType,), _class.get('fields'))
    odoo_map[_class.get('model')] = class_object

    # Model Mutation Class
    mutation_class_object = type(_class.get(
        'name') + 'Mut', (MutationBase,), {'Output': class_object})
    object_mapping[class_name] = _class.get('model')

    models[class_name] = graphene.List(graphene.NonNull(class_object), limit=graphene.Int(
    ), offset=graphene.Int(), domain=Domain(), order=graphene.String(), resolver=field_resolver)
    models_mut[class_name] = mutation_class_object.Field()

# Add fields_get model so we can get info about each field


def resolve_info(root, info, model, fields):
    model = object_mapping.get(model, False)
    odoo_fields = []
    odoo_fields_map = {}

    for sch in schema_list:
        if sch['model'] == model:
            for field in fields:
                odoo_name = sch['fields'][field].kwargs.get('source')
                if odoo_name:
                    odoo_fields.append(odoo_name)
                    odoo_fields_map[odoo_name] = field
                else:
                    odoo_fields.append(field)
                    odoo_fields_map[field] = field

    result = info.context["env"][model].fields_get(odoo_fields)

    new_result = {}
    for field in result:
        new_result[odoo_fields_map[field]] = result[field]

    return new_result


def resolve_count(root, info, model, domain=[]):
    model = object_mapping.get(model, False)
    return info.context["env"][model].with_context(active_test=False).search_count(domain)


models['count'] = graphene.Int(
    model=graphene.String(), domain=Domain(), resolver=resolve_count)
models['fieldsGet'] = graphene.types.json.JSONString(fields=graphene.List(
    graphene.String), model=graphene.String(), resolver=resolve_info)

Query = type("Query", (graphene.ObjectType,), models)
Mutation = type("Mutation", (graphene.ObjectType,), models_mut)

schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)

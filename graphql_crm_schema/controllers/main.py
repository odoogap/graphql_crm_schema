# Copyright OdooGAP LLP
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http
from odoo.addons.graphql_base import GraphQLControllerMixin
from odoo.http import request

from ..schema import schema

from graphql_server import get_graphql_params


class GraphQLController(http.Controller, GraphQLControllerMixin):

    # The GraphiQL route, providing an IDE for developers
    @http.route("/graphiql", auth="user", csrf=False, cors='*')
    def graphiql(self, **kwargs):
        return self._handle_graphiql_request(schema)

    # Optional monkey patch, needed to accept application/json GraphQL
    # requests. If you only need to accept GET requests or POST
    # with application/x-www-form-urlencoded content,
    # this is not necessary.
    GraphQLControllerMixin.patch_for_json("^/graphql/?$")

    # The graphql route, for applications.
    # Note csrf=False: you may want to apply extra security
    # (such as origin restrictions) to this route.

    @http.route("/graphql", auth="user", csrf=False, cors='*')
    def graphql(self, **kwargs):
    
        response = self._handle_graphql_request(schema)
        response.headers.set('Access-Control-Allow-Origin', request.httprequest.headers.get('Origin'))
        response.headers.set('Access-Control-Allow-Credentials', 'true')
    
        return response

class Login(http.Controller):
   @http.route('/odoogap/login', type='json', auth="none", csrf=False, cors='*')
   def web_login(self, **kw):
       uid = request.session.authenticate(request.params['db'], request.params['login'], request.params['password'])
       result = {'login_success': False}
       if uid is not False:
           result['login_success'] = True
           result['session_id'] = request.session.sid
       return result
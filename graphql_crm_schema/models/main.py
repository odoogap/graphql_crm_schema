# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Session

class Session(Session):
    """
    This function over-rides the default one from the 'web' module in Odoo.
    The difference here is that this one adds CORS support and we allow returning
    of only the session ID when simple=1 is added to the GET string.
    """
    @http.route('/web/session/authenticate', type='json', auth="none", cors="*")
    def authenticate(self, db, login, password, base_location=None):
        success = request.session.authenticate(db, login, password)
        if 'session_id_only' in request.httprequest.args:
            return dict(
                login_success=bool(success),
                session_id=request.env['ir.http'].session_info()['session_id'] if success else False,
            )
        return request.env['ir.http'].session_info()
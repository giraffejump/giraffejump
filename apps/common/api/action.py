# -*- coding: utf-8 -*-
#
from typing import Callable

from django.utils.translation import gettext as _
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from common.const.http import POST, PUT
from orgs.models import Organization
from orgs.utils import current_org

__all__ = ['SuggestionMixin', 'RenderToJsonMixin']


class SuggestionMixin:
    suggestion_limit = 10

    filter_queryset: Callable
    get_queryset: Callable
    paginate_queryset: Callable
    get_serializer: Callable
    get_paginated_response: Callable

    @action(methods=['get'], detail=False, url_path='suggestions')
    def match(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        org_id = str(current_org.id)
        if (
                not request.user.is_superuser and
                org_id != Organization.ROOT_ID and
                not request.user.orgs.filter(id=org_id).exists()
        ):
            queryset = queryset.none()

        queryset = self.filter_queryset(queryset)
        queryset = queryset[:self.suggestion_limit]
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RenderToJsonMixin:
    @action(methods=[POST, PUT], detail=False, url_path='render-to-json')
    def render_to_json(self, request: Request, *args, **kwargs):
        rows = request.data
        if rows and isinstance(rows[0], dict):
            first = list(rows[0].values())[0]
            if first.startswith('#Help'):
                rows.pop(0)

        data = {
            'title': (),
            'data': rows,
        }

        jms_context = getattr(request, 'jms_context', {})
        column_title_field_pairs = jms_context.get('column_title_field_pairs', ())
        data['title'] = column_title_field_pairs

        if isinstance(request.data, (list, tuple)) and not any(request.data):
            error = _("Request file format may be wrong")
            return Response(data={"error": error}, status=400)
        return Response(data=data)

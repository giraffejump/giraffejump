from django.conf import settings
from django.utils.translation import gettext_lazy as _

from authentication.mfa.base import BaseMFA
from authentication.mixins import AuthFaceMixin
from ..const import MFAType


class MFAFace(BaseMFA, AuthFaceMixin):
    name = MFAType.Face.value
    display_name = MFAType.Face.name
    placeholder = 'Face recognition'
    skip_cache_check = True
    has_code = False

    def _check_code(self, code):
        assert self.is_authenticated()

        try:
            code = self.get_face_code()
            if not self.user.check_face(code):
                return False, _('Facial comparison failed')
        except Exception as e:
            return False, "{}:{}".format(_('Facial comparison failed'), str(e))
        return True, ''

    def is_active(self):
        if not self.is_authenticated():
            return True
        return bool(self.user.face_vector)

    @staticmethod
    def global_enabled():
        return (
                settings.XPACK_LICENSE_IS_VALID and
                settings.XPACK_LICENSE_EDITION_ULTIMATE and
                settings.FACE_RECOGNITION_ENABLED
        )

    def get_enable_url(self) -> str:
        return '/ui/#/profile/index'

    def get_disable_url(self) -> str:
        return '/ui/#/profile/index'

    def disable(self):
        assert self.is_authenticated()
        self.user.face_vector = None
        self.user.save(update_fields=['face_vector'])

    def can_disable(self) -> bool:
        return True

    @staticmethod
    def help_text_of_enable():
        return _("Bind face to enable")

    @staticmethod
    def help_text_of_disable():
        return _("Unbind face to disable")

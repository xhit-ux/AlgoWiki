from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class RegisterChallengeRateThrottle(AnonRateThrottle):
    scope = "register_challenge"


class PasswordChangeRateThrottle(UserRateThrottle):
    scope = "password_change"


class ProfileUpdateRateThrottle(UserRateThrottle):
    scope = "profile_update"


class ContentCreateRateThrottle(UserRateThrottle):
    scope = "content_create"


class ContentUpdateRateThrottle(UserRateThrottle):
    scope = "content_update"


class ContentDeleteRateThrottle(UserRateThrottle):
    scope = "content_delete"

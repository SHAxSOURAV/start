from src.util.base_document import TimestampedDocument


class _Description(TimestampedDocument):
    description: str


class TermsConditions(_Description):
    class Settings:
        name = "termsconditions"


class PrivacyPolicy(_Description):
    class Settings:
        name = "privacypolicies"


class FAQ(_Description):
    class Settings:
        name = "faqs"


class AboutUs(_Description):
    class Settings:
        name = "aboutus"


class ContactUs(_Description):
    class Settings:
        name = "contactus"

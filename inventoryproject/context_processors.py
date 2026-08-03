from django.conf import settings


def report_settings(request):
    return {
        'REPORT_COMPANY_NAME': getattr(settings, 'REPORT_COMPANY_NAME', 'Eagle Health and Clinic Services'),
        'REPORT_ADDRESS': getattr(settings, 'REPORT_ADDRESS', 'Kikuyu Rd, Next to Kingdom Bank'),
        'REPORT_CONTACT': getattr(settings, 'REPORT_CONTACT', '+254 759 828928 / +254 579 3877154, emailinfo@eaglehealthandclinicservices.co.ke'),
        'REPORT_LOGO_PATH': getattr(settings, 'REPORT_LOGO_PATH', 'images/hospital_logo.png'),
    }

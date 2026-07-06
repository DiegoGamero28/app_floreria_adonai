from django.conf import settings


def floreria_config(request):
    return {
        'floreria': {
            'nombre': settings.FLORERIA_NOMBRE,
            'yape': settings.FLORERIA_YAPE,
            'whatsapp': settings.FLORERIA_WHATSAPP,
            'promo': settings.FLORERIA_PROMO,
            'qr_yape_static': settings.FLORERIA_QR_YAPE_STATIC,
        }
    }

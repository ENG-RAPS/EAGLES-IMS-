from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import CorrectiveMaintenance, PPM


def create_corrective(equipment, date, diagnosis, solution, remarks, user=None):
    cm = CorrectiveMaintenance.objects.create(
        equipment=equipment,
        date=date or timezone.now().date(),
        diagnosis=diagnosis,
        solution=solution or '',
        remarks=remarks or '',
        processed_by=user
    )
    return cm


def set_ppm_status(ppm_id, status, user=None):
    ppm = get_object_or_404(PPM, pk=ppm_id)
    if status not in dict(PPM.PPM_STATUS):
        raise ValueError('Invalid status')
    ppm.status = status
    ppm.save()
    return ppm

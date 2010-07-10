from main import design
from main.models import BandMember
from django.conf import settings

# the dictionary that will be available to preparsed files
CONTEXT = {
    'MEDIA_URL': settings.MEDIA_URL,
    'COMMENT_EDIT_TIME_HOURS': settings.COMMENT_EDIT_TIME_HOURS,
    'TIMED_COMMENT_SIZE': design.timed_comment_size,
    'VOLUME_ICON_SIZE': design.volume_icon_size,
    'WAVEFORM_WIDTH': design.waveform_size[0],
    'WAVEFORM_HEIGHT': design.waveform_size[1],
    'STR_SAMPLES_DIALOG_TITLE': design.samples_dialog_title,
    'STR_DEPS_DIALOG_TITLE': design.dependencies_dialog_title,
    'STR_COMMENT_DIALOG_TITLE': design.comment_dialog_title,
    'PLAYER_PLAY_ICON': design.play_icon,
    'PLAYER_PAUSE_ICON': design.pause_icon,
    'PLAYER_PLAY_ICON_SMALL': design.play_icon_small,
    'PLAYER_PAUSE_ICON_SMALL': design.pause_icon_small,
    'DEBUG': settings.DEBUG,
    'BAND_MEMBER_MANAGER': BandMember.MANAGER,
}



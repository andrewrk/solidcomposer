from main import design
from django.conf import settings

# strings that are displayed to the user.
this_field_is_required = design.this_field_is_required
uploaded_file_must_be_mp3 = design.uploaded_file_must_be_mp3
song_too_long = design.song_too_long
sketchy_mp3_file = design.sketchy_mp3_file
invalid_mp3_file = design.invalid_mp3_file
must_submit_via_post = design.must_submit_via_post
not_authenticated = design.not_authenticated
competition_not_found = 'Competition not found.'
past_submission_deadline = 'Past submission deadline.'
competition_not_started = 'Competition has not yet begun.'
mp3_too_big = 'MP3 file is too large.'
source_file_too_big = 'Project source file is too large.'
entry_title_required = 'Entry title is required.'
mp3_required = 'MP3 file submission is required.'
cannot_vote_for_yourself = 'You may not vote for yourself.'
no_votes_left = 'No votes left.'
cannot_start_compo_in_the_past = 'You cannot start a competition in the past.'
give_at_least_x_minutes_to_work = 'You have to give people at least %i minutes to work.' % settings.MINIMUM_COMPO_LENGTH
if_you_want_lp_set_date = 'If you want a listening party, you need to set a date.'
lp_gt_submission_deadline = 'Listening party must be after submission deadline.'

unknown_studio_icon = settings.MEDIA_URL + "img/question-white.png"

from opensourcemusic import settings

# this file is a list of variables, like settings.py, that are the strings
# that are displayed to the user. It's to provide a single place for editing
# the design so you don't have to peruse through code when designing.

this_field_is_required = 'This field is required.'
must_submit_via_post = 'Must submit via POST.'
competition_not_found = 'Competition not found.'
past_submission_deadline = 'Past submission deadline.'
competition_not_started = 'Competition has not yet begun.'
mp3_too_big = 'MP3 file is too large.'
source_file_too_big = 'Project source file is too large.'
entry_title_required = 'Entry title is required.'
mp3_required = 'MP3 file submission is required.'
invalid_mp3_file = 'Invalid MP3 file.'
sketchy_mp3_file = 'Sketchy MP3 file.'
song_too_long = 'Song is too long.'
unable_to_save_id3_tags = 'Unable to save ID3 tags.'
not_authenticated = 'You are not logged in.'
cannot_vote_for_yourself = 'You may not vote for yourself.'
no_votes_left = 'No votes left.'
uploaded_file_must_be_mp3 = 'Uploaded file must be an MP3.'
cannot_start_compo_in_the_past = 'You cannot start a competition in the past.'
give_at_least_x_minutes_to_work = 'You have to give people at least %i minutes to work.' % settings.MINIMUM_COMPO_LENGTH
if_you_want_lp_set_date = 'If you want a listening party, you need to set a date.'
lp_gt_submission_deadline = 'Listening party must be after submission deadline.'

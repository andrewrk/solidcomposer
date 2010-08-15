"""
this file is a list of variables, like settings.py, that make up the design
aspects of the source code. It's to provide a single place for editing
the design so you don't have to peruse through code when designing.
"""

# colors for waveforms
waveform_size = (800, 100)
waveform_center_color = (157, 203, 229, 255)
waveform_outer_color = (36, 128, 215, 255)

# the height of the comment bar in song player, as well as the 
# width and height of comment icons
timed_comment_size = 20
volume_icon_size = 24

# gravatar size
gravatar_icon_size = 24
gravatar_large_size = 128

# icons to use for the player
play_icon = 'play-circle-smooth-64.png'
pause_icon = 'pause-circle-smooth-64.png'
play_icon_small = 'play-circle-smooth-16.png'
pause_icon_small = 'pause-circle-smooth-16.png'

# strings that are displayed to the user.
must_submit_via_post = 'Must submit via POST.'
must_submit_via_get = 'Must submit via GET.'
uploaded_file_must_be_mp3 = 'Uploaded file must be an MP3.'
this_field_is_required = 'This field is required.'
your_account_not_activated = 'Your account is not activated.'
invalid_login = 'Invalid login.'
invalid_old_password = 'Invalid old password.'
no_login_data_supplied = 'No login data supplied.'
invalid_username_tips = 'Invalid username. Your account may have expired. You can try registering again.'
invalid_activation_code = 'Invalid activation code. Nice try!'
passwords_do_not_match = 'Your passwords do not match.'
user_x_already_exists = 'The user "%s" already exists.'
email_already_exists = 'This email address already exists.'
invalid_characters_in_user_name = 'You may not use any of these characters in your username: %s'
invalid_characters_in_artist_name = 'You may not use any of these characters in your solo band name: %s'
song_too_long = 'Song is too long.'
invalid_mp3_file = 'Invalid MP3 file.'
sketchy_mp3_file = 'Sketchy MP3 file.'
unable_to_save_id3_tags = 'Unable to save ID3 tags.'
not_authenticated = 'You are not logged in.'
bad_song_comment_node_id = 'Bad song comment node id.'
invalid_position = 'Invalid song position.'
comments_disabled_for_this_version = 'Comments are disabled for this version.'
you_dont_have_permission_to_comment = 'You do not have permission to comment on this song.'
too_late_to_delete_comment = 'It is too late to delete your comment.'
can_only_delete_your_own_comment = 'You can only delete your own comments.'
too_late_to_edit_comment = 'It is too late to edit your comment.'
can_only_edit_your_own_comment = 'You can only edit your own comments.'
must_agree_to_terms = 'You must agree to the terms and conditions to use SolidComposer.'
content_wrong_length = "Content must be between 1 and 2000 characters."

samples_dialog_title = "Download Project Files"
dependencies_dialog_title = "Song Dependencies"
comment_dialog_title = "Comments at "

# form labels
label_artist_name = 'Solo band name'

from moviepy.editor import AudioFileClip, concatenate_audioclips

# Name of the background file
background_file = 'bk.mp3'

# Base name for output files
output_base = 'audio'

# List of number file names
number_files = ['one.mp3', 'two.mp3', 'three.mp3', 'four.mp3', 'five.mp3',
                'six.mp3', 'seven.mp3', 'eight.mp3', 'nine.mp3', 'ten.mp3']

# Load the background audio file
bk_clip = AudioFileClip(background_file)

for i, number_file in enumerate(number_files, start=1):
    # Load the number audio file
    number_clip = AudioFileClip(number_file)

    # Merge the background with the number audio
    final_clip = concatenate_audioclips([bk_clip, number_clip])

    # Generate the output file name
    output_file = f'{output_base}{i}.mp3'

    # Write the result to a file
    final_clip.write_audiofile(output_file)

    print(f"Created {output_file}")

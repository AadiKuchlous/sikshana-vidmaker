#!/usr/bin/python3

import os
import re
import sys
import shutil

# Import the AudioSegment class for processing audio and the
# split_on_silence function for separating out silent chunks.
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_silence
from utils import concatenate_videos, read_excel, mongo_client, underline_html


# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)


def split_audio_on_silence(audio):
	print("SPLITTING AUDIO")
	ext = os.path.splitext(audio)[1][1:]
	print("EXT: " + ext)
	# Load your audio.
	song = AudioSegment.from_file(audio, ext)
	print("LOADED AUDIO")

	# Split track where the silence is 3 seconds or more and get chunks using
	# the imported function.
	chunks = split_on_silence (
	    # Use the loaded audio.
	    song,
	    # Specify that a silent chunk must be at least 3 seconds or 3000 ms long.
	    min_silence_len = 3000,
		seek_step=10,
	    # Consider a chunk silent if it's quieter than -50 dBFS.
	    silence_thresh = -50
	)

	print("Number of chunks {0}".format(len(chunks)))
	
	audio_files = []
	# Process each chunk with your parameters
	for i, chunk in enumerate(chunks):
		# Create a silence chunk that's 0.5 seconds (or 500 ms) long for padding.
		silence_chunk = AudioSegment.silent(duration=500)

		# Add the padding chunk to beginning and end of the entire chunk.
		audio_chunk = silence_chunk + chunk + silence_chunk

		# Export the audio chunk with new bitrate.
		print("Exporting chunk{0}.mp3.".format(i))
		audio_chunk.export(
			"./chunk{0}.mp3".format(i),
			bitrate = "192k",
			format = "mp3"
		)
		audio_files.append("chunk{0}.mp3".format(i))
	return(audio_files)


def create_intro_video(sheet, audio):
        intro_audio = AudioSegment.from_file(file=audio)
        image = sheet.cell(row=2, column=3).value
        text = (sheet.cell(row=2, column=2).value).split('\n')
        footer = sheet.cell(row=2, column=4).value
        if type(footer) == type('') and footer.strip() != '':
                footer_html = "<address style='text-align: center;'>"
                footer = footer.strip()
                for line in footer.split('\n'):
                        footer_html += line + "<br>"
                footer_bool = True
                footer_html += "</address>"
        else:
                footer_bool = False

        with open('intro.in', 'w') as f:
                f.write('\n'.join(["file \'images/{0}.jpg\'".format("intro"), "duration {}".format(len(intro_audio)/1000)]))
        headers = ''
        for i in range(len(text)):
                text[i] = ' '.join(text[i].strip().replace('*', '').split(' '))
        for line in text:
                headers += '<h1 style="font-size:{}rem">{}</h1>'.format(4-(0.5*len(text)), line)
        logo = '<img src="logo.png" style="position: absolute; top: 0px; left: 0px;"></img>'
        image_name = "intro.png"
        if type(image) == type('') and image.strip() != '':
                image_link = "https://drive.google.com/uc?export=download&id="+image.split('d/')[1].split('/view')[0]
                print("link: "+image_link)
                os.system("wget '{0}' -O '{1}'".format(image_link, image_name))
                print(headers)
                img = '<div style="height:350px"><img src="{}" style=""></img></div>'.format(image_name)
                if footer_bool:
                        html = "<!DOCTYPE html><html><body style='margin:0px'><div id='vid_area' style='height: 720px; width: 1280px; padding:10px'>{0}<div style='height: 360px; display: flex; justify-content: center; align-items:flex-start; padding-top:{3}px'>{1}</div>{2}{4}</div></body></html>".format(img, headers, logo, 80-(20*len(text)), footer_html)
                else:
                        html = '<!DOCTYPE html><html><body style="margin:0px"><div id="vid_area" style="height: 720px; width: 1280px; padding:10px">{0}<div style="height: 360px; display: flex; justify-content: center; align-items:flex-start; padding-top:{3}px">{1}</div>{2}</div></body></html>'.format(img, headers, logo, 80-(20*len(text)))
        else:
                if footer_bool:
                        html = '<!DOCTYPE html><html><body><div id="vid_area" style="height: 720px; width:1280px; display: flex; flex-direction: column; justify-content: center; align-items: center;">{0}{1}{2}</div></body></html>'.format(logo, headers, footer_html)
                else:
                       html = '<!DOCTYPE html><html><body><div id="vid_area" style="height: 720px; width:1280px; display: flex; flex-direction: column; justify-content: center; align-items: center;">{0}{1}</div></body></html>'.format(logo, headers)
        with open("intro.html", "w") as f:
                        f.write(html)
        print(os.getcwd())
        cmd = "node pup.js file://{}/intro.html images/{}.jpg".format(os.getcwd(), "intro")
        print("PUP CMD INTRO:{}".format(cmd))
        os.system(cmd)
        os.system("ffmpeg -y -i {0} -f concat -i intro.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {1}.mp4".format(audio, "intro"))
        return("intro.mp4")


def create_image(text, image, page_no, story=False):
        story = True if story=='1' else False
        no_of_lines = len(text.strip().split('\n'))
        text = underline_html(text)
        text = text.split('\n')
        print('lines:')
        print(text)
        new_text = []
        for line in text:
                new_text.append(line.strip())
        words = ' '.join(new_text).split(' ')
        words =  [i for i in words if i != '']
        print("create_images words:{0}".format(words))
        print("no_of_lines: " + str(no_of_lines))
        print(image)
        image_name = "tmp.png"
        if type(image) == type('') and image.strip() != '':
                image_link = "https://drive.google.com/uc?export=download&id="+image.split('d/')[1].split('/view')[0]
                print("link: "+image_link)
                os.system("wget '{0}' -O '{1}'".format(image_link, image_name))
        for i in range(len(words)):
                text_html = ''
                if words[i][0] in "-:#\n[/":
                                continue

                for j in range(len(words)):
                        if words[j][0] == "#":
                                text_html = text_html.strip()+"&nbsp;"*len(words[j])
                                continue

                        if words[j][0] == '[':
                                text_html += words[j][1:-1]
                                continue

                        if words[j] == '\n' or words[j] == "//":
                                text_html += '<br>'
                                continue

                        else:
                                text_html += words[j] + ' '

        br = '<br>'

        logo = '<img src="logo.png" style="position: absolute; top: 0px; left: 0px;"></img>'
        if type(image) == type(''):
                if story:
                        if no_of_lines < 4:
                                text = '<h1 style="font-size: {0}rem; margin: 0px"><p style="margin: 0px; text-align:center">{1}</p></h1>'.format(3, text_html)
                        else:
                                text = '<h1 style="font-size: {0}rem; margin: 0px"><p style="margin: 0px; text-align:center">{1}</p></h1>'.format(1, text_html)
                        img = '<div style="height:350px;"><img src="{}" style="padding-top:40px;"></img></div>'.format(image_name)
                        html = '<!DOCTYPE html><html><body style="margin:0px"><div id="vid_area" style="height: 720px; width: 1280px;">{0}<div style="height: 360px; display: flex; justify-content: center; align-items: center; padding: 20px; padding-top: 30px;">{1}{2}</div></div></body></html>'.format(img, text, logo)

                else:
                        img = '<div style="height:425px"><img src="{}" style="padding-top:30px"></img></div>'.format(image_name)
                        text = '<h1 style="font-size: {0}rem; margin: 0px"><p style="margin: 0px; text-align:center">{1}</p></h1>'.format(7-no_of_lines, text_html)
                        html = '<!DOCTYPE html><html><body style="margin:0px"><div id="vid_area" style="height: 720px; width: 1280px;">{0}<div style="height: 360px; display: flex; justify-content: center; align-items: center; padding:20px">{1}{2}</div></div></body></html>'.format(img, text, logo)
        else:
                if no_of_lines < 4:
                        text = '<div style="height: 720px; display: flex; justify-content: center; align-items: center;"><h1 style="font-size: {0}rem; margin-top: 0px"><p style="margin: 0.5em; text-align:center">{1}</p></h1></div>'.format(3.5, text_html)
                else:
                        text = '<div style="height: 720px; display: flex; justify-content: center; align-items: center;"><h1 style="font-size: {0}rem; margin-top: 0px"><p style="margin: 0.5em; text-align:center">{1}</p></h1></div>'.format(3, text_html)
                html = '<!DOCTYPE html><html><body style="margin:0px"><div id="vid_area" style="height: 720px; width: 1280px;">{0}{1}</div></body></html>'.format(text, logo)
#       print(text)
        with open("tmp.html", "w") as f:
                f.write(html)

        cmd = "node pup.js file://{0}/tmp.html images/{1}.jpg".format(os.getcwd(), str(page_no))
        print("PUP CMD: {}".format(cmd))
        os.system(cmd)

        return("images/{}.jpg".format(page_no))


def create_page_vid(page_no, audio_file, image):
	audio = AudioSegment.from_file(file=audio_file)
	audio_len = len(audio)/1000

	with open("ffmp.in", "w") as f:
		f.write("file '{0}' \n".format(image))
		f.write("duration {}".format(audio_len))

	os.system("ffmpeg -y -i {0} -f concat -i ffmp.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {1}.mp4".format(audio_file, page_no))


def create_vids(inpfile, sheet_name, tmpdir, story, first_slide, last_slide, audio_in, user):
	mdir = os.getcwd()
	files = ['pup.js', 'blank.mp3', 'blank_long.mp3', 'logo.png']
	for f in files:
		shutil.copy(f, "{0}/{1}".format(tmpdir, f))
	os.chdir(tmpdir)
	os.mkdir('images')
	audio_files = split_audio_on_silence(audio_in)
	print(audio_files)	
	sheet = read_excel(inpfile, sheet_name)
	create_intro_video(sheet, audio_files[0])
	page_videos = []
	start = int(first_slide)
	end = int(last_slide)+1
	for i in range(start, end):
		if not sheet.cell(row=i, column=1).value:
			continue

		page_no = i-start+1
		
		para = sheet.cell(row=i, column=2).value.strip()
		image_text = ' '.join(para.strip().replace('*', '').replace('\n', ' \n ').split(' '))
		image = create_image(image_text, sheet.cell(row=i, column=3).value, page_no, story)

		audio_file = audio_files[page_no]
		create_page_vid(page_no, audio_file, image)

		page_videos.append("{}.mp4".format(page_no))

	os.chdir(os.path.join(mdir, 'static', 'videos', user))

	if story=='1':
		os.chdir("Stories")
	else:
		os.chdir("Other Videos")
	
	os.mkdir(output_name)

	os.chdir(os.path.join(os.getcwd(), output_name))

	concatenate_videos(["intro.mp4"]+page_videos, "{}.mp4".format(output_name), tmpdir)


client = mongo_client()
db=client.vidmakerdb	

inpfile = str(sys.argv[1])
sheet_name = str(sys.argv[2])
tmpdir = str(sys.argv[3])
output_name = str(sys.argv[4])
story = str(sys.argv[5])
first_slide = sys.argv[6]
last_slide = sys.argv[7]
audio_in = sys.argv[8]
user = sys.argv[9]
tmpname = "tmp" + re.search("^.*tmp(.*)$", tmpdir)[1]
filter = {"tmp": tmpname}

try:
        create_vids(inpfile, sheet_name, tmpdir, story, first_slide, last_slide, audio_in, user)
        newvalues = { "$set": { 'status': "Successful" } }
        result=db.data.update_one(filter, newvalues)
except Exception as e:
        print(e)
        print(db.data.find_one(filter))
        newvalues = { "$set": { 'status': "Failed" } }
        result=db.data.update_one(filter, newvalues)


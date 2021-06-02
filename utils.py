#!/usr/bin/python3

import sys
import openpyxl
from pymongo import MongoClient
import subprocess as sub


def concatenate_videos(videos, output_name, tmpdir):
        with open('{}/con.in'.format(tmpdir), 'w') as f:
                print(videos)
                for video in videos:
                        f.write("file '{0}/{1}'\n".format(tmpdir, video))
        print(sys.path)
        sub.call("ffmpeg -y -f concat -safe 0 -i {0}/con.in -strict -2 -video_track_timescale 90000 -max_muxing_queue_size 4096 -tune animation -crf 6".format(tmpdir).split(' ') + [output_name])


def read_excel(inpfile, sheet):
        name = inpfile
        wb = openpyxl.load_workbook(name)
        print(wb.sheetnames)
        return(wb[sheet])

def mongo_client():
	return MongoClient("mongodb+srv://Aadi:Aadi4321@vidmaker-cluster.vtdh4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

def underline_html(text):
        return text.replace("._", "<u>").replace("_.", "</u>")

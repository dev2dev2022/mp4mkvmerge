#! /usr/bin/env python
#
# Copyright (c) 2022 DEV2DEV Community.
# mp4mkvmerge.py | MIT License | github.com/dev2dev2022/mp4mkvmerge/blob/main/LICENSE
#
from pathlib import Path
import sys
import os
import time
import shutil
import glob
import json
import argparse
import mmmerge
import datetime

#----------------------------------------------------------------
# is Directory empty
#----------------------------------------------------------------
def is_dirempty(d):
    f = os.listdir(d)
    if len(f) == 0:
        return True
    else:
        return False

#----------------------------------------------------------------
# error
#----------------------------------------------------------------
def disp_error(parser, errmsg = ''):
    if 0 < len(errmsg):
        print(errmsg)
    print('---- error --- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    parser.print_usage()
    sys.exit()

#----------------------------------------------------------------
# main
#----------------------------------------------------------------
def main_func(parser, args, mmm):
    if not is_dirempty(mmm.temp_dir):
        disp_error(parser, '---- temp_dir is Not Empty. ----')

    if not os.path.isdir(mmm.temp_ctrldir):
        disp_error(parser, '---- temp_ctrldir is Exists. ----')

    move_dir = mmm.move_directory
    base_dir = args.directory
    chk_file = args.file_match
    chaprenew = args.chapter_renew

    if args.extra_mode == '###' or args.extra_mode == 'ymd':
        chaprenew = False

    if args.merge_filename is not None and 0 < len(args.merge_filename):
        if args.merge_filename in ':':
            output_file = args.merge_filename + ".mkv"
        else:
            output_file = os.path.join(args.directory, args.merge_filename + ".mkv")
    else:
        output_file = os.path.join(args.directory, args.file_match + ".mkv")

    videos = []
    disp_videos = []

    #--------------------------------
    # pre check
    #
    if args.extra_mode == 'ymd' or args.extra_mode == '###':
        total_size = 0
        sub_total_size = 0
        fcount = 0
        sub_fcount = 0

        paths = list(Path(base_dir).glob('%s*.mp4' % chk_file))
        fcount = len(paths)
        for path in paths:
            fname = os.path.basename(path)
            bname, ext =  os.path.splitext(fname)
            if bname.endswith('$'):
                continue
            total_size += os.path.getsize(path)
            sub_total_size += os.path.getsize(path)
            sub_fcount += 1

        paths = list(Path(base_dir).glob('%s*.mkv' % chk_file))
        fcount += len(paths)
        for path in paths:
            fname = os.path.basename(path)
            bname, ext =  os.path.splitext(fname)
            if bname.endswith('$'):
                continue
            total_size += os.path.getsize(path)
            sub_total_size += os.path.getsize(path)
            sub_fcount += 1

        if sub_fcount < 2:
            print('---- PASS 0-1 mode %s file count %d < 2 no Action ----' % (args.extra_mode, sub_fcount))
            sys.exit()
        else:
            print('---- PASS 0-1 Target files = [%d/%d], marge / total / limit = [%s / %s / %s]' % (sub_fcount, fcount, format(sub_total_size, ','), format(total_size, ','), format(mmm.max_size, ',')))

    if args.extra_mode == 'ymd':
        print('---- PASS  0-2 ymd rename ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')

        # (mp4|mkv)
        # XXXXXXYYYYYY yyyymmdd-yyyymmdd -> XXXXXX yyyymmdd YYYYYY (日付を保管)
        # XXXXXXYYYYYY yyyymm-yyyymm -> XXXXXX yyyymm00 YYYYYY (日付を保管)
        # XXXXXXYYYYYY yyyymmdd -> XXXXXX yyyymmdd YYYYYY
        # XXXXXXYYYYYY_yyyymmdd -> XXXXXX yyyymmdd YYYYYY
        # XXXXXXYYYYYY          -> XXXXXX yyyymmdd YYYYYY （ファイルの作成日）

        paths = list(Path(base_dir).glob('%s*.mp4' % chk_file))
        paths.sort(key=os.path.getctime)
        for path in paths:
            fname = os.path.basename(path)
            bname, ext =  os.path.splitext(fname)
            if bname.endswith('$'):
                continue
            mmm.filename_check_ymd(base_dir, chk_file, path.stem, path.suffix[1:], datetime.datetime.fromtimestamp(path.stat().st_ctime).strftime('%Y%m%d'))

        paths = list(Path(base_dir).glob('%s*.mkv' % chk_file))
        paths.sort(key=os.path.getctime)
        for path in paths:
            fname = os.path.basename(path)
            bname, ext =  os.path.splitext(fname)
            if bname.endswith('$'):
                continue
            mmm.filename_check_ymd(base_dir, chk_file, path.stem, path.suffix[1:], datetime.datetime.fromtimestamp(path.stat().st_ctime).strftime('%Y%m%d'))

    #--------------------------------
    # mp4 to mkv add
    #
    print('---- PASS 1 mp4 to mkv -- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    videos = sorted(glob.glob(os.path.join(base_dir, chk_file + '*.mp4')))
    print('---- mp4 Count = %d' % len(videos))
    for video in videos:
        print(video)
        fname = os.path.basename(video)
        bname, ext =  os.path.splitext(fname)
        if bname.endswith('$'):
            continue
        if args.extra_mode == '###':
            mmm.filename_check_no_last(bname)
        mp4 = os.path.join(base_dir, '%s.%s' % (bname, 'mp4'))
        mkv = os.path.join(base_dir, '%s.%s' % (bname, 'mkv'))
        if mmm.moved:
             move_mp4 = os.path.join(move_dir, '%s.%s' % (bname, 'mp4'))
        if os.path.exists(mkv):
            print("already mkv File (mp4 to move) (%s)" % mp4)
            if mmm.moved:
                shutil.move(mp4, move_mp4)
            disp_videos.append(mp4)
            continue
        print('mp4 to tempDir (%s)' % mp4)
        shutil.copy(mp4, mmm.chkmp4file)
        disp_videos.append(mp4)
        reencode = mmm.subproc_ffprobe(mp4)
        if 0 != reencode:
            sys.exit()
        reencode = mmm.encoding_check(mp4)
        if reencode == -1:
            # for re encoding
            ret = mmm.reencoding('mp4', mkv)
            print('reencoding(mp4, %s) return = %d' % (mkv, ret))
            if mmm.moved:
                shutil.move(mp4, move_mp4)
        elif reencode == -2:
            # for re format
            mmm.mp4tomkv(mp4, mkv)
            if mmm.moved:
                shutil.move(mp4, move_mp4)
        else:
            continue
        if os.path.isfile(mmm.chkmp4file):
            os.remove(mmm.chkmp4file)

    #--------------------------------
    # mkv re encode check
    #
    print('---- PASS 2 re encode param check to tempdir  ---- ---- ---- ---- ---- ----')
    videos = sorted(glob.glob(os.path.join(base_dir, chk_file + '*.mkv')))
    print('---- mkv Count = %d' % len(videos))
    if args.extra_mode == '###' and len(videos) < 2:
        print('mode ### mkv 2 or more')
        sys.exit()
    i = 0
    for video in videos:
        fname = os.path.basename(video)
        bname, ext =  os.path.splitext(fname)
        if bname.endswith('$'):
            continue
        i += 1
        print(video)
        fname = os.path.basename(video)
        bname, ext =  os.path.splitext(fname)
        # bname に #NN-NN を抽出
        if args.extra_mode == '###':
            if 1 == mmm.filename_check_no(bname):
                mmm.filename_check_no_last(bname)
        mkv = os.path.join(base_dir, '%s.%s' % (bname, 'mkv'))
        enc_mkv = os.path.join(base_dir, '%s.e.%s' % (bname, 'mkv'))
        if mmm.moved:
            move_mkv = os.path.join(move_dir, '%s.%s' % (bname, 'mkv'))
        print('mkv to tempDir from (%s)' % mkv)
        print('mkv to tempDir to   (%s)' % mmm.chkmkvfile)
        shutil.copy(mkv, mmm.chkmkvfile)
        reencode = mmm.subproc_ffprobe(mmm.chkmkvfile)
        print('subproc_ffprobe return = %d' % reencode)
        if 0 != reencode:
            print('■■■■■■■■■■■■■■■■')
            disp_error(parser, "")
        reencode = mmm.encoding_check(mmm.chkmkvfile)
        print('encoding_check return  = %d' % reencode)
        if reencode == -1:
            # for re encoding
            ret = mmm.reencoding('mkv', enc_mkv)
            print('reencoding(mkv, %s) return = %d' % (enc_mkv, ret))
            if mmm.moved:
                shutil.move(mkv, move_mkv)
        elif reencode == -2:
            # for rename
            if mmm.moved:
                shutil.copy(mkv, move_mkv)
                shutil.move(mkv, enc_mkv)
        else:
            continue
        if os.path.isfile(mmm.chkmkvfile):
            os.remove(mmm.chkmkvfile)

    #--------------------------------
    # mkvmerge add chapter
    #
    print('---- PASS 3 ADD CHAPTER   ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    videos = sorted(glob.glob(os.path.join(base_dir, chk_file + '*.mkv')))
    print('---- ADD CHAPTER MKV Count = %d' % len(videos))
    i = 1
    for video in videos:
        print(video)
        fname = os.path.basename(video)
        bname, ext = os.path.splitext(fname)
        if bname.endswith('$'):
            continue
        mkv = os.path.join(base_dir, '%s.%s' % (bname, 'mkv'))
        if mmm.moved:
            move_mkv = os.path.join(move_dir, '%s.%s' % (bname, 'mkv'))
        mkt = os.path.join(mmm.temp_dir, 't%03d.mkv' % i)
        i += 1
        cchapter = mmm.check_chapter(mkv)
        print("[%d] = check to chapter (%s)" % (cchapter, mkv))
        nochap = True
        if chaprenew == False:
            if cchapter == -1:
                nochap = False
                # チャプターあり
                shutil.move(mkv, mkt)
                print('chapter reuse = %s' % (mkt))
            elif cchapter == -2:
                # チャプターなし
                nochap = True
        if chaprenew == True or nochap == True:
            # チャプター作成
            if cchapter == -1:
                # チャプターあり なので 削除
                mmm.remove_chapter(mkv)
                print('remove_chapter(%s)' % (mkv))
            if bname.endswith('.e'):
                bname = bname[:len(bname) -2]
            if bname.endswith('.e'):
                bname = bname[:len(bname) -2]
            chapter = mmm.add_chapter(mkv, mkt, bname)
            print('%s = add_chapter(%s, %s, %s)' % (chapter, mkv, mkt, bname))
            if chapter != 0:
                print('■■■■■■■■■■■■■■')
                disp_error(parser, "")
            if mmm.moved:
                shutil.move(mkv, move_mkv)

    #--------------------------------
    # mkvmerge marge syntax
    #
    print('---- PASS 4 ADD CHAPTER   ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    mkvfirst = 1
    mkvplus = ''
    mkvplus_append = ''
    videos = sorted(glob.glob(os.path.join(mmm.temp_dir, 't*.mkv')))
    print('---- marge chapter mkv Count = %d' % len(videos))
    for video in videos:
        if mkvfirst == 1:
            mkvfirst = 0
            mkvplus = video
        else:
            mkvplus += ' + ' + video
    print(mkvplus)

    #--------------------------------
    # mkvmerge marge 
    #
    print('---- PASS 5 MKVMERGE ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')
    try:
        print('execute mkvmerge')
        bat = open(mmm.batfilepath, "w+")
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        bat.write('"%s" -o %s %s %s\n' % (mmm.mkvmerge, mmm.mergefile, mkvplus, mkvplus_append))
        bat.close()
        cmd = [
            mmm.batfilepath]
        ret = mmm.subproc(cmd)
        print('mkvmerge return = %d' % ret)
        if ret != 0:
            print('mkvmerge Error')
            print('■■■■■■■■')
            disp_error(parser, "")
        print('Writing ...')
        print(output_file)
        check_path = Path(mmm.mergefile)
        check_filesize = check_path.stat().st_size
        print('File size ... %s' % (format(check_filesize, ',')))
        fileendstr = ""
        if check_filesize > mmm.max_size and mmm.max_size != 0:
              fileendstr = mmm.max_size_end
        if args.extra_mode == '###' and mmm.is_filename_generate_no():
            # 話数追加モード
            output_file = os.path.join(args.directory, '%s %s%s.mkv' % (args.file_match, mmm.filename_generate_no(), fileendstr))
            print(output_file)
        if args.extra_mode == 'ymd':
            # 放送日モード
            output_file = os.path.join(args.directory, '%s %s%s.mkv' % (args.file_match, mmm.filename_generate_ymd(), fileendstr))
            print(output_file)
        shutil.move(mmm.mergefile, output_file)
        mmm.disp_chapter(output_file)
        for f in glob.glob(os.path.join(mmm.temp_dir, '*.mkv')):
            if os.path.isfile(f):
                os.remove(f)
    except Exception as e:
        print('Exception')
        print(e)
        print('■■■■■■■■■■')
        disp_error(parser, "")

if __name__ == "__main__":
    start = time.time()
    print('---- [%d] %s' % (len(sys.argv), sys.argv))

    parser = argparse.ArgumentParser(prog='mkvadd')
    parser.add_argument('directory')
    parser.add_argument('file_match')
    parser.add_argument('-m', '--merge_filename', default='')
    parser.add_argument('-r', '--move_directory', default='')
    parser.add_argument('-c', '--config_filename', default='mkvadd.json')
    parser.add_argument('-t', '--chapter_renew', action='store_true')
    parser.add_argument('-e', '--extra_mode')
    args = parser.parse_args()

    if len(sys.argv) < 3:
        disp_error(parser, "")

    try:
        json_f = open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                os.path.basename(args.config_filename)), "r")
        json_d = json.load(json_f)
        json_f.close()
    except Exception as e:
        print('Exception :')
        print(e)
        disp_error(parser, "")

    mmm = mmmerge.MmMerge(
        json_d['mkvmerge'],
        json_d['ffmpeg'],
        json_d['ffprobe'],
        json_d['nvenc'],
        json_d['mkvextract'],
    )
    mmm.init_dirs(
        json_d['temp_dir'],
        json_d['temp_ctrldir'],
    )
    mmm.init_ctrlfiles(
        json_d['batfilename'],
        json_d['metafilename'],
        json_d['ffprobejson'],
        json_d['mergefilename'],
        json_d['chkmp4filename'],
        json_d['chkmkvfilename'],
        json_d['chkchapterfilename'],
        json_d['tmpchapfilename'],
    )
    mmm.init_codecs(
        json_d['codec_name_v'],
        json_d['codec_name_a'],
        json_d['width'],
        json_d['height'],
        json_d['sample_rate'],
    )
    mmm.init_recodecs(
        json_d['reenc_codec_v'],
        json_d['reenc_codec_a'],
        json_d['reenc_bitrate'],
    )
    mmm.init_nvenc_codecs(
        json_d['nvenc_codec_v'],
        json_d['nvenc_codec_a'],
        json_d['nvenc_opt'],
    )
    mmm.mode_encoding(
        json_d['reencexec'],
    )
    move_directory = ''
    if 0 < len(args.move_directory):
        move_directory = args.move_directory
    elif 0 < len(json_d['move_directory']):
        move_directory = json_d['move_directory']
    mmm.init_options(
        move_directory,
        json_d['max_size'],
        json_d['max_size_end']
    )

    main_func(parser, args, mmm)

    end = time.time()
    print("Laptime", end - start, "seconds.")
    print('---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----')

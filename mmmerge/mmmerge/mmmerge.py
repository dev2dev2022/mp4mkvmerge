#! /usr/bin/env python
#
# Copyright (c) 2022 DEV2DEV Community.
# mp4mkvmerge.py | MIT License | github.com/dev2dev2022/mp4mkvmerge/blob/main/LICENSE
#
import sys
import os
import time
import shutil
import subprocess
import glob
import json
import re

class MmMerge:
    #----------------------------------------------------------------
    # 各種プログラムパスを保存
    #----------------------------------------------------------------
    def __init__(self, mkvmerge, ffmpeg, ffprobe, nvenc, mkvextract):
        self.mkvmerge = mkvmerge
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.nvenc = nvenc
        self.mkvextract = mkvextract

    #----------------------------------------------------------------
    # 各種パラメータ
    #----------------------------------------------------------------
    def init_dirs(self, temp_dir, temp_ctrldir):
        self.temp_dir = temp_dir
        self.temp_ctrldir = temp_ctrldir

    def init_ctrlfiles(self, batfilename, metafilename, ffprobejson, mergefilename, chkmp4filename, chkmkvfilename, chkchapterfilename, tmpchapfilename):
        self.batfilepath = os.path.join(self.temp_ctrldir, batfilename)
        self.metafilepath = os.path.join(self.temp_ctrldir, metafilename)
        self.probefilepath = os.path.join(self.temp_ctrldir, ffprobejson)
        self.mergefile = os.path.join(self.temp_dir, mergefilename)
        self.chkmp4file = os.path.join(self.temp_dir, chkmp4filename)
        self.chkmkvfile = os.path.join(self.temp_dir, chkmkvfilename)
        self.chkchapfile = os.path.join(self.temp_dir, chkchapterfilename)
        self.tmpchapfile = os.path.join(self.temp_dir, tmpchapfilename)
        
    def init_codecs(self, codec_name_v, codec_name_a, width, height, sample_rate):
        self.codec_name_v = codec_name_v
        self.codec_name_a = codec_name_a
        self.width = width
        self.height = height
        self.sample_rate = sample_rate

    def init_recodecs(self, reenc_codec_v, reenc_codec_a, reenc_bitrate):
        self.reenc_codec_v = reenc_codec_v
        self.reenc_codec_a = reenc_codec_a
        self.reenc_bitrate = reenc_bitrate

    def init_nvenc_codecs(self, nvenc_codec_v, nvenc_codec_a, nvenc_opt):
        self.nvenc_codec_v = nvenc_codec_v
        self.nvenc_codec_a = nvenc_codec_a
        self.nvenc_opt = nvenc_opt

    def mode_encoding(self, reencexec):
        self.reencexec = reencexec

    def init_options(self, move_directory, max_size = 0, max_size_end = "$"):
        self.move_directory = move_directory
        if 0 < len(self.move_directory):
            self.moved = True
        else:
            self.moved = False
        self.max_size = max_size
        self.max_size_end = max_size_end

    param_ffprobe = '-loglevel quiet -show_streams -print_format json'

    def subproc(self, cmd) -> int:
        """ 外部プログラム起動.
        Args:
            cmd (list[str]): subprocess
        Returns:
            int: 正常=0
        """
        try:
            r = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
#           sys.stdout.write(r.decode() + '\n')
        except OSError as e:
            sys.stderr.write('file =%s\n' % str(e.filename))
            sys.stderr.write('errno=%s\n' % str(e.errno))
            sys.stderr.write('error=%s\n' % str(e.strerror))
            return 1
        except subprocess.CalledProcessError as e:
            sys.stderr.write('ret   =%s\n' % str(e.returncode))
            sys.stderr.write('cmd   =%s\n' % str(e.cmd))
            sys.stderr.write('output=%s\n' % str(e.output))
            return 2
        return 0

    def subproc_ffprobe(self, c) -> int:
        """ ffprobe 起動.
        Args:
            c (str): 解析する動画ファイルパス
        Returns:
            int: 正常=0
        Note:
            self.probefilepath ファイルに動画情報を出力
        """
        try:
            bat = open(self.batfilepath, "w+", encoding='UTF-8')
            bat.write("@echo off" + '\n')
            bat.write("chcp 65001 >NUL 2>&1" + '\n')
            bat.write('del /F /Q "%s"\n' 
                % self.probefilepath)
            bat.write('"%s" "%s" %s > %s\n' 
                % (self.ffprobe, c, self.param_ffprobe, self.probefilepath))
            bat.close()

            cmd = [
                self.batfilepath]
            ret = self.subproc(cmd)
            if ret != 0:
                print('subproc_ffprobe Error = %d' % ret)
            return ret
        except Exception as e:
            print('Exception :')
            print(e)
            return 3

    nn1 = 0
    nn2 = 0
    ymd1 = 0
    ymd2 = 0

    def filename_check_ymd(self, base_dir, chk_file, stem, suffix, ctime):
        """ ファイル名から日付関連を取得.
        Note:
            XXXXXXYYYYYY yyyymmdd-yyyymmdd -> XXXXXX yyyymmdd YYYYYY (日付を保管)
            XXXXXXYYYYYY yyyymm-yyyymm -> XXXXXX yyyymm00 YYYYYY (日付を保管)
            XXXXXXYYYYYY yyyymmdd -> XXXXXX yyyymmdd YYYYYY
            XXXXXXYYYYYY          -> XXXXXX yyyymmdd YYYYYY （ファイルの作成日）
        """
        print('---- ---- filename_check_ymd(%s,%s,%s,%s,%s)' % (base_dir, chk_file, stem, suffix, ctime))
        try:
            m = re.search(r'\d{6,8}-\d{6,8}', stem)
            if m is not None:
                r = m.group()
                ymd = r.split('-')
                rint1 = int(ymd[0])
                if self.ymd1 > (rint1 * 100) or self.ymd1 == 0:
                    self.ymd1 = rint1
                    if self.ymd1 < 1000000:
                        self.ymd1 = self.ymd1 * 100
                rint2 = int(ymd[1])
                if self.ymd2 < (rint2 * 100) or self.ymd2 == 0:
                    self.ymd2 = rint2
                    if self.ymd2 < 1000000:
                        self.ymd2 = self.ymd2 * 100
                stempart1 = str.strip(stem.strip(chk_file))
                stempart2 = str.strip(stempart1.strip(r))
                os.rename(os.path.join(base_dir, '%s.%s' % (stem, suffix)),
                        os.path.join(base_dir, '%s %d %s.%s' % (chk_file, self.ymd1, stempart2, suffix)))
                return 0
            m1 = re.search(r'\d{8}', stem)
            if m1 is not None:
                r = m1.group()
                rint = int(r)
                if self.ymd1 > rint or self.ymd1 == 0:
                    self.ymd1 = rint
                if self.ymd2 < rint or self.ymd2 == 0:
                    self.ymd2 = rint
                stempart1 = str.strip(stem.strip(chk_file))
                stempart2 = str.strip(stempart1.strip(r))
                os.rename(os.path.join(base_dir, '%s.%s' % (stem, suffix)),
                        os.path.join(base_dir, '%s %d %s.%s' % (chk_file, rint, stempart2, suffix)))
                return 0
            if self.ymd1 > int(ctime) or self.ymd1 == 0:
                self.ymd1 = int(ctime)
            if self.ymd2 < int(ctime) or self.ymd2 == 0:
                self.ymd2 = int(ctime)
            stempart1 = str.strip(stem.strip(chk_file))
            os.rename(os.path.join(base_dir, '%s.%s' % (stem, suffix)),
            os.path.join(base_dir, '%s %s %s.%s' % (chk_file, ctime, stempart1, suffix)))
        except Exception as e:
            print('Exception :')
            print(e)
            return 1
        return 0

    def filename_generate_ymd(self):
        """ 放送日情報のファイル名を生成.
            YYYYMMDD-YYYYMMDD を生成
        Returns:
            str: 放送日文字列
        """
        print('---- filename_generate_ymd')
        #if self.ymd1 > 0:
        #    self.ymd1 /= 100
        #if self.ymd2 > 0:
        #    self.ymd2 /= 100
        return '%08d-%08d' % (self.ymd1, self.ymd2)

    def filename_check_no(self, f):
        """ ファイル名から話数情報を取得.
            #NN-NN を抽出
            self.nn1 開始話数
            self.nn2 終了話数
        Args:
            c (str): 解析する動画ファイル名
        Returns:
            int: 正常=0
        """
        print('---- filename_check_no(%s)' % f)        
        m = re.search(r'#\d{1,4}-\d{1,4}', f)
        if m is not None:
            r = m.group()
            print(r)
            nn = r[1:].split('-')
            print(nn)

            if self.nn1 > int(nn[0]) or self.nn1 == 0:
                self.nn1 = int(nn[0])
            if self.nn2 < int(nn[0]) or self.nn2 == 0:
                self.nn2 = int(nn[0])

            if self.nn1 > int(nn[1]) or self.nn1 == 0:
                self.nn1 = int(nn[1])
            if self.nn2 < int(nn[1]) or self.nn2 == 0:
                self.nn2 = int(nn[1])
            return 0
        else:
            return 1

    def filename_check_no_last(self, f):
        """ ファイル名から最終話数情報を取得.
            #NN を抽出
            self.nn2 終了話数
        Args:
            c (str): 解析する動画ファイル名
        Returns:
            int: 正常=0
        """
        print('---- filename_check_no_last(%s)' % f)        
        m = re.search(r'#\d{1,4}', f)
        if m is not None:
            r = m.group()
            nn = r[1:]
            print(nn)
            if self.nn1 > int(nn) or self.nn1 == 0:
                self.nn1 = int(nn)
            if self.nn2 < int(nn) or self.nn2 == 0:
                self.nn2 = int(nn)
        return 0        

    def filename_generate_no(self):
        """ 話数情報のファイル名を生成.
            #NN-NN を生成
        Returns:
            str: 話数文字列
        """
        print('---- filename_generate_no')
        if self.nn2 > 99:
            return '#%03d-%03d' % (self.nn1, self.nn2)
        else:
            return '#%02d-%02d' % (self.nn1, self.nn2)

    def is_filename_generate_no(self):
        if self.nn2 > 0:
            return True
        else:
            return False

    #----------------------------------------------------------------
    # Encoding check
    #----------------------------------------------------------------
    def encoding_check(self, c):
        print('---- encoding_check(%s)' % c)
        ret = self.subproc_ffprobe(c)
        if ret != 0:
            return(ret)
        try:
            json_f = open(self.probefilepath, "r")
            json_data = json.load(json_f)
            json_f.close()
        except Exception as e:
            print('Exception :')
            print(e)
            return(4)
        reencdisp = ''
        reenc = False
        for stream in json_data['streams']:
            if stream['codec_type'] == 'video':
                reencdisp += '%s ' % stream['codec_type']
                if stream['codec_name'] != self.codec_name_v:
                    reencdisp += '%s≠%s ' % (self.codec_name_v, stream['codec_name'])
                    reenc = True 
                else:
                    reencdisp += '%s ' % (self.codec_name_v)
                if stream['width'] != self.width:
                    reencdisp += '%d≠%d ' % (self.width, stream['width'])
                    reenc = True 
                else:
                    reencdisp += '%d ' % (self.width)
                if stream['height'] != self.height:
                    reencdisp += '%d≠%d ' % (self.height, stream['height'])
                    reenc = True 
                else:
                    reencdisp += '%d ' % (self.height)
            elif stream['codec_type'] == 'audio':
                reencdisp += '%s ' % stream['codec_type']
                if stream['codec_name'] != self.codec_name_a:
                    reencdisp += '%s≠%s ' % (self.codec_name_a, stream['codec_name'])
                    reenc = True 
                else:
                    reencdisp += '%s ' % (self.codec_name_a)
                if stream['sample_rate'] != self.sample_rate:
                    reencdisp += '%s≠%s ' % (self.sample_rate, stream['sample_rate'])
                    reenc = True
                else:
                    reencdisp += '%s ' % (self.sample_rate)
        if reenc == True:
            print('---- encoding_check(%s)' % reencdisp)
            return(-1)
        else:
            print('---- encoding_check(%s)' % reencdisp)
            return(-2)

    #----------------------------------------------------------------
    # Re Encoding
    #----------------------------------------------------------------
    def reencoding(self, ext, mkv):
        if ext == 'mp4':
            chkfilepath = self.chkmp4file
        elif ext == 'mkv':
            chkfilepath = self.chkmkvfile
        print('---- reencoding (%s)' % chkfilepath)
        print('----         to (%s)' % mkv)
        bat = open(self.batfilepath, "w+", encoding='UTF-8')
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        if self.reencexec == 'nvenc':
            bat.write(
                '"%s" %s -c %s --audio-codec %s --audio-bitrate %s --output-res %dx%d -i "%s" -o "%s"\n'
                % (self.nvenc, self.nvenc_opt, self.nvenc_codec_v, self.nvenc_codec_a, self.sample_rate, self.width, self.height, chkfilepath, mkv)
            )
        else:
            bat.write(
                '"%s" -i "%s" -loglevel quiet -vf "yadif=deint=interlaced, scale=w=trunc(ih*dar/2)*2:h=trunc(ih/2)*2, setsar=1/1, scale=w=%d:h=%d:force_original_aspect_ratio=1, pad=w=%d:h=%d:x=(ow-iw)/2:y=(oh-ih)/2:color=#000000" -c:v %s -b:v %s -c:a %s -ar %s -pix_fmt yuv420p "%s"\n' 
                % (self.ffmpeg, chkfilepath, self.width, self.height, self.width, self.height, self.reenc_codec_v, self.reenc_bitrate, self.reenc_codec_a, self.sample_rate, mkv)
            )
        bat.close()
        cmd = [
            self.batfilepath]
        ret = self.subproc(cmd)
        print('reencoding return = %d' % ret)
        if ret != 0:
            print('reencoding Error = %d' % ret)
        return ret

    #----------------------------------------------------------------
    # Re Format
    #----------------------------------------------------------------
    def mp4tomkv(self, mp4, mkv):
        print('---- mp4tomkv(%s, %s)' % (mp4, mkv))

        bat = open(self.batfilepath, "w+", encoding='UTF-8')
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        bat.write('"%s" -i "%s" -c copy "%s"'
            % (self.ffmpeg, mp4, mkv))
        bat.close()

        cmd = [
            self.batfilepath]
        ret = self.subproc(cmd)
        print('---- mp4tomkv return = %d' % ret)
        return ret

    #----------------------------------------------------------------
    # Check Chapter
    #----------------------------------------------------------------
    def check_chapter(self, mkv):
        print('---- check chapter(%s)' % mkv)

        bat = open(self.batfilepath, "w+", encoding='UTF-8')
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        bat.write('del /F /Q "%s"\n' 
            % self.chkchapfile)
        bat.write('"%s" "%s" chapters -s "%s"\n'
            % (self.mkvextract, mkv, self.chkchapfile))
        bat.close()

        cmd = [
            self.batfilepath]
        ret = self.subproc(cmd)
        print('---- check_chapter return = %d' % ret)
        if ret != 0:
            return ret
        if os.path.exists(self.chkchapfile):
            print('---- check_chapter in chapter')
            if os.path.isfile(self.chkchapfile):
                os.remove(self.chkchapfile)
            return -1
        print('---- check_chapter no chapter')
        return -2

    #----------------------------------------------------------------
    # Add Chapter
    #----------------------------------------------------------------
    def add_chapter(self, mkv, mkn, bname) -> int:
        print('---- add_chapter(%s)' % mkv)

        metafile = open(self.metafilepath, 'w+')
        metafile.write('CHAPTER01=00:00:00.000\n')
        metafile.write('CHAPTER01NAME=%s\n' % bname)
        metafile.close()

        bat = open(self.batfilepath, "w+", encoding='UTF-8')
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        bat.write('"%s" --chapters "%s" -o "%s" "%s"\n'
            % (self.mkvmerge, self.metafilepath, mkn, mkv))
        bat.close()

        cmd = [
            self.batfilepath]
        ret = self.subproc(cmd)
        print('---- add_chapter return = %d' % ret)
        return ret

    #----------------------------------------------------------------
    # Remove Chapter
    #----------------------------------------------------------------
    def remove_chapter(self, mkv):
        print('---- remove_chapter(%s)' % mkv)

        bat = open(self.batfilepath, "w+", encoding='UTF-8')
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        bat.write('"%s" --no-chapters -o "%s" "%s"\n'
            % (self.mkvmerge, self.tmpchapfile, mkv))
        bat.close()

        cmd = [
            self.batfilepath]
        ret = self.subproc(cmd)
        shutil.move(self.tmpchapfile, mkv)
        print('---- remove_chapter return = %d' % ret)
        return ret

    #----------------------------------------------------------------
    # Disp Chapter
    #----------------------------------------------------------------
    def disp_chapter(self, m):
        print('---- disp_chapter(%s)' % m)

        bat = open(self.batfilepath, "w+", encoding='UTF-8')
        bat.write("@echo off" + '\n')
        bat.write("chcp 65001 >NUL 2>&1" + '\n')
        bat.write('del /F /Q "%s"\n' 
            % self.chkchapfile)
        bat.write('"%s" "%s" chapters -s "%s"\n'
            % (self.mkvextract, m, self.chkchapfile))
        bat.close()

        cmd = [
            self.batfilepath]
        ret = self.subproc(cmd)
        print('---- disp_chapter return = %d' % ret)
        if ret != 0:
            return ret
        try:
            f = open(self.chkchapfile, "r",  encoding='UTF-8')
            c = f.read()
            print(c)
            chapdir = os.path.dirname(m)
            bname =  os.path.splitext(os.path.basename(m))[0]
            chappath = os.path.join(chapdir, '%s.chap' % (bname))
            shutil.copy2(self.chkchapfile, chappath)
        except Exception as e:
            print(e)
            return 3
        finally:
            f.close()
            os.remove(self.chkchapfile)
        return 0


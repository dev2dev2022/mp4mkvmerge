# mp4mkvmerge

- mp4, mkv ファイルを再エンコードしないで結合するスクリプト
- 結合するファイルの先頭でチャプターを作成し、ファイル名をチャプター名として利用
- チャプター機能を簡易に作成するため、ファイルフォーマットを mkv にします
- すでにチャプターがついている mkvファイルはそのままそのチャプターを利用します

## 動作制限

1. Windows10 のみで動作確認
2. ソースファイルは、mp4 or mkv
3. 結合するファイル名は、python で デフォルトの sort される順番になる
4. 結合するファイル名の先頭部分は同一
5. 音ズレは最小限にしたい
6. Codec(A,V), 画素数, アスペクト比等は、結合するファイルで統一されている
7. フォーマットが異なる場合は、ある程度統一します（再エンコーディング ffmpeg/NVEncC しますので要時間）
8. 結合するだけなので再エンコードしない
9. pythonのコーディング久しぶりなのでコードが美しくないのはご容赦ください

## 利用ツール

公開して頂いてる皆様ありがとうございます

1. ffmpeg （https://ffmpeg.org/）
2. mkvmerge （https://mkvtoolnix.download/）

## 動作の流れ

1. ソースファイルを mkv に統一（ffmpeg利用）
2. 結合前のmkv状態で、00:00:00部分にチャプターを追加（mkvmerge利用）
3. mkvファイルを結合（mkvmerge利用）

## 変数

mkvadd.json で設定します（環境にあわせて修正が必要）。

mkvmergeを起動するバッチファイル名

> batfilename = 'mp4mkvmerge_.bat'

チャプターを作成するときの作業用ファイル名

> metafilename = 'metadata.txt'

mkvmerge.exe の場所

> mkvmerge = 'C:\\Program Files\\MKVToolNix\\mkvmerge.exe'

ffmpeg.exe の場所

> ffmpeg = 'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe'

ffprobe.exe の場所

> ffprobe = 'C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe'

mkvextract.exe の場所

> mkvextract = 'C:\\Program Files\\MKVToolNix\\mkvextract.exe'

NVEncC64.exe / QSVEncC64.exe / VCEEncC64.exe の場所

> nvenc = 'C:\\Program Files\\NVEnc_5.46\\NVEncC\\x64\\NVEncC64.exe'

NVEncC64.exe / QSVEncC64.exe / VCEEncC64.exe コマンドライン

> nvenc_opt = '--qvbr 29 --preset default --bref-mode each --lookahead 32 -c hevc --level 6 --output-depth 10 -b 3 --avhw --avsync vfr --gop-len auto'

作業用の空ディレクトリ（存在している必要あり）

> temp_dir = 'C:\\TEMP'

作業用ファイル名

> mergefilename = '000.mkv'
> 
> chkmp4filename = 'chk.mp4'
> 
> chkmkvfilename = 'chk.mkv'
> 
> chkchapterfilename = 'chap.txt'

結合時に異なるフォーマットの場合に揃えるパラメータ

> codec_name_v = 'hevc'
> 
> codec_name_a = 'aac'
> 
> width = 1280
> 
> height = 720
> 
> sample_rate = '48000'
> 
> reenc_codec_v = 'hevc_nvenc'
> 
> reenc_codec_a = 'aac'
> 
> reenc_bitrate = '1200k'

## 使い方

> C:\> python mkvadd.py <結合するファイルがあるディレクトリ> <結合するファイル名の先頭部分> <結合したファイル名> <元ファイルの移動先> [chaprenew]

### サンプル

> python mkvadd.py -e ### "C:\Videos" "DORAMA"

- C:\Videos ディレクトリにある DORAMAで始まるファイル（DORAMA #nn.mp4, DORAMA #nn.mkv）を（ファイル名を pythonの標準sort順で）結合します。
- DORAMA #01.mp4 と DORAMA #01.mkv が存在する場合は同一とみなし DORAMA #01.mkv を結合対象とします。
- #01から#12 の12ファイルが存在する場合
- 処理が終わったら、C:\Videos\DORAMA #01-12 END.mkv ファイルが生成されます。
- 結合前のファイルは、mkvadd.json の move_directory フォルダに移動されます。

> python mp4mkvmerge.py -e ymd "C:\Videos" "NEWS"

- C:\Videos ディレクトリにある NEWS NEWS*.mp4, NEWS*.mkv）を（ファイル名を pythonの標準sort順で）結合します。
- ファイル名に含まれている yyyymmdd もしくは ファイルのタイムスタンプ でソートして、マージします。
- 処理が終わったら、C:\Videos\NEWS 20220101-20220131.mkv ファイルが生成されます。
- 結合前のファイルは、mkvadd.json の move_directory フォルダに移動されます。

### 動作確認

* mkvextract.exe でチャプター内容確認しています
* Kodi (https://kodi.tv/) VLC（https://www.videolan.org/） で実際のチャプター名等確認しています

#### その他

* 2022 DEV2DEV Community. All rights reserved. | https://wiki.dev2dev.jp/

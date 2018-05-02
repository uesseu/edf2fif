#!/usr/bin/python
# coding: utf-8
import pyedflib
import mne
import json
import argparse
import numpy as np

'''
# 使い方
python edf2fif -i hoge.edf -o fuga.fif -s piyo.json
hoge.edf: edfのファイル名
fuga.fif: fifのファイル名
piyo.json: 設定ファイル名

python edf2fif -h でヘルプを表示

残念ながら設定ファイルが必要です。
設定ファイルの内容は読めばだいたい分かるかと…

'''


class EDF2FIF():
    '''
    edfをfifに変えるためのオブジェクト。
    使い方の例
    e2f = EDF2FIF()
    e2f.load_setting(setting_file)
    e2f.load_eeg(edf_file)
    e2f.make_mne_raw()
    e2f.save_fif(outfile)
    '''
    # length of list of edf event.
    edf_length = 0
    # edflibで読んだイベントリストのカウンター
    count_edf = -1
    # MNEで読んだイベントリストのカウンター
    count_mne = -1

    def __init__(self):
        pass

    def load_setting(self, filename):
        '''
        設定ファイルを読み込む
        self.settingsに入れる。filenameはファイル名。
        '''
        with open(filename) as fp:
            self.settings = json.load(fp)

    def _load_edflib_edf(self, filename):
        '''
        edflibでedfを読む。
        self.edf_eventsに格納 引数はファイル名。
        '''
        self.edf = pyedflib.EdfReader(filename)
        edf_df = pd.DataFrame(self.edf.read_annotation())
        self.edf_events = list(edf_df.ix[:, 2])
        self.edf_length = 0
        # ここで、edfのイベントリストの数を調べている。
        for n in self.edf_events:
            self.edf_length = self.edf_length + 1
        self.sfreq = self.edf.samplefrequency(0)

    def _load_mne_edf(self, filename):
        '''
        MNEでedfを読む。あとでedflibのやつとマージする。
        '''
        self.raw_mne = mne.io.read_raw_edf(filename, preload=True,
                                           exclude=self.settings['exclude'])
        self.raw_mne.rename_channels(self.settings['channel_list'])

    def load_eeg(self, filename):
        '''
        edfを読む。
        呼び出す時はこれでお願いします。
        '''
        self._load_mne_edf(filename)
        self._load_edflib_edf(filename)

    def skip_event(self):
        '''
        カウントを増やす関数。
        次のイベントまでcount_mneとcount_edfを増やす。
        listが終わっている場合も抜ける。
        リストの終わりでFalseを返し、そうじゃない場合はTrueを返す。
        '''
        if self.count_edf > self.edf_length:
            print('end of list')
            # もしlistが終わってたらFalseを返す
            return False
        else:
            # countをすすめる。
            self.count_edf = self.count_edf + 1
            self.count_mne = self.count_mne + 1
            # 頭文字が+じゃないならイベント情報。さっさととばす。
            while self.count_edf < self.edf_length:
                # countでedf側のeventを数える
                if len(self.edf_events[self.count_edf]) == 0:
                    # 例外的に0文字の場合もあるので、この時はカウント
                    self.count_edf = self.count_edf + 1
                elif self.edf_events[self.count_edf][0] == '+':
                    # 頭文字が+の場合はイベント情報なのでとばす
                    break
                else:
                    # +ではないので飛ばす
                    self.count_edf = self.count_edf + 1
            return True

    def extract_event(self):
        '''
        イベントの時間と内容を返す。
        list[time, event]
        もし、全てのイベントを読み終わってたらFalseを返す。
        '''
        if self.count_edf >= self.edf_length - 1:
            return False
        real_time = float(self.edf_events[self.count_edf].split('+')[1])
        time = int(real_time * self.sfreq)
        event = self.edf_events[self.count_edf + 1].decode('shift-jis')
        return [time, event]

    def make_eventlist(self):
        '''
        MNEのフォーマットのイベントリストを作る関数。
        結果はself.event_listに入れる。
        '''
        tmp_list = []
        while(self.skip_event()):
            tmp_event = self.extract_event()
            if tmp_event:
                tmp_list.append(tmp_event)
        # MNEのフォーマットに従って並べ替え
        # ここでif文を使っている理由は、要らないチャンネルが
        # そもそも入っていない時にエラーはいて落ちたりしないため。
        # そうすることにより、ポータブル脳波計にも対応する。
        event_list_tmp = []
        for n in tmp_list:
            if n[1] in self.settings['event']:
                event_number = int(self.settings['event'][n[1]])
                event_list_tmp.append([int(n[0]), 0, event_number])
            else:
                print('skipped translating channel!')
                print(n[1])
        self.event_list = np.array(event_list_tmp)
        # self.event_list = event_list_tmp
        # これがMNEのイベントリストだ
        print('--------------------')
        print(self.event_list)
        print('--------------------')

    def make_mne_raw(self):
        '''
        MNEのrawを作る。edfを読み込んだ後だけ実行可能。
        '''
        # とりあえず、色々読んでいく
        self.make_eventlist()
        montage = self.settings['montage']
        # チャンネルマップ
        ch_types = self.settings['type_all']
        sfreq = int(self.sfreq)
        channels_to_drop = self.settings['exclude']
        chnames_original = self.raw_mne.ch_names
        info = mne.create_info(chnames_original, sfreq, ch_types, montage)
        data = self.raw_mne.get_data()
        # 取り出すデータ
        self.raw_to_output = mne.io.RawArray(data, info)
        # ここからデータを加工していく
        # 要らないちゃんねるを消す
        for ch in channels_to_drop:
            if ch in self.raw_to_output.ch_names:
                self.raw_to_output.drop_channels([ch])
        self.raw_to_output.add_events(self.event_list)

    def save_fif(self, filename):
        '''
        fifファイルで保存するだけの関数。
        filename: string
        '''
        self.raw_to_output.save(filename, overwrite=True)


# 上記のオブジェクトを使ってedfをfifに変えるスクリプトの本体。
if __name__ == '__main__':
    # 引数をとってくるやつ
    parser = argparse.ArgumentParser(
        description='converter edf to fif')
    parser.add_argument('-i', '--infile', type=str,
                        help='The file to convert', required=True)
    parser.add_argument('-o', '--outfile', type=str,
                        help='output file', required=True)
    parser.add_argument('-s', '--setting_file', type=str,
                        help='setting_file', required=True)
    args = parser.parse_args()
    e2f = EDF2FIF()
    e2f.load_setting(args.setting_file)
    e2f.load_eeg(args.infile)
    e2f.make_mne_raw()
    e2f.save_fif(args.outfile)

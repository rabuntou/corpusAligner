日英アライメントツールです。以下はアライメント作業を実行できるための簡単な説明で、
具体的な説明はコツコツと追加するかも。
　　
0. 　　日本語側の解析はmecabを使っています。
　　　　mecab を先にインストールしてください。
　　　　http://taku910.github.io/mecab/#download

　　よって、以下のように環境変数をセットする必要があります
　　それぞれ、mecab　の実行ファイル、mecab日本語辞書のフルパスです


　　ここのパスはあくまでも例なので、使用者自身の環境に合わせて指定してください。
　　
　export KDS_MRPH=/usr/local/bin/mecab
　export KDS_MRPH_JDIC=/usr/lib64/mecab/dic/ipadic


１．　英語側の解析はnｌｔｋを使っていますので、先にインストールしてください。

　pip install nltk


２.  そして、NLTKの解析関数を使うには
必要な資源を先にnltk.downloadを使い、ダウンロードする必要があります。

　import nltk
　nltk.download('wordnet')


もし、NLTKインストール時に他に何か資源が漏れた場合、
アライメント本体を実行する際に、　何かをダウンロードすべきかというコマンド例はNLTKから提示してくれるので、
それに従ってください。


３．　アライメントツール本体のコマンド例
元データの構成は

入力用のファイル名の綴りは　.en 　あるいは 　.ja  と想定しています。
例として、sampleフォルダにも参照してください。

 python s_align_jk.py 入力フォルダ 　出力ファイル --raw rawファイル --no_div


英語の文切り効果は悪いので、　オプション --no_divを付けることを勧めます。 
オプション　--raw は　　　結果のフィルター前の生の出力です。
例えば、sampleフォルダをアライメントしようとすれば、

 python s_align_jk.py sample 　sample.txt --raw sample_raw.txt --no_div






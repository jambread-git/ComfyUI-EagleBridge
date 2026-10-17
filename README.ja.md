# ComfyUI-EagleBridge

**Languages:** [English](README.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [日本語](README.ja.md)

---

## 概要

ComfyUI-EagleBridge は、ComfyUIで生成した**画像・音声・動画**を保存し、そのまま Eagle ライブラリへ登録するための3つの出力ノードを提供します。

- **Eagle Save Image** — `IMAGE` を保存してEagleへ登録。画像プレビュー対応。元の `IMAGE` を右側の出力へそのまま渡せます。
- **Eagle Save Audio** — `AUDIO` を保存してEagleへ登録。再生ボタン・シークバー付きプレイヤー対応。
- **Eagle Save Video** — ComfyUIネイティブ `VIDEO` を保存してEagleへ登録。再生ボタン・シークバー付きプレイヤー対応。

さらに、上流ワークフローから取得できる生成情報を自動で抽出し、Eagleのタグとアノテーションへ整理して記録します。

> 非公式のコミュニティプロジェクトです。Comfy OrgおよびEagle公式とは提携・公認関係にありません。

## 必要環境

- 比較的新しいComfyUI。
- ComfyUIと同じPCで起動しているEagleデスクトップアプリ。
- ノード実行時にEagleでライブラリを開いていること。
- EagleローカルAPIの既定アドレス `127.0.0.1:41595` が利用できること。
- Eagle API呼び出しにはアプリ側のタイムアウトを設けず、Eagleから応答が返るまで待機します。
- Python依存パッケージ：`requests>=2.31.0`。
- 音声・動画のエンコード可否は、ComfyUI環境側のPyAV / FFmpeg / コーデック対応状況にも依存します。

## インストール

**ComfyUI Manager:** `ComfyUI-EagleBridge` または `eagle-bridge` で検索して、そのままインストールできます。

**手動インストール:**

1. ComfyUIを完全に終了します。
2. `ComfyUI-EagleBridge` フォルダを `ComfyUI/custom_nodes/` に配置します。
3. ComfyUIが使用している同じPython環境で依存パッケージをインストールします。

   ```bash
   pip install -r ComfyUI/custom_nodes/ComfyUI-EagleBridge/requirements.txt
   ```

4. Eagleを起動し、保存先として使うライブラリを開きます。
5. ComfyUIを起動します。
6. アップデート後に古いUIが残っている場合は、ブラウザで `Ctrl+Shift+R` を行い、対象ノードを一度削除して追加し直してください。

## Eagle保存先フォルダID

各Saveノードは `eagle_folder_id` のテキスト入力方式です。

1. Eagleで保存したいフォルダを右クリックし、**「リンクをコピー」** を選びます。
2. コピーされたリンクは次のような形式です。

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

3. `id=` の後ろにある文字列だけをコピーします。この例では `MU2LXTTH4KVRF` です。
4. そのIDを `eagle_folder_id` に貼り付けます。
5. `eagle_folder_id` を空欄にすると **Eagle Library Root** へ保存します。

フォルダIDはワークフローへ直接保存されます。

## 実行時に生成されるプロンプトの記録（`prompt_text`）

Saveノードは通常、ワークフローグラフ上からプロンプトテキストを読み取ります
（`CLIPTextEncode`など）。一方、一部のノードは実行時にのみプロンプトを生成します。
例えば`MOSSImageLayoutPrompt`はレイアウト要素からプロンプトを組み立てるため、
グラフ中にテキストが存在せず自動抽出できません。

こうしたワークフローのために、すべてのSaveノードに`prompt`という名前の
オプション入力ソケット（内部キーは`prompt_text`。テキスト欄ではなく接続プラグのみ表示）が
追加されました：

1. プロンプトを生成するノードのSTRING出力
   （例：`MOSSImageLayoutPrompt`の`prompt`出力）を`prompt`ソケットへ接続します。
2. 接続されたテキストがEagleのメモのPositive Prompt（音声・動画はPrompt）として
   記録され、自動抽出の結果を上書きします。

通常のワークフローでは`prompt`ソケットを接続しなければ従来通りです。

## 共通：ファイル名テンプレート

### `file_name_template`

初期値：

```text
%datetime%_%rand%
```

使える置換：

- `%date%` → `YYYYMMDD`
- `%time%` → `HHMMSS`
- `%datetime%` → `YYYYMMDD_HHMMSS`
- `%index%` → バッチ番号
- `%rand%` → 短いランダムID

例：

```text
20260915_203128_ab12cd34.webp
```

## 共通：ローカル保存フォルダテンプレート

`local_subfolder` では次の置換を使えます。

- `%date%` → `YYYY-MM-DD`
- `%time%` → `HH-MM-SS`
- `%datetime%` → `YYYY-MM-DD_HH-MM-SS`
- `%model%` → 最初に検出したモデル名。検出できない場合は `UnknownModel`

保存先は必ずComfyUIのoutput/tempディレクトリ配下に制限されます。

---

## Eagle Save Image

### 基本的な使い方

画像生成側の `IMAGE` 出力を、そのまま `image` 入力へ接続します。

保存後も元の `IMAGE` を右側の `image` 出力へそのまま渡すため、必要なら後続ノードへ接続できます。`Eagle Save Image` 自体も `OUTPUT_NODE` のままなので、EagleBridgeで保存するだけなら通常の `Save Image` ノードを別に置く必要はありません。

### 各項目

- **image** — ComfyUIの `IMAGE` 入力。
- **eagle_folder_id** — Eagle内の保存先フォルダ。
- **file_name_template** — ファイル名テンプレート。初期値 `%datetime%_%rand%`。
- **local_subfolder** — ComfyUI側のローカル保存先。初期値 `EagleBridge/Image/%date%/`。
- **format** — `webp` / `png` / `jpg`。
- **quality** — 1～100。初期値95。主に非可逆WebP/JPEGの品質に使用します。
- **lossless_webp** — ONならWebPをロスレス保存します。
- **save_local_copy** — ONならComfyUI output側にもファイルを残します。OFFならEagleへ取り込むための一時ファイルをtemp側に作ります。
- **preview** — ONならノード内に保存画像のプレビューを表示します。
- **memo** — 任意のメモ。Eagleアノテーション末尾へ `Memo:` として追加します。
- **website** — 任意のURL。EagleアイテムのWebsite欄へ登録します。

### Eagleへ登録される情報

取得できる場合、アノテーションは概ね次の順で整理されます。

```text
Positive Prompt:
...

Negative Prompt:
...

Model: ...
Size: ...
Seed: ...
Steps: ...
CFG: ...
Sampler: ...
Scheduler: ...

Memo:
...
```

取得できなかった項目は表示しません。

Eagleの**タグは最初に検出したモデル名1つだけ**を使用します。

### 画像ファイル内部のメタデータ

- **PNG** — ComfyUI側でメタデータ保存が無効化されていなければ、prompt / workflow系情報を埋め込みます。
- **WebP** — ComfyUI互換を意識したEXIF形式でprompt / extra情報を埋め込みます。
- **JPEG** — 現在、EagleBridgeからComfyUIワークフローメタデータは埋め込みません。

---

## Eagle Save Audio

### 基本的な使い方

音声生成側の `AUDIO` 出力を `audio` へ直接接続します。

保存後も元の `AUDIO` をそのまま出力するため、必要なら後続ノードへ接続できます。

### 各項目

- **audio** — ComfyUI `AUDIO`。
- **eagle_folder_id** — Eagle保存先。
- **file_name_template** — ファイル名テンプレート。
- **local_subfolder** — 初期値 `EagleBridge/Audio/%date%/`。
- **format** — `wav` / `flac` / `mp3` / `opus`。
- **bitrate** — `64k` / `96k` / `128k` / `192k` / `256k` / `320k`。MP3 / Opusで使用します。WAV / FLACはロスレスのため、この値を無視します。
- **save_local_copy** — ONならoutputへ保存。OFFなら一時ファイルを使用します。
- **preview** — ONならノード内に再生ボタン・シークバー付き音声プレイヤーを表示します。
- **memo** — Eagleアノテーションへ追記する任意メモ。
- **website** — Eagle Website欄へ保存する任意URL。

### PromptとLyricsの自動取得

音楽生成系は通常の画像ワークフローと構造が異なるため、上流から次のようなフィールド名を探します。

Prompt候補：

```text
caption
prompt
tags
sample_query
description
```

Lyrics候補：

```text
lyrics
lyric
```

ACE-Step系をはじめ、同様のフィールド名を使う音楽生成ノードで利用できます。見つからなかった項目は表示しません。

### Eagleアノテーション例

```text
Prompt:
Upbeat Japanese city-pop ...

Lyrics:
夜風に揺れる街の灯り
...

Model: acestep_v1.5_xl_sft_bf16
Duration: 30 sec
Sample Rate: 48000 Hz
Channels: 2

Memo:
...
```

Durationは読みやすいように小数を整理します。

Eagleタグは最初に検出したモデル名を使用します。

### 音声形式について

- WAVは16-bit PCMとして保存します。
- MP3 / Opusでは `bitrate` が有効です。
- FLAC / WAVでは `bitrate` を無視します。
- Opusで対応サンプルレートへの変換が必要な場合、利用可能なら `torchaudio` を使用します。
- 現在、音声ファイル内部へComfyUIの完全なワークフローメタデータは埋め込みません。PromptやモデルなどはEagleのアノテーション/タグ側で管理します。

---

## Eagle Save Video

### 基本的な使い方

動画生成側が出しているComfyUIネイティブの `VIDEO` 出力を `video` に直接接続します。

保存後も元の `VIDEO` をそのまま出力するため、後続ノードへ接続できます。

### 各項目

- **video** — ComfyUIネイティブ `VIDEO` 入力。
- **eagle_folder_id** — Eagle保存先。
- **file_name_template** — ファイル名テンプレート。
- **local_subfolder** — 初期値 `EagleBridge/Video/%date%/`。
- **format** — `mp4` / `webm` / `mkv`。
- **codec** — `auto` / `h264` / `av1`。
- **save_local_copy** — ONならComfyUI outputへ保存。OFFならtempを使用します。
- **preview** — ONならノード内に再生ボタン・シークバー付き動画プレイヤーを表示します。
- **memo** — Eagleアノテーションへ追記するメモ。
- **website** — Eagle Website欄へ保存する任意URL。

### format / codecについて

`webm + h264` の組み合わせはこのノードではエラーにします。

また、選択したコーデックを実際に使えるかどうかは、ComfyUI側のPyAV / FFmpeg / コーデック構成にも依存します。

### Video Promptの自動取得

動画ワークフローは標準KSamplerのPositive Prompt経路を通らないことがあるため、上流から以下のような名前を追加で探索します。

```text
prompt
positive_prompt
positive_text
prompt_text
text_prompt
caption
description
text
```

Negative Promptについても、対応するフィールドが見つかった場合のみ記録します。

### メイン動画モデルの自動選択

MiniMax H3 / Wan / LTXなどでは、上流に

- メイン動画生成モデル
- VAE
- Qwen / CLIP / T5などのテキスト・ビジョン系モデル
- LoRA等

が同時に存在する場合があります。

EagleBridgeは、それらをすべて `Model:` に並べるのではなく、**実際の動画生成に使われている可能性が高いメインモデルを優先**します。VAEやテキストエンコーダ等の補助モデルは優先度を下げます。

たとえばMiniMax H3のワークフローで複数モデルが見つかっても、Eagle側では次のように主要モデルだけを表示できることを狙っています。

```text
Model: minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16
```

### Eagleアノテーション例

```text
Prompt:
A cinematic 5-second shot ...

Model: minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16
Size: 960x544
Duration: 5.17 sec
FPS: 24
```

通常のSampler情報を取得できるワークフローでは、さらにSeed / Steps / CFG / Sampler / Schedulerも追加します。

DurationとFPSは `5.167 sec → 5.17 sec`、`24.000 → 24` のように読みやすく整形します。

### 動画ファイル内部のメタデータ

ComfyUI側でメタデータ保存が有効な場合、EagleBridgeはComfyUIネイティブ `VIDEO.save_to()` にprompt / extra情報を渡します。実際にどのようにコンテナへ格納されるかは、ComfyUI本体・コンテナ形式・コーデック側の実装に依存します。

---

## トラブルシューティング

### Eagleのfolder IDが分からない

1. Eagleで保存したいフォルダを右クリックします。
2. **「リンクをコピー」** を選びます。
3. コピーされたリンクを確認します。たとえば：

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

4. `id=` の後ろにある `MU2LXTTH4KVRF` のような文字列だけを `eagle_folder_id` に貼り付けます。
5. `eagle_folder_id` を空欄にするとEagle Library Rootへ保存します。

### アップデートしたのに古いノード表示のまま

ComfyUIを完全終了して再起動し、ブラウザで `Ctrl+Shift+R` を行ってください。それでも変わらない場合はワークフロー上の古いノードを削除し、新しく追加し直してください。

### プレイヤーが表示されない

Audio / Videoの `preview` がONになっていることを確認します。アップデート直後なら、ComfyUI再起動とブラウザのハードリフレッシュも行ってください。

### ファイル名は違うのにEagleが重複と判定する

Eagleはファイル名ではなく、同じ内容のファイルを重複として検出する場合があります。テスト時はSeedなどを変えて別の内容を生成してください。

### Prompt / Modelが出ない

自動抽出はbest-effort（可能な範囲で探索）です。カスタムノード固有のフィールド名や特殊な接続構造では取得できない場合があります。

### MP3 / Opus / Videoのエンコードに失敗する

ComfyUI環境に入っているPyAV / FFmpeg / codecの対応状況を確認してください。形式やcodecを変更すると動作する場合があります。

### セキュリティ上の注意

この拡張はComfyUIバックエンドからローカルファイルを作成し、EagleのローカルAPIへファイルパスを送信します。ComfyUIをインターネットへ公開している場合、信頼できないユーザーにワークフロー実行権限を与えないよう注意してください。

## ライセンス

GNU General Public License v3.0。詳細は `LICENSE` を参照してください。

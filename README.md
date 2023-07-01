# プロトコル/Protocol


## メンバー登録

- サーバーの特定のポートに接続する。
- クライアントからサーバーに最初の接続。HELLOの後に半角スペースと自分の名前を付け加えて送信。
```commandline
HELLO <your name>
```
- サーバーはACCEPTと受け取った名前を返す。
```commandline
ACCEPT <your name>
```

- メンバー登録後、抜ける場合はBYEを送信する。
```commandline
BYE
```


## 試合開始

- 試合が開始する合図はサーバーから送信される。
- 細かい設定も送信する予定だが、現在はプレイヤー名のみ
```commandline
START-MATCH player1=雀士1,player2=雀士2,player3=雀士3,payer4=雀士4
```
- これを受け取った各クライアントは、サーバー基準で10秒以内に返答する必要がある。
```commandline
OK
```

## 局の開始

- 一局の始まりはサーバーから送信される
- ```START-GAME ```

```
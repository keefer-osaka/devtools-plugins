# protoc-java-gen

[English](README.md)

一個 Claude Code Plugin，使用指定版本的 protoc 從 `.proto` 檔案產生 Java 程式碼，並自動複製到所有對應的子專案。

## 功能

- 使用固定版本的 `protoc` 執行（不依賴系統 PATH）
- 自動偵測所有含有 `src/main/java/proto/<ClassName>.java` 的子專案
- 略過未變更的檔案（覆寫前先比對差異）
- 輸出摘要：更新了幾個子專案中的幾個檔案

## 安裝

```
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install protoc-java-gen@devtools-plugins
```

## 設定

```
/protoc-java-gen:setup
```

設定項目：
| 欄位 | 說明 |
|------|------|
| `PROTOC_PATH` | `protoc` 執行檔的完整路徑 |
| `PROJECT_ROOT` | 專案根目錄的絕對路徑 |
| `PROTO_DIR` | 相對於專案根目錄的 proto 子目錄（預設：`proto`）|
| `PLUGIN_LANG` | 輸出語言：`en` 或 `zh-TW`（預設：`en`）|

設定儲存於 `~/.config/devtools-plugins/protoc-java-gen/.env`。

## 使用方式

```
/protoc-java-gen:generate pay.proto
```

列出可用的 proto 檔案：

```
/protoc-java-gen:generate
```

## 運作原理

1. 從 `~/.config/devtools-plugins/protoc-java-gen/.env` 讀取設定
2. 從指定的 `.proto` 檔案讀取 `java_outer_classname`
3. 執行 `protoc --java_out`，將 Java 檔案產生至暫存目錄
4. 在 `PROJECT_ROOT` 中搜尋所有 `*/src/main/java/proto/<ClassName>.java`
5. 逐一比對差異 — 未變更則略過，有變更則覆寫
6. 印出摘要

## 系統需求

- macOS / Linux
- `protoc` 執行檔（任意版本，路徑透過 setup 設定）
- 專案結構：產生的 Java 檔案位於 `src/main/java/proto/`

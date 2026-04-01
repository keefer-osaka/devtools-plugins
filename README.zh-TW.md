# devtools-plugins

[English](README.md)

一套為開發者工作流程設計的 [Claude Code](https://claude.ai/code) Plugin 集合。

## Plugin 列表

| Plugin | 說明 |
|--------|------|
| [export-chat-logs](plugins/export-chat-logs/README.zh-TW.md) | 將 Claude Code 與 Cowork 的對話記錄匯出為 HTML 或 Markdown，壓縮後透過 Telegram 傳送 |
| [protoc-java-gen](plugins/protoc-java-gen/README.zh-TW.md) | 使用指定版本的 protoc 從 `.proto` 檔案產生 Java 程式碼，並自動複製到各子專案 |

## 安裝

將此 marketplace 加入 Claude Code：

```
/plugin marketplace add keefer-osaka/devtools-plugins
```

安裝個別 Plugin：

```
/plugin install export-chat-logs@devtools-plugins
/plugin install protoc-java-gen@devtools-plugins
```

## 授權

MIT

S = {
    # convert_to_markdown.py
    "truncated": "... *({n} characters omitted)*",
    "label_date": "Date",
    "label_project": "Project",
    "label_source": "Source",
    "source_name": "Claude Code",
    "source_name_cowork": "Claude Cowork",
    "label_model": "Model",
    "label_messages": "Messages",
    "no_messages": "*(no valid messages)*",
    "role_user": "User",
    "role_assistant": "Assistant",
    "msg_done_convert": "Done: {n} messages \u2192 {path}",

    # generate_stats.py - report header
    "report_title": "Claude Code Usage Report",
    "report_title_cowork": "Claude Cowork Usage Report",
    "label_period": "Period",
    "label_generated": "Generated",
    "label_sessions": "Sessions",

    # generate_stats.py - summary section
    "section_summary": "Summary",
    "col_item": "Item",
    "col_count": "Count",
    "row_input": "Input token",
    "row_output": "Output token",
    "row_cache_read": "Cache read",
    "row_cache_creation": "Cache creation",
    "row_total": "Total",
    "row_cache_hit_rate": "Cache hit rate",
    "summary_ratio": "Input {in_pct:.1f}% / Output {out_pct:.1f}%",

    # generate_stats.py - type distribution section
    "section_type_dist": "Conversation Type Distribution",
    "pie_type_sessions": "Type (Sessions)",
    "pie_tokens_by_cat": "Tokens by Category",
    "ascii_label": "ASCII version (plain text)",
    "ascii_session_dist": "**Session Distribution**",
    "ascii_token_dist": "**Token Usage Distribution**",

    # generate_stats.py - category breakdown section
    "section_cat_breakdown": "Category Breakdown",
    "col_category": "Category",
    "col_sessions": "Sessions",
    "col_input": "Input token",
    "col_output": "Output token",
    "col_total": "Total",
    "col_share": "Share",

    # generate_stats.py - session details section
    "section_session_details": "Session Details",
    "col_datetime": "Date/Time",
    "col_title": "Title",
    "col_model": "Model",
    "col_duration": "Duration",
    "untitled": "*(untitled)*",
    "no_sessions_found": "*(no sessions found)*",
    "skipped_sessions": "({n} trivial sessions skipped)",
    "msg_stats_done": "\u2705 Claude Code usage report: {sessions} sessions, total {tokens} tokens \u2192 {path}",
    "msg_stats_done_cowork": "\u2705 Claude Cowork usage report: {sessions} sessions, total {tokens} tokens \u2192 {path}",
    "warn_no_files": "\u26a0\ufe0f  No JSONL files found, writing empty report.",

    # generate_stats.py - tool usage section
    "section_tool_usage": "Tool Usage",
    "col_tool_name": "Tool",
    "col_tool_calls": "Calls",

    # generate_stats.py - project breakdown section
    "section_project_breakdown": "Project Breakdown",
    "col_project": "Project",

    # generate_stats.py - model usage section
    "section_model_usage": "Model Usage",

    # Category display labels (internal keys stay in English for keyword matching)
    "cat_Coding": "Coding",
    "cat_Debugging": "Debugging",
    "cat_Config": "Config",
    "cat_Docs": "Docs",
    "cat_Refactoring": "Refactoring",
    "cat_Other": "Other",
}
